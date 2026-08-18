"""Rutas web de Academia Horizonte."""

import os
import secrets
from datetime import timedelta
from functools import wraps
from urllib.parse import urlsplit

from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from libreria import calcular_resultados, leer_evaluaciones, leer_maestro
from usuarios import (
    actualizar_usuario,
    autenticar,
    buscar_usuario_por_id,
    cambiar_contrasena,
    crear_usuario,
    listar_usuarios,
    preparar_base_de_datos,
)


app = Flask(__name__, template_folder="plantillas", static_folder="static")
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY"),
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("VERCEL") == "1",
)

if not app.config["SECRET_KEY"]:
    raise RuntimeError("Falta configurar la variable de entorno SECRET_KEY.")


def preparar_datos():
    """Une la lectura de los Excel con los cálculos de libreria.py."""
    estudiantes = leer_maestro()
    registros = leer_evaluaciones()
    return calcular_resultados(estudiantes, registros)


def armar_inconsistencias(resultados, sin_notas, sin_maestro):
    inconsistencias = []
    for estudiante in sin_notas:
        inconsistencias.append({
            "cedula": estudiante["identificacion"],
            "nombre": estudiante["nombre"],
            "detalle": "Estudiante del maestro sin ninguna evaluación.",
        })
    for estudiante in sin_maestro:
        inconsistencias.append({
            "cedula": estudiante["identificacion"],
            "nombre": "(no registrado en el maestro)",
            "detalle": (
                f"Identificación con {estudiante['modulos']} módulo(s) en "
                "evaluaciones pero sin registro en el maestro."
            ),
        })
    for resultado in resultados:
        if resultado["tipo"] == "SIN_CERTIFICADO" and resultado["modulos"] > 0:
            inconsistencias.append({
                "cedula": resultado["identificacion"],
                "nombre": resultado["nombre"],
                "detalle": "No certifica porque la asistencia es menor al 80%.",
            })
    return inconsistencias


def login_requerido(funcion):
    @wraps(funcion)
    def protegida(*args, **kwargs):
        if g.usuario is None:
            return redirect(url_for("iniciar_sesion", siguiente=request.full_path))
        return funcion(*args, **kwargs)

    return protegida


def administrador_requerido(funcion):
    @wraps(funcion)
    def protegida(*args, **kwargs):
        if g.usuario is None:
            return redirect(url_for("iniciar_sesion"))
        if g.usuario["rol"] != "administrador":
            abort(403)
        return funcion(*args, **kwargs)

    return protegida


def _csrf_valido():
    recibido = request.form.get("csrf_token", "")
    esperado = session.get("csrf_token", "")
    return bool(recibido and esperado and secrets.compare_digest(recibido, esperado))


def _destino_local(destino):
    """Impide redirecciones hacia sitios externos después de iniciar sesión."""
    partes = urlsplit(destino or "")
    return destino if not partes.scheme and not partes.netloc else ""


@app.before_request
def cargar_usuario_y_proteger_formularios():
    """Carga el usuario real desde PostgreSQL y valida todos los formularios POST."""
    g.usuario = None
    usuario_id = session.get("usuario_id")
    if usuario_id:
        usuario = buscar_usuario_por_id(usuario_id)
        if usuario and usuario["activo"]:
            g.usuario = usuario
        else:
            session.clear()

    if request.method == "POST" and not _csrf_valido():
        abort(400, description="El formulario venció. Recargue la página e intente de nuevo.")


@app.context_processor
def variables_comunes():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return {"usuario_actual": g.usuario, "csrf_token": session["csrf_token"]}


@app.after_request
def agregar_cabeceras_seguras(respuesta):
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["X-Frame-Options"] = "DENY"
    respuesta.headers["Referrer-Policy"] = "same-origin"
    respuesta.headers["Content-Security-Policy"] = (
        "default-src 'self'; frame-ancestors 'none'; form-action 'self'"
    )
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


@app.route("/iniciar-sesion", methods=["GET", "POST"])
def iniciar_sesion():
    if g.usuario:
        return redirect(url_for("index"))
    error_configuracion = None
    if request.method == "POST":
        try:
            preparar_base_de_datos()
            usuario = autenticar(
                request.form.get("correo", ""),
                request.form.get("contrasena", ""),
            )
        except (RuntimeError, ValueError) as error:
            usuario = None
            error_configuracion = str(error)
        if usuario:
            destino = _destino_local(request.form.get("siguiente"))
            session.clear()
            session["usuario_id"] = usuario["id"]
            session["csrf_token"] = secrets.token_urlsafe(32)
            session.permanent = True
            return redirect(destino or url_for("index"))
        if not error_configuracion:
            flash("Correo o contraseña incorrectos.", "error")
    return render_template(
        "login.html",
        error_configuracion=error_configuracion,
        siguiente=_destino_local(request.args.get("siguiente") or request.form.get("siguiente")),
    )


@app.post("/cerrar-sesion")
@login_requerido
def cerrar_sesion():
    session.clear()
    return redirect(url_for("iniciar_sesion"))


@app.route("/mi-contrasena", methods=["GET", "POST"])
@login_requerido
def mi_contrasena():
    if request.method == "POST":
        try:
            cambiar_contrasena(
                g.usuario["id"],
                request.form.get("contrasena_actual", ""),
                request.form.get("nueva_contrasena", ""),
            )
            flash("Su contraseña fue actualizada correctamente.", "exito")
            return redirect(url_for("index"))
        except ValueError as error:
            flash(str(error), "error")
    return render_template("mi_contrasena.html")


@app.route("/")
@login_requerido
def index():
    resultados, sin_notas, sin_maestro = preparar_datos()
    conteos = {
        "aprobacion": sum(1 for r in resultados if r["tipo"] == "APROBACION"),
        "participacion": sum(1 for r in resultados if r["tipo"] == "PARTICIPACION"),
        "sin_certificado": sum(
            1 for r in resultados
            if r["tipo"] == "SIN_CERTIFICADO" and r["modulos"] > 0
        ),
    }
    programas = sorted({r["programa"] for r in resultados})
    filtro = request.args.get("programa", "")
    tabla = [r for r in resultados if not filtro or r["programa"] == filtro]
    tabla.sort(key=lambda r: (r["programa"], r["nombre"]))
    return render_template(
        "index.html",
        **conteos,
        total_estudiantes=len(resultados),
        programas=programas,
        filtro=filtro,
        tabla=tabla,
        inconsistencias=armar_inconsistencias(resultados, sin_notas, sin_maestro),
    )


@app.route("/administracion/usuarios", methods=["GET", "POST"])
@administrador_requerido
def administrar_usuarios():
    if request.method == "POST":
        try:
            crear_usuario(
                request.form.get("correo", ""),
                request.form.get("contrasena", ""),
                request.form.get("rol", "normal"),
            )
            flash("Usuario creado correctamente.", "exito")
            return redirect(url_for("administrar_usuarios"))
        except ValueError as error:
            flash(str(error), "error")
    return render_template("usuarios.html", usuarios=listar_usuarios())


@app.post("/administracion/usuarios/<int:usuario_id>/editar")
@administrador_requerido
def editar_usuario(usuario_id):
    if usuario_id == g.usuario["id"]:
        flash("Cambie su propia clave desde la opción Mi contraseña.", "error")
        return redirect(url_for("administrar_usuarios"))
    try:
        actualizar_usuario(
            usuario_id,
            request.form.get("rol", "normal"),
            request.form.get("activo") == "1",
            request.form.get("nueva_contrasena", ""),
        )
        flash("Usuario actualizado correctamente.", "exito")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("administrar_usuarios"))


@app.route("/api/resumen")
@login_requerido
def api_resumen():
    resultados, _sin_notas, _sin_maestro = preparar_datos()
    return jsonify({
        "aprobacion": sum(1 for r in resultados if r["tipo"] == "APROBACION"),
        "participacion": sum(1 for r in resultados if r["tipo"] == "PARTICIPACION"),
        "sin_certificado": sum(
            1 for r in resultados
            if r["tipo"] == "SIN_CERTIFICADO" and r["modulos"] > 0
        ),
        "total_estudiantes": len(resultados),
    })


@app.errorhandler(403)
def acceso_denegado(_error):
    return render_template("error.html", titulo="Acceso denegado", mensaje="Su usuario no tiene permiso para entrar aquí."), 403


@app.errorhandler(400)
def solicitud_invalida(error):
    return render_template("error.html", titulo="Solicitud inválida", mensaje=error.description), 400


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", host="127.0.0.1", port=5000)

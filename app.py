# app.py — COCINA: orquesta las rutas de la aplicación web con Flask.
# Reutiliza la lógica validada de libreria.py (lectura, cruce y cálculo).
# Aquí NUNCA se escribe lógica de negocio: solo se preparan los datos
# para que las plantillas (el Salón) los muestren.

# LADRILLO 1: LIBRERÍAS (Flask para el servidor web)
from flask import Flask, render_template, request, jsonify

# LADRILLO 2: importamos las funciones de la biblioteca ya validada
from libreria import (
    leer_maestro,           # lee el Excel de estudiantes
    leer_evaluaciones,      # lee el Excel de notas
    calcular_resultados,    # cruza y calcula promedios y tipos
)

# Creamos la aplicación Flask indicando las carpetas del Salón
app = Flask(__name__, template_folder="plantillas", static_folder="static")


# ---------------------------------------------------------------------------
# LADRILLO 3: FUNCIÓN preparar_datos
# ---------------------------------------------------------------------------
def preparar_datos():
    """Lee los dos Excel y devuelve resultados + listas de inconsistencias.

    Esta función es el 'puente' entre la Bodega (Excel) y el Salón (HTML).
    Los tipos que devuelve:
        resultados   -> LISTA de dicts (una por estudiante del maestro)
        sin_notas    -> LISTA (estudiantes del maestro sin evaluaciones)
        sin_maestro  -> LISTA (evaluaciones sin estudiante en el maestro)
    """
    estudiantes = leer_maestro()      # BUCLE implícito dentro de la función
    registros = leer_evaluaciones()
    resultados, sin_notas, sin_maestro = calcular_resultados(estudiantes, registros)
    return resultados, sin_notas, sin_maestro


# ---------------------------------------------------------------------------
# LADRILLO 4: FUNCIÓN armar_inconsistencias
# ---------------------------------------------------------------------------
def armar_inconsistencias(resultados, sin_notas, sin_maestro):
    """Une todas las inconsistencias detectadas en una LISTA de DICCIONARIOS
    lista para mostrar en el Salón. Cada una tiene 'cedula', 'nombre'
    y 'detalle' (texto explicativo).
    """
    inconsistencias = []  # VARIABLE de tipo LISTA

    # LADRILLO 5: BUCLE sobre estudiantes del maestro que no tienen notas
    for s in sin_notas:
        inconsistencias.append({
            "cedula": s["identificacion"],
            "nombre": s["nombre"],
            "detalle": "Estudiante del maestro sin ninguna evaluación.",
        })

    # LADRILLO 6: BUCLE sobre evaluaciones que no existen en el maestro
    for s in sin_maestro:
        inconsistencias.append({
            "cedula": s["identificacion"],
            "nombre": "(no registrado en el maestro)",
            "detalle": (f"Identificación con {s['modulos']} módulo(s) en "
                        "evaluaciones pero sin registro en el maestro."),
        })

    # LADRILLO 7: BUCLE que detecta notas 0 / asistencia muy baja (posible abandono)
    for r in resultados:
        # CONDICIONAL: solo estudiantes que SÍ cursaron módulos pero no aprobaron
        if r["tipo"] == "SIN_CERTIFICADO" and r["modulos"] > 0:
            inconsistencias.append({
                "cedula": r["identificacion"],
                "nombre": r["nombre"],
                "detalle": ("No certifica (asistencia y/o promedio bajos); "
                            "revisar módulos con nota 0."),
            })

    return inconsistencias


# ---------------------------------------------------------------------------
# LADRILLO 8: RUTA PRINCIPAL (el Salón completo)
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """Página principal: contadores, filtro por programa, tabla y
    sección de inconsistencias.
    """
    resultados, sin_notas, sin_maestro = preparar_datos()

    # --- CONTADORES (regla: el 'sin certificado' cuenta solo a quien cursó) ---
    conteo_aprobacion = 0
    conteo_participacion = 0
    conteo_sin_certificado = 0
    # LADRILLO 9: BUCLE que recorre todos los resultados para contar
    for r in resultados:
        if r["tipo"] == "APROBACION":
            conteo_aprobacion += 1
        elif r["tipo"] == "PARTICIPACION":
            conteo_participacion += 1
        elif r["tipo"] == "SIN_CERTIFICADO" and r["modulos"] > 0:
            conteo_sin_certificado += 1  # solo quien cursó y no certificó

    # --- LISTA de programas para el filtro (sin repetidos) ---
    programas = []  # VARIABLE de tipo LISTA
    # LADRILLO 10: BUCLE para juntar los nombres únicos de programa
    for r in resultados:
        if r["programa"] not in programas:
            programas.append(r["programa"])
    programas.sort()  # ordenamos A-Z

    # --- FILTRO por programa (llega por la URL, ej: ?programa=Tecnico) ---
    filtro = request.args.get("programa", "")  # VARIABLE TEXTO de la consulta
    tabla = []  # lista que se mostrará en la tabla
    # LADRILLO 11: BUCLE que filtra los resultados según el programa elegido
    for r in resultados:
        # CONDICIONAL: si no hay filtro, entran todos
        if filtro == "" or r["programa"] == filtro:
            tabla.append(r)

    # --- Ordenamos la tabla por programa y nombre ---
    def clave_orden(r):
        return (r["programa"], r["nombre"])

    tabla_ordenada = sorted(tabla, key=clave_orden)

    # --- Inconsistencias (las 3 detectadas) ---
    inconsistencias = armar_inconsistencias(resultados, sin_notas, sin_maestro)

    return render_template(
        "index.html",
        aprobacion=conteo_aprobacion,
        participacion=conteo_participacion,
        sin_certificado=conteo_sin_certificado,
        total_estudiantes=len(resultados),
        programas=programas,
        filtro=filtro,
        tabla=tabla_ordenada,
        inconsistencias=inconsistencias,
    )


# ---------------------------------------------------------------------------
# LADRILLO 12: RUTA API de resumen (útil para validar con curl)
# ---------------------------------------------------------------------------
@app.route("/api/resumen")
def api_resumen():
    """Devuelve los contadores en formato JSON para validación rápida."""
    resultados, sin_notas, sin_maestro = preparar_datos()
    aprobacion = sum(1 for r in resultados if r["tipo"] == "APROBACION")
    participacion = sum(1 for r in resultados if r["tipo"] == "PARTICIPACION")
    sin_certificado = sum(
        1 for r in resultados
        if r["tipo"] == "SIN_CERTIFICADO" and r["modulos"] > 0
    )
    return jsonify({
        "aprobacion": aprobacion,
        "participacion": participacion,
        "sin_certificado": sin_certificado,
        "total_estudiantes": len(resultados),
    })


# ---------------------------------------------------------------------------
# LADRILLO 13: INICIO del programa (solo si ejecutas este archivo)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # arranca el servidor en http://localhost:5000
    app.run(debug=True, host="127.0.0.1", port=5000)

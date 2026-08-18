"""Persistencia de usuarios y contraseñas en PostgreSQL.

Las contraseñas nunca se guardan directamente: Werkzeug genera un hash seguro.
"""

import os

import psycopg
from psycopg.rows import dict_row
from werkzeug.security import check_password_hash, generate_password_hash


def _conexion():
    """Abre una conexión usando el secreto DATABASE_URL de Vercel."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("Falta configurar la variable de entorno DATABASE_URL.")
    return psycopg.connect(url, row_factory=dict_row)


def preparar_base_de_datos():
    """Crea la tabla y el primer administrador si todavía no existen."""
    with _conexion() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS usuarios (
                    id BIGSERIAL PRIMARY KEY,
                    correo VARCHAR(254) NOT NULL UNIQUE,
                    contrasena_hash TEXT NOT NULL,
                    rol VARCHAR(20) NOT NULL CHECK (rol IN ('administrador', 'normal')),
                    activo BOOLEAN NOT NULL DEFAULT TRUE,
                    creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            # Evita que dos funciones nuevas intenten crear al primer usuario a la vez.
            cursor.execute("LOCK TABLE usuarios IN EXCLUSIVE MODE")
            cursor.execute("SELECT COUNT(*) AS total FROM usuarios")
            if cursor.fetchone()["total"] == 0:
                correo = os.environ.get("ADMIN_EMAIL", "").strip().lower()
                contrasena = os.environ.get("ADMIN_PASSWORD", "")
                if not correo or not contrasena:
                    raise RuntimeError(
                        "La base está vacía. Configure ADMIN_EMAIL y ADMIN_PASSWORD."
                    )
                _validar_contrasena(contrasena)
                cursor.execute(
                    """
                    INSERT INTO usuarios (correo, contrasena_hash, rol)
                    VALUES (%s, %s, 'administrador')
                    """,
                    (correo, generate_password_hash(contrasena)),
                )


def _validar_contrasena(contrasena):
    if len(contrasena) < 12:
        raise ValueError("La contraseña debe tener al menos 12 caracteres.")


def buscar_usuario_por_id(usuario_id):
    with _conexion() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT id, correo, rol, activo, creado_en FROM usuarios WHERE id = %s",
                (usuario_id,),
            )
            return cursor.fetchone()


def autenticar(correo, contrasena):
    """Devuelve un usuario activo únicamente si la contraseña coincide."""
    with _conexion() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, correo, contrasena_hash, rol, activo
                FROM usuarios WHERE correo = %s
                """,
                (correo.strip().lower(),),
            )
            usuario = cursor.fetchone()
    if not usuario or not usuario["activo"]:
        return None
    if not check_password_hash(usuario["contrasena_hash"], contrasena):
        return None
    usuario.pop("contrasena_hash")
    return usuario


def listar_usuarios():
    with _conexion() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, correo, rol, activo, creado_en
                FROM usuarios ORDER BY correo
                """
            )
            return cursor.fetchall()


def crear_usuario(correo, contrasena, rol):
    correo = correo.strip().lower()
    if not correo or "@" not in correo:
        raise ValueError("Escriba un correo válido.")
    if rol not in ("administrador", "normal"):
        raise ValueError("El rol indicado no es válido.")
    _validar_contrasena(contrasena)
    try:
        with _conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO usuarios (correo, contrasena_hash, rol)
                    VALUES (%s, %s, %s)
                    """,
                    (correo, generate_password_hash(contrasena), rol),
                )
    except psycopg.errors.UniqueViolation as error:
        raise ValueError("Ya existe un usuario con ese correo.") from error


def cambiar_contrasena(usuario_id, contrasena_actual, nueva_contrasena):
    """Permite cambiar la clave propia después de comprobar la clave actual."""
    _validar_contrasena(nueva_contrasena)
    with _conexion() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT contrasena_hash FROM usuarios WHERE id = %s AND activo = TRUE",
                (usuario_id,),
            )
            usuario = cursor.fetchone()
            if not usuario or not check_password_hash(
                usuario["contrasena_hash"], contrasena_actual
            ):
                raise ValueError("La contraseña actual no es correcta.")
            cursor.execute(
                "UPDATE usuarios SET contrasena_hash = %s WHERE id = %s",
                (generate_password_hash(nueva_contrasena), usuario_id),
            )


def actualizar_usuario(usuario_id, rol, activo, nueva_contrasena=""):
    """Actualiza permisos y, si se indicó, reemplaza la contraseña."""
    if rol not in ("administrador", "normal"):
        raise ValueError("El rol indicado no es válido.")
    with _conexion() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT rol, activo FROM usuarios WHERE id = %s FOR UPDATE",
                (usuario_id,),
            )
            actual = cursor.fetchone()
            if not actual:
                raise ValueError("El usuario ya no existe.")

            pierde_administrador = (
                actual["rol"] == "administrador"
                and actual["activo"]
                and (rol != "administrador" or not activo)
            )
            if pierde_administrador:
                cursor.execute(
                    """
                    SELECT COUNT(*) AS total FROM usuarios
                    WHERE rol = 'administrador' AND activo = TRUE
                    """
                )
                if cursor.fetchone()["total"] <= 1:
                    raise ValueError("Debe quedar al menos un administrador activo.")

            if nueva_contrasena:
                _validar_contrasena(nueva_contrasena)
                cursor.execute(
                    """
                    UPDATE usuarios
                    SET rol = %s, activo = %s, contrasena_hash = %s
                    WHERE id = %s
                    """,
                    (
                        rol,
                        activo,
                        generate_password_hash(nueva_contrasena),
                        usuario_id,
                    ),
                )
            else:
                cursor.execute(
                    "UPDATE usuarios SET rol = %s, activo = %s WHERE id = %s",
                    (rol, activo, usuario_id),
                )

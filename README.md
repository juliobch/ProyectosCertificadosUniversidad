# Sistema de certificados de Academia Horizonte

Aplicación privada en Flask para consultar los resultados calculados desde los
Excel de `Insumos/`. Los archivos originales se leen, pero nunca se modifican.

## Acceso y roles

- Todo el panel y `/api/resumen` exigen iniciar sesión.
- Un usuario `normal` consulta el panel académico.
- Un `administrador` también entra a **Usuarios**, donde crea cuentas, cambia
  contraseñas y asigna, activa o desactiva roles.
- Cada persona puede cambiar su propia clave desde **Mi contraseña**, después de
  confirmar la contraseña actual.
- Ocultar el enlace en HTML no da seguridad: cada ruta administrativa vuelve a
  comprobar el rol en Flask.
- Las contraseñas se guardan como hashes en PostgreSQL; no pueden recuperarse
  como texto. Si se olvidan, un administrador define una nueva.

## Variables de entorno

Estas variables se configuran en Vercel, en **Project Settings > Environment
Variables**. No deben escribirse en archivos que se suban a GitHub.

| Variable | Uso |
| --- | --- |
| `SECRET_KEY` | Firma las cookies de sesión. Use un valor aleatorio largo. |
| `DATABASE_URL` | Conexión PostgreSQL externa, por ejemplo Neon o Vercel Postgres. |
| `ADMIN_EMAIL` | Correo del primer administrador cuando la tabla está vacía. |
| `ADMIN_PASSWORD` | Contraseña inicial, con 12 caracteres como mínimo. |

Para generar `SECRET_KEY` localmente:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

En local se pueden colocar valores privados en un archivo `.env`, que está
ignorado por Git, y cargarlos en la terminal. Flask no lee `.env` por sí solo
con las dependencias actuales.

## Primer inicio

1. Cree una base PostgreSQL y copie su URL segura en `DATABASE_URL`.
2. Configure las cuatro variables anteriores en Vercel para Producción, Preview
   y Desarrollo según corresponda.
3. Despliegue y abra `/iniciar-sesion`.
4. En el primer intento de acceso se crea la tabla y la cuenta indicada por
   `ADMIN_EMAIL`. Después puede quitar `ADMIN_PASSWORD` de Vercel: ya no se usa
   mientras exista al menos un usuario.
5. Entre como administrador y cree las cuentas normales desde **Usuarios**.

## Instalación local

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Después de exportar las variables, inicie con:

```bash
python3 -m flask --app app run
```

## Archivos subidos en Vercel

Vercel ejecuta funciones sin un disco persistente. El código desplegado y los
Excel incluidos en `Insumos/` son de solo lectura. `/tmp` permite archivos
temporales durante una ejecución, pero pueden desaparecer inmediatamente y no
se comparten de forma confiable entre solicitudes.

Por eso, una futura pantalla de carga debe enviar el archivo a almacenamiento
externo persistente, como Vercel Blob, Amazon S3 o un servicio equivalente, y
guardar en PostgreSQL solamente su URL y metadatos. No se debe guardar una carga
en `Insumos/`, en `salidas/` ni en otra carpeta local esperando encontrarla en
la siguiente petición. La app actual no ofrece carga de archivos y sigue usando
los Excel incluidos en el despliegue.

# AGENTS.md

Respond always in Spanish.

## Contexto del proyecto

Somos Academia Horizonte, un centro de formación que imparte programas técnicos a empresas. Al cerrar cada cohorte emitimos certificados por estudiante. Hoy el proceso es manual en Excel y Word; vamos a automatizarlo como una APLICACIÓN WEB.

## Arquitectura (3 piezas)

- **Bodega (datos):** los Excel en `Insumos/`. NO se modifican.
- **Cocina (backend):** Python con Flask, en `app.py`. Toda la lógica va aquí, NUNCA en la interfaz.
- **Salón (frontend):** páginas web HTML servidas por Flask. Solo muestra información; no calcula ni decide.

## Archivos de entrada

- `Insumos/Maestro_Estudiantes.xlsx`: lista oficial de estudiantes (Identificacion, Nombre_Completo, Correo, Programa, Cohorte).
- `Insumos/Registro_Evaluaciones.xlsx`: notas (0-100) y asistencia por módulo (Identificacion, Programa, Modulo, Nota, Asistencia_Pct, Fecha_Cierre).

Son archivos binarios `.xlsx`; nunca editar en su lugar como texto. Cualquier código/script debe leerlos sin modificar.

## Reglas de negocio

- Promedio = suma de Notas / cantidad de módulos cursados.
- Asistencia = promedio de Asistencia_Pct.
- Se agrupa por Identificacion + Programa. Un certificado por estudiante y programa.
- Aprobación si Promedio >= 70 y Asistencia >= 80.
- Participación si Promedio < 70 y Asistencia >= 80.
- Sin certificado si Asistencia < 80.
- Los límites INCLUYEN el valor.

## Estilo de trabajo

- Código simple y comentado en español, señalando dónde están los ladrillos: variables, tipos, condicionales, bucles y funciones.
- Diseño web en azul marino y dorado.
- Explícame en español sencillo lo que vayas haciendo.

## Decisiones técnicas

- Librerías: **Flask** (servidor web, con Jinja2) y **openpyxl** (lectura de `.xlsx`). Instalar con `pip install flask openpyxl`.
- La lógica de negocio vive en `libreria.py` (leer Excel, normalizar, cruzar, calcular). `app.py` solo orquesta rutas; las plantillas NUNCA calculan.
- Estructura del proyecto:
  - `app.py` — rutas Flask
  - `libreria.py` — lectura, cruce y cálculo
  - `plantillas/` — HTML con Jinja2 (index, resultado, panel)
  - `static/` — CSS (azul marino y dorado)
  - `salidas/` — certificados/archivos generados (FUERA de `Insumos/`)
  - `validar_datos.py` — script de validación del cruce (Etapa 1)
- Normalizar datos al leer: cédulas y notas pasan de texto a `int`/`float`; nombres/programas se limpian de acentos y espacios para que el cruce coincida.
- El plan detallado por etapas está en `PLAN.md`.

## Notas

- Hoy no hay build system ni tests; la validación se hace con scripts y `curl` (ver `PLAN.md`).
- Si se agrega código/scripts, colocar salidas y archivos generados fuera de `Insumos/` para no tocar los datos crudos.

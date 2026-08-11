# PLAN.md — Aplicación de Certificados (Academia Horizonte)

Plan de implementación por etapas. Estamos en modo Plan: todavía NO se escribe código.

## Etapa 1 — Validación del cruce de datos

**Objetivo:** asegurarse de que los dos Excel se leen bien y que el cruce por
`(Identificacion, Programa)` es correcto ANTES de tocar el servidor.

### Qué se hace
- Crear `libreria.py` (o `datos.py`) con una función que lea `Insumos/Maestro_Estudiantes.xlsx`
  y `Insumos/Registro_Evaluaciones.xlsx` usando **openpyxl**, sin modificar los archivos.
- Normalizar los datos al leerlos:
  - cédulas y notas pasan de texto a `int`/`float`;
  - nombres y programas se limpian de espacios y acentos inconsistentes
    (p. ej. entidades HTML/acentos) para que el cruce coincida.
- Función que cruza ambos archivos y reporta:
  - estudiantes del maestro sin notas (p. ej. `304560321`);
  - registros de evaluaciones que no existen en el maestro (p. ej. `999880777`);
  - duplicados de `(Identificacion, Programa, Modulo)`.
- Función de cálculo según reglas de AGENTS.md (Promedio, Asistencia, Aprobación,
  Participación, Sin certificado). Los límites INCLUYEN el valor (`>= 70`, `>= 80`).

### Cómo validamos
- Script `validar_datos.py` que imprime un resumen (contador de estudiantes,
  contador de registros, casos borde) y lo comparamos contra lo verificado hoy:
  24 estudiantes, 88 filas de notas, 22 certificados (19 Aprobación, 3 Participación).
- Validación manual: que la lista de casos borde coincida con el análisis anterior.

## Etapa 2 — Backend con Flask

**Objetivo:** exponer la lógica vía HTTP SIN interfaz bonita todavía.

### Qué se hace
- Crear `app.py` con Flask.
- Rutas mínimas:
  - `GET /` — página simple que muestra el resumen de la cohorte (JSON/HTML básico);
  - `GET /estudiante/<cedula>` — estado de un estudiante (promedio, asistencia, tipo);
  - `GET /api/resumen` — JSON con conteos por programa y tipo de certificado.
- Toda la lógica de negocio vive en `libreria.py`; `app.py` solo orquesta rutas.
  NUNCA calcular en la plantilla.

### Cómo validamos
- `flask --app app run` en local y probar con `curl`:
  - `curl localhost:5000/api/resumen` → esperamos 19 Aprobación / 3 Participación;
  - `curl localhost:5000/estudiante/999880777` → esperamos "no existe en maestro";
  - `curl localhost:5000/estudiante/304560321` → esperamos "sin notas".
- Verificar que `Insumos/` no cambió (los archivos se leen, nunca se escriben).

## Etapa 3 — Interfaz (Salón)

**Objetivo:** presentar la información con diseño azul marino y dorado.

### Qué se hace
- Plantillas HTML con Jinja2 en `plantillas/`:
  - `index.html` — buscador por cédula;
  - `resultado.html` — estado del estudiante;
  - `panel.html` — resumen de la cohorte (tablas por programa).
- CSS en `static/` con colores azul marino y dorado.
- Las plantillas SOLO muestran; no calculan ni deciden nada.

### Cómo validamos
- Revisión visual en el navegador (colores y legibilidad).
- Probar el flujo completo: buscar cédula, ver estado, volver al buscador.
- Verificar que un estudiante Aprobado, uno de Participación y uno sin
  certificado se muestran correctamente.

## Etapa 4 — Generación de certificados (opcional, después de validar lo anterior)

**Objetivo:** emitir los certificados en PDF a partir de una plantilla.

### Qué se hace
- Generar certificados solo para los estudiantes con Aprobación o Participación.
- Salidas en `salidas/` (FUERA de `Insumos/`).

### Cómo validamos
- Que salgan exactamente 22 certificados (19 Aprobación + 3 Participación).
- Abrir un par de PDFs y verificar datos del estudiante.

## Notas de trabajo
- Comandos a instalar: `pip install flask openpyxl`.
- En cada etapa: revisar que `Insumos/` permanezca intacto.
- Responder y documentar siempre en español.

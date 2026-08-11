# validar_datos.py — ETAPA 1: valida el cruce de datos y muestra el resumen.
# Este script usa las funciones de libreria.py (la COCINA) y solo MUESTRA,
# igual que hará la interfaz web en la Etapa 3.

# LADRILLO 1: LIBRERÍAS
from libreria import (
    leer_maestro,           # función para leer el Excel de estudiantes
    leer_evaluaciones,      # función para leer el Excel de notas
    calcular_resultados,    # función que cruza y calcula
    resumen_datos,          # función que arma el resumen
)


# LADRILLO 2: FUNCIÓN que imprime una tabla de resultados
def mostrar_tabla(resultados):
    """Recibe la lista de resultados y la imprime ordenada por programa y nombre."""
    # LADRILLO 3: FUNCIÓN interna de ordenamiento (clave = programa, luego nombre)
    def clave_orden(r):
        return (r["programa"], r["nombre"])

    ordenados = sorted(resultados, key=clave_orden)  # BUCLE implícito de sort

    # Encabezado de la tabla
    print(f"{'Cedula':<11} {'Nombre':<26} {'Programa':<28} {'Mod':>3} "
          f"{'Prom':>6} {'Asist':>6}  {'Tipo'}")

    # LADRILLO 4: BUCLE (for) que imprime fila por fila
    for r in ordenados:
        print(f"{r['identificacion']:<11} {r['nombre']:<26} {r['programa']:<28} "
              f"{r['modulos']:>3} {r['promedio']:>6.2f} {r['asistencia']:>6.2f}  "
              f"{r['tipo']}")


# LADRILLO 5: INICIO del programa (se ejecuta al correr el script)
if __name__ == "__main__":
    # LADRILLO 6: llamamos a las funciones de lectura (Bodega -> Cocina)
    estudiantes = leer_maestro()
    registros = leer_evaluaciones()

    # LADRILLO 7: llamamos a la función de resumen y mostramos cada dato
    resumen = resumen_datos(estudiantes, registros)
    print("=" * 90)
    print("RESUMEN DE DATOS")
    print("=" * 90)
    print(f"Estudiantes en el maestro: {resumen['total_estudiantes']}")
    print(f"Filas de evaluaciones:     {resumen['total_registros']}")
    print("Estudiantes por programa:")
    for programa, cantidad in resumen["por_programa"].items():
        print(f"  - {programa}: {cantidad}")
    print(f"Módulos existentes: {', '.join(resumen['modulos'])}")
    print(f"Rango de notas: {resumen['notas_min']} - {resumen['notas_max']}")

    # LADRILLO 8: llamamos a la función que cruza y calcula (el corazón)
    resultados, sin_notas, sin_maestro = calcular_resultados(estudiantes, registros)

    # LADRILLO 9: tabla completa
    print()
    print("=" * 90)
    print("TABLA DE CERTIFICADOS (ordenada por programa y nombre)")
    print("=" * 90)
    mostrar_tabla(resultados)

    # LADRILLO 10: conteo por tipo de certificado
    conteos = {}  # DICCIONARIO contador
    for r in resultados:
        tipo = r["tipo"]
        if tipo not in conteos:
            conteos[tipo] = 0  # CONDICIONAL: primera vez que vemos este tipo
        conteos[tipo] += 1
    print()
    print("Conteo por tipo de certificado:")
    for tipo, cantidad in sorted(conteos.items()):
        print(f"  - {tipo}: {cantidad}")
    print(f"  - TOTAL certificados emitidos (Aprobacion + Participacion): "
          f"{conteos.get('APROBACION', 0) + conteos.get('PARTICIPACION', 0)}")

    # LADRILLO 11: inconsistencias
    print()
    print("=" * 90)
    print("INCONSISTENCIAS")
    print("=" * 90)
    print("Estudiantes del maestro SIN ninguna evaluación:")
    if sin_notas:
        for s in sin_notas:
            print(f"  - {s['identificacion']} {s['nombre']} ({s['programa']})")
    else:
        print("  (ninguno)")
    print("Identificaciones en evaluaciones que NO están en el maestro:")
    if sin_maestro:
        for s in sin_maestro:
            print(f"  - {s['identificacion']} ({s['programa']}), "
                  f"{s['modulos']} módulo(s) registrado(s)")
    else:
        print("  (ninguno)")

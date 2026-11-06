# -*- coding: utf-8 -*-

"""
Extraccion de capacidades termicas de lineas.

PowerFactory 2025 SP4.
Ejecutar dentro de PowerFactory desde un ComPython.

External Object:
    Lineas

El SetSelect puede contener shortcuts a ElmLne o a conjuntos/branches
que contengan ElmLne.

No activa Study Cases, no cambia triggers y no modifica caracteristicas.

Modelos soportados:
1) ElmLne.typ_id -> TypLne -> sline.ChaRef -> ChaMat
2) ElmLne.typ_id -> TypTow -> pcond_c -> TypCon -> sline.ChaRef -> ChaMat
3) ElmLne.c_ptow -> ElmTow -> pGeo -> TypTow -> pcond_c -> TypCon
                                      -> sline.ChaRef -> ChaMat

ChaMat:
    scalecol -> TriDisc.cases
    scalerow -> TriDisc.cases
    matrix   -> matriz 2D de corrientes [kA]
"""

import csv
import datetime
import json
import math
import os

import powerfactory as pf


# =====================================================================
# CONFIGURACION
# =====================================================================

NOMBRE_SET = "Lineas"

CARPETA_SALIDA = os.path.expanduser("~")

CSV_PATH = os.path.join(
    CARPETA_SALIDA,
    "capacidades_termicas.csv"
)

JSON_PATH = os.path.join(
    CARPETA_SALIDA,
    "capacidades_termicas.json"
)

EXPORTAR_CSV = True
EXPORTAR_JSON = True
EXPORTAR_CEROS = True

RAIZ3 = 3 ** 0.5


# =====================================================================
# ARRANQUE
# =====================================================================

app = pf.GetApplication()

if app is None:
    raise RuntimeError("No hay aplicacion de PowerFactory")


def info(m):
    app.PrintPlain(str(m))


def warn(m):
    app.PrintWarn(str(m))


def err(m):
    app.PrintError(str(m))


# =====================================================================
# UTILERIA
# =====================================================================

def clase(obj):
    if obj is None:
        return ""
    try:
        return obj.GetClassName()
    except Exception:
        return ""


def nombre(obj):
    if obj is None:
        return ""
    try:
        return str(obj.loc_name)
    except Exception:
        return ""


def ruta_de(obj):
    if obj is None:
        return ""
    try:
        return obj.GetFullName()
    except Exception:
        return nombre(obj)


def get_attr(obj, atributo, default=None):
    if obj is None:
        return default
    try:
        value = obj.GetAttribute(atributo)
    except Exception:
        return default
    return default if value is None else value


def como_lista(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def solo_objetos_pf(values):
    salida = []
    for value in como_lista(values):
        if value is None:
            continue
        try:
            value.GetClassName()
        except Exception:
            continue
        salida.append(value)
    return salida


def unico(objs):
    salida = []
    vistos = set()

    for obj in objs or []:
        if obj is None:
            continue

        clave = ruta_de(obj)

        if clave in vistos:
            continue

        vistos.add(clave)
        salida.append(obj)

    return salida


def json_safe(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]

    try:
        return float(value)
    except Exception:
        return str(value)


# =====================================================================
# SETSELECT
# =====================================================================

def desreferenciar(item):
    if item is None:
        return None

    try:
        obj = item.obj_id
    except Exception:
        obj = None

    return obj if obj is not None else item


def contenido_de(s):
    if s is None:
        return []

    try:
        items = s.GetContents()
    except Exception:
        return []

    salida = []

    for item in items or []:
        obj = desreferenciar(item)
        if obj is not None:
            salida.append(obj)

    return salida


# =====================================================================
# EXPANDIR ENTRADA A ElmLne
# =====================================================================

def lineas_dentro_de(obj, vistos=None, profundidad=0):
    if obj is None:
        return []

    if vistos is None:
        vistos = set()

    if profundidad > 10:
        return []

    clave = ruta_de(obj)

    if clave in vistos:
        return []

    vistos.add(clave)

    if clase(obj) == "ElmLne":
        return [obj]

    salida = []

    try:
        hijos = obj.GetContents()
    except Exception:
        hijos = []

    for hijo in hijos or []:
        real = desreferenciar(hijo)

        if real is None:
            continue

        if clase(real) == "ElmLne":
            salida.append(real)
        else:
            salida += lineas_dentro_de(
                real,
                vistos,
                profundidad + 1
            )

    if not salida:
        try:
            directas = obj.GetContents("*.ElmLne", 1)
        except Exception:
            directas = []

        for linea in directas or []:
            if clase(linea) == "ElmLne":
                salida.append(linea)

    return unico(salida)


def lineas_del_set(set_lineas):
    salida = []

    for obj in contenido_de(set_lineas):
        encontradas = lineas_dentro_de(obj)

        if not encontradas:
            warn(
                "No encontre lineas dentro de %s [%s]"
                % (ruta_de(obj), clase(obj))
            )

        salida += encontradas

    return unico(salida)


# =====================================================================
# CHARACTERISTICS
# =====================================================================

def characteristic_de(owner, parametro="sline"):
    if owner is None:
        return None

    try:
        refs = owner.GetContents("%s.ChaRef" % parametro)
    except Exception:
        refs = []

    if not refs:
        try:
            todos = owner.GetContents("*.ChaRef")
        except Exception:
            todos = []

        refs = [
            ref for ref in (todos or [])
            if nombre(ref) == parametro
        ]

    if not refs:
        return None

    return get_attr(refs[0], "typ_id", None)


# =====================================================================
# TriDisc / ChaMat
# =====================================================================

def leer_casos_escala(scale):
    if scale is None:
        return []

    try:
        casos = scale.GetAttribute("cases")
    except Exception as ex:
        warn(
            "No pude leer cases de '%s' [%s]: %s"
            % (nombre(scale), clase(scale), ex)
        )
        return []

    if casos is None:
        return []

    if isinstance(casos, str):
        return [casos]

    if isinstance(casos, (list, tuple)):
        return [json_safe(v) for v in casos]

    try:
        return [json_safe(v) for v in list(casos)]
    except Exception:
        return [json_safe(casos)]


def leer_chamat(chamat):
    if chamat is None:
        return None

    if clase(chamat) != "ChaMat":
        warn(
            "La caracteristica '%s' es %s, no ChaMat"
            % (nombre(chamat), clase(chamat))
        )
        return None

    escala_columnas = get_attr(chamat, "scalecol", None)
    escala_filas = get_attr(chamat, "scalerow", None)

    if escala_columnas is None:
        warn("%s: no tiene scalecol" % nombre(chamat))
        return None

    if escala_filas is None:
        warn("%s: no tiene scalerow" % nombre(chamat))
        return None

    columnas = leer_casos_escala(escala_columnas)
    filas = leer_casos_escala(escala_filas)

    if not columnas:
        warn(
            "%s: scalecol '%s' no tiene cases"
            % (nombre(chamat), nombre(escala_columnas))
        )
        return None

    if not filas:
        warn(
            "%s: scalerow '%s' no tiene cases"
            % (nombre(chamat), nombre(escala_filas))
        )
        return None

    try:
        matrix = chamat.GetAttribute("matrix")
    except Exception as ex:
        warn("%s: no pude leer matrix: %s" % (nombre(chamat), ex))
        return None

    if matrix is None:
        warn("%s: matrix esta vacia" % nombre(chamat))
        return None

    try:
        matrix = [
            [json_safe(v) for v in row]
            for row in matrix
        ]
    except Exception as ex:
        warn("%s: no pude convertir matrix: %s" % (nombre(chamat), ex))
        return None

    if len(matrix) != len(filas):
        warn(
            "%s: matrix tiene %d filas pero scalerow '%s' tiene %d cases"
            % (
                nombre(chamat),
                len(matrix),
                nombre(escala_filas),
                len(filas)
            )
        )
        return None

    for i, row in enumerate(matrix):
        if len(row) != len(columnas):
            warn(
                "%s: matrix fila %d tiene %d columnas pero scalecol '%s' tiene %d cases"
                % (
                    nombre(chamat),
                    i,
                    len(row),
                    nombre(escala_columnas),
                    len(columnas)
                )
            )
            return None

    return {
        "row_scale": {
            "name": nombre(escala_filas),
            "class": clase(escala_filas),
            "path": ruta_de(escala_filas),
            "cases": filas,
        },
        "column_scale": {
            "name": nombre(escala_columnas),
            "class": clase(escala_columnas),
            "path": ruta_de(escala_columnas),
            "cases": columnas,
        },
        "matrix": matrix,
    }


# =====================================================================
# TOWER TYPE / LINE COUPLING
# =====================================================================

def couplings_de_linea(linea):
    raw = get_attr(linea, "c_ptow", None)

    salida = []

    for obj in solo_objetos_pf(raw):
        if clase(obj) == "ElmTow":
            salida.append(obj)

    return unico(salida)


def geometrias_de_coupling(tow):
    salida = []

    raw = get_attr(tow, "pGeo", None)

    for obj in solo_objetos_pf(raw):
        if clase(obj) in ("TypTow", "TypGeo"):
            salida.append(obj)

    if salida:
        return unico(salida)

    tabla = get_attr(tow, "tab_Geo", None)

    for fila in como_lista(tabla):
        if fila is None:
            continue

        if clase(fila) in ("TypTow", "TypGeo"):
            salida.append(fila)
            continue

        pgeo = get_attr(fila, "pGeo", None)

        for obj in solo_objetos_pf(pgeo):
            if clase(obj) in ("TypTow", "TypGeo"):
                salida.append(obj)

    return unico(salida)


def conductores_de_typtow(typtow):
    salida = []

    raw = get_attr(typtow, "pcond_c", None)

    for obj in solo_objetos_pf(raw):
        if clase(obj) == "TypCon":
            salida.append(obj)

    if salida:
        return unico(salida)

    tabla = get_attr(typtow, "tc", None)

    for fila in como_lista(tabla):
        if fila is None:
            continue

        if clase(fila) == "TypCon":
            salida.append(fila)
            continue

        pcond = get_attr(fila, "pcond_c", None)

        for obj in solo_objetos_pf(pcond):
            if clase(obj) == "TypCon":
                salida.append(obj)

    return unico(salida)


# =====================================================================
# TENSION / CAPACIDAD
# =====================================================================

def tension_linea(linea):
    value = get_attr(linea, "e:Unom", None)

    try:
        return float(value)
    except Exception:
        return None


def calcular_mva(unom, corriente):
    if unom is None or corriente is None:
        return None

    try:
        return RAIZ3 * float(unom) * float(corriente)
    except Exception:
        return None


def matriz_mva(unom, matrix_ka):
    return [
        [calcular_mva(unom, value) for value in row]
        for row in matrix_ka
    ]


# =====================================================================
# REGISTRO DE RATING
# =====================================================================

def registro_de_rating(
    linea,
    rating_obj,
    modelo,
    tow=None,
    typtow=None
):
    unom = tension_linea(linea)

    registro = {
        "line": {
            "name": nombre(linea),
            "path": ruta_de(linea),
            "class": clase(linea),
            "nominal_voltage_kV": unom,
            "sernum": json_safe(get_attr(linea, "sernum", None)),
            "length_km": json_safe(get_attr(linea, "dline", None)),
        },

        "model": modelo,

        "line_coupling": (
            None if tow is None
            else {
                "name": nombre(tow),
                "path": ruta_de(tow),
                "class": clase(tow),
            }
        ),

        "tower_type": (
            None if typtow is None
            else {
                "name": nombre(typtow),
                "path": ruta_de(typtow),
                "class": clase(typtow),
            }
        ),

        "rating_object": {
            "name": nombre(rating_obj),
            "path": ruta_de(rating_obj),
            "class": clase(rating_obj),
        },
    }

    cha = characteristic_de(rating_obj, "sline")

    # ---------------------------------------------------------
    # Capacidad fija
    # ---------------------------------------------------------

    if cha is None:
        inom = get_attr(rating_obj, "sline", None)

        try:
            inom = float(inom)
        except Exception:
            inom = None

        registro["rating"] = {
            "mode": "fixed",
            "current_kA": inom,
            "capacity_MVA": calcular_mva(unom, inom),
        }

        return registro

    # ---------------------------------------------------------
    # Capacidad matricial
    # ---------------------------------------------------------

    data = leer_chamat(cha)

    if data is None:
        return None

    matrix_ka = data["matrix"]

    registro["rating"] = {
        "mode": "matrix",

        "characteristic": {
            "name": nombre(cha),
            "path": ruta_de(cha),
            "class": clase(cha),
        },

        "row_scale": data["row_scale"],
        "column_scale": data["column_scale"],
        "current_kA": matrix_ka,
        "capacity_MVA": matriz_mva(unom, matrix_ka),
    }

    return registro


# =====================================================================
# RESOLVER UN TypTow
# =====================================================================

def procesar_typtow(
    linea,
    typtow,
    modelo,
    problemas,
    tow=None
):
    resultados = []

    typcons = conductores_de_typtow(typtow)

    if not typcons:
        warn(
            "%s: TypTow '%s' no entrega pcond_c"
            % (nombre(linea), nombre(typtow))
        )

        problemas.append({
            "line": nombre(linea),
            "path": ruta_de(linea),
            "problem": "TypTow has no pcond_c",
            "typ_id_name": nombre(typtow),
            "typ_id_class": clase(typtow),
        })

        return resultados

    info(
        "      TypCon encontrados: %d"
        % len(typcons)
    )

    for con in typcons:
        info(
            "        TypCon: %s"
            % nombre(con)
        )

    if len(typcons) == 1:
        registro = registro_de_rating(
            linea=linea,
            rating_obj=typcons[0],
            modelo=modelo,
            tow=tow,
            typtow=typtow
        )

        if registro is not None:
            resultados.append(registro)

        return resultados

    warn(
        "%s: TypTow '%s' usa %d TypCon distintos; "
        "falta resolver circuito -> conductor."
        % (
            nombre(linea),
            nombre(typtow),
            len(typcons)
        )
    )

    problemas.append({
        "line": nombre(linea),
        "path": ruta_de(linea),
        "problem": (
            "Multiple distinct TypCon; "
            "circuit-to-conductor mapping unresolved"
        ),
        "typ_id_name": nombre(typtow),
        "typ_id_class": clase(typtow),
        "TypCon_candidates": [
            {
                "name": nombre(con),
                "path": ruta_de(con),
            }
            for con in typcons
        ],
    })

    return resultados


# =====================================================================
# PROCESAR UNA LINEA
# =====================================================================

def procesar_linea(linea, problemas):
    resultados = []

    # ---------------------------------------------------------
    # 1. Revisar typ_id REAL
    # ---------------------------------------------------------

    tipo = get_attr(
        linea,
        "typ_id",
        None
    )

    tipo_clase = clase(tipo)

    if tipo is not None:
        info(
            "  typ_id: %s [%s]"
            % (
                nombre(tipo),
                tipo_clase
            )
        )

    # ---------------------------------------------------------
    # 1A. TypLne convencional
    # ---------------------------------------------------------

    if tipo is not None and tipo_clase == "TypLne":

        registro = registro_de_rating(
            linea=linea,
            rating_obj=tipo,
            modelo="TypLne"
        )

        if registro is not None:
            resultados.append(registro)

        return resultados

    # ---------------------------------------------------------
    # 1B. TypTow/TypGeo asignado DIRECTAMENTE en typ_id
    #
    # Este es el caso, por ejemplo, de líneas donde la GUI
    # muestra un Tower Type directamente en el campo Type.
    # ---------------------------------------------------------

    if tipo is not None and tipo_clase in (
        "TypTow",
        "TypGeo"
    ):

        info(
            "  Tower Type directo via typ_id"
        )

        return procesar_typtow(
            linea=linea,
            typtow=tipo,
            modelo="TypTow/TypCon (typ_id directo)",
            problemas=problemas,
            tow=None
        )

    # ---------------------------------------------------------
    # 2. Line Coupling via c_ptow
    # ---------------------------------------------------------

    couplings = couplings_de_linea(
        linea
    )

    if couplings:

        info(
            "  Line Couplings: %d"
            % len(couplings)
        )

        for tow in couplings:

            info(
                "    ElmTow: %s"
                % nombre(tow)
            )

            geometrias = geometrias_de_coupling(
                tow
            )

            if not geometrias:

                warn(
                    "%s: ElmTow '%s' no entrega pGeo"
                    % (
                        nombre(linea),
                        nombre(tow)
                    )
                )

                problemas.append({
                    "line": nombre(linea),
                    "path": ruta_de(linea),
                    "problem": "ElmTow has no pGeo",
                    "ElmTow": nombre(tow),
                })

                continue

            for typtow in geometrias:

                info(
                    "      %s: %s"
                    % (
                        clase(typtow),
                        nombre(typtow)
                    )
                )

                resultados += procesar_typtow(
                    linea=linea,
                    typtow=typtow,
                    modelo="TypTow/TypCon (Line Coupling)",
                    problemas=problemas,
                    tow=tow
                )

        return resultados

    # ---------------------------------------------------------
    # 3. Nada reconocible
    #
    # IMPORTANTE:
    # ya no se dice "sin typ_id" si typ_id SI existe.
    # ---------------------------------------------------------

    if tipo is None:

        mensaje = (
            "%s: sin typ_id y sin c_ptow"
            % nombre(linea)
        )

        problem = "No typ_id and no ElmTow found"

    else:

        mensaje = (
            "%s: typ_id existe (%s [%s]) pero no es un "
            "tipo soportado, y tampoco tiene c_ptow"
            % (
                nombre(linea),
                nombre(tipo),
                tipo_clase
            )
        )

        problem = "Unsupported typ_id class and no ElmTow found"

    warn(mensaje)

    problemas.append({
        "line": nombre(linea),
        "path": ruta_de(linea),
        "problem": problem,
        "typ_id_name": (
            None if tipo is None
            else nombre(tipo)
        ),
        "typ_id_class": (
            None if tipo is None
            else tipo_clase
        ),
    })

    return resultados


# =====================================================================
# CSV
# =====================================================================

COLUMNAS_CSV = [
    "Linea",
    "Ruta",
    "SerNum",
    "Modelo",
    "ElmTow",
    "TypTow",
    "Tipo capacidad",
    "Caracteristica",
    "Escala filas",
    "Caso fila",
    "Escala columnas",
    "Caso columna",
    "Tension nominal [kV]",
    "Longitud [km]",
    "Capacidad [kA]",
    "Capacidad [MVA]",
]


def aplanar_registros(registros):
    filas_csv = []

    for registro in registros:

        line = registro["line"]
        rating_obj = registro["rating_object"]
        rating = registro["rating"]

        comun = {
            "Linea": line["name"],
            "Ruta": line["path"],
            "SerNum": line.get("sernum"),
            "Longitud [km]": line.get("length_km"),
            "Modelo": registro["model"],

            "ElmTow": (
                ""
                if registro["line_coupling"] is None
                else registro["line_coupling"]["name"]
            ),

            "TypTow": (
                ""
                if registro["tower_type"] is None
                else registro["tower_type"]["name"]
            ),

            "Tipo capacidad":
                rating_obj["name"],

            "Tension nominal [kV]":
                line["nominal_voltage_kV"],
        }

        if rating["mode"] == "fixed":

            fila = dict(comun)

            fila.update({
                "Caracteristica": "",
                "Escala filas": "",
                "Caso fila": "",
                "Escala columnas": "",
                "Caso columna": "",
                "Capacidad [kA]":
                    rating["current_kA"],
                "Capacidad [MVA]":
                    rating["capacity_MVA"],
            })

            filas_csv.append(fila)
            continue

        row_scale = rating["row_scale"]
        col_scale = rating["column_scale"]

        matrix_ka = rating["current_kA"]
        matrix_mva = rating["capacity_MVA"]

        for i, caso_fila in enumerate(
            row_scale["cases"]
        ):

            for j, caso_columna in enumerate(
                col_scale["cases"]
            ):

                corriente = matrix_ka[i][j]
                mva = matrix_mva[i][j]

                if (
                    not EXPORTAR_CEROS
                    and corriente is not None
                ):
                    try:
                        if abs(float(corriente)) < 1e-12:
                            continue
                    except Exception:
                        pass

                fila = dict(comun)

                fila.update({
                    "Caracteristica":
                        rating["characteristic"]["name"],

                    "Escala filas":
                        row_scale["name"],

                    "Caso fila":
                        caso_fila,

                    "Escala columnas":
                        col_scale["name"],

                    "Caso columna":
                        caso_columna,

                    "Capacidad [kA]":
                        corriente,

                    "Capacidad [MVA]":
                        mva,
                })

                filas_csv.append(fila)

    return filas_csv


def guardar_csv(filas):
    carpeta = os.path.dirname(CSV_PATH)

    if carpeta and not os.path.isdir(carpeta):
        os.makedirs(carpeta)

    with open(
        CSV_PATH,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=COLUMNAS_CSV,
            delimiter=";"
        )

        writer.writeheader()

        for row in filas:
            writer.writerow(row)


# =====================================================================
# JSON
# =====================================================================

def guardar_json(registros, problemas):
    carpeta = os.path.dirname(JSON_PATH)

    if carpeta and not os.path.isdir(carpeta):
        os.makedirs(carpeta)

    salida = {
        "generated_at":
            datetime.datetime.now().isoformat(
                timespec="seconds"
            ),

        "source_set":
            NOMBRE_SET,

        "number_of_records":
            len(registros),

        "number_of_problems":
            len(problemas),

        "records":
            registros,

        "problems":
            problemas,
    }

    with open(
        JSON_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            salida,
            f,
            ensure_ascii=False,
            indent=2
        )


# =====================================================================
# MAIN
# =====================================================================

def main():

    info("=" * 72)
    info(
        "CAPACIDADES TERMICAS - "
        "LECTURA DIRECTA DE CHARACTERISTICS"
    )
    info("=" * 72)

    script = app.GetCurrentScript()

    if script is None:
        err("No pude obtener el ComPython.")
        return

    try:
        set_lineas = script.GetAttribute(
            NOMBRE_SET
        )
    except Exception:
        set_lineas = None

    if set_lineas is None:
        err(
            "Falta External Object '%s'"
            % NOMBRE_SET
        )
        return

    lineas = lineas_del_set(
        set_lineas
    )

    info(
        "Lineas encontradas: %d"
        % len(lineas)
    )

    if not lineas:
        return

    registros = []
    problemas = []

    for i, linea in enumerate(
        lineas,
        start=1
    ):

        info("")

        info(
            "[%d/%d] %s"
            % (
                i,
                len(lineas),
                nombre(linea)
            )
        )

        registros += procesar_linea(
            linea,
            problemas
        )

    seriales = {ruta_de(linea): json_safe(get_attr(linea, "sernum", None))
                for linea in lineas}
    for problema in problemas:
        problema["sernum"] = seriales.get(problema.get("path"))

    filas_csv = aplanar_registros(
        registros
    )

    if EXPORTAR_CSV:
        guardar_csv(
            filas_csv
        )

    if EXPORTAR_JSON:
        guardar_json(
            registros,
            problemas
        )

    info("")
    info("=" * 72)

    info(
        "Lineas de entrada: %d"
        % len(lineas)
    )

    info(
        "Registros resueltos: %d"
        % len(registros)
    )

    info(
        "Combinaciones CSV: %d"
        % len(filas_csv)
    )

    info(
        "Problemas: %d"
        % len(problemas)
    )

    if EXPORTAR_CSV:
        info("CSV: %s" % CSV_PATH)

    if EXPORTAR_JSON:
        info("JSON: %s" % JSON_PATH)

    info("=" * 72)


if __name__ == "__main__":
    main()

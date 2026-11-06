# autor: ViQ
# Versión 6
# Sigue la guía técnica
# Arregla carga trafos
# (copia de referencia entregada por el usuario el 06-10-2026; ver README.md)

import powerfactory as pf

app = pf.GetApplication()
script = app.GetCurrentScript()

if not script:
    app.PrintPlain("No se pudo acceder al script actual.")
    raise SystemExit


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def get_attr(obj, name, default=None):
    if obj is None:
        return default

    try:
        value = obj.GetAttribute(name)
        return value if value is not None else default
    except Exception:
        return default


def get_float_attr(obj, name, default=None):
    value = get_attr(obj, name, default)

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def set_pgini(gen, value):
    """
    Escribe pgini en PowerFactory.
    pgini corresponde a la potencia por máquina, no al total ngnum.
    """
    try:
        gen.SetAttribute("pgini", value)
    except Exception:
        try:
            gen.pgini = value
        except Exception as exc:
            app.PrintPlain(
                "No fue posible modificar {}: {}".format(
                    gen.GetFullName(),
                    exc
                )
            )


def calculate_unit_data(gen, group_number, base_percentage, use_percentage):
    """
    Obtiene:

    - Pmax nominal usada como ponderador de la prorrata.
    - Potencia disponible.
    - Potencia mínima.
    - Generación base antes de restringir.

    Todos los valores *_total consideran ngnum.

    El signo de pgini se conserva: una unidad con pgini < 0 está
    consumiendo (BESS en carga) y para ella aliviar es cargar menos, no
    generar menos. El sentido de cada unidad se resuelve en "direction".
    """

    ngnum = get_float_attr(gen, "ngnum", 1.0)

    if ngnum is None or ngnum <= 0:
        ngnum = 1.0

    p_max = get_float_attr(gen, "P_max", None)
    cosn = get_float_attr(gen, "cosn", 1.0)
    sgn = get_float_attr(gen, "sgn", None)

    nominal_candidates = []

    if p_max is not None and p_max > 0:
        nominal_candidates.append(p_max)

    if (
        sgn is not None
        and sgn > 0
        and cosn is not None
        and cosn > 0
    ):
        nominal_candidates.append(cosn * sgn)

    if not nominal_candidates:
        return None

    pmax_machine = min(nominal_candidates)

    pmax_uc = get_float_attr(gen, "Pmax_uc", None)

    available_candidates = [pmax_machine]

    if pmax_uc is not None:
        available_candidates.append(max(0.0, pmax_uc))

    pavailable_machine = min(available_candidates)

    # Un Pmin negativo no es un mínimo técnico: es cuánto puede consumir
    # la unidad. Se leen las dos cosas del mismo atributo según su signo.
    pmin_raw = None

    for attr_name in ("Pmin_uc", "P_min", "pgmin"):
        value = get_float_attr(gen, attr_name, None)

        if value is not None:
            pmin_raw = value
            break

    if pmin_raw is None:
        pmin_raw = 0.0

    pmin_machine = max(
        0.0,
        min(pmin_raw, pavailable_machine)
    )

    if pmin_raw < 0:
        pcharge_machine = -pmin_raw
    else:
        pcharge_machine = pavailable_machine

    pgini_machine = get_float_attr(gen, "pgini", 0.0)

    if pgini_machine is None:
        pgini_machine = 0.0

    if use_percentage:
        # El porcentaje se aplica sobre la potencia disponible y SU SIGNO
        # define el sentido: porcent_i = 20 despacha inyectando al 20 % de
        # la Pmax; porcent_i = -61 deja la unidad cargando al 61 %.
        base_machine = (
            base_percentage
            * pavailable_machine
            / 100.0
        )
    else:
        base_machine = pgini_machine

    if base_machine < 0:
        base_machine = max(base_machine, -pcharge_machine)
    else:
        base_machine = min(
            max(base_machine, pmin_machine),
            pavailable_machine
        )

    return {
        "gen": gen,
        "group": group_number,
        "ngnum": ngnum,
        "weight_total": pmax_machine * ngnum,
        "available_total": pavailable_machine * ngnum,
        "minimum_total": pmin_machine * ngnum,
        "current_total": pgini_machine * ngnum,
        "base_total": base_machine * ngnum,
        "lower_total": 0.0,
        "upper_total": 0.0,
        "target_total": base_machine * ngnum,
    }


def set_target_bounds(unit, no_aumentar):
    """
    Rango admisible del punto de operación de la unidad.

    La guía prorratea la colocación total, no el recorte, así que los
    límites se expresan sobre el punto de operación y no sobre el alivio.
    """

    if unit["base_total"] < 0:
        unit["lower_total"] = unit["base_total"]
        unit["upper_total"] = 0.0
        return

    unit["lower_total"] = unit["minimum_total"]

    if no_aumentar:
        unit["upper_total"] = unit["base_total"]
    else:
        unit["upper_total"] = unit["available_total"]


def apply_iterative_prorata(units, total_target):
    """
    Reparte la colocación total a prorrata de Pmax (guía CDC N°1-2024, IV.f):

        Punto de operación_i = Colocación Total x Pmax_i / suma(Pmax_j)

    Si a una unidad no le alcanza el recurso para su punto calculado, se
    fija en lo que puede generar y el excedente se redistribuye entre las
    demás. El proceso itera hasta alcanzar la colocación total.
    """

    tolerance = 1e-6

    lower_sum = sum(unit["lower_total"] for unit in units)
    upper_sum = sum(unit["upper_total"] for unit in units)

    total_target = max(lower_sum, min(total_target, upper_sum))

    remaining_target = total_target
    active_units = list(units)

    while active_units:
        weight_sum = sum(
            max(unit["weight_total"], 0.0)
            for unit in active_units
        )

        use_equal_weights = weight_sum <= tolerance

        if use_equal_weights:
            weight_sum = float(len(active_units))

        fixed_units = []

        for unit in active_units:
            weight = 1.0 if use_equal_weights else max(unit["weight_total"], 0.0)

            proposal = remaining_target * weight / weight_sum

            if proposal < unit["lower_total"] - tolerance:
                unit["target_total"] = unit["lower_total"]
                remaining_target -= unit["lower_total"]
                fixed_units.append(unit)

            elif proposal > unit["upper_total"] + tolerance:
                unit["target_total"] = unit["upper_total"]
                remaining_target -= unit["upper_total"]
                fixed_units.append(unit)

        if not fixed_units:
            for unit in active_units:
                weight = 1.0 if use_equal_weights else max(unit["weight_total"], 0.0)
                unit["target_total"] = remaining_target * weight / weight_sum
            break

        active_units = [
            unit
            for unit in active_units
            if unit not in fixed_units
        ]

    return total_target


def unit_target(unit):
    return unit["target_total"]


def set_conjunto(units):
    """
    Sentido del conjunto: +1 si inyecta, -1 si consume. Si se mezclan,
    manda el signo de la inyección neta.
    """
    return -1.0 if sum(u["base_total"] for u in units) < 0 else 1.0


# ============================================================
# ELEMENTO VIGILADO Y FLUJO DE POTENCIA
# ============================================================

# La carga es |S|/nominal: la mueve también el reactivo y puede CRECER con un
# recorte de P si el flujo se da vuelta. Por eso el alivio no se deduce, se
# itera midiendo c:loading después de cada flujo.
CARGA_ATTRS = {
    "TR": ("c:loading_m", "c:loading_h"),
    "LNE": ("c:loading",),
}

FLUJO_ATTRS = ("m:P:bus1", "m:P:bushv", "m:Psum:bus1")


def get_single_element(container):
    if not container:
        return None

    contents = container.GetContents()

    if not contents:
        return None

    if len(contents) > 1:
        app.PrintPlain(
            "Advertencia: el set vigilado tiene {} elementos; "
            "se usa el primero.".format(len(contents))
        )

    item = contents[0]
    element = get_attr(item, "obj_id")

    return element if element else item


def first_float(obj, attr_names):
    for name in attr_names:
        value = get_float_attr(obj, name, None)

        if value is not None:
            return value

    return None


def first_float_loading(obj, attr_names=CARGA_ATTRS):
    class_name = obj.GetClassName()

    if class_name in ("ElmTr2", "ElmTr3"):
        attrs = attr_names["TR"]
    else:
        attrs = attr_names["LNE"]

    values = []

    for name in attrs:
        value = get_float_attr(obj, name, None)

        if value is not None:
            values.append(value)

    if values == []:
        return None
    else:
        return max(values)


def run_load_flow(ldf):
    try:
        return ldf.Execute() == 0
    except Exception as exc:
        app.PrintPlain("El flujo lanzó una excepción: {}".format(exc))
        return False


def apply_relief(units, total_relief):
    """
    Traduce el alivio pedido a colocación total, reparte a prorrata de
    Pmax, escribe pgini y devuelve el alivio efectivamente aplicado.
    """

    base_total = sum(unit["base_total"] for unit in units)
    sentido = set_conjunto(units)

    total_target = base_total - sentido * total_relief

    effective_target = apply_iterative_prorata(units, total_target)

    for unit in units:
        set_pgini(
            unit["gen"],
            unit["target_total"] / unit["ngnum"]
        )

    return sentido * (base_total - effective_target)


def solve_by_loading(units, relief_ceiling, element, ldf, target_loading, loading_band, max_iterations, step_mw):
    """
    Busca el alivio mínimo que deja la carga del elemento vigilado en
    (target_loading - loading_band, target_loading].

    Secante sobre carga(alivio) con acotamiento: el intervalo [lower, upper]
    mantiene un punto que no cumple (lower) y, en cuanto aparece, uno que sí
    cumple (upper); si la secante se sale del intervalo se bisecta.
    """

    result = {"status": "sin_evaluar", "iterations": 0, "base_loading": None, "final_loading": None,
              "applied": 0.0, "history": []}

    applied = apply_relief(units, 0.0)

    if not run_load_flow(ldf):
        result["status"] = "flujo_falla"
        return result

    base_loading = first_float_loading(element, CARGA_ATTRS)

    if base_loading is None:
        result["status"] = "sin_carga"
        return result

    result["base_loading"] = base_loading
    result["final_loading"] = base_loading
    result["applied"] = applied
    result["history"].append((applied, base_loading))

    if base_loading <= target_loading:
        result["status"] = "sin_congestion"
        return result

    if relief_ceiling <= step_mw:
        result["status"] = "sin_margen"
        return result

    # Primera estimación: cota inferior del alivio (sensibilidad < 1).
    flow = first_float(element, FLUJO_ATTRS)

    if flow:
        candidate = abs(flow) * (1.0 - target_loading / base_loading)
    else:
        candidate = 0.25 * relief_ceiling

    candidate = min(max(candidate, step_mw), relief_ceiling)

    lower_relief = applied
    lower_loading = base_loading
    upper_relief = None
    upper_loading = None

    while result["iterations"] < max_iterations:
        result["iterations"] += 1

        applied = apply_relief(units, min(max(candidate, 0.0), relief_ceiling))

        if not run_load_flow(ldf):
            result["status"] = "flujo_falla"
            return result

        loading = first_float_loading(element, CARGA_ATTRS)

        if loading is None:
            result["status"] = "sin_carga"
            return result

        result["applied"] = applied
        result["final_loading"] = loading
        result["history"].append((applied, loading))

        if loading <= target_loading:
            upper_relief = applied
            upper_loading = loading

            if loading > target_loading - loading_band:
                result["status"] = "convergio"
                return result
        else:
            lower_relief = applied
            lower_loading = loading

            if applied >= relief_ceiling - step_mw:
                result["status"] = "sin_margen"
                return result

        if upper_relief is not None:
            if upper_relief - lower_relief <= step_mw:
                break

            slope_den = upper_loading - lower_loading

            if abs(slope_den) > 1e-9:
                candidate = lower_relief + ((target_loading - lower_loading) * (upper_relief - lower_relief) / slope_den)
            else:
                candidate = 0.5 * (lower_relief + upper_relief)

            inner = 0.05 * (upper_relief - lower_relief)
            candidate = min(max(candidate, lower_relief + inner), upper_relief - inner)
        else:
            (r_prev, l_prev) = result["history"][-2]
            (r_last, l_last) = result["history"][-1]

            slope = 0.0

            if abs(r_last - r_prev) > 1e-9:
                slope = (l_last - l_prev) / (r_last - r_prev)

            if slope < -1e-9:
                candidate = r_last + ((target_loading - l_last) / slope)
            else:
                result["status"] = "sin_sensibilidad"
                return result

            candidate = min(candidate, relief_ceiling)

            if candidate <= r_last + step_mw:
                candidate = min(relief_ceiling, r_last + max(step_mw, 0.05 * relief_ceiling))

    if upper_relief is None:
        result["status"] = "max_iteraciones"
        return result

    if abs(result["applied"] - upper_relief) > 1e-9:
        result["applied"] = apply_relief(units, upper_relief)

        if not run_load_flow(ldf):
            result["status"] = "flujo_falla"
            return result

        result["final_loading"] = first_float_loading(element, CARGA_ATTRS)

    if result["status"] == "sin_evaluar":
        result["status"] = "factible_sin_afinar"

    return result


# ============================================================
# PARÁMETROS GENERALES (objetos externos / parámetros del ComPython)
# ============================================================
# VIGILADO (set, 1 elemento), carga_objetivo (99.9), banda_carga (0.2), max_iteraciones (20),
# paso_minimo_mw (0.05), reduccion_total_mw (si no hay vigilado), no_aumentar (1),
# RENOV_1..9 + hacerF_i + porcent_i.
# El resto del script original (lectura de grupos, cálculo de relief_ceiling/floor, búsqueda y reporte por grupo)
# se omite en esta copia de referencia: la lógica reutilizable está arriba.

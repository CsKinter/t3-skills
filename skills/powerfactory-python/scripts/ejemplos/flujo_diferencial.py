# Flujo diferencial de PF (ComDiff «Compare», imode 2 = B − A) para un cambio on/off, con foto y tabla de factores.
# Plantilla para el puente (pf_drv.run): marcadores
#   __CASO__    caso de estudio (ruta relativa aceptada por cambiar_caso), p. ej. r"POI 2 - Buli\03_15 SS"
#   __ESC__     escenario, p. ej. r"POI 2 - Buli\1_Irrestrictos\E04_MAD_DB_15_BESS-D"
#   __CLASE__   clase del elemento que se apaga/enciende (ElmGenstat para un proyecto, ElmLne para una contingencia)
#   __ELEM__    nombre exacto del elemento
#   __A_FUERA__ "1": el caso A es con el elemento FUERA (impacto de un proyecto: B − A = con − sin)
#               "0": el caso A es con el elemento EN SERVICIO (contingencia: B − A = sin − con)
#   __REDES__   prefijos de las redes (ElmNet) a tabular, separados por coma, p. ej. "06-,07-,08-"
#   __PAGINA__  página gráfica a fotografiar ("" = sin foto)
#   __ARCH__    nombre base de la foto y del JSON
# Deja el escenario sin cambio neto: el elemento vuelve a su estado inicial en un finally.
print("DIF ctx", cambiar_caso(r"__CASO__", r"__ESC__"))
e = app.GetActiveScenario(); caso = app.GetActiveStudyCase()
assert e is not None and r"__ESC__".split("\\")[-1] == e.loc_name, e
cd = [c for c in caso.GetContents("*.ComDiff") if c.loc_name == "Compare"][0]
if get_attr(cd, "imode") != 2: cd.imode = 2
ldf = [c for c in caso.GetContents("*.ComLdf")][0]
el = [x for x in app.GetCalcRelevantObjects("*.__CLASE__") if x.loc_name == "__ELEM__"]
assert len(el) == 1, ("elemento ambiguo o ausente", len(el)); el = el[0]
A_FUERA = "__A_FUERA__" == "1"
prefijos = tuple(p.strip() for p in "__REDES__".split(",") if p.strip())
nets = [n for n in app.GetProjectFolder("netdat").GetContents("*.ElmNet", 1) if n.loc_name.startswith(prefijos)]
EL = {}
for n in nets:
    for cls in ("ElmLne", "ElmTr2", "ElmTr3", "ElmScap"):
        for x in n.GetContents("*." + cls, 1): EL.setdefault(x.GetFullName(), x)
def kv(x):
    u = get_attr(x, "Unom") if x.GetClassName() in ("ElmLne", "ElmScap") else None
    if not u:
        c = get_attr(x, "bushv") or get_attr(x, "bus1"); t = get_attr(c, "cterm") if c is not None else None
        u = get_attr(t, "uknom") if t is not None else 0
    return u or 0
def leer():
    out = {}
    for k, x in EL.items():
        p = get_attr(x, "m:P:bushv") if x.GetClassName() == "ElmTr3" else get_attr(x, "m:P:bus1")
        if p is None and x.GetClassName() == "ElmTr2": p = get_attr(x, "m:P:bushv")
        c = get_attr(x, "c:loading")
        if p is not None and c is not None: out[k] = (p, c)
    return out
def correr():
    r = ldf.Execute()
    if r:                                                    # respaldo: arranque plano
        ni0 = get_attr(ldf, "iopt_noinit")
        try:
            ldf.iopt_noinit = 0; r = ldf.Execute(); print("DIF   arranque plano", r)
        finally:
            ldf.iopt_noinit = ni0
    return r
def potencia():
    return get_attr(el, "m:P:bus1") or 0
out0 = get_attr(el, "outserv"); A = B = {}; ref = 0
try:
    i0 = get_attr(cd, "icomp")
    el.outserv = 1 if A_FUERA else 0
    rA = correr(); A = leer(); iA = get_attr(cd, "icomp")
    if not A_FUERA: ref = potencia()                         # contingencia: potencia que llevaba el elemento
    if iA == i0:                                             # comparación apagada: se enciende (botón de PF)
        cd.iopt_mode = "start"; print("DIF comparación encendida", cd.Execute())
        rA = correr(); A = leer(); iA = get_attr(cd, "icomp")
    assert iA != i0, "no se pudo encender la comparación de resultados"
    cd.ibase = iA - 1                                        # índice base 0 del caso A, antes del flujo B
    el.outserv = 0 if A_FUERA else 1
    rB = correr(); B = leer()
    if A_FUERA: ref = potencia()                             # proyecto: su despacho en el caso B
    print("DIF A ierr", rA, "| B ierr", rB, "| icomp", get_attr(cd, "icomp"), "| ibase", get_attr(cd, "ibase"), "| ref %.1f MW" % ref)
    if rA == 0 and rB == 0 and "__PAGINA__":
        for sc in app.GetActiveProject().GetContents("*.SetColscheme", 1) or []:
            try:
                if get_attr(sc, "cUseAlarm"): sc.cUseAlarm = 0  # sin rojo de sobrecarga en la foto de diferencias
            except Exception as x:
                print("DIF alarma no editable", sc.loc_name, str(x)[:80])
        dg = [x for x in app.GetProjectFolder("dia").GetContents("*.IntGrfnet", 1) if x.loc_name == "__PAGINA__"]
        if dg:
            try: dg[0].Close()
            except Exception: pass
            dg[0].Show()
        print("DIF WMF", exportar_grafico("__ARCH__", pagina="__PAGINA__"))
finally:
    el.outserv = out0
    print("DIF estado restaurado outserv", get_attr(el, "outserv"))
correr()
res = dict(caso=r"__CASO__", escenario=r"__ESC__", elemento="__ELEM__", a_fuera=A_FUERA, ref_MW=round(ref, 2), elementos=[])
for k in sorted(set(A) & set(B)):
    d = B[k][0] - A[k][0]
    if abs(d) >= 0.2:
        res["elementos"].append(dict(el=EL[k].loc_name, kV=round(kv(EL[k])), dP=round(d, 2), f=round(100 * d / ref, 2) if ref else None,
                                     PA=round(A[k][0], 1), PB=round(B[k][0], 1), cA=round(A[k][1], 1), cB=round(B[k][1], 1)))
for r in sorted(res["elementos"], key=lambda r: -abs(r["dP"]))[:25]:
    print("DIF %3d kV %-44s dP %+7.1f MW | f %+6.1f %% | carga %5.1f -> %5.1f %%" % (r["kV"], r["el"][:44], r["dP"], r["f"] or 0, r["cA"], r["cB"]))
print("DIF json", guardar("__ARCH__", res), "| elementos con |dP| >= 0,2 MW:", len(res["elementos"]))
if get_attr(e, "iModified"):
    print("DIF el escenario quedó marcado como modificado (mismos valores): guardar sólo si el usuario lo autorizó")

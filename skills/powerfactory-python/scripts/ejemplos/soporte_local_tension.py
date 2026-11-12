# Soporte local de tension por zona, barra por barra (receta verificada en Sidon, 11-11-2026). Sin cambios de P.
# Referencia: references/soporte-local-tension.md. Plantilla para el puente full; marcadores:
#   __PROY__     fragmento del nombre del proyecto activo (control de identidad)
#   __CASO__     loc_name del caso de estudio que debe estar activo
#   __CARPETA__  ruta de la carpeta de escenarios bajo Operation Scenarios, separada por "/", p. ej. "00_X/3_Base"
#   __RESPALDO__ carpeta hermana para la copia previa, p. ej. "99_Respaldo"
#   __ZONA__     prefijos (2 caracteres) de las ElmNet de la zona, p. ej. ("05", "06", "07")
#   __TRONCAL__  prefijos de las redes cuya tension >= 200 kV no puede empeorar
#   __MONITOR__  (nombre que empieza, kV) de la barra de control de la solucion buena, p. ej. ("MONTENEGRO", 154)
#   __EXCLUIR__  fragmentos de nombre de unidades que no se tocan (proyecto, BESS...), p. ej. ("SIDON",)
#   __ESC__ prefijo del escenario | __GUARDAR__ True/False | __PRESUP__ s | __PASOS__ "BV", "B" o "V" | __RESET__ None
# Adaptar banda() a los criterios acordados con el usuario. Correr envuelto (ver la referencia): exec + DiscardChanges.
import time
T0 = time.time()
ESC = "__ESC__"; GUARDAR = __GUARDAR__; PRESUP = __PRESUP__; PASOS = "__PASOS__"  # A siempre; B local; V vecinas
p = app.GetActiveProject()
if "__PROY__" not in p.GetFullName(): raise RuntimeError("proyecto")
assert app.GetActiveStudyCase().loc_name == "__CASO__"
fb = app.GetProjectFolder("scen")
for _n in "__CARPETA__".split("/"): fb = fb.GetContents(_n + ".IntFolder")[0]
resp = fb.GetParent().GetContents("__RESPALDO__.IntFolder")[0]
Z = __ZONA__; TRONCAL = __TRONCAL__; MONI = __MONITOR__; EXCL = __EXCLUIR__; R = {"esc": ESC}
def grid(o):
    q = o
    while q and q.GetClassName() != "ElmNet": q = q.GetParent()
    return q.loc_name[:2] if q else "?"
def ga(o, a, d=None):
    try:
        v = o.GetAttribute(a); return d if v is None else v
    except Exception: return d
def se(t):
    s = ga(t, "cpSubstat"); return s.loc_name if s else t.loc_name
def bus(x, a="bus1"):
    c = ga(x, a)
    return ga(c, "cterm") if c else None
e = [x for x in fb.GetContents("*.IntScenario") if x.loc_name.startswith(ESC)]
if len(e) != 1: raise RuntimeError("escenario")
e = e[0]; e.Activate(); R["iMod_ini"] = ga(e, "iModified")
ldf = app.GetFromStudyCase("ComLdf")
keep = {x: ldf.GetAttribute(x) for x in ("i_power", "iopt_noinit", "iopt_lim", "iopt_plim", "ictrlx", "iopt_at", "iopt_asht")}
R["ldf"] = keep
def lf(plano=False, ip=None):
    ldf.i_power = keep["i_power"] if ip is None else ip; ldf.iopt_noinit = 0 if plano else 1
    return ldf.Execute() == 0
SL = [x for x in app.GetCalcRelevantObjects("*.ElmSym") if x.ip_ctrl == 1 and not x.outserv][0]
def banda(kv):
    if kv >= 400: return 0.97, 1.03
    if kv >= 154: return 0.95, 1.05
    return 0.93, 1.07
TZ = [t for t in app.GetCalcRelevantObjects("*.ElmTerm") if not t.outserv and grid(t) in Z and t.uknom >= 33
      and "STATCOM" not in (t.loc_name + se(t)).upper() and "SVC" not in t.loc_name.upper()]
TN = [t for t in app.GetCalcRelevantObjects("*.ElmTerm") if not t.outserv and grid(t) in TRONCAL and t.uknom >= 200]
GR = {}
for t in TZ: GR.setdefault(grid(t) + "|" + se(t), []).append(t)
MON = [t for t in TZ if t.loc_name.upper().startswith(MONI[0]) and abs(t.uknom - MONI[1]) < 5]
def dev(t):
    u = ga(t, "m:u", 0)
    if not u or u < 0.3: return 0.0
    lo, hi = banda(t.uknom)
    return lo - u if u < lo else (u - hi if u > hi else 0.0)
def F(): return sum(dev(t) for t in TZ)
def umxN():
    v = [ga(t, "m:u", 0) or 0 for t in TN]; return max(v) if v else 0
def met():
    m = {"slack": round(SL.GetAttribute("m:P:bus1"), 1), "F": round(F(), 3), "n": sum(1 for t in TZ if dev(t) > 0),
         "umxN": round(umxN(), 3), "mon": [round(u, 3) for u in (ga(t, "m:u", 0) or 0 for t in MON) if u > 0.3][:2]}
    return m
# --- recursos por S/E
def terms_of(x):
    out = []
    for a in ("bus1", "bus2", "bushv", "busmv", "buslv"):
        t = bus(x, a)
        if t: out.append(t)
    return out
RES = {}
# v3: transformadores en paralelo (mismo devanado, mismas S/E y kV en cada lado y mismo rango de tap) se mueven
#     juntos con el mismo paso; conservan su diferencia original. Rangos distintos quedan independientes.
TG = {}
def tg_add(x, at, mn, mx):
    k = (at, mn, mx, tuple(sorted("%s@%d" % (se(t), round(t.uknom)) for t in terms_of(x))))
    g = TG.setdefault(k, [[], mn, mx]); g[0].append(x); g[1] = max(g[1], mn); g[2] = min(g[2], mx)
for x in app.GetCalcRelevantObjects("*.ElmTr2"):
    if x.outserv or grid(x) not in Z: continue
    ty = ga(x, "typ_id"); mn, mx = ga(ty, "ntpmn", 0), ga(ty, "ntpmx", 0)
    if mx > mn: tg_add(x, "nntap", mn, mx)
for x in app.GetCalcRelevantObjects("*.ElmTr3"):
    if x.outserv or grid(x) not in Z: continue
    ty = ga(x, "typ_id")
    for w in ("h", "m", "l"):
        mn, mx = ga(ty, "n3tmn_" + w, 0), ga(ty, "n3tmx_" + w, 0)
        if mx > mn: tg_add(x, "n3tap_" + w, mn, mx)
for (at, _mn, _mx, tk), (xs, mn, mx) in TG.items():
    for t in terms_of(xs[0]): RES.setdefault(se(t), []).append(("tap", tuple(xs), at, mn, mx))
R["paralelos"] = [[x.loc_name for x in xs] for (xs, a, b) in TG.values() if len(xs) > 1]
for x in app.GetCalcRelevantObjects("*.ElmShnt"):
    if grid(x) not in Z or x.loc_name.upper().startswith("RL") or ga(x, "shtype") not in (1, 2): continue
    t = bus(x)
    if t: RES.setdefault(se(t), []).append(("sh", x, None, 0, ga(x, "ncapx", 1) or 1))
for k in RES:
    v = []; [v.append(r) for r in RES[k] if not any(r[1] == q[1] and r[2] == q[2] for q in v)]; RES[k] = v
# --- respaldo
R["version"] = str(p.CreateVersion("Antes_%s_soporte_local_v4%s_%s" % (ESC, PASOS, time.strftime("%Y%m%d_%H%M")), 0, 0, 0, "%s soporte local de tension zona" % ESC)) if GUARDAR else None
cp = "%s_antes_%s_soporte_local_%s" % (fb.loc_name, ESC, time.strftime("%Y%m%d"))
if GUARDAR and not resp.GetContents(cp + ".IntFolder"): resp.AddCopy(fb, cp)
# --- reposicion opcional (v3): devuelve taps y bancos de una corrida B anterior a su valor previo
RESET = __RESET__; RS = []
if RESET:
    OBJ = {}
    for cl in ("ElmTr2", "ElmTr3", "ElmShnt"):
        for x in app.GetCalcRelevantObjects("*." + cl):
            if grid(x) in Z: OBJ.setdefault(x.loc_name, []).append(x)
    for kind, n, at, v in RESET:
        xs = OBJ.get(n, [])
        if len(xs) != 1: raise RuntimeError("reset ambiguo: %s (%d)" % (n, len(xs)))
        x = xs[0]
        if kind == "tap": RS.append([n, at, ga(x, at), v]); x.SetAttribute(at, v)
        else: RS.append([n, "sh", [x.outserv, ga(x, "ncapa")], v]); x.outserv = v[0]; x.SetAttribute("ncapa", v[1])
R["reset"] = RS
# --- solucion de partida (buena): i_power = 0 plano, luego continuacion con el original
PART = [("ip0_plano+cont", lambda: lf(plano=True, ip=0) and lf()), ("orig_plano", lambda: lf(plano=True)), ("orig_caliente", lambda: lf())]
ok1 = False
for _n, _f in PART:
    if _f(): ok1 = True; R["partida"] = _n; break
R["m0"] = met() if ok1 else None
if not ok1: e.DiscardChanges(); raise RuntimeError("partida no converge")
def es_ren(x):
    c = ga(x, "cCategory", "") or ""; n = x.loc_name.upper()
    if any(s in n for s in EXCL) or n.startswith("BESS") or "STATCOM" in n or "VSC" in n: return False
    return c in ("Eólica", "Wind", "Photovoltaic", "Fotovoltaica")
REN = [x for x in app.GetCalcRelevantObjects("*.ElmGenstat") if not x.outserv and grid(x) in Z and es_ren(x)
       and (ga(x, "pgini", 0) or 0) > 0.5]
# --- A) renovables a control de tension
A = []; SAT = []
for x in REN:
    A.append([grid(x), x.loc_name, x.av_mode, round(ga(x, "usetp", 0), 4), round(ga(x, "qgini", 0), 2)])
    x.av_mode = "constv"; x.usetp = 1.0
R["A_n"] = len(A); R["A_prev"] = A
okA = lf()
if not okA: okA = lf(plano=True, ip=0) and lf()
for it in range(4):
    if not okA: break
    nuevo = 0
    for x in REN:
        if x.av_mode != "constv": continue
        pn = (ga(x, "sgn", 0) or 0) * (ga(x, "cosn", 1) or 1); q = (ga(x, "m:Q:bus1", 0) or 0) / max(x.ngnum, 1)
        if abs(q) > 0.33 * pn + 0.05:
            x.av_mode = "constq"; x.qgini = (0.33 * pn) * (1 if q > 0 else -1); nuevo += 1
            SAT.append([x.loc_name, round(q, 1), round(x.qgini, 1)])
    if not nuevo: break
    okA = lf() or (lf(plano=True, ip=0) and lf())
R["A_sat"] = SAT; R["mA"] = met() if okA else None
if not okA: e.DiscardChanges(); R["fin"] = "A no converge"; raise RuntimeError("A no converge")
# --- B) barra por barra
UN0 = max(umxN(), 1.055) + 0.002
B = []
def prueba(fun_set, fun_rev, fbest, extra=None):
    fun_set()
    if lf() and umxN() <= UN0 and (extra is None or extra()):
        f = F()
        if f < fbest - 1e-3: return f
    fun_rev(); lf() or (lf(plano=True, ip=0) and lf())
    return None
def qviol():
    n = 0
    for x in REN:
        if x.av_mode == "constv":
            pn = (ga(x, "sgn", 0) or 0) * (ga(x, "cosn", 1) or 1); q = (ga(x, "m:Q:bus1", 0) or 0) / max(x.ngnum, 1)
            if abs(q) > 0.33 * pn + 0.05: n += 1
    return n
QV0 = [qviol()]
def qok(): return qviol() <= QV0[0]
def intentar(g, lista, bajo, fb_, reg, chk=None):
    n_ok = 0
    for kind, x, at, mn, mx in lista:
        if time.time() - T0 > PRESUP: break
        if kind == "tap":
            xs = x
            for d in (1, -1):
                while True:
                    c = [ga(y, at) for y in xs]
                    if any(v is None or not (mn <= v + d <= mx) for v in c): break
                    def st(xs=xs, c=c, d=d):
                        for y, v in zip(xs, c): y.SetAttribute(at, v + d)
                    def rv(xs=xs, c=c):
                        for y, v in zip(xs, c): y.SetAttribute(at, v)
                    f = prueba(st, rv, fb_, extra=chk)
                    if f is None: break
                    reg.append([g, " + ".join(y.loc_name for y in xs), at, c, [v + d for v in c], round(fb_ - f, 4)])
                    fb_ = f; n_ok += 1
        elif kind == "v":
            d = 0.01 if bajo else -0.01
            while True:
                c = round(ga(x, "usetp", 1.0), 3); m = round(c + d, 3)
                if x.av_mode != "constv" or not (0.95 <= m <= 1.05): break
                def st(x=x, m=m): x.usetp = m
                def rv(x=x, c=c): x.usetp = c
                f = prueba(st, rv, fb_, extra=qok)
                if f is None: break
                reg.append([g, x.loc_name, "usetp", c, m, round(fb_ - f, 4)]); fb_ = f; n_ok += 1
        else:
            cap = ga(x, "shtype") == 2
            for _ in range(int(mx)):
                n = 0 if x.outserv else (ga(x, "ncapa", 0) or 0)
                sube = (bajo and cap) or (not bajo and not cap)
                m = n + 1 if sube else n - 1
                if m < 0 or m > mx: break
                o0, n0 = x.outserv, ga(x, "ncapa", 0)
                def st(x=x, m=m):
                    if m == 0: x.outserv = 1
                    else: x.outserv = 0; x.SetAttribute("ncapa", m)
                def rv(x=x, o0=o0, n0=n0): x.outserv = o0; x.SetAttribute("ncapa", n0)
                f = prueba(st, rv, fb_, extra=chk)
                if f is None: break
                reg.append([g, x.loc_name, "ncapa", [o0, n0], m, round(fb_ - f, 4)]); fb_ = f; n_ok += 1
    return fb_, n_ok
def peores():
    gd = sorted(((sum(dev(t) for t in ts), g) for g, ts in GR.items()), reverse=True)
    return [x for x in gd if x[0] > 0.002]
def es_bajo(ts):
    us = [ga(t, "m:u", 0) or 0 for t in ts if dev(t) > 0]
    return bool(us) and sum(1 for u in us if u < 1) >= len(us) / 2.0
if "B" in PASOS:
    for ronda in range(3):
        if time.time() - T0 > PRESUP: break
        mejora_ronda = 0
        for dg, g in peores():
            if time.time() - T0 > PRESUP: break
            ts = GR[g]
            if dg <= 0.002: continue
            fb_, k = intentar(g, RES.get(g.split("|", 1)[1], []), es_bajo(ts), F(), B); mejora_ronda += k
        if not mejora_ronda: break
# --- B2 (v4): barras aun fuera de banda -> recursos de S/E vecinas (hasta 6 saltos por lineas/trafos, misma red),
#     mas cercana primero: taps, bancos y consigna de tension de ERNC en control V (0,95-1,05, tope Q 0,33 Pn).
B2 = []
if "V" in PASOS:
    QV0[0] = qviol(); R["qviol0"] = QV0[0]
    ADJ = {}
    def arista(a, b):
        if a != b: ADJ.setdefault(a, set()).add(b); ADJ.setdefault(b, set()).add(a)
    for cl in ("ElmLne", "ElmTr2", "ElmTr3", "ElmZpu", "ElmCoup"):
        for x in app.GetCalcRelevantObjects("*." + cl):
            if ga(x, "outserv", 0) or grid(x) not in Z: continue
            tt = [grid(t) + "|" + se(t) for t in terms_of(x)]
            for i in range(len(tt)):
                for j in range(i + 1, len(tt)): arista(tt[i], tt[j])
    RV = {}
    for x in REN:
        t = bus(x)
        if t: RV.setdefault(grid(t) + "|" + se(t), []).append(("v", x, None, 0, 0))
    def vecinos(g, prof=6):
        dist = {g: 0}; fr = [g]
        for k in range(1, prof + 1):
            nf = []
            for a in fr:
                for b in ADJ.get(a, ()):
                    if b not in dist and b[:2] == g[:2]: dist[b] = k; nf.append(b)
            fr = nf
        return sorted(dist.items(), key=lambda kv: kv[1])
    for ronda in range(2):
        if time.time() - T0 > PRESUP: break
        mejora_ronda = 0
        for dg, g in peores():
            if time.time() - T0 > PRESUP: break
            if sum(dev(t) for t in GR[g]) <= 0.002: continue
            lista = []
            for h, k in vecinos(g):
                lista += RES.get(h.split("|", 1)[1], []) if k > 0 else []
                lista += RV.get(h, [])
            vist = set(); ls = []
            for r in lista:
                key = (id(r[1]) if not isinstance(r[1], tuple) else tuple(id(y) for y in r[1]), r[2])
                if key not in vist: vist.add(key); ls.append(r)
            fb_, k = intentar(g, ls, es_bajo(GR[g]), F(), B2, chk=qok); mejora_ronda += k
        if not mejora_ronda: break
R["B2"] = B2
R["B"] = B; R["mB"] = met(); R["t_B"] = round(time.time() - T0)
R["resto"] = {g: [[t.loc_name, round(t.uknom), round(ga(t, "m:u", 0) or 0, 3)] for t in ts if dev(t) > 0]
              for g, ts in GR.items() if any(dev(t) > 0 for t in ts)}
# --- C) validacion: original desde plano vs continuacion
mc = met()
okP = lf(plano=True); mp = met() if okP else None
R["val"] = {"cont": mc, "plano": mp}
valido = bool(okP and abs(mp["slack"] - mc["slack"]) < 1.5 and mp["mon"] and all(u > 0.93 for u in mp["mon"]))
R["valido"] = valido
if GUARDAR and valido:
    lf(); e.Save(); R["guardado"] = True; R["iMod_fin"] = ga(e, "iModified")
else:
    e.DiscardChanges(); R["guardado"] = False
for k, v in keep.items(): ldf.SetAttribute(k, v)
if R["guardado"]:
    # control: los cambios deben quedar solo en este escenario (atributos de operacion)
    o = [x for x in fb.GetContents("*.IntScenario") if x is not e][0]; o.Activate()
    R["ctrl_otro"] = [[x.loc_name, x.av_mode] for x in REN[:5]]
    e.Activate(); R["ctrl_esc"] = [[x.loc_name, x.av_mode] for x in REN[:5]]
R["t"] = round(time.time() - T0)
resultado = R

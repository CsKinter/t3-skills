#!/usr/bin/env python
"""Consulta repetible de metadatos GUI de PowerFactory desde la DB de localización.

Origen de los datos: SQLite en <instalación>\\localisation\\<idioma>\\data.db, tabla
Message(lang, class, param, message). Es un catálogo de cadenas de la GUI localizada:
contiene etiquetas/abbr y a veces el texto de un menú inline — NO es un inventario
completo de atributos/results, NO da valores activos y NO autoriza escrituras en PF.
Cobertura, límites y casos verificados: references/attribute-metadata.md en esta skill.

Solo stdlib. No conecta a PowerFactory (sin COM ni puente). La DB se abre en modo
read-only (URI ?mode=ro + PRAGMA query_only): si la ruta no existe se falla y NUNCA
se crea un archivo nuevo. Todas las consultas van parametrizadas (?).

Ejemplos:
  python pf_attribute_metadata.py --class ComInc --attribute iopt_solvinc
  python pf_attribute_metadata.py --class ElmGenstat --attribute iSimModel
  python pf_attribute_metadata.py --search "A-stable"
  python pf_attribute_metadata.py --class ComInc                 # params de la clase (acotado)
  python pf_attribute_metadata.py --list-classes
  python pf_attribute_metadata.py --schema
  python pf_attribute_metadata.py --class ComInc --output catalogo.csv       # exportar a archivo
  python pf_attribute_metadata.py --export --output catalogo_completo.csv   # tabla completa

La salida por pantalla se acota a --limit (default 40) con indicador de truncado;
la salida amplia (o la tabla completa con --export/--all) exige --output ARCHIVO.
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
import sqlite3
import sys
import urllib.parse

DEFAULT_INSTALL = r"C:\Program Files\DIgSILENT\PowerFactory 2025 SP4"
PF_PARENT = r"C:\Program Files\DIgSILENT"
DEFAULT_LOC = "en-GB"
DISPLAY_LIMIT = 40
CSV_SEP = ";"  # CSV amigable con Excel en locales ES (misma convención de la skill)
MIN_SEARCH_CHARS = 3
_REQUIRED_MSG_COLS = ("lang", "class", "param", "message")

# Heurística conservadora para tablas de códigos de enum SI existieran: la DB
# 2025 SP4 verificada solo tiene «Message» (sin códigos). Si otra instalación
# trajera una tabla (class, param, código, texto), el par de opciones se reporta
# como explicit_row con el código leído de la fila — jamás un código generado.
_CODE_COLS = {"code", "attr_code", "value", "i_val", "nr", "num", "idx", "index", "id"}
_TEXT_COLS = {"text", "message", "label", "name", "description", "s_val", "title"}
_DRIVE = re.compile(r"^[A-Za-z]:/")


class MetadataToolError(RuntimeError):
    """Error con mensaje para el usuario (ruta ausente, esquema inesperado, uso)."""


# ----------------------------------------------------------------------
# Ubicación de la DB y apertura segura
# ----------------------------------------------------------------------

def sqlite_ro_uri(path: str) -> str:
    """URI file:<ruta escapada>?mode=ro.

    En Windows produce file:///C:/... (forma comprobada con la DB real).
    '#' y '?' no van en el safe-set de quote(): un '#' sin escapar cortaría la
    ruta como fragmento de URI; también se escapan espacios y '%'.
    """
    p = os.path.abspath(path)
    if os.name == "nt":
        p = p.replace("\\", "/")
    quoted = urllib.parse.quote(p, safe=":/")
    if _DRIVE.match(quoted):
        quoted = "/" + quoted  # 'C:/...' -> '/C:/...' => 'file:///C:/...'
    return "file://" + quoted + "?mode=ro"


def open_readonly(db_path: str):
    """Abre la DB en solo lectura. No existe => error explícito (nunca crea)."""
    db_path = os.path.abspath(db_path)
    if not os.path.isfile(db_path):
        parent = os.path.dirname(db_path)
        hint = "" if os.path.isdir(parent) else f" (el directorio '{parent}' tampoco existe)"
        raise MetadataToolError(
            f"La DB '{db_path}' no existe{hint}. No se crea ningún archivo nuevo: "
            "revisa --installation / --db / --loc.")
    uri = sqlite_ro_uri(db_path)
    try:
        con = sqlite3.connect(uri, uri=True)
    except sqlite3.Error as exc:
        raise MetadataToolError(f"No se pudo abrir '{db_path}' en solo lectura: {exc}") from exc
    con.execute("PRAGMA query_only=ON")  # refuerzo: cualquier write fallará
    return con, {
        "db": db_path,
        "uri": uri,
        "size_bytes": os.path.getsize(db_path),
    }


def installations_with_db():
    """Roots de instalación PF bajo C:\\Program Files\\DIgSILENT con localisation/*/data.db."""
    pat = os.path.join(PF_PARENT, "PowerFactory*", "localisation", "*", "data.db")
    roots = set()
    for hit in glob.glob(pat):
        roots.add(os.path.dirname(os.path.dirname(os.path.dirname(hit))))
    return sorted(roots)


def resolve_db(args):
    """Escoge --db o compone <instalación>\\localisation\\<--loc>\\data.db.

    Devuelve (ruta_db, root_de_instalación_para_mostrar, localización).
    """
    if args.db:
        db = os.path.abspath(args.db)
        parent = os.path.basename(os.path.dirname(db))
        loc = parent if re.fullmatch(r"[a-z]{2}(-[A-Za-z]{2})?", parent) else "-"
        return db, "-", loc
    root = args.installation or DEFAULT_INSTALL
    if not os.path.isdir(root):
        cand = installations_with_db()
        if cand and not args.installation:
            # sin default y sin flag: usa la última instal. disponible (orden alfabético);
            # lo honesto es pasar --installation explícito
            root = cand[-1]
        else:
            found = ", ".join(cand) or "(ninguna)"
            raise MetadataToolError(
                f"La instalación '{root}' no existe. Encontradas bajo '{PF_PARENT}': {found}. "
                "Indica --installation explícita.")
    db = os.path.join(root, "localisation", args.loc, "data.db")
    if os.path.isfile(db):
        return db, root, args.loc
    locdir = os.path.join(root, "localisation")
    avail = []
    if os.path.isdir(locdir):
        avail = sorted(d for d in os.listdir(locdir)
                       if os.path.isfile(os.path.join(locdir, d, "data.db")))
    raise MetadataToolError(
        f"No se encuentra '{db}'. data.db disponibles bajo '{locdir}'"
        + (": " + ", ".join(avail) if avail else ": (nada)")
        + ". Elige otro --loc o pásalo directo con --db.")


def open_db(args):
    db, root, loc = resolve_db(args)
    con, prov = open_readonly(db)
    prov["install_root"] = root
    prov["loc"] = loc
    return con, prov


# ----------------------------------------------------------------------
# Esquema y detección conservadora de tablas de códigos
# ----------------------------------------------------------------------

def list_tables(con):
    rows = con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    return [r[0] for r in rows]

def table_columns(con, table):
    q = '"' + table.replace('"', '""') + '"'
    cur = con.execute(f"SELECT * FROM {q} LIMIT 0")
    return [d[0] for d in cur.description]


def validate_schema(con, prov):
    """Valida Message(lang,class,param,message) y llena cabecera de procedencia."""
    try:
        tables = list_tables(con)
    except sqlite3.DatabaseError as exc:  # p. ej. «file is not a database»
        raise MetadataToolError(f"La DB no es SQLite legible o está corrupta: {exc}") from exc
    prov["tables"] = tables
    prov["enum_candidates"] = find_enum_candidates(con, tables)
    if "Message" not in tables:
        shown = ", ".join(tables[:12]) or "(ninguna)"
        raise MetadataToolError(
            f"Esquema inesperado: no hay tabla 'Message' (tablas: {shown}). "
            "No parece una DB de localización de PF: revisa --installation/--db.")
    cols = [c.lower() for c in table_columns(con, "Message")]
    missing = [c for c in _REQUIRED_MSG_COLS if c not in cols]
    if missing:
        raise MetadataToolError(
            f"Esquema inesperado: Message no tiene columnas {missing} (tiene: {cols}). "
            "Revisa --installation/--db.")
    try:
        prov["total_rows"] = con.execute("SELECT COUNT(*) FROM Message").fetchone()[0]
        prov["langs"] = dict(con.execute(
            "SELECT lang, COUNT(*) FROM Message GROUP BY lang ORDER BY lang").fetchall())
    except sqlite3.DatabaseError as exc:  # p. ej. «not a database»
        raise MetadataToolError(f"La DB no es SQLite legible o está corrupta: {exc}") from exc
    return prov


def find_enum_candidates(con, tables):
    """Tablas distintas de Message que se parecen a (class, param, código, texto)."""
    out = {}
    for t in tables:
        if t.lower() == "message":
            continue
        try:
            cols = [c.lower() for c in table_columns(con, t)]
        except sqlite3.DatabaseError:
            continue
        if ({"class", "param"} <= set(cols)
                and (set(cols) & _CODE_COLS) and (set(cols) & _TEXT_COLS)):
            code_col = sorted(set(cols) & _CODE_COLS)[0]
            text_col = sorted(set(cols) & _TEXT_COLS)[0]
            out[t] = {"code_col": code_col, "text_col": text_col}
    return out


def enum_rows_for(con, enum_cands, cls: str, attr: str):
    """Filas explícitas (class, param) en tablas de códigos, por rowid."""
    found = []
    for t, info in (enum_cands or {}).items():
        q = '"' + t.replace('"', '""') + '"'
        cc = '"' + info["code_col"].replace('"', '""') + '"'
        tc = '"' + info["text_col"].replace('"', '""') + '"'
        try:
            rows = con.execute(
                f"SELECT {cc}, {tc} FROM {q} WHERE class = ? AND param = ? ORDER BY rowid",
                (cls, attr)).fetchall()
        except sqlite3.DatabaseError:
            continue
        for code, text in rows:
            found.append({"table": t,
                          "code": None if code is None else str(code),
                          "text": text})
    return found


# ----------------------------------------------------------------------
# Parseo de message: SOLO filas lang='en' (texto de GUI). Comentarios crudos.
# ----------------------------------------------------------------------

def parse_en_message(raw: str):
    """Devuelve (label, abreviatura|'', opciones|None).

    - '|' dentro de la etiqueta: 'etiqueta|abreviatura' (ej. ComInc.iopt_lt).
    - El primer ':' separa la etiqueta del resto; el resto son opciones inline
      en el orden del mensaje (ej. ElmGenstat.iSimModel 'Model:op 1:op 2').
      Sin ':' => etiqueta sin opciones.
    - Si el mensaje empieza por ':' no se interpreta como menú: queda crudo.
    - Jamás se generan códigos numéricos: códigos que no están se reportan como
      desconocidos (ver rows_to_dicts).
    """
    label = raw
    abbrev = ""
    options = None
    if ":" in raw:
        first, rest = raw.split(":", 1)
        if first == "":
            label = raw
            options = None
        else:
            label = first
            options = rest.split(":") if rest else None
    if "|" in label:
        a, b = label.split("|", 1)
        label, abbrev = a, b
    return label, abbrev, options


def rows_to_dicts(con, rows, prov, cls=None, attr=None):
    """Filas crudas -> dicts con label/opciones y fuente clara; mensaje preservado.

    Acepta filas (lang, param, message) — consultas con la clase fija — o
    (lang, class, param, message) — export de la tabla completa: la clase sale
    de la fila. Todos los caminos usan consultas parametrizadas y jamás
    fabrican códigos; ver parse_en_message.
    """
    dicts = []
    for row in rows:
        if len(row) == 4:
            lang, row_class, param, message = row
        else:
            lang, param, message = row
            row_class = cls
        d = {
            "db": prov["db"],
            "lang": lang,
            "class": row_class,
            "param": param,
            "message": message,  # mensaje crudo preservado íntegro
        }
        if lang == "en":
            label, abbrev, options = parse_en_message(message)
            d["label"] = label
            d["label_abbrev"] = abbrev or None
            d["inline_options"] = options
            d["attr_codes"] = None
            if options is not None:
                expl = enum_rows_for(con, prov["enum_candidates"],
                                     d["class"] or "", attr or param)
                if expl:
                    tables = ", ".join(sorted({e["table"] for e in expl}))
                    d["option_source"] = f"explicit_row ({tables})"
                    if len(expl) == len(options):
                        d["attr_codes"] = [e["code"] for e in expl]
                else:
                    d["option_source"] = ("inline_sequence (Message, lang=en, orden del "
                                          "mensaje; la DB no trae tabla de códigos)")
            else:
                d["option_source"] = "sin opciones en el mensaje"
        else:
            d["label"] = None
            d["label_abbrev"] = None
            d["inline_options"] = None
            d["attr_codes"] = None
            d["option_source"] = f"sin parsear (lang={lang})"
        dicts.append(d)
    return dicts


# ----------------------------------------------------------------------
# Consultas (siempre parametrizadas); limit None => sin LIMIT (solo export)
# ----------------------------------------------------------------------

def _escape_like(text: str) -> str:
    return re.sub(r"([\\%_])", r"\\\1", text)


def fetch_class_param(con, cls, attr):
    return con.execute(
        "SELECT lang, param, message FROM Message WHERE class = ? AND param = ? ORDER BY lang",
        (cls, attr)).fetchall()


def fetch_class_params(con, cls, limit=None):
    total = con.execute(
        "SELECT COUNT(DISTINCT param) FROM Message WHERE class = ?", (cls,)).fetchone()[0]
    sql = "SELECT DISTINCT param FROM Message WHERE class = ? ORDER BY param"
    params: list = [cls]
    if limit is not None:
        sql += " LIMIT ?"
        params.append(int(limit))
    return [r[0] for r in con.execute(sql, params)], total


def fetch_class_rows(con, cls):
    return con.execute(
        "SELECT lang, param, message FROM Message WHERE class = ? ORDER BY param, lang",
        (cls,)).fetchall()


def fetch_classes(con, search=None, limit=None):
    where, params = "", []
    if search:
        where = " WHERE class LIKE ? ESCAPE '\\' "
        params = ["%" + _escape_like(search) + "%"]
    total = con.execute(f"SELECT COUNT(DISTINCT class) FROM Message{where}", params).fetchone()[0]
    sql = f"SELECT DISTINCT class FROM Message{where} ORDER BY class"
    if limit is not None:
        sql += " LIMIT ?"
        params.append(int(limit))
    return [r[0] for r in con.execute(sql, params)], total


def fetch_search(con, search, field, cls=None, limit=None):
    like = "%" + _escape_like(search) + "%"
    conds, params = [], []
    if field in ("param", "any"):
        conds.append("param LIKE ? ESCAPE '\\'")
        params.append(like)
    if field in ("message", "any"):
        conds.append("message LIKE ? ESCAPE '\\'")
        params.append(like)
    if cls:
        conds.append("class = ?")
        params.append(cls)
    where = " WHERE (" + " OR ".join(conds) + ") "
    total = con.execute(f"SELECT COUNT(*) FROM Message{where}", params).fetchone()[0]
    sql = f"SELECT lang, class, param, message FROM Message{where}ORDER BY class, param, lang"
    if limit is not None:
        sql += " LIMIT ?"
        params.append(int(limit))
    return con.execute(sql, params).fetchall(), total


# ----------------------------------------------------------------------
# Presentación y exportación
# ----------------------------------------------------------------------

def render_head(prov, install_root: str):
    m = re.search(r"PowerFactory\s+([\d.]+(?:\s*SP\d+)?)", install_root or "")
    ver = f" — versión (por ruta): PowerFactory {m.group(1)}" if m else ""
    cands = (", ".join(sorted(prov["enum_candidates"]))
             if prov["enum_candidates"] else "(ninguna)")
    langs = "; ".join(f"{k}={v:,}" for k, v in prov["langs"].items())
    return [
        f"# DB: {prov['db']} (solo lectura mode=ro; {prov['size_bytes'] / (1024 * 1024):.1f} MiB){ver}",
        f"# esquema: Message(lang,class,param,message); tablas: {', '.join(prov['tables']) or '(ninguna)'}",
        f"# tablas de códigos de enum: {cands}; total Message: {prov['total_rows']:,} filas ({langs})",
        f"# instalación/localización: {install_root or '-'} / {prov['loc']} — metadatos GUI "
        "localizados: NO inventario completo de atributos, NO valores activos",
    ]


def render_block(d):
    need = f"{d['class']}.{d['param']}"
    if d["lang"] != "en":
        return f"{need}\n  [{d['lang']}] {d['param']}: {d['message']}"
    opts = d["inline_options"]
    op_txt = ("ninguna en el mensaje" if opts is None
              else "; ".join(f"[{i}] {o}" for i, o in enumerate(opts)))
    abbrev = f" | abreviatura: {d['label_abbrev']}" if d["label_abbrev"] else ""
    codes = ("" if not d["attr_codes"]
             else f" (códigos de la DB: [{', '.join(str(c) for c in d['attr_codes'])}])")
    return (f"{need}\n"
            f"  lang=en; fuente: {d['option_source']}\n"
            f"  etiqueta: {d['label']}{abbrev}\n"
            f"  opciones inline: {op_txt}{codes}\n"
            f"  message(crudo): {d['message']}")


def render_compact(d):
    if d["lang"] != "en":
        return f"{d['class']}.{d['param']} [{d['lang']}] {d['message']}"
    tail = f" etiqueta: {d['label']}"
    if d["label_abbrev"]:
        tail += f" ({d['label_abbrev']})"
    if d["inline_options"]:
        tail += " opciones: " + " | ".join(d["inline_options"])
        if d["attr_codes"]:
            tail += f" (códigos {','.join(str(c) for c in d['attr_codes'])})"
    return f"{d['class']}.{d['param']} [{d['lang']}]{tail}"


def trunc_note(shown: int, total: int) -> str:
    if total > shown:
        return (f">> Truncado: {total:,} filas coinciden y se mostraron {shown}. "
                "Para exportar todas: --output ARCHIVO.")
    return ""


def ensure_export_path(out, db, overwrite):
    out = os.path.abspath(out)
    db = os.path.abspath(db)
    if os.path.isdir(out):
        raise MetadataToolError(f"--output es un directorio: '{out}' (indica un archivo).")
    if os.path.normcase(out) == os.path.normcase(db):
        raise MetadataToolError(
            f"--output no puede apuntar al mismo archivo que la DB ('{db}'): "
            "la exportación no debe pisar los metadatos. Elige otra ruta.")
    if os.path.exists(out) and not overwrite:
        raise MetadataToolError(
            f"El archivo de salida ya existe: '{out}'. Pasa --overwrite para reemplazarlo.")
    parent = os.path.dirname(out)
    if not os.path.isdir(parent):
        raise MetadataToolError(f"El directorio destino no existe: '{parent}'.")
    return out


def _csv_cell(v):
    if v is None:
        return ""
    if isinstance(v, list):
        return "; ".join(str(x) for x in v)
    return v


def write_export(out, fmt, columns, dicts, prov):
    if fmt == "json":
        with open(out, "w", encoding="utf-8") as fh:
            json.dump({
                "provenance": {
                    "db": prov["db"],
                    "install_root": prov.get("install_root"),
                    "loc": prov.get("loc"),
                    "total_rows": prov["total_rows"],
                    "langs": prov["langs"],
                    "schema_tables": prov["tables"],
                    "enum_candidates": prov["enum_candidates"],
                },
                "columns": columns,
                "rows": dicts,
            }, fh, ensure_ascii=False, indent=2)
    else:
        with open(out, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh, delimiter=CSV_SEP)
            w.writerow(columns)
            for d in dicts:
                w.writerow([_csv_cell(d.get(c)) for c in columns])


_ROW_COLUMNS = ["db", "lang", "class", "param", "message", "label",
                "label_abbrev", "inline_options", "attr_codes", "option_source"]


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        prog="pf_attribute_metadata.py",
        description="Consulta de metadatos GUI (etiquetas y opciones) por parámetro "
                    "desde la DB de localización del PowerFactory instalado "
                    "(SQLite solo lectura; no conecta a PF). Cobertura y límites: "
                    "references/attribute-metadata.md en esta skill.",
        epilog="--search puede filtrar dentro de --class; --list-classes --search TXT "
               "filtra clases. La exportación amplia exige --output ARCHIVO.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group()
    src.add_argument("--installation", metavar="DIR",
                     help=f"root de instalación PF (default: {DEFAULT_INSTALL})")
    src.add_argument("--db", metavar="FILE",
                     help="ruta directa al data.db (debe existir; nunca se crea ni pisa)")
    p.add_argument("--loc", default=DEFAULT_LOC,
                   help="directorio de localización bajo localisation\\ (default en-GB)")
    p.add_argument("--class", dest="iclass", metavar="CLASE",
                   help="clase (con --attribute: consulta exacta; solo: lista sus params)")
    p.add_argument("--attribute", dest="iattribute", metavar="PARAM",
                   help="nombre del atributo; requiere --class")
    p.add_argument("--search", metavar="TEXTO",
                   help=f"búsqueda textual acotada en param/message (min "
                        f"{MIN_SEARCH_CHARS} caracteres)")
    p.add_argument("--search-in", dest="search_in", choices=("any", "param", "message"),
                   default="any", help="campo de la búsqueda textual (default any)")
    p.add_argument("--list-classes", action="store_true",
                   help="lista de clases distintas (acotada; --search filtra)")
    p.add_argument("--schema", action="store_true",
                   help="tablas/columnas y conteos de la DB (no exporta)")
    p.add_argument("--limit", type=int, default=DISPLAY_LIMIT,
                   help=f"límite de filas en pantalla (default {DISPLAY_LIMIT})")
    p.add_argument("--export", "--all", dest="export_all", action="store_true",
                   help="exportar a archivo en vez de pantalla (equivale a dar --output); "
                        "sin filtros exporta la tabla completa")
    p.add_argument("--output", metavar="ARCHIVO",
                   help="archivo de exportación (resuelto; no puede ser el mismo data.db)")
    p.add_argument("--format", choices=("csv", "json"), default="csv",
                   help="formato de exportación (default csv ';' + utf-8-sig)")
    p.add_argument("--overwrite", action="store_true",
                   help="reemplaza el archivo de salida si ya existe")
    return p


def validate_usage(args):
    if args.iattribute and not args.iclass:
        raise MetadataToolError("--attribute requiere --class.")
    if args.iattribute and args.search is not None:
        raise MetadataToolError("Elige un modo: --class --attribute (exacto) o --search (texto).")
    if args.search is not None and len(args.search) < MIN_SEARCH_CHARS:
        raise MetadataToolError(
            f"--search pide al menos {MIN_SEARCH_CHARS} caracteres (búsqueda textual "
            "acotada); para una consulta exacta usa --class --attribute.")
    if args.limit is not None and args.limit < 1:
        raise MetadataToolError("--limit debe ser >= 1.")
    if args.export_all and not args.output:
        raise MetadataToolError(
            "--export/--all requiere --output ARCHIVO (la salida normal por pantalla está "
            f"acotada a {DISPLAY_LIMIT} filas; la tabla completa no se imprime).")
    if args.output and args.schema:
        raise MetadataToolError("--schema es informativo por pantalla; no exporta.")


def run_display(args, con, prov, print_fn):
    """Modos de pantalla (limit acota); sin dump de la tabla completa."""
    if args.schema:
        print_fn(f"# tablas: {', '.join(prov['tables'])}")
        print_fn(f"# total Message: {prov['total_rows']:,} filas; langs: {prov['langs']}")
        print_fn("# tablas de códigos de enum (heurística class/param/código/texto): "
                 + (", ".join(sorted(prov["enum_candidates"])) or "(ninguna)"))
        return
    if args.iclass and args.iattribute:
        rows = fetch_class_param(con, args.iclass, args.iattribute)
        dicts = rows_to_dicts(con, rows, prov, args.iclass, args.iattribute)
        if not dicts:
            print_fn(f"Sin filas para {args.iclass}.{args.iattribute} en esta DB. "
                     "Ausencia aquí NO es 'no existe': repórtalo como desconocido "
                     "(ver references/attribute-metadata.md).")
            return
        for d in dicts:
            print_fn(render_block(d))
        return
    if args.list_classes:
        classes, total = fetch_classes(con, args.search, args.limit)
        print_fn(f"# clases distintas en la DB: {total:,}; mostradas {len(classes)} (límite {args.limit})")
        if not classes:
            print_fn("(ninguna)")
        else:
            for c in classes:
                print_fn(c)
            note = trunc_note(len(classes), total)
            if note:
                print_fn(note)
        return
    if args.iclass:
        params, total = fetch_class_params(con, args.iclass, args.limit)
        print_fn(f"# clase {args.iclass}: {total:,} params distintos; mostrados {len(params)} "
                 "(solo nombres; consulta etiqueta/opciones con --attribute)")
        if not params:
            print_fn(f"Sin params para la clase '{args.iclass}' en esta DB "
                     "(ausencia aqui no prueba inexistencia del atributo).")
            return
        for pr in params:
            print_fn(pr)
        note = trunc_note(len(params), total)
        if note:
            print_fn(note)
        return
    if args.search:
        rows, total = fetch_search(con, args.search, args.search_in, args.iclass, args.limit)
        dicts = rows_to_dicts(con, rows, prov)
        print_fn(f"# búsqueda textual '{args.search}' ({args.search_in}): {total:,} filas "
                 f"coinciden; mostradas {len(dicts)} (límite {args.limit})")
        for d in dicts:
            print_fn(render_compact(d))
        note = trunc_note(len(dicts), total)
        if note:
            print_fn(note)
        return
    raise MetadataToolError(
        "Indica un modo: --class [--attribute] | --search TEXTO | --list-classes | --schema.")


def run_export(args, con, prov):
    """Exporta a archivo ARCHIVO la selección (o la tabla completa sin filtros)."""
    out = ensure_export_path(args.output, prov["db"], args.overwrite)
    if args.list_classes:
        classes, _ = fetch_classes(con, args.search, None)
        dicts = [{"class": c} for c in classes]
        write_export(out, args.format, ["class"], dicts, prov)
        return len(dicts), out
    if args.iclass and args.iattribute:
        rows = fetch_class_param(con, args.iclass, args.iattribute)
        dicts = rows_to_dicts(con, rows, prov, args.iclass, args.iattribute)
    elif args.iclass:
        dicts = rows_to_dicts(con, fetch_class_rows(con, args.iclass), prov, args.iclass)
    elif args.search:
        rows, _ = fetch_search(con, args.search, args.search_in, args.iclass, None)
        dicts = rows_to_dicts(con, rows, prov)
    else:
        rows = con.execute(
            "SELECT lang, class, param, message FROM Message ORDER BY class, param, lang"
        ).fetchall()
        dicts = rows_to_dicts(con, rows, prov)
    write_export(out, args.format, _ROW_COLUMNS, dicts, prov)
    return len(dicts), out


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        validate_usage(args)
        con, prov = open_db(args)
    except MetadataToolError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    try:
        validate_schema(con, prov)
        if args.schema:
            for line in render_head(prov, prov["install_root"]):
                print(line)
            run_display(args, con, prov, print)
            return 0
        if args.output:
            n_rows, out = run_export(args, con, prov)
            print(f"# exportación OK: {n_rows:,} filas -> '{out}' (formato {args.format}, "
                  "datos no impresos en pantalla)")
            return 0
        print_fn = print
        for line in render_head(prov, prov["install_root"]):
            print_fn(line)
        run_display(args, con, prov, print_fn)
        return 0
    except MetadataToolError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except sqlite3.DatabaseError as exc:
        print(f"Error: la DB falló al consultar ({exc}).", file=sys.stderr)
        return 1
    finally:
        try:
            con.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())

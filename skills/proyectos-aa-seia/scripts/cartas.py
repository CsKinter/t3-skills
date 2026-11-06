#!/usr/bin/env python3
"""Buscador de cartas del Coordinador Electrico Nacional (cartas.coordinador.cl).

Uso:
    python cartas.py buscar "Andes Solar S.A." --desde 01/01/2024 --hasta 02/11/2026
    python cartas.py buscar "Transemel" --detalle
    python cartas.py show 69820dab3563571d7543be86
    python cartas.py bajar 69820dab3563571d7543be86 salida.pdf

Notas:
- El parametro `q` (texto libre) del buscador esta roto en el servidor: devuelve
  "No se encontraron resultados" para cualquier termino, incluso para uno que
  existe. Filtrar por empresa y periodo, y leer la columna "Referencia".
- El nombre de la empresa debe ser exacto como aparece en /api/empresas.
  "Andes Solar S.A." (con punto) y "Andes Solar S.A" (sin punto) devuelven
  conjuntos distintos. Probar las dos.
- Los anexos marcados "es confidencial" no se descargan, pero el PDF principal
  de la carta suele estar en /download_saved_file/<id> y a veces si se baja.
"""
import argparse
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://cartas.coordinador.cl"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def _dec(raw):
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def _get(url, data=None, timeout=90):
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers={
        "User-Agent": UA,
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "text/html,application/json,*/*",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return _dec(r.read())


class _ShowParser(HTMLParser):
    """Extrae pares etiqueta/valor de la ficha /show/<id>."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pairs = {}
        self._in_label = False
        self._in_value = False
        self._depth = 0
        self._buf = []
        self._last_label = None

    def handle_starttag(self, tag, attrs):
        cls = dict(attrs).get("class", "")
        if tag == "span" and "show-label" in cls:
            self._in_label = True
            self._buf = []
        elif tag == "div" and "show-value" in cls and self._last_label:
            self._in_value = True
            self._depth = 0
            self._buf = []
        elif tag == "div" and self._in_value:
            self._depth += 1

    def handle_endtag(self, tag):
        if tag == "span" and self._in_label:
            self._in_label = False
            self._last_label = " ".join("".join(self._buf).split())
            self._buf = []
        elif tag == "div" and self._in_value:
            if self._depth == 0:
                self._in_value = False
                val = " ".join("".join(self._buf).split())
                if self._last_label and self._last_label not in self.pairs:
                    self.pairs[self._last_label] = val
                self._last_label = None
            else:
                self._depth -= 1

    def handle_data(self, data):
        if self._in_label or self._in_value:
            self._buf.append(data)


def show(doc_id):
    p = _ShowParser()
    p.feed(_get(f"{BASE}/show/{doc_id}"))
    return p.pairs


def buscar(empresa, desde, hasta, page=1, detalle=False):
    periodo = f"{desde} 00:00:00 - {hasta} 23:59:59"
    url = f"{BASE}/search?" + urllib.parse.urlencode({
        "q": "", "empresa": empresa, "model_type": "todos", "correlativo": "",
        "periodo_reporte": periodo, "page": page})
    page_html = _get(url)
    ids = []
    for m in re.finditer(r"/show/([a-f0-9]{24})", page_html):
        if m.group(1) not in ids:
            ids.append(m.group(1))
    total = re.search(r"total de (\d+) cartas", page_html)
    print(f"# {len(ids)} cartas en la pagina {page}"
          + (f" (total {total.group(1)})" if total else ""))
    for doc_id in ids:
        if detalle:
            d = show(doc_id)
            print(f"{doc_id} | {d.get('Nº Envío','')} | {d.get('Fecha del Documento','')} "
                  f"| {d.get('Referencia (Palabras Clave)','')}")
        else:
            print(f"{doc_id} | {BASE}/show/{doc_id}")
    return ids


def bajar(doc_id, out):
    req = urllib.request.Request(f"{BASE}/download_saved_file/{doc_id}",
                                 headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180) as r, open(out, "wb") as f:
        f.write(r.read())
    print(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("buscar", help="buscar por empresa y periodo")
    b.add_argument("empresa")
    b.add_argument("--desde", default="01/01/2024")
    b.add_argument("--hasta", default="31/12/2026")
    b.add_argument("--page", type=int, default=1)
    b.add_argument("--detalle", action="store_true")

    s = sub.add_parser("show", help="ficha de una carta")
    s.add_argument("id")

    d = sub.add_parser("bajar", help="descargar el PDF principal")
    d.add_argument("id")
    d.add_argument("salida")

    a = ap.parse_args()
    if a.cmd == "buscar":
        buscar(a.empresa, a.desde, a.hasta, a.page, a.detalle)
    elif a.cmd == "show":
        for k, v in show(a.id).items():
            print(f"{k}: {v}")
    elif a.cmd == "bajar":
        bajar(a.id, a.salida)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        pass

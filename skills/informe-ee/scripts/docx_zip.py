"""Desarmar y rearmar un .docx para editar su XML a mano (no hay `zip` en la bash de Windows).

    python docx_zip.py extraer informe.docx carpeta_unz
    python docx_zip.py armar carpeta_unz informe_original.docx informe_nuevo.docx

Al armar se respeta el orden del zip original ([Content_Types].xml primero) y se agregan al final los archivos nuevos
de la carpeta (p. ej. imágenes en word/media) que el original no tenía. Si se agregan PNG, verificar que
[Content_Types].xml tenga <Default Extension="png" ContentType="image/png"/> (asegurar_png lo hace).
"""
import os
import re
import sys
import zipfile


def extraer(docx, carpeta):
    with zipfile.ZipFile(docx) as z:
        z.extractall(carpeta)


def asegurar_png(carpeta):
    p = os.path.join(carpeta, "[Content_Types].xml")
    s = open(p, encoding="utf-8").read()
    if 'Extension="png"' not in s:
        s = re.sub(r"(<Types[^>]*>)", r'\1<Default Extension="png" ContentType="image/png"/>', s, count=1)
        open(p, "w", encoding="utf-8").write(s)


def armar(carpeta, original, nuevo):
    asegurar_png(carpeta)
    with zipfile.ZipFile(original) as zo:
        nombres = [i.filename for i in zo.infolist()]
    todos = []
    for raiz, _, archivos in os.walk(carpeta):
        for a in archivos:
            todos.append(os.path.relpath(os.path.join(raiz, a), carpeta).replace(os.sep, "/"))
    orden = [n for n in nombres if n in todos] + sorted(n for n in todos if n not in nombres)
    if "[Content_Types].xml" in orden:
        orden.remove("[Content_Types].xml"); orden.insert(0, "[Content_Types].xml")
    with zipfile.ZipFile(nuevo, "w", zipfile.ZIP_DEFLATED) as zn:
        for n in orden:
            zn.write(os.path.join(carpeta, n), n)
    return nuevo


if __name__ == "__main__":
    if sys.argv[1] == "extraer":
        extraer(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "armar":
        print(armar(sys.argv[2], sys.argv[3], sys.argv[4]))
    else:
        print(__doc__)

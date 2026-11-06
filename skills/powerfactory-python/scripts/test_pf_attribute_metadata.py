#!/usr/bin/env python
"""Tests stdlib de pf_attribute_metadata.py (sin DB real ni PowerFactory).

Ejecutar:  python scripts\\test_pf_attribute_metadata.py

Cubre lo que pide references/attribute-metadata.md: ruta ausente no se crea,
esquema inesperado, espacios/'#' en ruta (URI), consultas parametrizadas
(inyección en search y nombres con comillas), límite de pantalla con indicador
de truncado, inline_options sin códigos inventados y fuente estable,
explicit_row solo si existe tabla de códigos, --export exige --output y
--output nunca apunta al mismo archivo DB.
"""

from __future__ import annotations

import csv
import io
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pf_attribute_metadata as pfm  # noqa: E402


def _mk_db(path, rows, extra_tables=None):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE Message(lang, class, param, message)")
    con.executemany("INSERT INTO Message VALUES (?,?,?,?)", rows)
    for table, cols, trows in (extra_tables or []):
        con.execute(f"CREATE TABLE {table}({', '.join(cols)})")
        ph = ", ".join("?" * len(cols))
        con.executemany(f"INSERT INTO {table} VALUES ({ph})", trows)
    con.commit()
    con.close()
    return path


class PfAttributeMetadataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pfmd_test_")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    # --- helpers -------------------------------------------------------
    def db(self, name="data.db", rows=None, schema=True, extra_tables=None):
        p = os.path.join(self.tmp, name)
        if schema is True:
            return _mk_db(p, rows or [], extra_tables)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("this is NOT a sqlite file")
        return p

    def run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = pfm.main(argv)
        return rc, out.getvalue(), err.getvalue()

    # --- rutas, apertura, esquema --------------------------------------
    def test_missing_db_is_not_created(self):
        p = os.path.join(self.tmp, "no", "falta.db")
        self.assertEqual(os.path.dirname(p), self.tmp + os.sep + "no")
        with self.assertRaises(pfm.MetadataToolError) as ctx:
            pfm.open_readonly(p)
        self.assertIn("no existe", str(ctx.exception))
        self.assertFalse(os.path.exists(p), "no debe crearse ningún archivo")
        self.assertFalse(os.path.exists(os.path.dirname(p)))

    def test_path_with_spaces_and_hash(self):
        sub = os.path.join(self.tmp, "dir con espacio y #num", "sub#dir")
        os.makedirs(sub)
        p = os.path.join(sub, "meta #db.db")
        db = _mk_db(p, [("en", "ComX", "a_b", "Label one")])
        con, prov = pfm.open_readonly(db)  # URI mode=ro con espacios y '#'
        self.assertEqual(pfm.fetch_class_param(con, "ComX", "a_b"),
                         [("en", "a_b", "Label one")])
        self.assertIn("#", con.execute("SELECT 'ok#literal'").fetchone()[0])
        con.close()
        self.assertTrue(os.path.isfile(db), "la DB debió seguir existiendo")

    def test_schema_without_message_table(self):
        # DB solo con otra tabla: helper db() siempre trae Message, se hace directo
        p = os.path.join(self.tmp, "sin_message.db")
        con = sqlite3.connect(p)
        con.execute("CREATE TABLE Otra(lang, class, param, message)")
        con.commit()
        con.close()
        con, prov = pfm.open_readonly(p)
        with self.assertRaises(pfm.MetadataToolError) as ctx:
            pfm.validate_schema(con, prov)
        self.assertIn("no hay tabla 'Message'", str(ctx.exception))
        con.close()

    def test_schema_message_bad_columns(self):
        p = os.path.join(self.tmp, "badcols.db")
        con = sqlite3.connect(p)
        con.execute("CREATE TABLE Message(lang, class)")  # faltan param/message
        con.commit()
        con.close()
        con, prov = pfm.open_readonly(p)
        with self.assertRaises(pfm.MetadataToolError) as ctx:
            pfm.validate_schema(con, prov)
        self.assertIn("columnas", str(ctx.exception))
        con.close()

    def test_not_a_database(self):
        p = self.db(schema=False)
        con, prov = pfm.open_readonly(p)
        with self.assertRaises(pfm.MetadataToolError) as ctx:
            pfm.validate_schema(con, prov)
        self.assertIn("no es SQLite legible", str(ctx.exception))
        con.close()

    # --- consultas parametrizadas y límites ----------------------------
    def test_parameterized_queries(self):
        db = self.db(rows=[
            ("en", "Com'Inc", "i; DROP TABLE", "Etiqueta 'rara' con -"),
            ("comment", "Com'Inc", "i; DROP TABLE", "comentario 'raro'"),
            ("en", "ComInc", "iopt_solvinc",
             "Solve dynamic model equations at initialisation"),
        ])
        con, prov = pfm.open_readonly(db)
        pfm.validate_schema(con, prov)
        self.assertEqual(len(pfm.fetch_class_param(con, "Com'Inc", "i; DROP TABLE")), 2)
        self.assertEqual(pfm.fetch_class_param(con, "ComInc", "iopt_solvinc"), [
            ("en", "iopt_solvinc", "Solve dynamic model equations at initialisation")])
        rows, total = pfm.fetch_search(con, "' OR 1=1 --", "any")
        self.assertEqual((rows, total), ([], 0), "la inyección no debe matchear nada")
        self.assertEqual(pfm.fetch_classes(con, "Com'")[0], ["Com'Inc"])
        con.close()

    def test_search_like_wildcards_are_escaped(self):
        db = self.db(rows=[
            ("en", "C", "p1", "contiene 100% arriba"),
            ("en", "C", "p2", "otro texto"),
        ])
        con, prov = pfm.open_readonly(db)
        rows, total = pfm.fetch_search(con, "100%", "message")
        self.assertEqual([r[2] for r in rows], ["p1"])  # '%' literal, no comodín
        con.close()

    def test_display_limit_with_truncation_marker(self):
        rows = [("en", "K", f"p{i:03d}", f"etiqueta {i}") for i in range(55)]
        db = self.db(rows=rows)
        rc, out, err = self.run_main(["--db", db, "--class", "K"])
        self.assertEqual(rc, 0, err)
        self.assertIn("# clase K: 55", out)
        self.assertIn("mostrados 40", out)
        self.assertIn("Truncado: 55", out)
        self.assertIn("p039", out)
        self.assertNotIn("p040", out)
        self.assertIn("# DB:", out)

    def test_exact_query_absence_is_not_membership(self):
        db = self.db(rows=[("en", "C", "x", "hola")])
        rc, out, err = self.run_main(["--db", db, "--class", "C", "--attribute", "no_esta"])
        self.assertEqual(rc, 0, err)
        self.assertIn("Ausencia aquí NO es 'no existe'", out)

    # --- opciones inline: sin códigos inventados, fuente estable -------
    def test_parse_en_message_cases(self):
        label, abbrev, options = pfm.parse_en_message(
            "Solve dynamic model equations at initialisation")
        self.assertEqual((label, abbrev, options),
                         ("Solve dynamic model equations at initialisation", "", None))
        label, abbrev, options = pfm.parse_en_message(
            "A-stable integration algorithm|A-stable alg.")
        self.assertEqual((label, abbrev, options),
                         ("A-stable integration algorithm", "A-stable alg.", None))
        label, abbrev, options = pfm.parse_en_message(
            "Model:Según señales de entrada conectadas:fuente de corriente:fuente de tensión")
        self.assertEqual(options, ["Según señales de entrada conectadas",
                                   "fuente de corriente", "fuente de tensión"])
        label, abbrev, options = pfm.parse_en_message(":raro")
        self.assertEqual((label, abbrev, options), (":raro", "", None))

    def test_inline_options_without_enum_table_no_codes(self):
        db = self.db(rows=[
            ("en", "ElmGenstat", "iSimModel",
             "Model:Según señales de entrada conectadas:fuente de corriente"),
            ("en", "ComInc", "iopt_lt", "A-stable integration algorithm|A-stable alg."),
        ])
        con, prov = pfm.open_readonly(db)
        pfm.validate_schema(con, prov)
        dicts = pfm.rows_to_dicts(con, pfm.fetch_class_rows(con, "ElmGenstat"),
                                  prov, "ElmGenstat")
        self.assertEqual(dicts[0]["inline_options"],
                         ["Según señales de entrada conectadas", "fuente de corriente"])
        self.assertIsNone(dicts[0]["attr_codes"], "sin tabla de códigos => unknown")
        self.assertIn("inline_sequence", dicts[0]["option_source"])
        self.assertIn("no trae tabla de códigos", dicts[0]["option_source"])
        self.assertEqual(dicts[0]["message"],
                         "Model:Según señales de entrada conectadas:fuente de corriente")

    def test_explicit_row_only_when_table_and_code_reads_as_is(self):
        db = self.db(
            rows=[("en", "C", "i_x", "Model:alpha:beta")],
            extra_tables=[("AttrCode", ["class", "param", "code", "description"],
                           [("C", "i_x", 0, "alpha"), ("C", "i_x", 1, "beta")])])
        con, prov = pfm.open_readonly(db)
        pfm.validate_schema(con, prov)
        self.assertIn("AttrCode", prov["enum_candidates"])
        dicts = pfm.rows_to_dicts(con, pfm.fetch_class_rows(con, "C"), prov, "C")
        self.assertIn("explicit_row", dicts[0]["option_source"])
        self.assertIn("AttrCode", dicts[0]["option_source"])
        self.assertEqual(dicts[0]["attr_codes"], ["0", "1"], "códigos leídos, no generados")

    def test_comment_rows_stay_raw(self):
        db = self.db(rows=[("comment", "C", "x", "texto: con dos puntos y | raro")])
        con, prov = pfm.open_readonly(db)
        dicts = pfm.rows_to_dicts(con, con.execute(
            "SELECT lang, param, message FROM Message").fetchall(), prov, "C")
        self.assertIsNone(dicts[0]["inline_options"])
        self.assertIn("sin parsear", dicts[0]["option_source"])
        self.assertEqual(dicts[0]["message"], "texto: con dos puntos y | raro")

    # --- exportaciones -------------------------------------------------
    def test_export_requires_output_file(self):
        db = self.db(rows=[("en", "C", "x", "hola")])
        rc, out, err = self.run_main(["--db", db, "--export"])
        self.assertEqual(rc, 1)
        self.assertIn("requiere --output", err)

    def test_output_same_file_as_db_is_refused(self):
        db = self.db(rows=[("en", "C", "x", "hola")])
        rc, out, err = self.run_main(["--db", db, "--class", "C", "--attribute", "x",
                                      "--output", db])
        self.assertEqual(rc, 1)
        self.assertIn("mismo archivo", err)
        # la DB sobrevive intacta
        con = sqlite3.connect(db)
        self.assertEqual(con.execute("SELECT COUNT(*) FROM Message").fetchone()[0], 1)
        con.close()

    def test_export_filtered_and_json(self):
        db = self.db(rows=[
            ("en", "C", "k1", "Model:uno:dos"),
            ("comment", "C", "k1", "nota"),
            ("en", "C", "k2", "Simple"),
            ("en", "D", "k1", "otro"),
        ])
        target = os.path.join(self.tmp, "salida_c.json")
        rc, out, err = self.run_main(["--db", db, "--class", "C", "--output", target,
                                      "--format", "json"])
        self.assertEqual(rc, 0, err)
        with open(target, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(len(data["rows"]), 3, "clasifica solo C (2 langs de k1 + k2)")
        self.assertEqual(data["columns"][0], "db")
        self.assertIn("# exportación OK: 3 filas", out)

    def test_export_full_table_without_dumping(self):
        db = self.db(rows=[
            ("en", "A", "a1", "x"), ("en", "B", "b1", "y"), ("comment", "B", "b1", "nota")])
        target = os.path.join(self.tmp, "completo.csv")
        rc, out, err = self.run_main(["--db", db, "--export", "--output", target])
        self.assertEqual(rc, 0, err)
        with open(target, encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.reader(fh, delimiter=pfm.CSV_SEP))
        self.assertEqual(len(rows), 4, "cabecera + 3 filas")
        self.assertEqual(rows[0][0], "db")
        self.assertIn("# exportación OK: 3 filas", out)
        self.assertEqual(len(out.strip().splitlines()), 1,
                         "los datos no se imprimen en pantalla (solo el resumen)")

    def test_export_list_classes(self):
        db = self.db(rows=[("en", "Z", "p", "x"), ("en", "A", "p", "y")])
        target = os.path.join(self.tmp, "clases.csv")
        rc, out, err = self.run_main(["--db", db, "--list-classes", "--output", target])
        self.assertEqual(rc, 0, err)
        with open(target, encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.reader(fh, delimiter=pfm.CSV_SEP))
        self.assertEqual([r[0] for r in rows], ["class", "A", "Z"])
        self.assertEqual(len(out.strip().splitlines()), 1)
    
    # --- esquema / modo informativo -------------------------------------
    def test_schema_mode_prints_counts(self):
        db = self.db(rows=[("en", "A", "p", "x"), ("comment", "A", "p", "n")])
        rc, out, err = self.run_main(["--db", db, "--schema"])
        self.assertEqual(rc, 0, err)
        self.assertIn("# total Message: 2", out)
        self.assertIn("comment=1", out)
        self.assertIn("Message(lang,class,param,message)", out)
        self.assertIn("(ninguna)", out)  # sin tablas de códigos

    def test_wrong_usage_errors(self):
        db = self.db(rows=[])
        for argv in (["--db", db, "--attribute", "x"],
                     ["--db", db, "--search", "ab"],
                     ["--db", db, "--class", "C", "--attribute", "x", "--search", "abc"]):
            rc, out, err = self.run_main(argv)
            self.assertEqual(rc, 1, argv)
            self.assertIn("Error:", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Execute a ComPython file against fake_powerfactory.

    from run_with_fake import run_script
    import fake_powerfactory as pf
    prj = pf.build_project()
    ...build the objects the script expects...
    run_script("mi_script.py", replace={"DRY_RUN = True": "DRY_RUN = False",
                                        "USE_DIALOG = True": "USE_DIALOG = False"})
    assert ...  # inspect pf.APP / objects / pf.LOG afterwards

`replace` does literal text substitution on the script source (config constants, paths).
Run it twice to test idempotency, and once in dry-run mode asserting nothing changed.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import fake_powerfactory  # noqa: E402

sys.modules["powerfactory"] = fake_powerfactory


def run_script(path, replace=None, namespace=None):
    source = Path(path).read_text(encoding="utf-8")
    for old, new in (replace or {}).items():
        if old not in source:
            raise ValueError(f"Text to replace not found in script: {old!r}")
        source = source.replace(old, new)
    ns = {"__name__": "__main__", "__file__": str(path)}
    ns.update(namespace or {})
    exec(compile(source, str(path), "exec"), ns)
    return ns


def load_functions(path, strip_call="\nmain()\n"):
    """Load a script's functions without running its entry point (for unit-testing pieces)."""
    source = Path(path).read_text(encoding="utf-8").replace(strip_call, "\n")
    ns = {"__name__": "pf_script"}
    exec(compile(source, str(path), "exec"), ns)
    return ns

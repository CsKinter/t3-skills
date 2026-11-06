"""Fake of the PowerFactory Python API surface, for testing ComPython scripts outside PowerFactory.

It does NOT validate the real API (attribute names, return codes, units). It catches logic errors:
wrong pointer handling, list vs single-object attributes, dry-run paths that write, missing
idempotency checks, variation/stage flow. Behaviour mirrored from real PowerFactory runs:

- GetFullName() is the stable identity ("\\user\\...\\Grid.ElmNet\\Line.ElmLne").
- An object created in a grid while a stage is recording reports the GRID as its parent;
  the record lives inside the recording IntSstage (visible via stage.GetContents("*", 1)).
- SetAttribute on a grid element while recording adds an entry inside the stage.
- Library objects (types, characteristics, scales) are not recorded by variations.
- AddCopy(obj, name) copies the object and its children (e.g. the "sline.ChaRef" inside a type).

Usage (see run_with_fake.py for executing a whole ComPython file):

    import fake_powerfactory as pf
    prj = pf.build_project()                       # standard folder layout
    grid = prj.grids[0]
    typ = pf.Obj("TypLne", "Cu 250", prj.equip, sline=0.5)
    line = pf.Obj("ElmLne", "A - B 66 kV", grid, typ_id=typ)
    pf.APP.calc_objects.append(line)               # returned by GetCalcRelevantObjects
"""
import copy
import fnmatch

LOG = []
OPERATIVOS = {"outserv", "pgini", "qgini", "plini", "qlini", "usetp", "nntap"}
GRID_CLASSES = {"ElmLne", "ElmTow", "ElmTr2", "ElmTr3", "ElmLod", "ElmSym", "ElmGenstat", "ElmTerm",
                "ElmCoup", "ElmShnt", "ElmPvsys", "ElmBranch", "StaCubic"}


class Obj:
    def __init__(self, cls, name, parent=None, path=None, **attrs):
        self.__dict__.update(_cls=cls, _parent=parent, _children=[], _path=path, _shadow=None,
                             _attrs={"loc_name": name, **attrs})
        if parent is not None:
            parent._children.append(self)

    # Attribute access like PF: obj.typ_id, obj.loc_name = "x"
    def __getattr__(self, k):
        if k in self._attrs:
            return self._attrs[k]
        raise AttributeError(f"{self._cls} has no attribute {k!r}")

    def __setattr__(self, k, v):
        self.SetAttribute(k, v)

    def __repr__(self):
        return f"<{self.GetFullName()}>"

    def GetClassName(self):
        return self._cls

    def GetParent(self):
        return self._parent

    def GetFullName(self):
        if self._path:
            return self._path
        prefix = self._parent.GetFullName() + "\\" if self._parent is not None else ""
        return f"{prefix}{self._attrs['loc_name']}.{self._cls}"

    def GetAttribute(self, k):
        if k not in self._attrs:
            raise AttributeError(f"{self._cls} has no attribute {k!r}")
        return self._attrs[k]

    def SetAttribute(self, k, v):
        self._attrs[k] = v
        if APP.scenario is not None and self._cls in GRID_CLASSES and k in OPERATIVOS:
            APP.scenario._attrs["iModified"] = 1        # como PF: dato operativo -> escenario activo, no la variation
            return
        if APP.recording is not None and self._cls in GRID_CLASSES and k != "loc_name":
            # como PF: un solo delta por objeto en el stage, con los valores nuevos
            delta = next((c for c in APP.recording._children
                          if c._cls == self._cls and c._attrs["loc_name"] == self._attrs["loc_name"]), None)
            if delta is None:
                delta = Obj(self._cls, self._attrs["loc_name"], APP.recording,
                            **{kk: vv for kk, vv in self._attrs.items() if kk != "loc_name"})
            delta._attrs[k] = v

    def GetContents(self, pattern="*", recursive=0):
        out = []
        for child in self._children:
            if fnmatch.fnmatchcase(f"{child._attrs['loc_name']}.{child._cls}", pattern):
                out.append(child)
            if recursive:
                out += child.GetContents(pattern, 1)
        return out

    def CreateObject(self, cls, name):
        obj = Obj(cls, name, self)
        if APP.recording is not None and self._is_in_grid():
            obj.__dict__["_shadow"] = Obj(cls, name, APP.recording)
        return obj

    def AddCopy(self, other, *name_parts):
        name = "".join(str(p) for p in name_parts) or other._attrs["loc_name"]
        new = Obj(other._cls, name, self, **copy.copy({k: v for k, v in other._attrs.items() if k != "loc_name"}))
        for child in other._children:
            new.AddCopy(child, child._attrs["loc_name"])
        return new

    def Delete(self):
        self._parent._children.remove(self)
        if self._shadow is not None:
            self._shadow._parent._children.remove(self._shadow)
        return 0

    def Activate(self):
        if self._cls == "IntScheme" and self not in APP.active_variations:
            APP.active_variations.append(self)
        if self._cls == "IntSstage":
            APP.recording = self
        if self._cls == "IntCase":
            APP.case = self
        if self._cls == "IntScenario":
            APP.scenario = self
        return 0

    def Save(self):
        if self._cls == "IntScenario":
            self._attrs["iModified"] = 0
        return 0

    def Deactivate(self):
        if self._cls == "IntScenario" and APP.scenario is self:
            APP.scenario = None
            return 0
        if self in APP.active_variations:
            APP.active_variations.remove(self)
        if APP.recording is not None and APP.recording._parent is self:
            APP.recording = None
        return 0

    def SetStudyTime(self, t):
        self._attrs["iStudyTime"] = t
        return 0

    def _is_in_grid(self):
        p = self
        while p is not None:
            if p._cls == "ElmNet":
                return True
            p = p._parent
        return False


class OutputWindow:
    """Output Window falsa: refleja LOG (tipo, texto). GetContent(filtro) como en PF 2021+."""
    class MessageType:
        Plain, Error, Warn, Info = 0, 1, 2, 3

    _MAPA = {1: "error", 2: "warn", 3: "info"}

    def GetContent(self, filtro=None):
        if filtro is None:
            return [m for _, m in LOG]
        return [m for t, m in LOG if t == self._MAPA.get(filtro)]


class App:
    def __init__(self):
        self.reset()

    def reset(self):
        self.recording, self.active_variations, self.folders = None, [], {}
        self.calc_objects, self.project, self.case, self.script = [], None, None, None
        self.scenario = None
        LOG.clear()

    def PrintPlain(self, m):
        LOG.append(("info", str(m))); print(m)

    def PrintInfo(self, m):
        LOG.append(("info", str(m))); print(m)

    def PrintWarn(self, m):
        LOG.append(("warn", str(m))); print("WARN", m)

    def PrintError(self, m):
        LOG.append(("error", str(m))); print("ERROR", m)

    def GetOutputWindow(self):
        return OutputWindow()

    def GetActiveProject(self):
        if getattr(self, "_muerto", False):           # simula "'powerfactory.Application' already deleted"
            raise RuntimeError("'powerfactory.Application' already deleted")
        return self.project

    def SearchObject(self, ruta):
        def rec(o):
            if o.GetFullName() == ruta:
                return o
            for c in o._children:
                r = rec(c)
                if r is not None:
                    return r
        return rec(self.project) if self.project is not None else None

    def GetProjectFolder(self, key):
        return self.folders.get(key)

    def GetCalcRelevantObjects(self, pattern="*", *args):
        return [o for o in self.calc_objects if fnmatch.fnmatchcase(f"{o._attrs['loc_name']}.{o._cls}", pattern)]

    def GetActiveStudyCase(self):
        return self.case

    def GetActiveScenario(self):
        return self.scenario

    def GetActiveNetworkVariations(self):
        return list(self.active_variations)

    def GetRecordingStage(self):
        return self.recording

    def GetCurrentScript(self):
        return self.script


APP = App()


def GetApplication():
    APP._muerto = False
    return APP


def build_project(name="Test", grids=("Grid",)):
    """Standard layout; folder keys mirror app.GetProjectFolder()."""
    APP.reset()
    prj = Obj("IntPrj", name)
    lib = Obj("IntPrjfolder", "Library", prj)
    equip = Obj("IntPrjfolder", "Equipment Type Library", lib)
    oplib = Obj("IntPrjfolder", "Operational Library", lib)
    chars = Obj("IntPrjfolder", "Characteristics", oplib)
    scales = Obj("IntScales", "Scale", chars)
    netmod = Obj("IntPrjfolder", "Network Model", prj)
    netdat = Obj("IntPrjfolder", "Network Data", netmod)
    scheme = Obj("IntPrjfolder", "Variations", netmod)
    study = Obj("IntPrjfolder", "Study Cases", prj)
    scen = Obj("IntPrjfolder", "Operation Scenarios", prj)
    APP.case = Obj("IntCase", "Study Case", study)
    APP.project = prj
    APP.folders = {"equip": equip, "oplib": oplib, "chars": chars, "scheme": scheme,
                   "netdat": netdat, "study": study, "lib": lib, "scen": scen}
    prj.__dict__.update(scen=scen, equip=equip, oplib=oplib, chars=chars, scales=scales, scheme=scheme,
                        netdat=netdat, grids=[Obj("ElmNet", g, netdat) for g in grids])
    return prj

"""Extract the AgentDojo 0.1.35 default v1 suites (banking, slack, travel, workspace) into plain JSON.

The unpacked wheel is treated as untrusted DATA. Nothing from it is installed, imported or executed:
- Python sources are read as text and parsed with ``ast.parse`` (never compiled or exec'd);
- YAML is read with ``yaml.safe_load`` semantics (a SafeLoader subclass whose only addition is an
  ``!include`` constructor restricted to .yaml files inside the suite's own data directory);
- every file read is checked against the SHA-256 in the wheel's RECORD.

Ground-truth arguments that depend on the pre-environment are evaluated by the small interpreter in
this file, which supports a whitelisted subset of expressions (attribute/index lookups, comprehensions,
comparisons, max/min/sorted with lambda keys, f-strings, a few str/date methods, class helper methods
made of for/if/return) over the extracted environment data. Anything outside that subset is left
unresolved, with the reason, rather than guessed.

Usage (from the repo root):
    .venv/Scripts/python -I experiments/extract_agentdojo.py <unpacked_dir> <out_dir> [--wheel PATH]

Outputs (in <out_dir>): <suite>/environment.json, <suite>/tools.json, <suite>/tasks.json,
manifest.json and LICENSE (AgentDojo's MIT notice, copied verbatim).
"""

from __future__ import annotations

import argparse
import ast
import base64
import csv
import datetime as dt
import hashlib
import json
import operator
import posixpath
import re
import string
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

SUITES = ("banking", "slack", "travel", "workspace")
EXPECTED_NAME = "agentdojo"
EXPECTED_VERSION = "0.1.35"
DIST_INFO = f"{EXPECTED_NAME}-{EXPECTED_VERSION}.dist-info"
DEFAULT_WHEEL_NAME = f"{EXPECTED_NAME}-{EXPECTED_VERSION}-py3-none-any.whl"

# Tool classification (name verb first; body mutations and docstring wording as cross-checks).
STATE_VERBS = {
    "send", "schedule", "update", "create", "delete", "share", "reserve", "invite",
    "remove", "add", "post", "append", "cancel", "reschedule",
}
READ_VERBS = {"get", "read", "search", "list", "check", "find", "retrieve"}
MUTATING_METHODS = {"append", "extend", "insert", "pop", "remove", "clear", "update", "setdefault",
                    "popitem", "add", "discard"}
DOC_MUTATION_RE = re.compile(
    r"\b(sends?|creates?|deletes?|removes?|updates?|adds?|appends?|posts?|invites?|reserves?|"
    r"makes? a reservation|schedules?|cancels?|reschedules?|shares?|marked as)\b",
    re.IGNORECASE,
)
ISO_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
CURRENT_DATE_KEYS = {"current_day", "current_date", "today", "now"}
PLACEHOLDER_RE = re.compile(r"^(<[^<>]+>|\.\.\.)$")

# Pydantic-model behaviour the interpreter reproduces (read from the tool sources):
# Calendar/Inbox/CloudDrive build events/emails/files keyed by id_ from initial_* in a model
# validator, and _get_next_id() returns str(max(int(id)) + 1).
NEXT_ID_SOURCES = {"calendar": "initial_events", "inbox": "initial_emails", "cloud_drive": "initial_files"}
MODEL_SHIMS_DOC = [
    "<x>._get_next_id() for x in calendar/inbox/cloud_drive = str(max(int(id_) over x.initial_events/"
    "initial_emails/initial_files) + 1), as Calendar/Inbox/CloudDrive._get_next_id over the id-keyed dict "
    "their model validators build from initial_*",
]


# --------------------------------------------------------------------------------------------
# Package access (paths confined to the unpacked dir, every read verified against RECORD)
# --------------------------------------------------------------------------------------------


class Package:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.used: dict[str, str] = {}
        record_path = self.root / DIST_INFO / "RECORD"
        self.record: dict[str, str] = {}
        with open(record_path, encoding="utf-8", newline="") as f:
            for row in csv.reader(f):
                if row and len(row) >= 2:
                    self.record[row[0]] = row[1]
        self.record_sha256 = hashlib.sha256(record_path.read_bytes()).hexdigest()

    def exists(self, rel: str) -> bool:
        return rel in self.record

    def read_bytes(self, rel: str) -> bytes:
        p = (self.root / rel).resolve()
        if self.root not in p.parents:
            raise SystemExit(f"refusing to read outside the package: {rel}")
        data = p.read_bytes()
        expected = self.record.get(rel)
        if not expected:
            raise SystemExit(f"{rel} has no hash in RECORD")
        algo, _, b64 = expected.partition("=")
        digest = hashlib.sha256(data)
        got = base64.urlsafe_b64encode(digest.digest()).rstrip(b"=").decode()
        if algo != "sha256" or got != b64:
            raise SystemExit(f"{rel}: SHA-256 does not match RECORD")
        self.used[rel] = digest.hexdigest()
        return data

    def read_text(self, rel: str) -> str:
        return self.read_bytes(rel).decode("utf-8")

    def module_rel(self, module: str) -> str | None:
        base = module.replace(".", "/")
        for cand in (base + ".py", base + "/__init__.py"):
            if self.exists(cand):
                return cand
        return None


_PARSED: dict[str, tuple[str, ast.Module]] = {}


def parse_module(pkg: Package, rel: str) -> tuple[str, ast.Module]:
    if rel not in _PARSED:
        src = pkg.read_text(rel)
        _PARSED[rel] = (src, ast.parse(src, filename=rel))  # parse only; never compiled or executed
    return _PARSED[rel]


# --------------------------------------------------------------------------------------------
# Environment: includes resolved, injection placeholders replaced by their defaults
# --------------------------------------------------------------------------------------------


def load_yaml_with_includes(pkg: Package, rel: str, allowed_dir: str, included: list[str]):
    base_dir = posixpath.dirname(rel)

    class _Loader(yaml.SafeLoader):
        pass

    def _include(loader, node):
        target = posixpath.normpath(posixpath.join(base_dir, loader.construct_scalar(node)))
        if not target.startswith(allowed_dir + "/") or not target.endswith((".yaml", ".yml")):
            raise SystemExit(f"!include outside the suite data dir or not YAML: {target}")
        included.append(target)
        return load_yaml_with_includes(pkg, target, allowed_dir, included)

    _Loader.add_constructor("!include", _include)
    return yaml.load(pkg.read_text(rel), Loader=_Loader)  # SafeLoader subclass: no object construction


class _QuotedDumper(yaml.SafeDumper):
    pass


_QuotedDumper.add_representer(
    str, lambda d, s: d.represent_scalar("tag:yaml.org,2002:str", s, style='"')
)


def substitute_placeholders(text: str, defaults: dict[str, str]) -> tuple[str, Counter]:
    """Equivalent of ``text.format(**defaults)`` restricted to plain ``{name}`` fields."""
    out, counts = [], Counter()
    for literal, field, spec, conv in string.Formatter().parse(text):
        out.append(literal)
        if field is None:
            continue
        if field not in defaults or spec or conv:
            raise SystemExit(f"unexpected format field {{{field}}} in environment text")
        out.append(defaults[field])
        counts[field] += 1
    return "".join(out), counts


def build_environment(pkg: Package, suite: str):
    """Reproduce TaskSuite.load_and_inject_default_environment with no injections, statically.

    AgentDojo loads environment.yaml (resolving !include), dumps it back to YAML with every string
    double-quoted and keys sorted, fills the placeholders with str.format(**defaults) and reloads it
    with yaml.safe_load. The same steps are done here, so escape sequences in the defaults (e.g.
    '\\t', '\\n' in the banking bill) are interpreted exactly as in AgentDojo.
    """
    data_dir = f"agentdojo/data/suites/{suite}"
    included: list[str] = []
    raw = load_yaml_with_includes(pkg, f"{data_dir}/environment.yaml", data_dir, included)
    env_text = yaml.dump(raw, Dumper=_QuotedDumper, default_flow_style=False)
    vec_raw = load_yaml_with_includes(pkg, f"{data_dir}/injection_vectors.yaml", data_dir, [])
    vectors = yaml.safe_load(yaml.dump(vec_raw, Dumper=_QuotedDumper, default_flow_style=False))
    defaults = {}
    for vid, info in vectors.items():
        d = info["default"]
        if not isinstance(d, str):
            raise SystemExit(f"{suite}: default of {vid} is not a string")
        defaults[vid] = d
    injected, counts = substitute_placeholders(env_text, defaults)
    env = yaml.safe_load(injected)

    leftover = set()

    def scan(o):
        if isinstance(o, dict):
            for k, v in o.items():
                scan(k)
                scan(v)
        elif isinstance(o, list):
            for x in o:
                scan(x)
        elif isinstance(o, str):
            for vid in defaults:
                if "{" + vid + "}" in o:
                    leftover.add(vid)

    scan(env)
    if leftover:
        raise SystemExit(f"{suite}: placeholders left after substitution: {sorted(leftover)}")

    env_src_text = pkg.read_text(f"{data_dir}/environment.yaml")
    include_of_key = {m.group(1): f"{data_dir}/{m.group(2)}" for m in
                      re.finditer(r"^(\w+):\s*!include\s+(\S+)", env_src_text, re.M)}
    placeholders = [
        {"vector": vid, "default": defaults[vid], "occurrences": counts[vid],
         "description": vectors[vid].get("description", "")}
        for vid in vectors if counts[vid]
    ]
    unused = [vid for vid in vectors if not counts[vid]]
    info = {
        "source_files": [f"{data_dir}/environment.yaml", *included, f"{data_dir}/injection_vectors.yaml"],
        "injection_placeholders_replaced": placeholders,
        "injection_vectors_not_in_environment": unused,
        "procedure": (
            "AgentDojo's own default-environment procedure, reproduced statically: load environment.yaml "
            "resolving !include, yaml.dump with all strings double-quoted (sort_keys=True, as AgentDojo), "
            "replace each {vector} placeholder by injection_vectors.yaml's default, yaml.safe_load"
        ),
        "serialization": (
            "keys in AgentDojo's (sorted) order; YAML dates/timestamps serialized as ISO 8601 strings; "
            "other values exactly as YAML loads them (pydantic would further coerce, e.g. datetime-like "
            "strings to datetime and ints in float fields to float)"
        ),
    }
    return env, info, include_of_key


# --------------------------------------------------------------------------------------------
# Static interpreter for ground-truth expressions
# --------------------------------------------------------------------------------------------


class Unresolvable(Exception):
    pass


class Unresolved:
    __slots__ = ("reason",)

    def __init__(self, reason: str):
        self.reason = reason


class EnvRef:
    """A value read from the environment, with its path (kept for provenance)."""

    __slots__ = ("v", "path")

    def __init__(self, v, path: str):
        self.v, self.path = v, path


class Builtin:
    def __init__(self, name):
        self.name = name


class BoundMethod:
    def __init__(self, obj, name):
        self.obj, self.name = obj, name


class Closure:
    def __init__(self, node, scope):
        self.node, self.scope = node, scope


class Helper:
    def __init__(self, fd, self_obj, label):
        self.fd, self.self_obj, self.label = fd, self_obj, label


class Shim:
    def __init__(self, name, ref):
        self.name, self.ref = name, ref


class EnumNS:
    def __init__(self, name, members):
        self.name, self.members = name, members


class ClassInfo:
    def __init__(self, name, ns, methods, rel, src):
        self.name, self.ns, self.methods, self.rel, self.src = name, ns, methods, rel, src


class TaskObj:
    def __init__(self, info: ClassInfo):
        self.info = info


class Scope:
    def __init__(self, vars=None, parent=None):
        self.vars = {} if vars is None else vars
        self.parent = parent


class _Ret:
    def __init__(self, value=None, node=None, scope=None):
        self.value, self.node, self.scope = value, node, scope


class _Break(Exception):
    pass


class _Continue(Exception):
    pass


BUILTINS = {"max", "min", "len", "sum", "sorted", "list", "zip", "enumerate", "str", "int", "float",
            "round", "abs", "any", "all", "set"}
STR_METHODS = {"startswith", "endswith", "lower", "upper", "strip", "lstrip", "rstrip", "split", "join",
               "replace", "title", "capitalize", "count", "find", "format"}
DATE_METHODS = {"isoformat", "date", "strftime"}
DICT_METHODS = {"keys", "values", "items", "get"}
LIST_METHODS = {"index", "count"}
BINOPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
          ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod}
CMPOPS = {ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt, ast.LtE: operator.le,
          ast.Gt: operator.gt, ast.GtE: operator.ge, ast.In: lambda a, b: a in b,
          ast.NotIn: lambda a, b: a not in b, ast.Is: operator.is_, ast.IsNot: operator.is_not}


def deep(x):
    if isinstance(x, EnvRef):
        x = x.v
    if isinstance(x, list):
        return [deep(i) for i in x]
    if isinstance(x, tuple):
        return tuple(deep(i) for i in x)
    if isinstance(x, dict):
        return {deep(k): deep(v) for k, v in x.items()}
    if isinstance(x, set):
        return {deep(i) for i in x}
    return x


def coercion_hazard(v) -> str | None:
    if isinstance(v, EnvRef):
        u = v.v
        if isinstance(u, bool):
            return None
        if isinstance(u, (int, float)):
            return ("numeric environment value turned into text; pydantic type coercion (e.g. int to float) "
                    "could change the text")
        if isinstance(u, str) and ISO_DATETIME_RE.match(u):
            return "datetime-like environment string; pydantic would hold a datetime, not this string"
    return None


def deep_datetime_hazard(v) -> str | None:
    if isinstance(v, EnvRef) and isinstance(v.v, str) and ISO_DATETIME_RE.match(v.v):
        return coercion_hazard(v)
    if isinstance(v, EnvRef):
        v = v.v
    if isinstance(v, (list, tuple)):
        for x in v:
            h = deep_datetime_hazard(x)
            if h:
                return h
    if isinstance(v, dict):
        for x in v.values():
            h = deep_datetime_hazard(x)
            if h:
                return h
    return None


def short(node) -> str:
    s = ast.unparse(node)
    return s if len(s) <= 100 else s[:97] + "..."


class Evaluator:
    def __init__(self, module: dict, strict: bool = False):
        self.module = module
        self.strict = strict
        self.traces: list[list[str]] = [[]]
        self.gt_scope: Scope | None = None
        self.local_traces: dict[str, list[str]] = {}
        self.depth = 0

    # -- trace ---------------------------------------------------------------------------
    def log(self, item: str):
        self.traces[-1].append(item)

    def push(self):
        self.traces.append([])

    def pop(self) -> list[str]:
        return self.traces.pop()

    def hazard(self, v):
        if self.strict:
            h = coercion_hazard(v)
            if h:
                raise Unresolvable(h)

    def truth(self, v) -> bool:
        return bool(deep(v))

    # -- names -----------------------------------------------------------------------------
    def lookup(self, name: str, scope: Scope):
        s = scope
        while s is not None:
            if name in s.vars:
                v = s.vars[name]
                if s is self.gt_scope and name in self.local_traces:
                    self.log("local:" + name)
                    self.traces[-1].extend(self.local_traces[name])
                if isinstance(v, Unresolved):
                    raise Unresolvable(f"'{name}' is unresolved ({v.reason})")
                if isinstance(v, EnvRef) and v.path == "":
                    self.log("env:")
                return v
            s = s.parent
        if name in self.module:
            v = self.module[name]
            if isinstance(v, Unresolved):
                raise Unresolvable(f"'{name}': {v.reason}")
            return v
        if name in BUILTINS:
            return Builtin(name)
        raise Unresolvable(f"name '{name}' is not statically resolvable")

    # -- expressions -----------------------------------------------------------------------
    def ev(self, node, scope: Scope):
        fn = getattr(self, "ev_" + type(node).__name__, None)
        if fn is None:
            raise Unresolvable(f"unsupported expression {type(node).__name__}: `{short(node)}`")
        try:
            return fn(node, scope)
        except (Unresolvable, _Break, _Continue):
            raise
        except Exception as e:  # noqa: BLE001 - any failure of the static evaluation = unresolved
            raise Unresolvable(f"{type(e).__name__}: {e} in `{short(node)}`") from None

    def ev_Constant(self, node, scope):
        return node.value

    def ev_Name(self, node, scope):
        return self.lookup(node.id, scope)

    def ev_Attribute(self, node, scope):
        return self.get_attr(self.ev(node.value, scope), node.attr)

    def get_attr(self, obj, attr):
        if isinstance(obj, TaskObj):
            info = obj.info
            if attr in info.ns:
                v = info.ns[attr]
                if isinstance(v, Unresolved):
                    raise Unresolvable(f"{info.name}.{attr}: {v.reason}")
                self.log(f"const:{info.name}.{attr}")
                return v
            if attr in info.methods:
                return Helper(info.methods[attr], obj, f"{info.name}.{attr}")
            raise Unresolvable(f"{info.name}.{attr} is not defined in the class body")
        if isinstance(obj, EnumNS):
            if attr in obj.members:
                self.log(f"enum:{obj.name}.{attr}")
                return obj.members[attr]
            raise Unresolvable(f"{obj.name}.{attr} is not a member")
        if isinstance(obj, EnvRef) and isinstance(obj.v, dict):
            if attr in obj.v:
                path = f"{obj.path}.{attr}" if obj.path else attr
                self.log("env:" + path)
                return EnvRef(obj.v[attr], path)
            if attr == "_get_next_id" and obj.path in NEXT_ID_SOURCES:
                return Shim(attr, obj)
            raise Unresolvable(
                f"'{attr}' is not in the environment data at '{obj.path or 'pre_environment'}' "
                "(pydantic-derived fields are not modeled)"
            )
        u = obj.v if isinstance(obj, EnvRef) else obj
        if isinstance(u, str):
            allowed = STR_METHODS
        elif isinstance(u, dt.date):
            allowed = DATE_METHODS
        elif isinstance(u, dict):
            allowed = DICT_METHODS
        elif isinstance(u, list):
            allowed = LIST_METHODS
        else:
            allowed = set()
        if attr in allowed:
            return BoundMethod(obj, attr)
        raise Unresolvable(f"attribute '{attr}' of {type(u).__name__} is not supported")

    def ev_Subscript(self, node, scope):
        obj = self.ev(node.value, scope)
        if isinstance(node.slice, ast.Slice):
            parts = [None if p is None else deep(self.ev(p, scope))
                     for p in (node.slice.lower, node.slice.upper, node.slice.step)]
            key = slice(*parts)
        else:
            key = deep(self.ev(node.slice, scope))
        if isinstance(obj, EnvRef):
            u = obj.v
            if isinstance(key, slice):
                return [EnvRef(u[i], f"{obj.path}[{i}]") for i in range(len(u))[key]]
            path = f"{obj.path}[{key!r}]" if isinstance(u, dict) else f"{obj.path}[{key}]"
            child = u[key]
            self.log("env:" + path)
            return EnvRef(child, path)
        if isinstance(obj, (list, tuple, dict, str)):
            return obj[key]
        raise Unresolvable(f"cannot index {type(obj).__name__}")

    def ev_List(self, node, scope):
        return [self.ev(e, scope) for e in node.elts]

    def ev_Tuple(self, node, scope):
        return tuple(self.ev(e, scope) for e in node.elts)

    def ev_Set(self, node, scope):
        return {deep(self.ev(e, scope)) for e in node.elts}

    def ev_Dict(self, node, scope):
        out = {}
        for k, v in zip(node.keys, node.values):
            if k is None:
                raise Unresolvable("dict unpacking (**) is not supported")
            out[deep(self.ev(k, scope))] = self.ev(v, scope)
        return out

    def ev_JoinedStr(self, node, scope):
        parts = []
        for v in node.values:
            if isinstance(v, ast.Constant):
                parts.append(str(v.value))
            elif isinstance(v, ast.FormattedValue):
                val = self.ev(v.value, scope)
                self.hazard(val)
                u = deep(val)
                if v.conversion == 115:
                    u = str(u)
                elif v.conversion == 114:
                    u = repr(u)
                elif v.conversion == 97:
                    u = ascii(u)
                spec = "" if v.format_spec is None else self.ev(v.format_spec, scope)
                parts.append(format(u, spec))
            else:
                raise Unresolvable("unsupported f-string part")
        return "".join(parts)

    def ev_BinOp(self, node, scope):
        op = BINOPS.get(type(node.op))
        if op is None:
            raise Unresolvable(f"operator {type(node.op).__name__} is not supported")
        left, right = self.ev(node.left, scope), self.ev(node.right, scope)
        lu, ru = (left.v if isinstance(left, EnvRef) else left), (right.v if isinstance(right, EnvRef) else right)
        if isinstance(node.op, ast.Add) and isinstance(lu, list) and isinstance(ru, list):
            return self.iterate(left) + self.iterate(right)
        if isinstance(node.op, ast.Mod) and isinstance(lu, str):
            raise Unresolvable("%-formatting is not supported")
        res = op(deep(left), deep(right))
        if isinstance(res, str):
            self.hazard(left)
            self.hazard(right)
        if (isinstance(left, EnvRef) or isinstance(right, EnvRef)) and isinstance(res, (int, float)) \
                and not isinstance(res, bool):
            return EnvRef(res, "<derived>")
        return res

    def ev_UnaryOp(self, node, scope):
        v = self.ev(node.operand, scope)
        if isinstance(node.op, ast.Not):
            return not self.truth(v)
        if isinstance(node.op, (ast.USub, ast.UAdd)):
            res = -deep(v) if isinstance(node.op, ast.USub) else +deep(v)
            return EnvRef(res, "<derived>") if isinstance(v, EnvRef) else res
        raise Unresolvable("unsupported unary operator")

    def ev_BoolOp(self, node, scope):
        res = None
        for value in node.values:
            res = self.ev(value, scope)
            t = self.truth(res)
            if isinstance(node.op, ast.And) and not t:
                return res
            if isinstance(node.op, ast.Or) and t:
                return res
        return res

    def ev_Compare(self, node, scope):
        left = self.ev(node.left, scope)
        for op, comp in zip(node.ops, node.comparators):
            right = self.ev(comp, scope)
            for side in (left, right):
                if self.strict and isinstance(side, EnvRef) and isinstance(side.v, str) \
                        and ISO_DATETIME_RE.match(side.v):
                    raise Unresolvable(coercion_hazard(side))
            fn = CMPOPS.get(type(op))
            if fn is None:
                raise Unresolvable("unsupported comparison")
            if not fn(deep(left), deep(right)):
                return False
            left = right
        return True

    def ev_IfExp(self, node, scope):
        return self.ev(node.body if self.truth(self.ev(node.test, scope)) else node.orelse, scope)

    def comprehension(self, generators, scope, emit):
        cs = Scope({}, parent=scope)

        def rec(i):
            if i == len(generators):
                emit(cs)
                return
            g = generators[i]
            if g.is_async:
                raise Unresolvable("async comprehension")
            for item in self.iterate(self.ev(g.iter, scope if i == 0 else cs)):
                self.bind(g.target, item, cs)
                if all(self.truth(self.ev(c, cs)) for c in g.ifs):
                    rec(i + 1)

        rec(0)

    def ev_ListComp(self, node, scope):
        out = []
        self.comprehension(node.generators, scope, lambda cs: out.append(self.ev(node.elt, cs)))
        return out

    ev_GeneratorExp = ev_ListComp

    def ev_SetComp(self, node, scope):
        out = set()
        self.comprehension(node.generators, scope, lambda cs: out.add(deep(self.ev(node.elt, cs))))
        return out

    def ev_DictComp(self, node, scope):
        out = {}

        def emit(cs):
            out[deep(self.ev(node.key, cs))] = self.ev(node.value, cs)

        self.comprehension(node.generators, scope, emit)
        return out

    def ev_Lambda(self, node, scope):
        return Closure(node, scope)

    def ev_Call(self, node, scope):
        f = self.ev(node.func, scope)
        args = []
        for a in node.args:
            if isinstance(a, ast.Starred):
                raise Unresolvable("starred arguments are not supported")
            args.append(self.ev(a, scope))
        kwargs = {}
        for k in node.keywords:
            if k.arg is None:
                raise Unresolvable("**kwargs are not supported")
            kwargs[k.arg] = self.ev(k.value, scope)
        return self.call(f, args, kwargs)

    # -- calls -----------------------------------------------------------------------------
    def iterate(self, v) -> list:
        if isinstance(v, EnvRef):
            u = v.v
            if isinstance(u, list):
                return [EnvRef(x, f"{v.path}[{i}]") for i, x in enumerate(u)]
            if isinstance(u, dict):
                return list(u.keys())
            if isinstance(u, str):
                return list(u)
            raise Unresolvable(f"cannot iterate over {type(u).__name__}")
        if isinstance(v, (list, tuple, set, str)):
            return list(v)
        if isinstance(v, dict):
            return list(v.keys())
        raise Unresolvable(f"cannot iterate over {type(v).__name__}")

    def bind(self, target, value, scope: Scope):
        if isinstance(target, ast.Name):
            scope.vars[target.id] = value
        elif isinstance(target, (ast.Tuple, ast.List)):
            items = self.iterate(value)
            if len(items) != len(target.elts):
                raise Unresolvable("unpacking length mismatch")
            for t, v in zip(target.elts, items):
                self.bind(t, v, scope)
        else:
            raise Unresolvable(f"unsupported assignment target `{short(target)}`")

    def call(self, f, args, kwargs):
        if isinstance(f, Builtin):
            self.log("builtin:" + f.name)
            return self.call_builtin(f.name, args, kwargs)
        if isinstance(f, BoundMethod):
            return self.call_method(f, args, kwargs)
        if isinstance(f, Closure):
            a = f.node.args
            if a.vararg or a.kwarg or a.kwonlyargs or a.defaults or a.posonlyargs or kwargs \
                    or len(args) != len(a.args):
                raise Unresolvable("unsupported lambda call")
            return self.ev(f.node.body, Scope({p.arg: v for p, v in zip(a.args, args)}, parent=f.scope))
        if isinstance(f, Helper):
            return self.call_helper(f, args, kwargs)
        if isinstance(f, Shim):
            if args or kwargs:
                raise Unresolvable("unexpected arguments to _get_next_id")
            key = NEXT_ID_SOURCES[f.ref.path]
            self.log(f"shim:{f.ref.path}._get_next_id()")
            self.log(f"env:{f.ref.path}.{key}[*].id_")
            return str(max((int(x["id_"]) for x in f.ref.v[key]), default=0) + 1)
        raise Unresolvable(f"calling {type(f).__name__} is not supported")

    def call_builtin(self, name, args, kwargs):
        def keyfn(k):
            if k is None:
                return deep
            return lambda x: deep(self.call(k, [x], {}))

        if name in ("max", "min"):
            key = kwargs.pop("key", None)
            has_default = "default" in kwargs
            default = kwargs.pop("default", None)
            if kwargs:
                raise Unresolvable(f"unsupported keywords for {name}()")
            items = self.iterate(args[0]) if len(args) == 1 else list(args)
            if not items:
                if has_default:
                    return default
                raise Unresolvable(f"{name}() of an empty sequence")
            return (max if name == "max" else min)(items, key=keyfn(key))
        if name == "sorted":
            key = kwargs.pop("key", None)
            reverse = bool(deep(kwargs.pop("reverse", False)))
            if kwargs:
                raise Unresolvable("unsupported keywords for sorted()")
            return sorted(self.iterate(args[0]), key=keyfn(key), reverse=reverse)
        if kwargs:
            raise Unresolvable(f"keywords for {name}() are not supported")
        if name == "len":
            return len(deep(args[0]))
        if name == "sum":
            items = self.iterate(args[0])
            res = sum((deep(x) for x in items), deep(args[1]) if len(args) > 1 else 0)
            return EnvRef(res, "<derived>") if any(isinstance(x, EnvRef) for x in items) else res
        if name == "list":
            return self.iterate(args[0]) if args else []
        if name == "zip":
            return list(zip(*[self.iterate(a) for a in args]))
        if name == "enumerate":
            return list(enumerate(self.iterate(args[0])))
        if name == "set":
            return {deep(x) for x in self.iterate(args[0])} if args else set()
        if name == "str":
            if not args:
                return ""
            self.hazard(args[0])
            return str(deep(args[0]))
        if name in ("int", "float", "round", "abs"):
            res = {"int": int, "float": float, "round": round, "abs": abs}[name](*[deep(a) for a in args])
            return EnvRef(res, "<derived>") if any(isinstance(a, EnvRef) for a in args) else res
        if name in ("any", "all"):
            vals = [self.truth(x) for x in self.iterate(args[0])]
            return any(vals) if name == "any" else all(vals)
        raise Unresolvable(f"builtin {name} is not supported")

    def safe_format(self, template: str, args, kwargs) -> str:
        out, auto = [], 0
        for literal, field, spec, conv in string.Formatter().parse(template):
            out.append(literal)
            if field is None:
                continue
            if field == "":
                v, auto = args[auto], auto + 1
            elif field.isdigit():
                v = args[int(field)]
            elif field.isidentifier():
                v = kwargs[field]
            else:
                raise Unresolvable(f"format field '{field}' is not supported")
            if spec and "{" in spec:
                raise Unresolvable("nested format spec is not supported")
            self.hazard(v)
            u = deep(v)
            if conv == "r":
                u = repr(u)
            elif conv == "s":
                u = str(u)
            elif conv == "a":
                u = ascii(u)
            out.append(format(u, spec or ""))
        return "".join(out)

    def call_method(self, f: BoundMethod, args, kwargs):
        obj, name = f.obj, f.name
        u = obj.v if isinstance(obj, EnvRef) else obj
        if isinstance(u, str):
            if name == "format":
                return self.safe_format(u, args, kwargs)
            if name == "join":
                items = self.iterate(args[0])
                for x in items:
                    self.hazard(x)
                return u.join(deep(x) for x in items)
            return getattr(u, name)(*[deep(a) for a in args], **{k: deep(v) for k, v in kwargs.items()})
        if isinstance(u, dt.date):
            return getattr(u, name)(*[deep(a) for a in args])
        if isinstance(u, dict):
            if name == "keys":
                return list(u.keys())
            if isinstance(obj, EnvRef):
                kids = [(k, EnvRef(v, f"{obj.path}[{k!r}]")) for k, v in u.items()]
                if name == "values":
                    return [v for _, v in kids]
                if name == "items":
                    return kids
                if name == "get":
                    k = deep(args[0])
                    return dict(kids)[k] if k in u else (args[1] if len(args) > 1 else None)
            return {"values": lambda: list(u.values()), "items": lambda: list(u.items()),
                    "get": lambda: u.get(*[deep(a) for a in args])}[name]()
        if isinstance(u, list):
            return getattr(deep(u), name)(*[deep(a) for a in args])
        raise Unresolvable(f"method {name} is not supported")

    def call_helper(self, f: Helper, args, kwargs):
        fd = f.fd
        a = fd.args
        if a.vararg or a.kwarg or a.kwonlyargs or a.posonlyargs:
            raise Unresolvable(f"helper {f.label} has an unsupported signature")
        self.log("helper:" + f.label)
        params = [p.arg for p in a.args]
        bound = ([f.self_obj] if f.self_obj is not None else []) + list(args)
        n_def = len(a.defaults)
        values = {}
        kwargs = dict(kwargs)
        for i, p in enumerate(params):
            if i < len(bound):
                values[p] = bound[i]
            elif p in kwargs:
                values[p] = kwargs.pop(p)
            elif i >= len(params) - n_def:
                values[p] = self.ev(a.defaults[i - (len(params) - n_def)], Scope())
            else:
                raise Unresolvable(f"missing argument {p} for {f.label}")
        if kwargs:
            raise Unresolvable(f"unexpected keywords for {f.label}")
        self.depth += 1
        if self.depth > 20:
            raise Unresolvable("helper recursion too deep")
        try:
            r = self.exec_body(fd.body, Scope(values), "helper")
        finally:
            self.depth -= 1
        return None if r is None else r.value

    # -- statements ------------------------------------------------------------------------
    def exec_body(self, stmts, scope: Scope, mode: str):
        for st in stmts:
            r = self.exec_stmt(st, scope, mode)
            if r is not None:
                return r
        return None

    def assign(self, targets, value_node, scope, mode, combine_with=None):
        if mode == "gt":
            self.push()
            try:
                v = self.ev(value_node, scope)
            except Unresolvable as e:
                v = Unresolved(str(e))
            tr = (combine_with or []) + self.pop()
        else:
            v, tr = self.ev(value_node, scope), None
        for t in targets:
            names = [n.id for n in ast.walk(t) if isinstance(n, ast.Name)]
            if isinstance(v, Unresolved):
                for n in names:
                    scope.vars[n] = v
            else:
                try:
                    self.bind(t, v, scope)
                except Unresolvable as e:
                    if mode != "gt":
                        raise
                    for n in names:
                        scope.vars[n] = Unresolved(str(e))
            if tr is not None and scope is self.gt_scope:
                for n in names:
                    self.local_traces[n] = tr

    def exec_stmt(self, st, scope: Scope, mode: str):
        if isinstance(st, ast.Return):
            if mode == "gt":
                return _Ret(node=st.value, scope=scope)
            return _Ret(value=None if st.value is None else self.ev(st.value, scope))
        if isinstance(st, ast.Assign):
            self.assign(st.targets, st.value, scope, mode)
            return None
        if isinstance(st, ast.AnnAssign):
            if st.value is not None:
                self.assign([st.target], st.value, scope, mode)
            return None
        if isinstance(st, ast.AugAssign):
            if not isinstance(st.target, ast.Name):
                raise Unresolvable("augmented assignment to a non-name target")
            fake = ast.BinOp(left=ast.Name(id=st.target.id, ctx=ast.Load()), op=st.op, right=st.value)
            ast.copy_location(fake, st)
            ast.fix_missing_locations(fake)
            self.assign([st.target], fake, scope, mode)
            return None
        if isinstance(st, ast.Expr):
            if isinstance(st.value, ast.Constant):
                return None
            self.push()
            try:
                self.ev(st.value, scope)  # supported expressions have no side effects; value discarded
            except Unresolvable:
                pass
            finally:
                self.pop()
            return None
        if isinstance(st, ast.If):
            return self.exec_body(st.body if self.truth(self.ev(st.test, scope)) else st.orelse, scope, mode)
        if isinstance(st, ast.For):
            for item in self.iterate(self.ev(st.iter, scope)):
                self.bind(st.target, item, scope)
                try:
                    r = self.exec_body(st.body, scope, mode)
                except _Break:
                    break
                except _Continue:
                    continue
                if r is not None:
                    return r
            else:
                return self.exec_body(st.orelse, scope, mode)
            return None
        if isinstance(st, ast.Break):
            raise _Break()
        if isinstance(st, ast.Continue):
            raise _Continue()
        if isinstance(st, ast.Pass):
            return None
        raise Unresolvable(f"unsupported statement {type(st).__name__}")


# --------------------------------------------------------------------------------------------
# User tasks
# --------------------------------------------------------------------------------------------


def collect_enums(tree: ast.Module) -> dict[str, EnumNS]:
    out = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and any(ast.unparse(b).endswith("Enum") for b in node.bases):
            members = {}
            for st in node.body:
                if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name) \
                        and isinstance(st.value, ast.Constant):
                    members[st.targets[0].id] = st.value.value
            out[node.name] = EnumNS(node.name, members)
    return out


def module_context(pkg: Package, tree: ast.Module) -> dict:
    ctx: dict = {}
    for name, enum in collect_enums(tree).items():
        ctx[name] = enum
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            enums = {}
            rel = pkg.module_rel(node.module) if node.module and node.module.startswith("agentdojo") else None
            if rel:
                enums = collect_enums(parse_module(pkg, rel)[1])
            for alias in node.names:
                nm = alias.asname or alias.name
                ctx[nm] = enums.get(alias.name) or Unresolved(f"imported {node.module}.{alias.name} (not evaluated)")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                nm = (alias.asname or alias.name).split(".")[0]
                ctx[nm] = Unresolved(f"imported module {alias.name} (not evaluated)")
        elif isinstance(node, ast.FunctionDef):
            ctx[node.name] = Helper(node, None, node.name)
        elif isinstance(node, ast.ClassDef) and node.name not in ctx:
            ctx[node.name] = Unresolved(f"class {node.name} (not evaluated)")
    ev = Evaluator(ctx)
    for node in tree.body:
        if isinstance(node, ast.Assign) and all(isinstance(t, ast.Name) for t in node.targets):
            try:
                v = ev.ev(node.value, Scope())
            except Unresolvable as e:
                v = Unresolved(str(e))
            for t in node.targets:
                ctx[t.id] = v
    return ctx


def class_info(node: ast.ClassDef, ctx: dict, rel: str, src: str) -> ClassInfo:
    ns: dict = {}
    methods: dict = {}
    ev = Evaluator(ctx)
    scope = Scope(ns)
    for st in node.body:
        if isinstance(st, ast.FunctionDef):
            methods[st.name] = st
        elif isinstance(st, (ast.Assign, ast.AnnAssign)) and st.value is not None:
            targets = st.targets if isinstance(st, ast.Assign) else [st.target]
            try:
                v = ev.ev(st.value, scope)
            except Unresolvable as e:
                v = Unresolved(str(e))
            for t in targets:
                if isinstance(t, ast.Name):
                    ns[t.id] = v
    return ClassInfo(node.name, ns, methods, rel, src)


def is_register_decorator(dec) -> bool:
    return isinstance(dec, ast.Attribute) and dec.attr == "register_user_task"


def task_number(class_name: str) -> int:
    m = re.match(r"UserTask(\d+)", class_name)  # TaskSuite._get_task_number(task, "UserTask")
    if not m:
        raise SystemExit(f"unexpected user-task class name {class_name}")
    return int(m.group(1))


def flatten_return(node) -> list | None:
    if isinstance(node, ast.List):
        if all(isinstance(e, ast.Call) and isinstance(e.func, ast.Name) and e.func.id == "FunctionCall"
               for e in node.elts):
            return list(node.elts)
        return None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        a, b = flatten_return(node.left), flatten_return(node.right)
        return None if a is None or b is None else a + b
    return None


def normalize_paths(paths: set[str]) -> list[str]:
    norm = {re.sub(r"\[\d+\]", "[*]", p) for p in paths if p}
    return sorted(p for p in norm if not any(q != p and (q.startswith(p + ".") or q.startswith(p + "["))
                                             for q in norm))


def describe(kind: str, trace: list[str]) -> str:
    groups = defaultdict(set)
    for t in trace:
        k, _, v = t.partition(":")
        groups[k].add(v)
    parts = []
    if kind == "environment":
        parts.append("evaluated statically over environment.json (the pre-environment)")
        env = normalize_paths(groups["env"])
        if env:
            parts.append("reads " + ", ".join(env))
    if groups["shim"]:
        parts.append("model method(s) " + ", ".join(sorted(groups["shim"])) + " (see manifest model_shims)")
    if groups["helper"]:
        parts.append("helper method(s) " + ", ".join(sorted(groups["helper"])))
    if groups["local"]:
        parts.append("local variable(s) " + ", ".join(sorted(groups["local"])))
    if groups["const"]:
        parts.append("class constant(s) " + ", ".join(sorted(groups["const"])))
    if groups["enum"]:
        parts.append("enum member(s) " + ", ".join(sorted(groups["enum"])))
    if groups["builtin"]:
        parts.append("builtin(s) " + ", ".join(sorted(groups["builtin"])))
    if kind == "static_expression" and not (groups["const"] or groups["enum"]):
        parts.append("expression over literals")
    return "; ".join(parts)


def classify_arg(vnode, trace: list[str]) -> str:
    if any(t.startswith(("env:", "shim:")) for t in trace):
        return "environment"
    try:
        ast.literal_eval(vnode)
        return "literal"
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        pass
    if isinstance(vnode, ast.Attribute) and isinstance(vnode.value, ast.Name) and vnode.value.id == "self":
        return "class_constant"
    if isinstance(vnode, ast.Attribute) and any(t.startswith("enum:") for t in trace):
        return "enum_constant"
    return "static_expression"


STATIC_KINDS = {"literal", "class_constant", "enum_constant", "static_expression"}


def process_call(call: ast.Call, scope: Scope, ev: Evaluator, src: str) -> dict:
    kw = {k.arg: k.value for k in call.keywords}
    fn_node = kw.get("function", call.args[0] if call.args else None)
    args_node = kw.get("args", call.args[1] if len(call.args) > 1 else None)
    rec: dict = {"function": None, "args": {}}
    resolution, unresolved, placeholders = {}, {}, []
    try:
        rec["function"] = deep(ev.ev(fn_node, scope))
    except (Unresolvable, AttributeError) as e:
        unresolved["<function>"] = {"expr": ast.get_source_segment(src, fn_node) if fn_node else None,
                                    "reason": str(e)}
    pairs = []
    if isinstance(args_node, ast.Dict) and all(isinstance(k, ast.Constant) and isinstance(k.value, str)
                                               for k in args_node.keys):
        pairs = [(k.value, v) for k, v in zip(args_node.keys, args_node.values)]
    elif args_node is not None:
        unresolved["<args>"] = {"expr": ast.get_source_segment(src, args_node),
                                "reason": "args is not a dict literal with constant keys"}
    static_ok, all_values = not unresolved, not unresolved
    for name, vnode in pairs:
        ev.push()
        ok, reason, val = True, None, None
        try:
            v = ev.ev(vnode, scope)
            h = deep_datetime_hazard(v)
            if h:
                raise Unresolvable(h)
            val = deep(v)
        except Unresolvable as e:
            ok, reason = False, str(e)
        trace = ev.pop()
        kind = classify_arg(vnode, trace)
        expr = ast.get_source_segment(src, vnode)
        if ok:
            rec["args"][name] = val
            if kind != "literal":
                resolution[name] = {"kind": kind, "expr": expr, "how": describe(kind, trace)}
            if kind == "literal" and isinstance(val, str) and PLACEHOLDER_RE.match(val):
                placeholders.append(name)
        else:
            rec["args"][name] = None
            unresolved[name] = {"kind": kind, "expr": expr, "reason": reason}
            all_values = False
        if not ok or kind not in STATIC_KINDS:
            static_ok = False
    rec["args_resolved"] = static_ok
    rec["all_args_have_values"] = all_values
    if resolution:
        rec["resolution"] = resolution
    if unresolved:
        rec["unresolved"] = unresolved
    if placeholders:
        rec["placeholder_args"] = placeholders
    rec["source"] = ast.get_source_segment(src, call)
    return rec


def run_ground_truth(info: ClassInfo, ctx: dict, env) -> tuple[list | None, str | None]:
    fd = info.methods.get("ground_truth")
    if fd is None:
        return None, "class defines no ground_truth method"
    params = [a.arg for a in fd.args.args]
    if len(params) != 2:
        return None, "unexpected ground_truth signature"
    ev = Evaluator(ctx, strict=True)
    scope = Scope({params[0]: TaskObj(info), params[1]: EnvRef(env, "")})
    ev.gt_scope = scope
    try:
        r = ev.exec_body(fd.body, scope, "gt")
    except Unresolvable as e:
        return None, f"ground_truth body is not statically executable: {e}"
    if r is None or r.node is None:
        return None, "ground_truth returns nothing"
    calls = flatten_return(r.node)
    if calls is None:
        return None, "ground_truth does not return a literal list of FunctionCall(...)"
    return [process_call(c, r.scope, ev, info.src) for c in calls], None


def combinator_template(pkg: Package):
    rel = "agentdojo/task_suite/task_combinators.py"
    src, tree = parse_module(pkg, rel)
    prompt_expr, gt_ok = None, False
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "NewCombinedTask":
            for st in node.body:
                if isinstance(st, ast.If) and ast.unparse(st.test) == "prompt is None":
                    a = st.body[0]
                    if isinstance(a, ast.Assign) and ast.unparse(a.targets[0]) == "PROMPT":
                        prompt_expr = a.value
                if isinstance(st, ast.FunctionDef) and st.name == "ground_truth":
                    gt_ok = [ast.unparse(s) for s in st.body] == [
                        "return user_task_1.ground_truth(pre_environment) + "
                        "user_task_2.ground_truth(pre_environment)"]
    if prompt_expr is None:
        raise SystemExit("could not find the combined-task PROMPT template in task_combinators.py")
    return prompt_expr, gt_ok, rel


def extract_tasks(pkg: Package, suite: str, env, combined_template):
    rel = f"agentdojo/default_suites/v1/{suite}/user_tasks.py"
    src, tree = parse_module(pkg, rel)
    ctx = module_context(pkg, tree)
    specs: dict[str, dict] = {}
    infos: dict[str, ClassInfo] = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            decs = node.decorator_list
            if any(is_register_decorator(d) for d in decs):
                if len(decs) != 1:
                    raise SystemExit(f"{suite}.{node.name}: unexpected extra decorators")
                tid = f"user_task_{task_number(node.name)}"
                if tid in specs:
                    raise SystemExit(f"{suite}: duplicate {tid}")
                info = class_info(node, ctx, rel, src)
                infos[tid] = info
                specs[tid] = {"kind": "class", "info": info}
            elif any(ast.unparse(d).endswith(("update_user_task", ")")) for d in decs):
                raise SystemExit(f"{suite}.{node.name}: unexpected decorator {ast.unparse(decs[0])}")
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) \
                and isinstance(node.value.func, ast.Attribute):
            attr = node.value.func.attr
            if attr == "update_combined_task":
                raise SystemExit(f"{suite}: update_combined_task in v1 is unexpected")
            if attr == "create_combined_task":
                c = node.value
                name = c.args[0].value
                comps = []
                for a in c.args[1:3]:
                    if not (isinstance(a, ast.Subscript) and isinstance(a.slice, ast.Constant)
                            and ast.unparse(a.value) == "task_suite.user_tasks"):
                        raise SystemExit(f"{suite}: unexpected combined-task component {ast.unparse(a)}")
                    comps.append(a.slice.value)
                prompt_node = next((k.value for k in c.keywords if k.arg == "prompt"), None)
                tid = f"user_task_{task_number(name)}"
                if tid in specs:
                    raise SystemExit(f"{suite}: duplicate {tid}")
                specs[tid] = {"kind": "combined", "name": name, "components": comps,
                              "prompt_node": prompt_node, "source": ast.get_source_segment(src, node)}

    prompt_expr, combined_gt_ok, comb_rel = combined_template
    cache: dict[str, dict] = {}

    def build(tid: str) -> dict:
        if tid in cache:
            return cache[tid]
        spec = specs[tid]
        if spec["kind"] == "class":
            info = spec["info"]
            rec = {"id": tid, "class": info.name}
            p = info.ns.get("PROMPT")
            if isinstance(p, str):
                rec["prompt"] = p
            else:
                rec["prompt"] = None
                rec["prompt_unresolved"] = True
                rec["prompt_reason"] = p.reason if isinstance(p, Unresolved) else "PROMPT is not a string"
            if rec.get("prompt_unresolved"):
                for cls in tree.body:
                    if isinstance(cls, ast.ClassDef) and cls.name == info.name:
                        for st in cls.body:
                            if isinstance(st, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "PROMPT"
                                                                  for t in st.targets):
                                rec["prompt"] = ast.get_source_segment(src, st.value)
            c = info.ns.get("COMMENT")
            if isinstance(c, str):
                rec["comment"] = c
            calls, err = run_ground_truth(info, ctx, env)
            rec["ground_truth"] = calls or []
            if err:
                rec["ground_truth_unresolved"] = True
                rec["ground_truth_reason"] = err
                rec["ground_truth_source"] = ast.get_source_segment(src, info.methods.get("ground_truth"))
            util = [ast.get_source_segment(src, info.methods[m]) for m in ("utility", "utility_from_traces")
                    if m in info.methods]
            rec["utility_source"] = "\n\n".join(util) if util else None
        else:
            comps = [build(c) for c in spec["components"]]
            rec = {"id": tid, "class": spec["name"], "combined_of": spec["components"]}
            if spec["prompt_node"] is not None:
                try:
                    rec["prompt"] = deep(Evaluator(ctx).ev(spec["prompt_node"], Scope()))
                    rec["prompt_source"] = "prompt= argument of create_combined_task"
                except Unresolvable as e:
                    rec["prompt"] = ast.get_source_segment(src, spec["prompt_node"])
                    rec["prompt_unresolved"] = True
                    rec["prompt_reason"] = str(e)
            else:
                pseudo = [ClassInfo(c["class"], {"PROMPT": c["prompt"]}, {}, rel, src) for c in comps]
                ev = Evaluator({})
                try:
                    rec["prompt"] = ev.ev(prompt_expr, Scope({"user_task_1": TaskObj(pseudo[0]),
                                                              "user_task_2": TaskObj(pseudo[1])}))
                    rec["prompt_source"] = f"combined-task template in {comb_rel}: {ast.unparse(prompt_expr)}"
                except Unresolvable as e:
                    rec["prompt"] = ast.unparse(prompt_expr)
                    rec["prompt_unresolved"] = True
                    rec["prompt_reason"] = str(e)
            if combined_gt_ok and not any(c.get("ground_truth_unresolved") for c in comps):
                gt = []
                for c in comps:
                    for call in c["ground_truth"]:
                        call = dict(call)
                        call["from_task"] = c["id"]
                        gt.append(call)
                rec["ground_truth"] = gt
            else:
                rec["ground_truth"] = []
                rec["ground_truth_unresolved"] = True
                rec["ground_truth_reason"] = ("combined-task ground truth could not be composed "
                                              "(template changed or a component is unresolved)")
            rec["combined_task_source"] = spec["source"]
            rec["utility_source"] = None
        cache[tid] = rec
        return rec

    ordered = sorted(specs, key=lambda t: int(t.rsplit("_", 1)[1]))
    return [build(t) for t in ordered]


# --------------------------------------------------------------------------------------------
# Tools
# --------------------------------------------------------------------------------------------


def root_name(node):
    while isinstance(node, (ast.Attribute, ast.Subscript, ast.Call, ast.Starred)):
        node = node.func if isinstance(node, ast.Call) else node.value
    return node.id if isinstance(node, ast.Name) else None


def names_in(node) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def tainted_names(fd) -> set[str]:
    a = fd.args
    tainted = {x.arg for x in [*a.posonlyargs, *a.args, *a.kwonlyargs]}
    tainted |= {x.arg for x in (a.vararg, a.kwarg) if x is not None}
    changed = True
    while changed:
        changed = False
        for n in ast.walk(fd):
            pairs = []
            if isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and n.value is not None:
                targets = n.targets if isinstance(n, ast.Assign) else [n.target]
                pairs = [(n.value, t) for t in targets]
            elif isinstance(n, (ast.For, ast.comprehension)):
                pairs = [(n.iter, n.target)]
            for value, target in pairs:
                if names_in(value) & tainted:
                    for nm in ast.walk(target):
                        if isinstance(nm, ast.Name) and nm.id not in tainted:
                            tainted.add(nm.id)
                            changed = True
    return tainted


class ToolIndex:
    def __init__(self):
        self.funcs: dict[tuple[str, str], ast.FunctionDef] = {}
        self.methods: dict[str, list[tuple[str, ast.FunctionDef, str]]] = defaultdict(list)

    def add_module(self, rel: str, tree: ast.Module):
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                self.funcs[(rel, node.name)] = node
            elif isinstance(node, ast.ClassDef):
                for m in node.body:
                    if isinstance(m, ast.FunctionDef):
                        self.methods[m.name].append((node.name, m, rel))


def mutation_evidence(fd, rel: str, index: ToolIndex, depth: int, seen: set) -> list[str]:
    tainted = tainted_names(fd)
    out: list[str] = []
    for n in ast.walk(fd):
        targets = []
        if isinstance(n, ast.Assign):
            targets = n.targets
        elif isinstance(n, (ast.AugAssign, ast.AnnAssign)):
            targets = [n.target]
        elif isinstance(n, ast.Delete):
            targets = n.targets
        for t in targets:
            for sub in (t.elts if isinstance(t, (ast.Tuple, ast.List)) else [t]):
                if isinstance(sub, (ast.Attribute, ast.Subscript)) and root_name(sub) in tainted:
                    out.append(ast.unparse(n).splitlines()[0])
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute) and root_name(f.value) in tainted:
                if f.attr in MUTATING_METHODS:
                    out.append(ast.unparse(n))
                elif depth < 3:
                    for cls, m, mrel in index.methods.get(f.attr, []):
                        key = (mrel, cls, m.name)
                        if key in seen:
                            continue
                        seen.add(key)
                        out += [f"via {cls}.{m.name}: {s}" for s in mutation_evidence(m, mrel, index, depth + 1, seen)]
            elif isinstance(f, ast.Name) and (rel, f.id) in index.funcs and depth < 3 and \
                    any(names_in(x) & tainted for x in [*n.args, *[k.value for k in n.keywords]]):
                key = (rel, "", f.id)
                if key not in seen:
                    seen.add(key)
                    callee = index.funcs[(rel, f.id)]
                    out += [f"via {f.id}: {s}" for s in mutation_evidence(callee, rel, index, depth + 1, seen)]
    return list(dict.fromkeys(out))


def split_docstring(doc: str | None):
    if not doc:
        return "", {}
    m = re.search(r"^\s*:(param|return|returns|raises)\b", doc, re.M)
    desc = (doc[:m.start()] if m else doc).strip()
    params = {}
    for pm in re.finditer(r":param\s+(\w+):(.*?)(?=^\s*:(?:param|return|returns|raises)\b|\Z)", doc, re.S | re.M):
        params[pm.group(1)] = " ".join(pm.group(2).split())
    return desc, params


def depends_target(node) -> str | None:
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "Depends" and n.args \
                and isinstance(n.args[0], ast.Constant):
            return n.args[0].value
    return None


def extract_tools(pkg: Package, suite: str, index: ToolIndex):
    rel = f"agentdojo/default_suites/v1/{suite}/task_suite.py"
    _, tree = parse_module(pkg, rel)
    imports = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                imports[alias.asname or alias.name] = (node.module, alias.name)
    tool_names = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "TOOLS" for t in node.targets):
            if not (isinstance(node.value, ast.List) and all(isinstance(e, ast.Name) for e in node.value.elts)):
                raise SystemExit(f"{suite}: TOOLS is not a list of names")
            tool_names = [e.id for e in node.value.elts]
    if tool_names is None:
        raise SystemExit(f"{suite}: no TOOLS list in task_suite.py")
    tools = []
    for name in tool_names:
        module, orig = imports[name]
        mrel = pkg.module_rel(module)
        if mrel is None:
            raise SystemExit(f"{suite}: cannot locate module {module}")
        msrc, mtree = parse_module(pkg, mrel)
        fd = next((n for n in mtree.body if isinstance(n, ast.FunctionDef) and n.name == orig), None)
        if fd is None:
            raise SystemExit(f"{suite}: {orig} not found in {mrel}")
        aliases = {}
        for n in mtree.body:
            if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
                dep = depends_target(n.value)
                if dep:
                    aliases[n.targets[0].id] = dep
        doc = ast.get_docstring(fd, clean=True)
        desc, pdocs = split_docstring(doc)
        a = fd.args
        if a.vararg or a.kwarg or a.posonlyargs:
            raise SystemExit(f"{suite}: {orig} has an unsupported signature")
        params, deps = [], []
        positional = list(a.args)
        defaults = [None] * (len(positional) - len(a.defaults)) + list(a.defaults)
        allp = list(zip(positional, defaults)) + list(zip(a.kwonlyargs, a.kw_defaults))
        for arg, default in allp:
            ann = ast.unparse(arg.annotation) if arg.annotation is not None else None
            dep = depends_target(arg.annotation) if arg.annotation is not None else None
            if dep is None and isinstance(arg.annotation, ast.Name):
                dep = aliases.get(arg.annotation.id)
            if dep is not None:
                deps.append({"name": arg.arg, "annotation": ann, "depends_on": dep})
                continue
            p = {"name": arg.arg, "annotation": ann, "required": default is None}
            if default is not None:
                try:
                    p["default"] = ast.literal_eval(default)
                except ValueError:
                    p["default"] = None
                    p["default_source"] = ast.unparse(default)
            else:
                p["default"] = None
            if arg.arg in pdocs:
                p["description"] = pdocs[arg.arg]
            params.append(p)
        verb = orig.split("_")[0]
        body_ev = mutation_evidence(fd, mrel, index, 0, set())
        doc_ev = sorted({m.group(0) for m in DOC_MUTATION_RE.finditer(desc)})
        if verb in STATE_VERBS and (body_ev or doc_ev):
            cls, certain, reason = "state_changing", True, None
        elif verb in READ_VERBS and not body_ev and not doc_ev:
            cls, certain, reason = "read", True, None
        else:
            certain = False
            if verb in STATE_VERBS:
                cls = "state_changing"
            elif verb in READ_VERBS:
                cls = "read"
            else:
                cls = "state_changing" if body_ev else "read"
            bits = [f"name verb '{verb}' suggests {cls.replace('_', '-')}"
                    if verb in STATE_VERBS | READ_VERBS else f"name verb '{verb}' is not in the verb lists"]
            if body_ev:
                bits.append("body mutates state: " + " | ".join(body_ev))
            if doc_ev:
                bits.append("docstring says: " + ", ".join(doc_ev))
            if verb in STATE_VERBS and not body_ev:
                bits.append("no mutation found in the body")
            reason = "; ".join(bits)
        tools.append({
            "name": orig,
            "module": mrel,
            "docstring": doc,
            "description": desc,
            "params": params,
            "injected_dependencies": deps,
            "returns": ast.unparse(fd.returns) if fd.returns is not None else None,
            "classification": cls,
            "classification_certain": certain,
            "classification_evidence": {"name_verb": verb, "body_mutations": body_ev, "docstring_phrases": doc_ev,
                                        **({"uncertain_reason": reason} if reason else {})},
            "body_source": ast.get_source_segment(msrc, fd),
        })
    return tools


# --------------------------------------------------------------------------------------------
# Environment date and summaries
# --------------------------------------------------------------------------------------------


def walk_env(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            p = f"{path}.{k}" if path else str(k)
            yield p, k, v
            yield from walk_env(v, p)
    elif isinstance(o, list):
        for i, x in enumerate(o):
            yield from walk_env(x, f"{path}[{i}]")


def iso(v):
    return v.isoformat() if isinstance(v, dt.date) else v


def collect_gt_dates(tasks) -> list[str]:
    out = set()

    def rec(v):
        if isinstance(v, str) and ISO_DATE_RE.match(v):
            out.add(v)
        elif isinstance(v, (list, tuple)):
            for x in v:
                rec(x)
        elif isinstance(v, dict):
            for x in v.values():
                rec(x)

    for t in tasks:
        for c in t["ground_truth"]:
            rec(c["args"])
    return sorted(out)


def environment_date(suite, env, tools, tasks, include_of_key) -> dict:
    found = [(p, v) for p, k, v in walk_env(env) if k in CURRENT_DATE_KEYS]
    date_tools = [t for t in tools if re.search(r"current_(day|date|time)|today", t["name"])]
    if found:
        path, value = found[0]
        top = path.split(".")[0]
        yaml_file = include_of_key.get(top, f"agentdojo/data/suites/{suite}/environment.yaml")
        out = {"value": iso(value), "source": f"environment: {path} (from {yaml_file})"}
        if len(found) > 1:
            out["other_fields"] = [{"path": p, "value": iso(v)} for p, v in found[1:]]
        if date_tools:
            out["tools_exposing_it"] = [{"name": t["name"], "body_source": t["body_source"]} for t in date_tools]
        else:
            out["tools_exposing_it"] = []
            out["note"] = "no tool of this suite returns the current date"
        return out
    ranges: dict[str, list] = {}
    for p, k, v in walk_env(env):
        if isinstance(k, str) and re.search(r"date|day|time", k) and (
                isinstance(v, dt.date) or (isinstance(v, str) and ISO_DATE_RE.match(v))):
            key = re.sub(r"\[\d+\]", "[*]", p)
            s = iso(v)
            r = ranges.setdefault(key, [s, s])
            r[0], r[1] = min(r[0], s), max(r[1], s)
    return {
        "value": None,
        "source": "none: the environment has no current-date field and no tool of the suite returns a date",
        "date_fields_in_environment": {k: {"min": v[0], "max": v[1]} for k, v in sorted(ranges.items())},
        "dates_in_ground_truth_args": collect_gt_dates(tasks),
    }


def annotate_and_summarize(tasks, tools) -> dict:
    by_name = {t["name"]: t for t in tools}
    sc = {t["name"] for t in tools if t["classification"] == "state_changing"}
    unc = {t["name"] for t in tools if not t["classification_certain"]}
    for t in tasks:
        idx = []
        for i, c in enumerate(t["ground_truth"]):
            fn = c["function"]
            flagged = {"state_changing": fn in sc}
            if fn in unc:
                flagged["classification_uncertain"] = True
            if fn not in by_name:
                flagged["tool_not_in_suite"] = True
            items = list(c.items())
            pos = next(j for j, (k, _) in enumerate(items) if k == "all_args_have_values") + 1
            t["ground_truth"][i] = dict(items[:pos] + list(flagged.items()) + items[pos:])
            if fn in sc:
                idx.append(i)
        t["state_changing_call_indices"] = idx
        t["first_state_changing_call"] = idx[0] if idx else None
    with_sc = [t for t in tasks if t["state_changing_call_indices"]]

    def ids(pred):
        return [t["id"] for t in with_sc if pred(t)]

    first = lambda t: t["ground_truth"][t["first_state_changing_call"]]  # noqa: E731
    all_sc = lambda t: [t["ground_truth"][i] for i in t["state_changing_call_indices"]]  # noqa: E731
    unresolved_args = []
    for t in tasks:
        for i, c in enumerate(t["ground_truth"]):
            for a, info in c.get("unresolved", {}).items():
                unresolved_args.append({"task": t["id"], "call_index": i, "function": c["function"], "arg": a,
                                        "reason": info["reason"]})
    return {
        "n_tasks_with_state_changing_call": len(with_sc),
        "tasks_with_state_changing_call": [t["id"] for t in with_sc],
        "tasks_without_state_changing_call": [t["id"] for t in tasks if not t["state_changing_call_indices"]],
        "n_all_state_changing_calls_static_resolved": len(ids(lambda t: all(c["args_resolved"] for c in all_sc(t)))),
        "n_all_state_changing_calls_resolved_incl_environment": len(
            ids(lambda t: all(c["all_args_have_values"] for c in all_sc(t)))),
        "n_first_state_changing_call_static_resolved": len(ids(lambda t: first(t)["args_resolved"])),
        "n_first_state_changing_call_resolved_incl_environment": len(ids(lambda t: first(t)["all_args_have_values"])),
        "first_state_changing_call_environment_dependent": ids(
            lambda t: not first(t)["args_resolved"] and first(t)["all_args_have_values"]),
        "first_state_changing_call_unresolved": ids(lambda t: not first(t)["all_args_have_values"]),
        "state_changing_calls_unresolved_any": ids(lambda t: not all(c["all_args_have_values"] for c in all_sc(t))),
        "first_state_changing_function_counts": dict(Counter(first(t)["function"] for t in with_sc)),
        "prompts_unresolved": [t["id"] for t in tasks if t.get("prompt_unresolved")],
        "ground_truth_unresolved": [t["id"] for t in tasks if t.get("ground_truth_unresolved")],
        "unresolved_args": unresolved_args,
    }


# --------------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------------


def json_default(o):
    if isinstance(o, dt.date):
        return o.isoformat()
    if isinstance(o, (set, frozenset)):
        return sorted(o)
    raise TypeError(f"not JSON serializable: {type(o).__name__}")


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, indent=2, ensure_ascii=False, default=json_default) + "\n")


def parse_metadata(text: str) -> dict:
    head = text.split("\n\n", 1)[0]
    out = defaultdict(list)
    for line in head.splitlines():
        if ": " in line and not line.startswith(" "):
            k, v = line.split(": ", 1)
            out[k].append(v)
    return out


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("unpacked_dir", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--wheel", type=Path, default=None,
                    help=f"the wheel the dir was unpacked from (default: <unpacked_dir>/../agentdojo_dl/{DEFAULT_WHEEL_NAME})")
    args = ap.parse_args()

    pkg = Package(args.unpacked_dir)
    wheel = args.wheel or (args.unpacked_dir.resolve().parent / "agentdojo_dl" / DEFAULT_WHEEL_NAME)
    if not wheel.is_file():
        raise SystemExit(f"wheel not found: {wheel}")
    wheel_sha = hashlib.sha256(wheel.read_bytes()).hexdigest()

    meta = parse_metadata(pkg.read_text(f"{DIST_INFO}/METADATA"))
    name, version = meta["Name"][0], meta["Version"][0]
    if name != EXPECTED_NAME or version != EXPECTED_VERSION:
        raise SystemExit(f"unexpected package {name} {version}")
    license_classifiers = [c for c in meta.get("Classifier", []) if c.startswith("License ::")]
    license_rel = f"{DIST_INFO}/licenses/LICENSE"
    license_bytes = pkg.read_bytes(license_rel)
    license_text = license_bytes.decode("utf-8")
    if "MIT License" not in license_text or not any("MIT" in c for c in license_classifiers):
        raise SystemExit("license is not MIT as expected")

    combined = combinator_template(pkg)
    index = ToolIndex()
    tools_dir = "agentdojo/default_suites/v1/tools/"
    for rel in sorted(r for r in pkg.record if r.startswith(tools_dir) and r.endswith(".py")):
        index.add_module(rel, parse_module(pkg, rel)[1])

    out = args.out_dir
    suites_manifest = {}
    printed = []
    for suite in SUITES:
        env, env_info, include_of_key = build_environment(pkg, suite)
        tools = extract_tools(pkg, suite, index)
        tasks = extract_tasks(pkg, suite, env, combined)
        summary = annotate_and_summarize(tasks, tools)
        date = environment_date(suite, env, tools, tasks, include_of_key)
        write_json(out / suite / "environment.json", env)
        write_json(out / suite / "tools.json", tools)
        write_json(out / suite / "tasks.json", tasks)
        suites_manifest[suite] = {
            "n_user_tasks": len(tasks),
            "task_ids": [t["id"] for t in tasks],
            "combined_tasks": {t["id"]: t["combined_of"] for t in tasks if "combined_of" in t},
            "n_tools": len(tools),
            "state_changing_tools": [t["name"] for t in tools if t["classification"] == "state_changing"],
            "read_tools": [t["name"] for t in tools if t["classification"] == "read"],
            "uncertain": [{"name": t["name"], "tentative": t["classification"],
                           "reason": t["classification_evidence"]["uncertain_reason"]}
                          for t in tools if not t["classification_certain"]],
            "classification_note": ("uncertain tools are also listed under their tentative class, and the "
                                    "counts below use the tentative class"),
            "environment_date": date,
            "environment": env_info,
            "ground_truth_summary": summary,
        }
        printed.append((suite, len(tasks), summary, suites_manifest[suite]))

    (out / "LICENSE").write_bytes(license_bytes)
    script = Path(__file__).resolve()
    manifest = {
        "package": {
            "name": name,
            "version": version,
            "summary": meta.get("Summary", [None])[0],
            "project_urls": meta.get("Project-URL", []),
            "author_email": meta.get("Author-email", [None])[0],
        },
        "wheel": {"file": wheel.name, "sha256": wheel_sha},
        "license": {
            "spdx": "MIT",
            "source": f"METADATA classifier {license_classifiers} and License-File; text in {license_rel}",
            "copyright_line": next((ln for ln in license_text.splitlines() if ln.startswith("Copyright")), None),
            "license_file_sha256": hashlib.sha256(license_bytes).hexdigest(),
            "copied_to": "LICENSE",
        },
        "extraction": {
            "method": "static: ast + yaml.safe_load; no AgentDojo code executed",
            "details": [
                "Python sources parsed with ast.parse from text; never compiled, imported or executed",
                "YAML read with a yaml.SafeLoader subclass whose only addition is !include (restricted to .yaml "
                "files inside the suite's data directory)",
                "every file read verified against the SHA-256 recorded in the wheel's RECORD",
                "suite version: default_suites/v1 only (v1_1 and later overrides ignored)",
                "user task id = user_task_N from class name UserTaskN (TaskSuite.register_user_task); combined "
                "tasks (TaskCombinator.create_combined_task) get the template prompt and the concatenated ground "
                "truth of their two components, as in task_combinators.py",
                "ground-truth args: literals, class constants and expressions over them are resolved statically "
                "(args_resolved=true); args that depend on pre_environment have args_resolved=false and are "
                "evaluated by this script's whitelisted interpreter over environment.json, with the method "
                "recorded per arg under 'resolution'; anything unsupported is left null under 'unresolved' with "
                "the reason",
                "tool classification: name verb (state-changing verbs: " + ", ".join(sorted(STATE_VERBS)) +
                "), cross-checked against mutations of the injected state in the body (following method calls "
                "into the tools' model classes) and against the docstring; disagreements are listed as "
                "uncertain",
            ],
            "deviation_from_prereg_text": (
                "docs/GENERALIZATION_PREREG.md Amendment 1 says the extraction is done 'with AgentDojo installed "
                "in a separate environment'; this extraction instead reads the wheel's files statically and "
                "executes none of its code"
            ),
            "model_shims": MODEL_SHIMS_DOC,
            "script": "experiments/extract_agentdojo.py",
            "script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
            "python": sys.version.split()[0],
            "pyyaml": yaml.__version__,
            "record_sha256": pkg.record_sha256,
            "input_files": [{"path": p, "sha256": h} for p, h in sorted(pkg.used.items())],
        },
        "suites": suites_manifest,
        "totals": {
            "n_user_tasks": sum(m["n_user_tasks"] for m in suites_manifest.values()),
            "n_tasks_with_state_changing_call": sum(
                m["ground_truth_summary"]["n_tasks_with_state_changing_call"] for m in suites_manifest.values()),
        },
    }
    write_json(out / "manifest.json", manifest)

    for suite, n, s, m in printed:
        print(f"{suite}: {n} tasks; with state-changing call {s['n_tasks_with_state_changing_call']}; "
              f"first call static-resolved {s['n_first_state_changing_call_static_resolved']}, "
              f"incl. env {s['n_first_state_changing_call_resolved_incl_environment']}; "
              f"all sc calls static {s['n_all_state_changing_calls_static_resolved']}, "
              f"incl. env {s['n_all_state_changing_calls_resolved_incl_environment']}")
        print(f"  uncertain tools: {[u['name'] for u in m['uncertain']]}")
        print(f"  date: {m['environment_date']['value']} ({m['environment_date']['source']})")
        if s["prompts_unresolved"] or s["ground_truth_unresolved"] or s["unresolved_args"]:
            print(f"  unresolved: prompts {s['prompts_unresolved']} gt {s['ground_truth_unresolved']} "
                  f"args {[(u['task'], u['call_index'], u['arg']) for u in s['unresolved_args']]}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

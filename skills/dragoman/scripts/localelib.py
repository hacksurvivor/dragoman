"""Shared helpers for dragoman's scripts: locale file discovery and loading,
key flattening, message placeholder parsing (ICU and i18next), and CLDR
plural categories. Standard library only (PyYAML is used for .yml if present).
"""
import glob
import hashlib
import json
import os
import re
from collections import Counter

# --- CLDR plural categories -------------------------------------------------
# Generated from Node's Intl.PluralRules (ICU 78.2, CLDR 48).
# Each group is "all categories | categories reachable by integers 0..1000".
# Categories outside the second set only apply to fractions or very large
# round numbers (e.g. French "1 000 000 de membres"), so missing them is a
# warning, not an error.
_PLURAL_GROUPS = {
    "one other": "af ak am an as az bg bn ce da de dv ee el en eo et eu fa ff fi fo fy gl gu ha hi hu hy ia ie io is ka kk kl kn ks ku ky lb lg ln mg ml mn mr nb nd ne nl nn no nr ny om or os pa ps rm rn rw sc sd sn so sq ss st sv sw ta te tg ti tk tl tn tr ts tt ug ur uz ve vo wa xh yi zu fil haw ast ceb chr ckb gsw kab sdh smn syr".split(),
    "zero one two few many other": "ar cy kw".split(),
    "one few many other | one few many": "be pl ru uk".split(),
    "other": "bm bo dz id ig ii ja jv km ko lo ms my sg su th to vi wo yo zh yue kea lkt nqo sah".split(),
    "one two few many other | one two few other": "br gv sgs".split(),
    "one few other": "bs hr ro sr shi".split(),
    "one many other | one other": "ca es fr it pt scn vec pt-pt".split(),
    "one few many other | one few other": "cs lt sk".split(),
    "zero one other": "cv lv ksh prg".split(),
    "one two few many other": "ga mt".split(),
    "one two few other": "gd sl dsb hsb".split(),
    "one two other": "he iu se".split(),
}
PLURAL_ORDER = ["zero", "one", "two", "few", "many", "other"]
PLURALS = {}
for _group, _langs in _PLURAL_GROUPS.items():
    _all, _, _core = _group.partition(" | ")
    for _lang in _langs:
        PLURALS[_lang] = (_all.split(), (_core or _all).split())


def plural_categories(locale):
    """Return (all_categories, integer_categories) for a locale, or None."""
    tag = locale.replace("_", "-").lower()
    parts = tag.split("-")
    for candidate in ("-".join(parts[:2]), parts[0]):
        if candidate in PLURALS:
            return PLURALS[candidate]
    return None


# --- Files ------------------------------------------------------------------
LOCALE_RE = r"([A-Za-z]{2,3}(?:[-_][A-Za-z0-9]{2,8})*)"


def find_locale_files(pattern):
    """Expand a pattern containing [locale] (and optional * for namespaces).

    Returns {locale: {namespace: path}}. The namespace is the part matched by
    '*' (e.g. 'common' for public/locales/[locale]/*.json), or '' if none.
    """
    if "[locale]" not in pattern:
        raise ValueError("pattern must contain [locale], e.g. messages/[locale].json")
    glob_pattern = pattern.replace("[locale]", "*")
    regex = "^" + re.escape(pattern).replace(re.escape("[locale]"), LOCALE_RE).replace(re.escape("*"), "([^/]*)") + "$"
    found = {}
    for path in sorted(glob.glob(glob_pattern)):
        m = re.match(regex, path.replace(os.sep, "/"))
        if not m:
            continue
        locale, ns = m.group(1), "/".join(m.groups()[1:])
        found.setdefault(locale, {})[ns] = path
    return found


def load_file(path, locale=None):
    """Load a JSON/ARB/YAML locale file into a nested dict."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if path.endswith((".yml", ".yaml")):
        try:
            import yaml
        except ImportError:
            raise SystemExit("PyYAML is needed for YAML files: pip install pyyaml")
        data = yaml.safe_load(text) or {}
        # Rails-style files wrap everything in the locale code: {en: {...}}
        if locale and isinstance(data, dict) and list(data) == [locale]:
            data = data[locale]
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top level must be an object")
    return data


def flatten(data, prefix=""):
    """Nested dict -> {"a.b.c": value}. ARB metadata keys (@...) are skipped."""
    out = {}
    items = data.items() if isinstance(data, dict) else enumerate(data)
    for key, value in items:
        key = str(key)
        if key.startswith("@"):
            continue
        full = f"{prefix}.{key}" if prefix else key
        if isinstance(value, (dict, list)):
            out.update(flatten(value, full))
        else:
            out[full] = value
    return out


def load_messages(files, locale):
    """{namespace: path} -> {"ns:key" or "key": value} for one locale."""
    messages = {}
    for ns, path in files.items():
        for key, value in flatten(load_file(path, locale)).items():
            messages[f"{ns}:{key}" if ns else key] = value
    return messages


def digest(value):
    return hashlib.sha1(json.dumps(value, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]


# --- Message syntax -----------------------------------------------------------
PLURAL_SUFFIX = re.compile(r"^(.*)_(zero|one|two|few|many|other)$")
ORDINAL_SUFFIX = re.compile(r"^(.*)_ordinal_(zero|one|two|few|many|other)$")


def plural_groups(keys):
    """Map base -> {category: key} for i18next-style key_one/key_other groups."""
    groups = {}
    for key in keys:
        if ORDINAL_SUFFIX.match(key):
            continue
        m = PLURAL_SUFFIX.match(key)
        if m:
            groups.setdefault(m.group(1), {})[m.group(2)] = key
    return {base: forms for base, forms in groups.items() if "other" in forms}


def expected_keys(source, locale, syntax):
    """Target keys a locale should have -> the source text they translate.

    For i18next plural groups the target needs one key per plural category the
    locale uses for whole numbers (plus 'other'), which can differ from the
    source's keys (ru needs item_few/item_many, ja only item_other). Those keys
    map to the whole source group, so editing any source form invalidates them.
    """
    groups = plural_groups(source) if syntax == "i18next" else {}
    grouped = {k for forms in groups.values() for k in forms.values()}
    expected = {k: v for k, v in source.items() if k not in grouped}
    cats = plural_categories(locale)
    for base, forms in groups.items():
        needed = set(cats[1]) | {"other"} if cats else set(forms)
        if "zero" in forms:
            needed.add("zero")  # i18next's optional count === 0 form
        ref = {c: source[k] for c, k in sorted(forms.items())}
        for c in PLURAL_ORDER:
            if c in needed:
                expected[f"{base}_{c}"] = ref
    return expected


def detect_syntax(values):
    """'i18next' if messages use {{var}} or key_one/key_other plurals, else 'icu'."""
    for key, value in values.items():
        if isinstance(value, str) and re.search(r"\{\{[^}]+\}\}", value):
            return "i18next"
    keys = set(values)
    for key in keys:
        m = PLURAL_SUFFIX.match(key)
        if m and m.group(2) == "other" and any(f"{m.group(1)}_{c}" in keys for c in PLURAL_ORDER[:-1]):
            return "i18next"
    return "icu"


class MessageError(ValueError):
    pass


class Placeholders:
    """What a message references: arguments (name -> type), tags, and the
    selector sets of each plural/select argument."""

    def __init__(self):
        self.args = {}
        self.tags = Counter()
        self.branches = []  # (arg, kind, [selectors])

    def signature(self):
        return {"args": dict(sorted(self.args.items())), "tags": dict(sorted(self.tags.items()))}


def parse_icu(message):
    """Parse an ICU MessageFormat string (FormatJS / next-intl flavour)."""
    info = Placeholders()
    _IcuParser(message, info).parse_message(0, in_plural=False, until=None)
    return info


class _IcuParser:
    def __init__(self, text, info):
        self.s, self.i, self.info = text, 0, info

    def error(self, msg):
        raise MessageError(f"{msg} at position {self.i}")

    def parse_message(self, depth, in_plural, until):
        s = self.s
        while self.i < len(s):
            c = s[self.i]
            if c == "'":
                self.skip_quote(in_plural)
            elif c == "{":
                self.parse_argument(depth)
            elif c == "}":
                if depth == 0:
                    self.error("unmatched '}'")
                return
            elif c == "<" and self.i + 1 < len(s) and s[self.i + 1] == "/":
                if until is None:
                    self.error("unexpected closing tag")
                m = re.match(r"</([A-Za-z0-9_-]+)\s*>", s[self.i:])
                if not m or m.group(1) != until:
                    self.error(f"expected </{until}>")
                self.i += m.end()
                return
            elif c == "<" and re.match(r"<[A-Za-z0-9_-]+\s*/?>", s[self.i:]):
                m = re.match(r"<([A-Za-z0-9_-]+)\s*(/?)>", s[self.i:])
                self.i += m.end()
                self.info.tags[m.group(1)] += 1
                if not m.group(2):
                    self.parse_message(depth, in_plural, until=m.group(1))
            else:
                self.i += 1
        if depth > 0:
            self.error("unclosed '{'")
        if until is not None:
            self.error(f"unclosed <{until}>")

    def skip_quote(self, in_plural):
        s, i = self.s, self.i
        if s.startswith("''", i):
            self.i += 2
            return
        nxt = s[i + 1] if i + 1 < len(s) else ""
        if nxt in "{}<>" or (in_plural and nxt == "#"):
            end = i + 1
            while True:
                end = s.find("'", end + 1)
                if end == -1:
                    self.i = len(s)  # quoted to end of message
                    return
                if s.startswith("''", end):
                    end += 1
                    continue
                self.i = end + 1
                return
        self.i += 1  # a lone apostrophe is literal text (l'application)

    def ws(self):
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1

    def word(self):
        m = re.match(r"[^\s{}<>,'#]+", self.s[self.i:])
        if not m:
            self.error("expected a name")
        self.i += m.end()
        return m.group(0)

    def parse_argument(self, depth):
        self.i += 1  # {
        self.ws()
        name = self.word()
        self.ws()
        if self.s.startswith("}", self.i):
            self.i += 1
            self.record(name, "string")
            return
        if not self.s.startswith(",", self.i):
            self.error(f"expected ',' or '}}' after {{{name}")
        self.i += 1
        self.ws()
        kind = self.word()
        self.ws()
        if kind in ("plural", "selectordinal", "select"):
            if not self.s.startswith(",", self.i):
                self.error(f"expected ',' after {kind}")
            self.i += 1
            self.record(name, kind)
            selectors = []
            while True:
                self.ws()
                if self.i >= len(self.s):
                    self.error(f"unclosed {{{name}, {kind}}}")
                if self.s.startswith("}", self.i):
                    self.i += 1
                    break
                if kind != "select" and self.s.startswith("offset:", self.i):
                    self.i += len("offset:")
                    self.ws()
                    self.word()
                    continue
                selectors.append(self.word())
                self.ws()
                if not self.s.startswith("{", self.i):
                    self.error(f"expected '{{' after selector {selectors[-1]}")
                self.i += 1
                self.parse_message(depth + 1, in_plural=kind != "select", until=None)
                if not self.s.startswith("}", self.i):
                    self.error("unclosed branch")
                self.i += 1
            if "other" not in selectors:
                raise MessageError(f"{{{name}, {kind}}} has no 'other' branch")
            self.info.branches.append((name, kind, selectors))
        else:
            # number/date/time with optional style or ::skeleton
            if self.s.startswith(",", self.i):
                end = self.s.find("}", self.i)
                if end == -1:
                    self.error("unclosed '{'")
                self.i = end
            self.ws()
            if not self.s.startswith("}", self.i):
                self.error(f"expected '}}' to close {{{name}")
            self.i += 1
            self.record(name, kind)

    def record(self, name, kind):
        prev = self.info.args.get(name)
        if prev and prev != kind and "string" not in (prev, kind):
            raise MessageError(f"{{{name}}} used as both {prev} and {kind}")
        if not prev or prev == "string":
            self.info.args[name] = kind


I18NEXT_VAR = re.compile(r"\{\{\s*-?\s*([^,}\s]+)\s*(?:,[^}]*)?\}\}")
I18NEXT_NEST = re.compile(r"\$t\(\s*([^,)\s]+)")
I18NEXT_TAG = re.compile(r"<(/?)([A-Za-z0-9_-]+)\s*(/?)>")
VOID_TAGS = {"br", "hr", "img", "wbr"}


def parse_i18next(message):
    info = Placeholders()
    for m in I18NEXT_VAR.finditer(message):
        info.args[m.group(1)] = "string"
    for m in I18NEXT_NEST.finditer(message):
        info.args["$t(" + m.group(1) + ")"] = "nesting"
    stack = []
    for m in I18NEXT_TAG.finditer(message):
        closing, name, self_closing = m.groups()
        if name.lower() in VOID_TAGS:
            if not closing:
                info.tags[name] += 1
            continue
        if closing:
            if not stack or stack.pop() != name:
                raise MessageError(f"unexpected </{name}>")
        else:
            info.tags[name] += 1
            if not self_closing:
                stack.append(name)
    if stack:
        raise MessageError(f"unclosed <{stack[-1]}>")
    return info


def parse(message, syntax):
    return parse_icu(message) if syntax == "icu" else parse_i18next(message)

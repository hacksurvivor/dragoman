#!/usr/bin/env python3
"""Audit String(localized:) calls against the project's String Catalogs.

Reports keys used in Swift code that no .xcstrings file contains (usually: the
project hasn't been built since the string was added), catalog keys with no
translation for a locale, and translations still marked needs_review.
Handles comment:/table: arguments, escaped quotes, nested interpolations and
typed specifiers (%lld, %lf); skips shouldTranslate:false and stale entries.

  xcstrings_audit.py --locale ru
  xcstrings_audit.py --locale de --root MyApp
"""
import argparse, json, os, re, sys

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--locale", required=True, help="target locale, e.g. ru")
parser.add_argument("--root", default=".", help="project directory to scan (default: .)")
args = parser.parse_args()
SWIFT_ROOT = args.root
TARGET_LOCALE = args.locale
SKIP_DIRS = {".git", ".build", "build", "DerivedData", "Pods", "Carthage"}

# Xcode turns each interpolation into a typed specifier: String → %@, Int → %lld,
# Double → %lf (untyped extraction writes %arg). Code alone can't tell the type,
# so collapse every specifier to %@ on both sides before comparing.
SPECIFIER = re.compile(r"%(?:\d+\$)?(?:arg|[-+ #0]*\d*(?:\.\d+)?(?:hh|h|ll|l|q|z|t|j|L)?[@dDiuUxXoOfFeEgGcCsSaA])")
CALL = re.compile(r'String\(\s*localized:\s*"(?!"")')  # skips """multi-line""" literals
ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "0": "\0", '"': '"', "'": "'", "\\": "\\"}

def normalize(key):
    return SPECIFIER.sub("%@", key)

def read_literal(src, i):
    """Read a Swift string literal starting just after its opening quote.
    Returns the catalog-style key (interpolations → %@) or None."""
    out = []
    while i < len(src):
        c = src[i]
        if c == '"':
            return "".join(out)
        if c == "\n":
            return None
        if c == "\\":
            nxt = src[i + 1]
            if nxt == "(":  # interpolation — skip balanced parentheses
                depth, i = 1, i + 2
                while i < len(src) and depth:
                    depth += {"(": 1, ")": -1}.get(src[i], 0)
                    i += 1
                out.append("%@")
                continue
            if nxt == "u" and src[i + 2] == "{":
                end = src.index("}", i)
                out.append(chr(int(src[i + 3:end], 16)))
                i = end + 1
                continue
            out.append(ESCAPES.get(nxt, nxt))
            i += 2
            continue
        out.append(c)
        i += 1
    return None

def states(node):
    """All stringUnit states under a localization (covers plural/device variations)."""
    if isinstance(node, dict):
        if "state" in node:
            yield node["state"]
        for v in node.values():
            yield from states(v)

swift_files, catalogs = [], {}
for dirpath, dirnames, filenames in os.walk(SWIFT_ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for name in filenames:
        path = os.path.join(dirpath, name)
        if name.endswith(".swift"):
            swift_files.append(path)
        elif name.endswith(".xcstrings"):
            with open(path, encoding="utf-8") as f:
                catalogs[path] = json.load(f)

# Keys can live in any table (String(localized:table:)), so check against all catalogs.
known = {normalize(k) for c in catalogs.values() for k in c["strings"]}

missing = []
for path in swift_files:
    with open(path, encoding="utf-8") as f:
        src = f.read()
    for m in CALL.finditer(src):
        key = read_literal(src, m.end())
        if key is not None and normalize(key) not in known:
            missing.append((path, src[:m.start()].count("\n") + 1, key))

untranslated, needs_review = [], []
for path, catalog in catalogs.items():
    if catalog.get("sourceLanguage") == TARGET_LOCALE:
        continue
    for key, entry in catalog["strings"].items():
        if entry.get("shouldTranslate") is False or entry.get("extractionState") == "stale":
            continue
        found = set(states(entry.get("localizations", {}).get(TARGET_LOCALE, {})))
        if not found or "new" in found:
            untranslated.append((path, key))
        elif "needs_review" in found:
            needs_review.append((path, key))

print(f"String(localized:) keys missing from every catalog: {len(missing)}")
print("  (usually fixed by building in Xcode so the key gets extracted)")
for path, line, key in missing:
    print(f"  {path}:{line} — {key!r}")
print(f"\nKeys with no {TARGET_LOCALE} translation: {len(untranslated)}")
for path, key in untranslated[:50]:
    print(f"  {os.path.basename(path)}: {key!r}")
print(f"\n{TARGET_LOCALE} translations still marked needs_review: {len(needs_review)}")
for path, key in needs_review[:50]:
    print(f"  {os.path.basename(path)}: {key!r}")
sys.exit(1 if missing or untranslated else 0)

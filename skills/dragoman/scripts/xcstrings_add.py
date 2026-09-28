#!/usr/bin/env python3
"""Add AI-drafted translations to an xcstrings catalog, marked needs_review so
they stay flagged in Xcode until a person approves them. Never overwrites a
reviewed ("translated") entry unless --overwrite-reviewed, skips plural keys
(edit those per category in Xcode), and reports keys missing from the catalog
instead of inventing them. Writes the file in Xcode's own format.

  xcstrings_add.py Resources/Localizable.xcstrings --locale ru --translations ru.json

translations file: {"Coming Up": "Ближайшие", "Your Week": "Ваша неделя"}
"""
import argparse, json, re

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("catalog", help="path to the .xcstrings file")
parser.add_argument("--locale", required=True)
parser.add_argument("--translations", required=True, help="JSON file mapping catalog keys to translations")
parser.add_argument("--overwrite-reviewed", action="store_true", help="replace translations a person already approved")
args = parser.parse_args()

CATALOG, LOCALE, OVERWRITE_REVIEWED = args.catalog, args.locale, args.overwrite_reviewed
with open(args.translations, encoding="utf-8") as f:
    translations = json.load(f)

with open(CATALOG, encoding="utf-8") as f:
    raw = f.read()
catalog = json.loads(raw)
strings = catalog["strings"]

added, kept, not_extracted, plural = [], [], [], []
for key, value in translations.items():
    entry = strings.get(key)
    if entry is None:
        not_extracted.append(key)  # build in Xcode first so the key is extracted
        continue
    locs = entry.setdefault("localizations", {})
    if any("variations" in loc for loc in locs.values()):
        plural.append(key)  # needs one value per plural category — edit in Xcode
        continue
    state = locs.get(LOCALE, {}).get("stringUnit", {}).get("state")
    if state == "translated" and not OVERWRITE_REVIEWED:
        kept.append(key)
        continue
    # AI output is a draft: needs_review keeps it visible in Xcode until someone approves it
    locs[LOCALE] = {"stringUnit": {"state": "needs_review", "value": value}}
    entry["localizations"] = dict(sorted(locs.items()))  # Xcode keeps locales sorted
    added.append(key)

# Match Xcode's own formatting (2-space indent, " : ", empty objects split over
# lines) so diffs show only real changes
text = json.dumps(catalog, indent=2, ensure_ascii=False, separators=(",", " : "))
text = re.sub(r"^( *)(.*)\{\}(,?)$", lambda m: f"{m[1]}{m[2]}{{\n\n{m[1]}}}{m[3]}", text, flags=re.M)
with open(CATALOG, "w", encoding="utf-8") as f:
    f.write(text + ("\n" if raw.endswith("\n") else ""))

print(f"Added as needs_review: {added}")
print(f"Kept existing reviewed translations: {kept}")
print(f"Not in catalog yet (build first): {not_extracted}")
print(f"Plural keys to edit in Xcode: {plural}")

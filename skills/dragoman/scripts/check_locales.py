#!/usr/bin/env python3
"""Check translated locale files against the source locale.

Errors (exit 1): missing or empty keys, placeholders/tags that differ from the
source, broken ICU syntax, plural forms a language needs but lacks.
Warnings: orphan keys, unused plural forms, missing select branches, values
identical to the source, style/glossary misses. Info (--verbose): plural forms
only used for fractions or huge round numbers.

  check_locales.py "messages/[locale].json"
  check_locales.py "public/locales/[locale]/*.json" --source en --locales de,fr
  check_locales.py "lib/l10n/app_[locale].arb" --json
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from localelib import (MessageError, Placeholders, detect_syntax, find_locale_files,  # noqa: E402
                       load_messages, parse, plural_categories, plural_groups)


class Report:
    def __init__(self):
        self.items = []

    def add(self, locale, level, key, message):
        item = {"locale": locale, "level": level, "key": key, "message": message}
        if item not in self.items:  # source problems would otherwise repeat per locale
            self.items.append(item)

    def count(self, level):
        return sum(1 for i in self.items if i["level"] == level)


def load_style(path):
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def safe_parse(report, locale, key, value, syntax):
    try:
        return parse(value, syntax)
    except MessageError as e:
        report.add(locale, "error", key, f"invalid {syntax.upper()} message: {e}")
        return None


def compare(report, locale, key, src, tgt, syntax):
    for name in sorted(set(src.args) - set(tgt.args)):
        report.add(locale, "error", key, f"placeholder {fmt(name, syntax)} missing")
    for name in sorted(set(tgt.args) - set(src.args)):
        report.add(locale, "error", key, f"placeholder {fmt(name, syntax)} not in source")
    for name in sorted(set(src.args) & set(tgt.args)):
        a, b = src.args[name], tgt.args[name]
        if a != b and "string" not in (a, b):
            report.add(locale, "error", key, f"{fmt(name, syntax)} is {a} in source but {b} here")
    if src.tags != tgt.tags:
        report.add(locale, "error", key,
                   f"tags differ: source {dict(src.tags) or '{}'} vs {dict(tgt.tags) or '{}'}")


def fmt(name, syntax):
    if name.startswith("$t("):
        return name
    return "{{" + name + "}}" if syntax == "i18next" else "{" + name + "}"


def check_plural_forms(report, locale, key, forms, cats, label):
    """forms: selectors present. cats: (all, integer) categories or None."""
    if not cats:
        return
    all_cats, core = cats
    present = {f for f in forms if not f.startswith("=")}
    for c in all_cats:
        if c in present:
            continue
        if c in core:
            report.add(locale, "error", key, f"{label} missing '{c}' form ({locale} needs {', '.join(all_cats)})")
        else:
            report.add(locale, "info", key, f"{label} has no '{c}' form (only used for fractions or large round numbers in {locale}; falls back to 'other')")
    for f in sorted(present - set(all_cats) - {"zero"}):
        report.add(locale, "warn", key, f"{label} form '{f}' is never used in {locale}")


def looks_untranslated(src, tgt):
    return src == tgt and len(src) >= 12 and " " in src.strip()


def check_icu(report, locale, source, target, cats, style_checks):
    for key, sval in source.items():
        if key not in target:
            continue
        tval = target[key]
        if not isinstance(sval, str) or not isinstance(tval, str):
            continue
        src, tgt = safe_parse(report, "source", key, sval, "icu"), safe_parse(report, locale, key, tval, "icu")
        if not src or not tgt:
            continue
        compare(report, locale, key, src, tgt, "icu")
        src_selects = {(a, k): sel for a, k, sel in src.branches}
        for arg, kind, selectors in tgt.branches:
            if kind == "plural":
                check_plural_forms(report, locale, key, selectors, cats, f"{{{arg}, plural}}")
            elif kind == "select":
                missing = set(src_selects.get((arg, kind), [])) - set(selectors)
                for sel in sorted(missing):
                    report.add(locale, "warn", key, f"{{{arg}, select}} has no '{sel}' branch (falls back to 'other')")
        style_checks(key, sval, tval)


def check_i18next(report, locale, source, target, cats, style_checks):
    src_groups, tgt_groups = plural_groups(source), plural_groups(target)
    grouped = {k for forms in src_groups.values() for k in forms.values()}
    for key, sval in source.items():
        if key in grouped or key not in target:
            continue
        tval = target[key]
        if not isinstance(sval, str) or not isinstance(tval, str):
            continue
        src, tgt = safe_parse(report, "source", key, sval, "i18next"), safe_parse(report, locale, key, tval, "i18next")
        if src and tgt:
            compare(report, locale, key, src, tgt, "i18next")
            style_checks(key, sval, tval)
    for base, sforms in src_groups.items():
        tforms = tgt_groups.get(base, {})
        if not tforms:
            report.add(locale, "error", f"{base}_*", "missing (plural group)")
            continue
        check_plural_forms(report, locale, f"{base}_*", list(tforms), cats, "plural")
        src_info = [safe_parse(report, "source", k, source[k], "i18next") for k in sforms.values()]
        tgt_info = [safe_parse(report, locale, k, target[k], "i18next") for k in tforms.values()
                    if isinstance(target[k], str)]
        if None in src_info or None in tgt_info:
            continue
        # A form may drop {{count}} ("One item"), so compare the union of all forms.
        compare(report, locale, f"{base}_*", _merge(src_info), _merge(tgt_info), "i18next")
        for cat, key in tforms.items():
            if key in source:
                style_checks(key, source[key], target[key])


def _merge(infos):
    merged = Placeholders()
    for info in infos:
        merged.args.update(info.args)
        for tag, n in info.tags.items():
            merged.tags[tag] = max(merged.tags[tag], n)
    return merged


def run(args):
    files = find_locale_files(args.pattern)
    if not files:
        sys.exit(f"No files match {args.pattern}")
    style = load_style(args.style)
    source_locale = args.source or style.get("sourceLocale") or "en"
    if source_locale not in files:
        sys.exit(f"Source locale '{source_locale}' not found. Found: {', '.join(sorted(files))}")
    locales = args.locales.split(",") if args.locales else sorted(l for l in files if l != source_locale)

    report = Report()
    source = load_messages(files[source_locale], source_locale)
    syntax = args.syntax if args.syntax != "auto" else detect_syntax(source)
    source_groups = plural_groups(source) if syntax == "i18next" else {}

    for locale in locales:
        if locale not in files:
            report.add(locale, "error", "-", f"no file for locale {locale}")
            continue
        target = load_messages(files[locale], locale)
        cats = plural_categories(locale)
        if cats is None:
            report.add(locale, "warn", "-", f"unknown plural rules for '{locale}'; plural checks skipped")

        grouped_src = {k for forms in source_groups.values() for k in forms.values()}
        target_groups = plural_groups(target) if syntax == "i18next" else {}
        grouped_tgt = {k for base, forms in target_groups.items() if base in source_groups for k in forms.values()}

        for key, value in source.items():
            if key in grouped_src:
                continue
            if key not in target:
                if not args.allow_missing:
                    report.add(locale, "error", key, "missing")
            elif isinstance(value, str) and value.strip() and not str(target[key]).strip():
                report.add(locale, "error", key, "empty translation")
            elif looks_untranslated(value, target[key]):
                report.add(locale, "warn", key, "identical to source — untranslated?")
        for key in target:
            if key not in source and key not in grouped_tgt:
                report.add(locale, "warn", key, "not in source (orphan key)")

        dnt = style.get("doNotTranslate", [])
        glossary = style.get("glossary", {}).get(locale, {})

        def style_checks(key, sval, tval, locale=locale):
            for term in dnt:
                if term in sval and term not in tval:
                    report.add(locale, "warn", key, f"'{term}' should stay untranslated")
            for term, wanted in glossary.items():
                if re.search(rf"\b{re.escape(term)}\b", sval, re.I) and wanted.lower() not in tval.lower():
                    report.add(locale, "warn", key, f"glossary: '{term}' should be '{wanted}'")

        checker = check_icu if syntax == "icu" else check_i18next
        checker(report, locale, source, target, cats, style_checks)

    return report, syntax, source_locale, locales


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("pattern", help='path with [locale], e.g. "messages/[locale].json"')
    p.add_argument("--source", help="source locale (default: style file's sourceLocale, else en)")
    p.add_argument("--locales", help="comma-separated target locales (default: all found)")
    p.add_argument("--syntax", choices=["auto", "icu", "i18next"], default="auto")
    p.add_argument("--style", default=".dragoman/style.json", help="project style file")
    p.add_argument("--allow-missing", action="store_true", help="don't report missing keys (work in progress)")
    p.add_argument("--verbose", action="store_true", help="also show info-level notes")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    args = p.parse_args()

    report, syntax, source_locale, locales = run(args)
    errors, warnings = report.count("error"), report.count("warn")
    if args.json:
        print(json.dumps({"syntax": syntax, "source": source_locale, "locales": locales,
                          "errors": errors, "warnings": warnings, "issues": report.items},
                         ensure_ascii=False, indent=2))
    else:
        print(f"{args.pattern}: source {source_locale}, {syntax.upper()} syntax, checked {', '.join(locales) or 'nothing'}")
        rank = {"error": 0, "warn": 1, "info": 2}
        for item in sorted(report.items, key=lambda i: (i["locale"], rank[i["level"]], i["key"])):
            if item["level"] != "info" or args.verbose:
                print(f"  {item['level']:5}  {item['locale']:6} {item['key']}: {item['message']}")
        infos = report.count("info")
        hidden = f", {infos} note(s) (--verbose)" if infos and not args.verbose else ""
        print(f"{errors} error(s), {warnings} warning(s){hidden}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

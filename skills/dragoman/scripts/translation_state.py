#!/usr/bin/env python3
"""Track which translations are drafts, which a person reviewed, and which
went stale because the source text changed. State lives in
.dragoman/state.json (commit it).

  todo     what to translate: missing keys, and keys whose source changed
           (new language: --locales de,ru; it lists the files to create)
  mark     record current translations (default status: draft)
  approve  mark drafts as reviewed once a person has checked them
  status   counts per locale; fails if a reviewed translation was edited
           without approval

  translation_state.py todo "messages/[locale].json" --json
  translation_state.py mark "messages/[locale].json" --locale de
  translation_state.py mark "messages/[locale].json" --locale de --status reviewed   # first run: adopt existing
  translation_state.py approve "messages/[locale].json" --locale de --keys cart.total nav.home
  translation_state.py status "messages/[locale].json"
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from localelib import (detect_syntax, digest, expected_keys, find_locale_files,  # noqa: E402
                       load_messages)


def load_state(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"version": 1, "files": {}}


def save_state(path, state):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def source_from_style(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f).get("sourceLocale", "en")
    return "en"


def filled(value):
    return value is not None and (not isinstance(value, str) or value.strip() != "")


class Project:
    def __init__(self, args):
        self.pattern = args.pattern
        self.files = find_locale_files(args.pattern)
        if not self.files:
            sys.exit(f"No files match {args.pattern}")
        self.source_locale = args.source or source_from_style(".dragoman/style.json")
        if self.source_locale not in self.files:
            sys.exit(f"Source locale '{self.source_locale}' not found. Found: {', '.join(sorted(self.files))}")
        self.source = load_messages(self.files[self.source_locale], self.source_locale)
        self.syntax = detect_syntax(self.source)
        wanted = getattr(args, "locale", None) or getattr(args, "locales", None)
        self.locales = wanted.split(",") if wanted else sorted(l for l in self.files if l != self.source_locale)
        self.state_path = args.state
        self.state = load_state(args.state)
        self.entries = self.state["files"].setdefault(self.pattern, {})

    def locale_files(self, locale):
        """Existing files for a locale, or the paths to create for a new one."""
        if locale in self.files:
            return self.files[locale]
        base = self.pattern.replace("[locale]", locale)
        return {ns: base.replace("*", ns) for ns in self.files[self.source_locale]}

    def target(self, locale):
        return load_messages(self.files[locale], locale) if locale in self.files else {}

    def classify(self, locale):
        """key -> (kind, source_text, target_value) for every expected key."""
        expected = expected_keys(self.source, locale, self.syntax)
        target = self.target(locale)
        entries = self.entries.get(locale, {})
        out = {}
        for key, src in expected.items():
            tgt = target.get(key)
            entry = entries.get(key)
            if not filled(tgt):
                kind = "missing"
            elif entry is None:
                kind = "untracked"
            elif entry["source"] != digest(src):
                kind = "stale-reviewed" if entry["status"] == "reviewed" else "stale"
            elif entry["status"] == "reviewed" and entry["target"] != digest(tgt):
                kind = "edited-reviewed"
            else:
                kind = entry["status"]
            out[key] = (kind, src, tgt)
        return out

    def record(self, locale, keys, status):
        expected = expected_keys(self.source, locale, self.syntax)
        target = self.target(locale)
        entries = self.entries.setdefault(locale, {})
        for key in keys:
            entries[key] = {"source": digest(expected[key]), "target": digest(target[key]), "status": status}
        # Forget keys that no longer exist in the source
        for key in [k for k in entries if k not in expected]:
            del entries[key]
        save_state(self.state_path, self.state)


def cmd_todo(project, args):
    result = {}
    for locale in project.locales:
        translate, update = {}, {}
        for key, (kind, src, tgt) in project.classify(locale).items():
            if kind == "missing":
                translate[key] = src
            elif kind in ("stale", "stale-reviewed"):
                update[key] = {"source": src, "current": tgt, "was": "reviewed" if kind == "stale-reviewed" else "draft"}
        result[locale] = {"files": project.locale_files(locale), "new": locale not in project.files,
                          "translate": translate, "update": update}
    if args.json:
        print(json.dumps({"syntax": project.syntax, "source": project.source_locale, "locales": result},
                         ensure_ascii=False, indent=2))
        return 0
    for locale, r in result.items():
        created = f" — create {', '.join(r['files'].values())}" if r["new"] else ""
        print(f"{locale}: {len(r['translate'])} to translate, {len(r['update'])} to update (source changed){created}")
        for key in r["translate"]:
            print(f"  + {key}")
        for key, u in r["update"].items():
            print(f"  ~ {key}" + ("  (was reviewed — needs review again)" if u["was"] == "reviewed" else ""))
    return 0


def cmd_mark(project, args):
    for locale in project.locales:
        states = project.classify(locale)
        entries = project.entries.get(locale, {})
        if args.keys:
            unknown = sorted(set(args.keys) - set(states))
            if unknown:
                sys.exit(f"{locale}: unknown keys {unknown}")
            keys = list(args.keys)
        else:
            # Untracked = just translated (or, on a first run, existing translations).
            # Stale keys count only if their translation actually changed; an
            # un-updated stale key must stay stale.
            keys, still_stale = [], []
            for key, (kind, _, tgt) in states.items():
                if kind == "untracked":
                    keys.append(key)
                elif kind in ("stale", "stale-reviewed"):
                    (keys if digest(tgt) != entries[key]["target"] else still_stale).append(key)
            if still_stale:
                print(f"{locale}: {len(still_stale)} stale key(s) not updated yet, left as stale: {', '.join(still_stale)}")
        missing = [k for k in keys if states[k][0] == "missing"]
        if missing:
            sys.exit(f"{locale}: can't mark keys that have no translation yet: {missing}")
        protected = [k for k in keys if states[k][0] in ("reviewed", "edited-reviewed")]
        if protected and args.status == "draft":
            sys.exit(f"{locale}: {protected} are reviewed; use approve, or restore their reviewed text")
        project.record(locale, keys, args.status)
        print(f"{locale}: marked {len(keys)} key(s) as {args.status}")
    return 0


def cmd_approve(project, args):
    for locale in project.locales:
        states = project.classify(locale)
        if args.all_drafts:
            keys = [k for k, (kind, _, _) in states.items() if kind == "draft"]
        else:
            keys = args.keys or []
            bad = [k for k in keys if k not in states or states[k][0] == "missing"]
            if bad:
                sys.exit(f"{locale}: no translation to approve for {bad}")
        project.record(locale, keys, "reviewed")
        print(f"{locale}: approved {len(keys)} key(s)")
    return 0


def cmd_status(project, args):
    kinds = ["reviewed", "draft", "untracked", "missing", "stale", "stale-reviewed", "edited-reviewed"]
    violations = {}
    rows = {}
    for locale in project.locales:
        states = project.classify(locale)
        rows[locale] = {k: sum(1 for kind, _, _ in states.values() if kind == k) for k in kinds}
        edited = [key for key, (kind, _, _) in states.items() if kind == "edited-reviewed"]
        if edited:
            violations[locale] = edited
    if args.json:
        print(json.dumps({"locales": rows, "editedReviewed": violations}, ensure_ascii=False, indent=2))
    else:
        print(f"{'locale':8}" + "".join(f"{k:>16}" for k in kinds))
        for locale, row in rows.items():
            print(f"{locale:8}" + "".join(f"{row[k]:>16}" for k in kinds))
        for locale, keys in violations.items():
            print(f"\n{locale}: reviewed translations changed without approval: {', '.join(keys)}")
            print(f"  Restore them, or approve the new text: approve \"{project.pattern}\" --locale {locale} --keys ...")
    return 1 if violations else 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    def common(sp):
        sp.add_argument("pattern", help='path with [locale], e.g. "messages/[locale].json"')
        sp.add_argument("--source", help="source locale (default: style file's sourceLocale, else en)")
        sp.add_argument("--state", default=".dragoman/state.json", help="state file")

    sp = sub.add_parser("todo", help="list keys to translate or update")
    common(sp)
    sp.add_argument("--locales", help="comma-separated target locales (default: all found)")
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("mark", help="record current translations")
    common(sp)
    sp.add_argument("--locale", required=True, help="comma-separated locales")
    sp.add_argument("--status", choices=["draft", "reviewed"], default="draft")
    sp.add_argument("--keys", nargs="+", help="only these keys (default: untracked and updated keys)")

    sp = sub.add_parser("approve", help="mark drafts as reviewed")
    common(sp)
    sp.add_argument("--locale", required=True, help="comma-separated locales")
    group = sp.add_mutually_exclusive_group(required=True)
    group.add_argument("--keys", nargs="+")
    group.add_argument("--all-drafts", action="store_true")

    sp = sub.add_parser("status", help="counts per locale; exit 1 if reviewed text was edited")
    common(sp)
    sp.add_argument("--locales", help="comma-separated target locales (default: all found)")
    sp.add_argument("--json", action="store_true")

    args = p.parse_args()
    project = Project(args)
    handler = {"todo": cmd_todo, "mark": cmd_mark, "approve": cmd_approve, "status": cmd_status}[args.command]
    sys.exit(handler(project, args))


if __name__ == "__main__":
    main()

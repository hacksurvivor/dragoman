"""Tests for dragoman's bundled scripts. Run: python3 -m unittest discover tests"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "dragoman", "scripts")
FIXTURES = os.path.join(ROOT, "tests", "fixtures")
sys.path.insert(0, SCRIPTS)

import localelib  # noqa: E402


def run(script, *args, cwd):
    proc = subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args],
                          cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    return proc.returncode, proc.stdout, proc.stderr


def issues(report, locale=None, level=None):
    return {(i["locale"], i["key"], i["message"]) for i in report["issues"]
            if (locale is None or i["locale"] == locale) and (level is None or i["level"] == level)}


class IcuParserTest(unittest.TestCase):
    def test_arguments_tags_and_branches(self):
        info = localelib.parse_icu("Hi <b>{name}</b>, {count, plural, one {# item} other {# items}}")
        self.assertEqual(info.args, {"name": "string", "count": "plural"})
        self.assertEqual(dict(info.tags), {"b": 1})
        self.assertEqual(info.branches, [("count", "plural", ["one", "other"])])

    def test_apostrophes(self):
        self.assertEqual(localelib.parse_icu("Press '{' to open").args, {})
        self.assertEqual(localelib.parse_icu("l'application de {name}").args, {"name": "string"})

    def test_errors(self):
        for bad in ["{count, plural, one {#} other {#}", "Hi {name", "<b>bold", "{n, plural, one {x}}"]:
            with self.assertRaises(localelib.MessageError, msg=bad):
                localelib.parse_icu(bad)

    def test_i18next(self):
        info = localelib.parse_i18next("Click <1>here</1>, {{name}}.<br/> $t(common.undo)")
        self.assertEqual(set(info.args), {"name", "$t(common.undo)"})
        self.assertEqual(dict(info.tags), {"1": 1, "br": 1})

    def test_plural_categories(self):
        self.assertEqual(localelib.plural_categories("ru"), (["one", "few", "many", "other"], ["one", "few", "many"]))
        self.assertEqual(localelib.plural_categories("fr")[1], ["one", "other"])
        self.assertEqual(localelib.plural_categories("pt_BR"), localelib.plural_categories("pt"))
        self.assertEqual(localelib.plural_categories("ja"), (["other"], ["other"]))
        self.assertIsNone(localelib.plural_categories("xx"))


class CheckLocalesIcuTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        code, out, err = run("check_locales.py", "messages/[locale].json", "--style", "style.json", "--json",
                             cwd=os.path.join(FIXTURES, "icu"))
        cls.code, cls.report = code, json.loads(out)

    def test_fails_with_errors(self):
        self.assertEqual(self.code, 1)
        self.assertEqual(self.report["syntax"], "icu")

    def test_clean_locale(self):
        self.assertEqual(issues(self.report, "de"), set())

    def test_detects_broken_translations(self):
        errors = issues(self.report, "ru", "error")
        self.assertIn(("ru", "cart.total", "placeholder {amount} missing"), errors)
        self.assertIn(("ru", "cart.total", "placeholder {sum} not in source"), errors)
        self.assertIn(("ru", "nav.settings", "empty translation"), errors)
        self.assertTrue(any(k == "terms" and "tags differ" in m for _, k, m in errors))
        self.assertTrue(any(k == "cart.items" and "'few'" in m for _, k, m in errors))
        self.assertTrue(any(k == "cart.items" and "'many'" in m for _, k, m in errors))
        self.assertIn(("fr", "hint", "missing"), issues(self.report, "fr", "error"))
        self.assertTrue(any("unclosed" in m for _, _, m in issues(self.report, "ja", "error")))

    def test_warnings_and_notes(self):
        warns = issues(self.report, level="warn")
        self.assertIn(("ru", "legacy", "not in source (orphan key)"), warns)
        self.assertIn(("ru", "cart.greeting", "'Acme' should stay untranslated"), warns)
        self.assertIn(("ja", "cart.greeting", "identical to source — untranslated?"), warns)
        self.assertTrue(any(k == "invite" and "'male'" in m for _, k, m in issues(self.report, "ja", "warn")))
        # French 'many' only covers large round numbers: a note, not an error
        self.assertTrue(any("'many'" in m for _, _, m in issues(self.report, "fr", "info")))


class CheckLocalesI18nextTest(unittest.TestCase):
    def test_plural_keys_and_placeholders(self):
        code, out, _ = run("check_locales.py", "locales/[locale]/*.json", "--json", cwd=os.path.join(FIXTURES, "i18next"))
        report = json.loads(out)
        self.assertEqual((code, report["syntax"]), (1, "i18next"))
        errors = issues(report, "ru", "error")
        self.assertIn(("ru", "common:welcome", "placeholder {{name}} missing"), errors)
        self.assertIn(("ru", "common:nested", "placeholder $t(common.undo) missing"), errors)
        self.assertTrue(any(k == "common:item_*" and "'many'" in m for _, k, m in errors))
        self.assertNotIn("common:item_few", {k for _, k, _ in issues(report, "ru")})  # needed, not an orphan
        self.assertEqual(issues(report, "ja", "error"), set())
        self.assertTrue(any("'one' is never used" in m for _, _, m in issues(report, "ja", "warn")))


class TranslationStateTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.dir, "messages"))
        for loc in ("en", "de"):
            shutil.copy(os.path.join(FIXTURES, "icu", "messages", f"{loc}.json"), os.path.join(self.dir, "messages"))

    def tearDown(self):
        shutil.rmtree(self.dir)

    def state(self, *args):
        return run("translation_state.py", args[0], "messages/[locale].json", *args[1:], cwd=self.dir)

    def edit(self, locale, fn):
        path = os.path.join(self.dir, "messages", f"{locale}.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        fn(data)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def todo(self):
        return json.loads(self.state("todo", "--json")[1])["locales"]["de"]

    def test_lifecycle(self):
        self.assertEqual(self.state("mark", "--locale", "de", "--status", "reviewed")[0], 0)
        self.edit("en", lambda d: (d["nav"].__setitem__("help", "Help"),
                                   d["cart"].__setitem__("greeting", "Hi {name}, good to see you!")))
        todo = self.todo()
        self.assertEqual(todo["translate"], {"nav.help": "Help"})
        self.assertEqual(todo["update"]["cart.greeting"]["was"], "reviewed")

        # Translating only the new key leaves the changed one stale
        self.edit("de", lambda d: d["nav"].__setitem__("help", "Hilfe"))
        code, out, _ = self.state("mark", "--locale", "de")
        self.assertIn("left as stale: cart.greeting", out)
        self.assertEqual(list(self.todo()["update"]), ["cart.greeting"])

        # Editing a reviewed translation is caught
        self.edit("de", lambda d: (d["cart"].__setitem__("greeting", "Hallo {name}, schön dich zu sehen!"),
                                   d["nav"].__setitem__("home", "Start")))
        self.state("mark", "--locale", "de")
        code, out, _ = self.state("status")
        self.assertEqual(code, 1)
        self.assertIn("nav.home", out)

        self.assertEqual(self.state("approve", "--locale", "de", "--all-drafts")[0], 0)
        self.assertEqual(self.state("approve", "--locale", "de", "--keys", "nav.home")[0], 0)
        self.assertEqual(self.state("status")[0], 0)
        self.assertEqual(self.todo(), {"files": {"": "messages/de.json"}, "new": False, "translate": {}, "update": {}})

    def test_new_language(self):
        code, out, _ = self.state("todo", "--locales", "ja", "--json")
        ja = json.loads(out)["locales"]["ja"]
        self.assertEqual((ja["new"], ja["files"]), (True, {"": "messages/ja.json"}))
        self.assertEqual(len(ja["translate"]), 8)

    def test_i18next_plural_keys_per_locale(self):
        src = os.path.join(FIXTURES, "i18next", "locales")
        shutil.copytree(src, os.path.join(self.dir, "locales"))
        code, out, _ = run("translation_state.py", "todo", "locales/[locale]/*.json", "--json", cwd=self.dir)
        locales = json.loads(out)["locales"]
        self.assertEqual(set(locales["ru"]["translate"]), {"common:item_many"})
        self.assertEqual(locales["ja"]["translate"], {})


class XcstringsTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        shutil.copytree(os.path.join(FIXTURES, "xcstrings"), self.dir, dirs_exist_ok=True)
        self.catalog = os.path.join(self.dir, "Resources", "Localizable.xcstrings")

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_audit(self):
        code, out, _ = run("xcstrings_audit.py", "--locale", "ru", cwd=self.dir)
        self.assertEqual(code, 1)
        self.assertIn("missing from every catalog: 1", out)
        self.assertIn("'Tap \"Save\" to continue'", out)   # escaped quotes parsed
        self.assertNotIn("Ratio", out.split("Keys with no")[0])  # %lf matches \(ratio)
        self.assertIn("'Coming Up'", out)
        self.assertNotIn("'Debug'", out)                  # shouldTranslate: false
        self.assertIn("marked needs_review: 1", out)

    def test_add_round_trips_xcode_format(self):
        with open(self.catalog, encoding="utf-8") as f:
            before = f.read()
        tr = os.path.join(self.dir, "empty.json")
        with open(tr, "w") as f:
            f.write("{}")
        run("xcstrings_add.py", self.catalog, "--locale", "ru", "--translations", tr, cwd=self.dir)
        with open(self.catalog, encoding="utf-8") as f:
            self.assertEqual(f.read(), before)

    def test_add(self):
        tr = os.path.join(self.dir, "ru.json")
        with open(tr, "w", encoding="utf-8") as f:
            json.dump({"Coming Up": "Ближайшие", "Hello %@": "Здравствуйте, %@", "Nope": "x"}, f, ensure_ascii=False)
        code, out, _ = run("xcstrings_add.py", self.catalog, "--locale", "ru", "--translations", tr, cwd=self.dir)
        self.assertIn("Added as needs_review: ['Coming Up']", out)
        self.assertIn("Kept existing reviewed translations: ['Hello %@']", out)
        self.assertIn("Not in catalog yet (build first): ['Nope']", out)
        with open(self.catalog, encoding="utf-8") as f:
            strings = json.load(f)["strings"]
        self.assertEqual(strings["Coming Up"]["localizations"]["ru"]["stringUnit"],
                         {"state": "needs_review", "value": "Ближайшие"})
        self.assertEqual(strings["Hello %@"]["localizations"]["ru"]["stringUnit"]["value"], "Привет, %@")


if __name__ == "__main__":
    unittest.main()

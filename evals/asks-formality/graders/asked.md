---
type: llm
focus: last_message
---

PASS if, before any German translation exists, the assistant asks the user whether German should use informal "du" or formal "Sie" (it may ask other setup questions too, such as regional variant or terms to keep untranslated).
FAIL if it doesn't ask about du/Sie, or if it says it already wrote the German translations.

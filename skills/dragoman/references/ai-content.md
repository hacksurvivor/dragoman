# Localizing AI-generated content

If the app asks an LLM to write user-facing text (summaries, suggestions, titles), that text has to come back in the user's language. Localizing the UI isn't enough.

## Pattern: tell the model the output language

Use the language the app's UI is actually shown in, not the first system language (the app may not support it), and derive the language name from the locale instead of a hardcoded switch.

```swift
enum AppLanguage {
    /// The localization the app is running in, e.g. "pt-BR".
    static var code: String { Bundle.main.preferredLocalizations.first ?? "en" }

    /// English name of that language for the prompt, e.g. "Portuguese (Brazil)".
    static var name: String {
        Locale(identifier: "en").localizedString(forIdentifier: code) ?? "English"
    }

    /// Append to system prompts that produce user-facing text.
    static var outputInstruction: String {
        code.hasPrefix("en") ? "" : """

        Write every user-facing field (titles, body text, labels, suggestions) in \(name). \
        Keep JSON keys and enum values exactly as specified in English.
        """
    }
}

let systemPrompt = """
You summarize support tickets for the agent handling them. …
\(AppLanguage.outputInstruction)
"""
```

```typescript
// Web: the locale your i18n library resolved for this request
const languageName = new Intl.DisplayNames(['en'], { type: 'language' }).of(locale); // "Brazilian Portuguese"
const outputInstruction = locale.startsWith('en') ? '' :
  `\n\nWrite every user-facing field in ${languageName}. Keep JSON keys and enum values in English.`;
```

## What to localize

| Element | Localize? | Why |
|---|---|---|
| Generated titles, body text, suggestions | Yes | The user reads them |
| JSON keys in the response schema | No | Your parser depends on them |
| Enum values the code switches on | No | Code depends on the exact values |
| Classifier prompts returning structured data | No | Output is machine-read |
| The prompt instructions themselves | No | Keep one prompt; state the output language |

Check generated output in each shipped language at least once: models occasionally fall back to English for part of a response, especially inside JSON string fields.

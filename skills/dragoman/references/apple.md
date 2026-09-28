# Apple platforms: SwiftUI and String Catalogs

For iOS, macOS, watchOS, tvOS and visionOS apps using String Catalogs (`.xcstrings`, Xcode 15+). Check the project's deployment target before using an API below: `LocalizedStringResource` needs iOS 16 / macOS 13 / tvOS 16 / watchOS 9.

## Contents
- How String Catalogs work
- What Xcode extracts (and what it silently skips)
- Passing localizable text around: `LocalizedStringResource`
- Pitfalls that leave text in English
- Comments, plurals, tables, generated symbols
- Scripts: audit and bulk-add
- Info.plist, formatting, previews, RTL, accessibility, export
- Troubleshooting

## How String Catalogs work

1. Create `Localizable.xcstrings` in Xcode (File → New → String Catalog)
2. Add target languages in Project → Info → Localizations
3. Build — Xcode extracts localizable strings from code into the catalog
4. Translate in the catalog editor, or with `scripts/xcstrings_add.py`

Each entry has a state: **New** (not translated), **Needs Review**, **Translated** (reviewed), **Stale** (no longer in code). dragoman writes its translations as Needs Review; the user approves them in Xcode.

## What Xcode extracts

Xcode only extracts string literals whose type it can see is localizable. Verified with the Swift compiler's key extraction:

```swift
// Extracted:
Text("Welcome back")                          // literal → LocalizedStringKey
Button("Save") { save() }
Label("Settings", systemImage: "gear")
String(localized: "Buy a book")
headerKey("Coming up")                        // param typed LocalizedStringKey
headerResource("Coming up")                   // param typed LocalizedStringResource
var label: LocalizedStringResource { "Shipped" }  // computed property of that type

// NOT extracted — stays English:
headerString("Coming up")                     // param typed String
Text(someStringVariable)                      // String variable: shown verbatim, no lookup
Text(verbatim: "DEBUG: \(value)")             // explicitly verbatim
Text(LocalizedStringKey(someString))          // looked up at runtime, but never extracted —
                                              // the key must be added to the catalog by hand
```

Interpolations become typed format specifiers in the key: `Text("\(count) items")` with an `Int` is the key `%lld items`, a `Double` is `%lf`, a `String` is `%@`.

## Passing localizable text around: `LocalizedStringResource`

When text crosses a function, property or enum boundary, type it as `LocalizedStringResource` (iOS 16+). Literals passed to it are extracted, it works in and outside SwiftUI (`Text(resource)`, `String(localized: resource)`), and it resolves in the user's locale when displayed. Use `LocalizedStringKey` only when you target iOS 15 or earlier and the text is only used by SwiftUI views.

```swift
func sectionHeader(_ title: LocalizedStringResource, icon: String) -> some View {
    HStack {
        Image(systemName: icon)
        Text(title)
    }
}
sectionHeader("Coming Up", icon: "calendar")   // extracted and translated
```

## Pitfalls that leave text in English

These are the most common SwiftUI localization bugs. Find candidates with:

```bash
grep -rnE 'func [^(]*\([^)]*: String' --include='*.swift' .   # helpers taking String
grep -rnE 'Text\([a-zA-Z_.]+\)' --include='*.swift' .          # Text(variable)
grep -rn 'rawValue' --include='*.swift' . | grep -E 'Text|Label|capitalized'
```

### 1. Helper functions with `String` parameters

```swift
// ❌ Text(title) receives a String: no catalog lookup, not extracted
private func sectionHeader(_ title: String, icon: String) -> some View {
    HStack { Image(systemName: icon); Text(title) }
}

// ✅ Type the parameter as LocalizedStringResource (or LocalizedStringKey pre-iOS 16)
private func sectionHeader(_ title: LocalizedStringResource, icon: String) -> some View {
    HStack { Image(systemName: icon); Text(title) }
}
```

### 2. One string used for display and as a logic key

`LocalizedStringKey` and `LocalizedStringResource` can't be dictionary keys. Keep a stable identifier for logic and map it to display text:

```swift
enum Filter: String, CaseIterable { case today, week, month }

extension Filter {
    var title: LocalizedStringResource {
        switch self {
        case .today: "Today"
        case .week:  "This Week"
        case .month: "This Month"
        }
    }
}

ForEach(Filter.allCases, id: \.self) { filter in
    Text(filter.title)
        .opacity(counts[filter, default: 0] > 0 ? 1 : 0.5)   // logic uses the enum
}
```

Quick fix when refactoring isn't possible: `Text(LocalizedStringKey(label))` looks the string up at runtime, but Xcode won't extract it — add every possible value to the catalog manually, or it silently stays English.

### 3. Enum `rawValue` as display text

```swift
// ❌ Shows "Shipped" in every language
enum OrderStatus: String { case pending, shipped, delivered }
Text(status.rawValue.capitalized)

// ✅ Display text lives in a localizable property
extension OrderStatus {
    var title: LocalizedStringResource {
        switch self {
        case .pending:   "Pending"
        case .shipped:   "Shipped"
        case .delivered: "Delivered"
        }
    }
}
Text(status.title)
```

### 4. Computed properties returning plain `String`

```swift
// ❌ Plain String literals are invisible to the catalog
var statusLabel: String {
    switch self { case .granted: "Granted"; case .denied: "Not Granted" }
}

// ✅ Return LocalizedStringResource, or wrap each literal in String(localized:)
var statusLabel: LocalizedStringResource {
    switch self { case .granted: "Granted"; case .denied: "Not Granted" }
}
```

### 5. Picker items whose tag doubles as display text

```swift
// ❌ Text(freq) renders the raw String
let frequencies = ["Daily", "Weekly", "Monthly"]
ForEach(frequencies, id: \.self) { freq in Text(freq).tag(freq) }

// ✅ Use an enum for storage and a localizable title for display (see pitfall 2)
enum Frequency: String, CaseIterable { case daily, weekly, monthly }
ForEach(Frequency.allCases, id: \.self) { f in Text(f.title).tag(f) }
```

## Comments for translators

```swift
Text("Explore", comment: "Tab bar item title for the discovery section")

String(localized: "Failed to load data",
       comment: "Error shown when the API request fails")

// A stable key with a default value, for strings whose English may change:
String(localized: "cart.itemCount",
       defaultValue: "\(count) items",
       comment: "Number of items in the cart")
```

## Plurals

Right-click a string in the catalog → **Vary by Plural**. Xcode shows exactly the categories each language needs (English: one/other; Russian: one/few/many/other; Arabic: all six).

```swift
Text("\(count) items")   // key "%lld items"; plural variants live in the catalog
```

## Multiple catalogs and packages

```swift
Text("Explore", tableName: "Navigation")                 // Navigation.xcstrings
String(localized: "Get Started", table: "Onboarding")

// Frameworks and Swift packages: pass the bundle
Text("Cast & Crew", bundle: .module)
String(localized: "Cast & Crew", bundle: .module)
```

## Type-safe keys: generated symbols

Instead of hand-written `struct Strings { static let … }` wrappers, let Xcode generate them. Turn on **Generate String Catalog Symbols** (`STRING_CATALOG_GENERATE_SYMBOLS = YES`, off by default), then add strings to the catalog manually (with a key such as `onboarding.welcome`). Xcode generates a static member per manually-added string, with arguments for its placeholders:

```swift
Text(.onboardingWelcome(userName))   // LocalizedStringResource.onboardingWelcome(_:)
```

Generated symbols are `LocalizedStringResource` members, so they need iOS 16 / macOS 13. Strings Xcode extracts automatically from code don't get symbols — they don't need them.

## Non-view code

```swift
enum AppError: LocalizedError {
    case networkFailed, unauthorized

    var errorDescription: String? {
        switch self {
        case .networkFailed:
            String(localized: "Network connection failed. Please try again.",
                   comment: "Error when a network request fails")
        case .unauthorized:
            String(localized: "Please sign in to continue.",
                   comment: "Error when the session expired")
        }
    }
}

let content = UNMutableNotificationContent()
content.title = String(localized: "Export complete", comment: "Notification title")
content.body = String(localized: "Your report is ready.", comment: "Notification body")
```

## Scripts

Both live in `scripts/` and use only the Python standard library.

```bash
# Keys used in code but missing from every catalog, untranslated keys, and
# translations still awaiting review. Exit 1 if anything is missing.
python3 scripts/xcstrings_audit.py --locale ru --root .

# Add translations as needs_review. Keeps reviewed entries, skips plural keys
# (edit those per category in Xcode), refuses keys the catalog doesn't have yet
# (build first), and writes the file in Xcode's own format.
python3 scripts/xcstrings_add.py Resources/Localizable.xcstrings --locale ru --translations ru.json
```

`ru.json` is a flat map of catalog keys to translations: `{"Coming Up": "Ближайшие", "%lld items": "%lld шт."}`. Placeholders (`%@`, `%lld`, `%1$@`) must survive unchanged; reorder with positional forms (`%2$@ … %1$@`) when the language needs it.

## Info.plist strings

Create `InfoPlist.xcstrings` to localize:
- `CFBundleDisplayName` — app name on the home screen
- `NSCameraUsageDescription`, `NSMicrophoneUsageDescription`, `NSLocationWhenInUseUsageDescription` — permission prompts

## Formatting

```swift
Text(date, style: .date)
Text(date, format: .dateTime.month(.wide).day().year())
Text(price, format: .currency(code: "USD"))
Text(ratio, format: .percent)
Text(count, format: .number)

let distance = Measurement(value: 5, unit: UnitLength.kilometers)
Text(distance, format: .measurement(width: .wide))
```

## Previews and testing

```swift
#Preview("English") { ContentView() }

#Preview("Русский") {
    ContentView().environment(\.locale, Locale(identifier: "ru"))
}

#Preview("العربية") {
    ContentView()
        .environment(\.locale, Locale(identifier: "ar"))
        .environment(\.layoutDirection, .rightToLeft)
}
```

To run the whole app in a language: Scheme → Edit Scheme → Run → Options → App Language (and App Region for date/number formats).

## RTL

SwiftUI mirrors standard layouts automatically. For custom drawing, read the direction:

```swift
@Environment(\.layoutDirection) var layoutDirection
```

## Accessibility

```swift
Text("Welcome")
    .accessibilityLabel(Text("Welcome to the app", comment: "VoiceOver label for the welcome heading"))
```

Test with the largest Dynamic Type sizes in your longest language (often German); avoid fixed widths on text.

## Export for external translators

```bash
xcodebuild -exportLocalizations -project MyApp.xcodeproj -localizationPath ./translations
xcodebuild -importLocalizations -project MyApp.xcodeproj -localizationPath ./translations/es.xcloc
```

## Troubleshooting

| Problem | Fix |
|---|---|
| Strings not appearing in catalog | Build the project (Cmd+B); check the literal's type is localizable (see "What Xcode extracts") |
| Stale strings showing | Clean build folder (Cmd+Shift+K) |
| Plurals not working | Right-click the key → Vary by Plural |
| Framework/package strings missing | Pass `bundle:` (`.module` in Swift packages) |
| App name / permission prompts in English | Create `InfoPlist.xcstrings` |
| `xcstrings_audit.py` reports a key as missing | Build first; if it persists, the key's type isn't localizable in code |

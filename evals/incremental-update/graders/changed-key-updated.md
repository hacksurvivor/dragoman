---
type: regex
target: { source: file, path: messages/de.json }
pattern: '"greeting"\s*:\s*"(?!Schön, dass du wieder da bist, \{name\}!")[^"]*\{name\}[^"]*"'
---

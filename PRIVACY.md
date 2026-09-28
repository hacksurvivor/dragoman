# Privacy

Dragoman is a set of instructions and local scripts for Claude. It has no servers, accounts, analytics or telemetry, and it doesn't collect, store or send any data of its own.

## What it touches

- **Your files.** Claude reads the locale files and, in Claude Code or Cowork, the project files needed for the task. The bundled Python scripts read locale files and write only `.dragoman/` (style choices and review state) and the files being translated. In chat they run inside Claude's code-execution sandbox.
- **Your conversation with Claude.** Translations are written by Claude in your session, so your content is handled under [Anthropic's Privacy Policy](https://www.anthropic.com/legal/privacy), like any other conversation.

## Optional third-party tools

Dragoman only uses these if you choose them:

- **Lingo.dev** compiler or CLI send your source strings to Lingo.dev or to the model provider you configure, under their terms and privacy policies.
- **Package managers** (npm and others) download the i18n libraries Dragoman suggests for your project when you install them.

## Contact

Questions or concerns: [open an issue](https://github.com/hacksurvivor/dragoman/issues).

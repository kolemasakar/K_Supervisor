# PROJECT_FILE_STANDARD
Універсальний стандарт назв, форматів, кодування, версійності та розміщення файлів у GitHub-проєктах.

Standard: PROJECT_FILE_STANDARD
Version: 1.0
Status: ACTIVE
Canonical repository: AI_general

## Local Use

This file records the project adoption of the canonical reusable standard maintained in `kolemasakar/AI_general`.

K_Supervisor follows these mandatory rules:

- file and directory names use ASCII characters;
- documentation filenames use stable descriptive names;
- project documentation is ASCII by default;
- each documentation file contains exactly one short Ukrainian description line after the top-level heading unless the canonical standard itself requires an example;
- reports, analyses, and generated work results use UTF-8 by default;
- documentation uses Git history instead of `final2`, `latest`, or similar suffixes;
- dates use `YYYY-MM-DD`;
- generated artifacts use stable task/run identifiers when needed;
- temporary files, secrets, runtime output, and caches are excluded from Git by default;
- `.gitkeep` may temporarily preserve required empty directories.

The canonical full standard remains authoritative:

```text
Repository: kolemasakar/AI_general
Path: docs/PROJECT_FILE_STANDARD.md
Version: 1.0
```

If this local summary conflicts with the canonical standard, the canonical standard wins unless K_Supervisor records an explicit project-specific exception.

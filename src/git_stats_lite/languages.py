"""Language detection by file extension and special filenames."""

from __future__ import annotations

import os

# Map extensions (lowercase, with leading dot) to canonical language names
EXTENSION_MAP: dict[str, str] = {
    # Systems & Compiled
    ".c": "C",
    ".h": "C/C++ Header",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++ Header",
    ".hh": "C++ Header",
    ".hxx": "C++ Header",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".swift": "Swift",
    ".d": "D",
    ".zig": "Zig",
    ".nim": "Nim",
    ".m": "Objective-C",
    ".mm": "Objective-C++",
    ".f90": "Fortran",
    ".f": "Fortran",
    ".pas": "Pascal",
    ".ada": "Ada",
    ".adb": "Ada",

    # JVM
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".scala": "Scala",
    ".sc": "Scala",
    ".groovy": "Groovy",
    ".clj": "Clojure",
    ".cljs": "ClojureScript",

    # Web & Scripting
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".jsx": "JavaScript (React)",
    ".ts": "TypeScript",
    ".mts": "TypeScript",
    ".cts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".py": "Python",
    ".pyw": "Python",
    ".pyi": "Python (Stub)",
    ".rb": "Ruby",
    ".rake": "Ruby",
    ".php": "PHP",
    ".phtml": "PHP",
    ".pl": "Perl",
    ".pm": "Perl",
    ".lua": "Lua",
    ".dart": "Dart",
    ".r": "R",
    ".jl": "Julia",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".hrl": "Erlang",
    ".hs": "Haskell",
    ".lhs": "Haskell",
    ".ml": "OCaml",
    ".mli": "OCaml",

    # Shell
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".fish": "Fish Shell",
    ".ps1": "PowerShell",
    ".psm1": "PowerShell",
    ".bat": "Batch",
    ".cmd": "Batch",

    # Markup & Styling
    ".html": "HTML",
    ".htm": "HTML",
    ".xhtml": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    ".styl": "Stylus",
    ".vue": "Vue",
    ".svelte": "Svelte",

    # Data & Configuration
    ".json": "JSON",
    ".jsonc": "JSON with Comments",
    ".json5": "JSON5",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".xml": "XML",
    ".svg": "SVG",
    ".ini": "INI",
    ".cfg": "Config",
    ".conf": "Config",
    ".env": "Environment Config",
    ".sql": "SQL",
    ".graphql": "GraphQL",
    ".gql": "GraphQL",
    ".proto": "Protocol Buffers",

    # Documentation & Text
    ".md": "Markdown",
    ".markdown": "Markdown",
    ".rst": "reStructuredText",
    ".txt": "Plain Text",
    ".tex": "TeX/LaTeX",
    ".adoc": "AsciiDoc",
    ".org": "Emacs Org",

    # Build & Infra
    ".dockerignore": "Docker Ignore",
    ".gitignore": "Git Ignore",
    ".gitattributes": "Git Attributes",
    ".editorconfig": "EditorConfig",
    ".tf": "Terraform",
    ".tfvars": "Terraform",
    ".hcl": "HCL",
    ".bzl": "Starlark",
    ".cmake": "CMake",
}

# Special exact filenames (case-insensitive comparison)
SPECIAL_FILENAMES: dict[str, str] = {
    "dockerfile": "Dockerfile",
    "containerfile": "Dockerfile",
    "makefile": "Makefile",
    "gnumakefile": "Makefile",
    "cmakelists.txt": "CMake",
    "gemfile": "Ruby",
    "rakefile": "Ruby",
    "vagrantfile": "Ruby",
    "jenkinsfile": "Groovy",
    "procfile": "Procfile",
    "brewfile": "Ruby",
    "cargo.lock": "Cargo Lock",
    "package-lock.json": "Package Lock",
    "yarn.lock": "Yarn Lock",
    "pnpm-lock.yaml": "Pnpm Lock",
    "poetry.lock": "Poetry Lock",
    "license": "License",
    "licence": "License",
}


def detect_language(path: str) -> str:
    """Detect language of a given file path by extension or filename."""
    if not path:
        return "Unknown"

    basename = os.path.basename(path)
    lower_base = basename.lower()

    if lower_base in SPECIAL_FILENAMES:
        return SPECIAL_FILENAMES[lower_base]

    # Handle multi-part extensions like .d.ts or .tar.gz
    if lower_base.endswith(".d.ts"):
        return "TypeScript (Type Definitions)"
    if lower_base.endswith((".spec.ts", ".test.ts")):
        return "TypeScript"
    if lower_base.endswith((".spec.js", ".test.js")):
        return "JavaScript"

    _, ext = os.path.splitext(lower_base)
    if ext in EXTENSION_MAP:
        return EXTENSION_MAP[ext]

    if ext:
        # e.g. .xyz -> "XYZ (Other)" or uppercase extension
        return ext.lstrip(".").upper()

    return "No Extension"

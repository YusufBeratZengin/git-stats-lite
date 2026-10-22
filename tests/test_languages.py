"""Unit tests for language detection."""

import sys
import unittest
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from git_stats_lite.languages import detect_language


class TestLanguages(unittest.TestCase):
    def test_standard_extensions(self):
        self.assertEqual(detect_language("src/main.py"), "Python")
        self.assertEqual(detect_language("src/lib.rs"), "Rust")
        self.assertEqual(detect_language("cmd/app.go"), "Go")
        self.assertEqual(detect_language("index.ts"), "TypeScript")
        self.assertEqual(detect_language("Component.tsx"), "TypeScript (React)")
        self.assertEqual(detect_language("script.js"), "JavaScript")
        self.assertEqual(detect_language("styles.css"), "CSS")
        self.assertEqual(detect_language("styles.scss"), "SCSS")
        self.assertEqual(detect_language("index.html"), "HTML")
        self.assertEqual(detect_language("schema.sql"), "SQL")
        self.assertEqual(detect_language("deploy.sh"), "Shell")
        self.assertEqual(detect_language("data.json"), "JSON")
        self.assertEqual(detect_language("config.yaml"), "YAML")
        self.assertEqual(detect_language("config.yml"), "YAML")
        self.assertEqual(detect_language("Cargo.toml"), "TOML")
        self.assertEqual(detect_language("README.md"), "Markdown")

    def test_special_filenames(self):
        self.assertEqual(detect_language("Dockerfile"), "Dockerfile")
        self.assertEqual(detect_language("docker/Dockerfile"), "Dockerfile")
        self.assertEqual(detect_language("Makefile"), "Makefile")
        self.assertEqual(detect_language("Gemfile"), "Ruby")
        self.assertEqual(detect_language("Jenkinsfile"), "Groovy")
        self.assertEqual(detect_language("CMakeLists.txt"), "CMake")
        self.assertEqual(detect_language("LICENSE"), "License")

    def test_compound_extensions(self):
        self.assertEqual(detect_language("types.d.ts"), "TypeScript (Type Definitions)")
        self.assertEqual(detect_language("auth.spec.ts"), "TypeScript")
        self.assertEqual(detect_language("auth.test.js"), "JavaScript")

    def test_case_insensitivity(self):
        self.assertEqual(detect_language("SCRIPT.PY"), "Python")
        self.assertEqual(detect_language("MAIN.RS"), "Rust")
        self.assertEqual(detect_language("dockerfile"), "Dockerfile")

    def test_unknown_and_empty(self):
        self.assertEqual(detect_language(""), "Unknown")
        self.assertEqual(detect_language("some_binary_file"), "No Extension")
        self.assertEqual(detect_language("archive.unknownext"), "UNKNOWNEXT")


if __name__ == "__main__":
    unittest.main()

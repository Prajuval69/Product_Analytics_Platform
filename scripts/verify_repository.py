"""Inspect deliverable sources while excluding local data, secrets and runtime state."""

import ast
import json
import os
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {
    ".venv",
    ".runtime",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "outputs",
    "target",
    "logs",
    "generated",
    "build",
    "dist",
    "dbt_packages",
}


def inspect_repository():
    files = []
    for folder, directories, filenames in os.walk(ROOT):
        directories[:] = [
            d for d in directories if d not in EXCLUDED and not d.endswith(".egg-info")
        ]
        for name in filenames:
            if name.startswith(".env") and name != ".env.example":
                continue
            path = Path(folder) / name
            if path.suffix in (
                ".py",
                ".sql",
                ".yml",
                ".yaml",
                ".toml",
                ".md",
                ".ps1",
                ".lock",
            ) or name in (".gitignore", ".dockerignore", "Dockerfile", "LICENSE", ".env.example"):
                files.append(path)
    secret_values = [
        v
        for k, v in dotenv_values(ROOT / ".env").items()
        if k.endswith("PASSWORD") and v and len(v) >= 12
    ]
    secret_matches = []
    for path in files:
        text = path.read_text(encoding="utf-8-sig")
        if path.suffix == ".py":
            ast.parse(text, filename=str(path))
        if any(secret in text for secret in secret_values):
            secret_matches.append(str(path.relative_to(ROOT)))
    if secret_matches:
        raise ValueError(f"Runtime password found in deliverable source: {secret_matches}")
    result = {
        "source_files_inspected": len(files),
        "python_syntax": "passed",
        "runtime_passwords_in_source": 0,
        "git_repository_present": (ROOT / ".git").exists(),
        "excluded_runtime_paths": sorted(EXCLUDED),
        "required_environment_placeholders": (ROOT / ".env.example").exists(),
    }
    folder = ROOT / "outputs/verification"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "repository_check.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(inspect_repository(), indent=2))

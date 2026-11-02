#!/usr/bin/env python3
"""
AFFECTORYX Secret Scanner
Audits repository files and git staging/status for accidentally committed credentials,
private keys, hardcoded tokens, or untracked .env files.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

# High-risk patterns to catch
SECRET_PATTERNS = [
    (r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----", "Private cryptographic key"),
    (r"ghp_[A-Za-z0-9_]{36,}", "GitHub Personal Access Token"),
    (r"github_pat_[A-Za-z0-9_]{82}", "Fine-grained GitHub Token"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"(?:api[_-]?key|auth[_-]?token|secret[_-]?key)\s*[:=]\s*['\"][A-Za-z0-9_\-\.]{24,}['\"]", "High-entropy API key assignment"),
    (r"postgres(?:ql)?:\/\/[a-zA-Z0-9_\-]+:[a-zA-Z0-9_\-]+@", "PostgreSQL connection string with credentials"),
    (r"mongodb(?:\+srv)?:\/\/[a-zA-Z0-9_\-]+:[a-zA-Z0-9_\-]+@", "MongoDB connection string with credentials"),
]

ALLOWED_FILES = {
    ".env.example",
    "backend/.env.example",
}


def check_env_files(root: Path):
    violations = []
    for p in root.rglob(".env*"):
        rel = str(p.relative_to(root))
        if rel in ALLOWED_FILES:
            continue
        if "node_modules" in rel or ".venv" in rel:
            continue
        violations.append(f"Forbidden environment file found in filesystem: {rel}")
    return violations


def check_tracked_files(root: Path):
    violations = []
    try:
        tracked = subprocess.check_output(
            ["git", "ls-files"], cwd=str(root), text=True
        ).splitlines()
    except Exception:
        # Not a git repo yet or no commits
        tracked = [
            str(p.relative_to(root))
            for p in root.rglob("*")
            if p.is_file() and not any(part in p.parts for part in [".git", "node_modules", ".venv"])
        ]

    for rel_path in tracked:
        if rel_path in ALLOWED_FILES:
            continue
        file_path = root / rel_path
        if not file_path.is_file():
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for pattern, label in SECRET_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for m in matches:
                # Exclude mock test patterns or schema docs if explicitly intended
                matched_text = m.group(0)
                if "replace-with" in matched_text or "example" in matched_text or "placeholder" in matched_text:
                    continue
                line_no = content[:m.start()].count("\n") + 1
                violations.append(
                    f"{rel_path}:{line_no} - {label} detected: {matched_text[:30]}..."
                )

    return violations


def main():
    root = Path(__file__).resolve().parent.parent
    print(f"[*] Scanning AFFECTORYX workspace at: {root}")

    env_violations = check_env_files(root)
    content_violations = check_tracked_files(root)

    all_violations = env_violations + content_violations

    if all_violations:
        print("\n❌ SECURITY VIOLATIONS DETECTED:")
        for v in all_violations:
            print(f"  - {v}")
        print("\nFix all issues before committing or pushing.")
        sys.exit(1)
    else:
        print("\n✅ Clean repository: No committed .env files, credentials, or high-risk secret patterns found.")
        sys.exit(0)


if __name__ == "__main__":
    main()

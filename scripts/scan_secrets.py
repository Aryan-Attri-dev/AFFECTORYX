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


def is_file_tracked(root: Path, rel_path: str) -> bool:
    try:
        res = subprocess.run(
            ["git", "ls-files", "--error-unmatch", rel_path],
            cwd=str(root),
            capture_output=True,
            text=True,
        )
        return res.returncode == 0
    except Exception:
        return False


def is_file_gitignored(root: Path, rel_path: str) -> bool:
    try:
        res = subprocess.run(
            ["git", "check-ignore", "-q", rel_path],
            cwd=str(root),
            capture_output=True,
        )
        return res.returncode == 0
    except Exception:
        # Fallback if git is unavailable: check .gitignore directly
        gitignore = root / ".gitignore"
        if gitignore.is_file():
            patterns = [line.strip() for line in gitignore.read_text().splitlines() if line.strip() and not line.startswith("#")]
            return any(p in rel_path or rel_path == p.lstrip("/") for p in patterns)
        return False


def check_env_files(root: Path):
    violations = []
    for p in root.rglob(".env*"):
        rel = str(p.relative_to(root))
        if rel in ALLOWED_FILES:
            continue
        if "node_modules" in rel or ".venv" in rel or ".git" in rel:
            continue

        # 1. Strictly forbid any .env file tracked in git
        if is_file_tracked(root, rel):
            violations.append(
                f"CRITICAL SECURITY VIOLATION: Environment file '{rel}' is TRACKED in git. Remove it immediately with 'git rm --cached {rel}'."
            )
        # 2. Forbid any .env file that is untracked and NOT ignored
        elif not is_file_gitignored(root, rel):
            violations.append(
                f"SECURITY VIOLATION: Environment file '{rel}' is present and NOT protected by .gitignore. Add it to .gitignore immediately."
            )
        else:
            # Safely ignored local developer file
            pass

    return violations


def check_tracked_and_staged_files(root: Path):
    violations = []
    tracked_or_untracked = []

    try:
        # 1. All tracked files
        tracked = subprocess.check_output(
            ["git", "ls-files"], cwd=str(root), text=True
        ).splitlines()
        tracked_or_untracked.extend(tracked)

        # 2. Untracked files that are NOT ignored
        untracked = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=str(root), text=True
        ).splitlines()
        for line in untracked:
            if line.startswith("?? "):
                file_rel = line[3:].strip()
                if not is_file_gitignored(root, file_rel):
                    tracked_or_untracked.append(file_rel)
    except Exception:
        tracked_or_untracked = [
            str(p.relative_to(root))
            for p in root.rglob("*")
            if p.is_file() and not any(part in p.parts for part in [".git", "node_modules", ".venv"])
        ]

    for rel_path in set(tracked_or_untracked):
        if rel_path in ALLOWED_FILES:
            continue
        if any(part in rel_path for part in [".git", "node_modules", ".venv", ".pytest_cache", ".next"]):
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
                matched_text = m.group(0)
                matched_text_lower = matched_text.lower()
                if any(x in matched_text_lower for x in ["replace-with", "example", "placeholder", "mock", "dummy", "test"]):
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
    content_violations = check_tracked_and_staged_files(root)

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

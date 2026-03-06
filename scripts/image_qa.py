#!/usr/bin/env python3
"""
War Chronicle — Image Rights QA Pipeline
=========================================
Checks all blog posts for:
1. Cover image attribution (caption + source)
2. License identification
3. DoD disclaimer presence (required for DVIDS/Pentagon images)
4. Known problematic sources (Getty, Shutterstock, AP Photo etc. - NOT free)
5. Missing or incomplete attribution

Run:
  python3 scripts/image_qa.py              # Check all posts
  python3 scripts/image_qa.py --fix-dod   # Auto-add DoD disclaimer where missing

Exit code: 0 = all clear, 1 = issues found
"""

import os
import re
import sys
import glob
from pathlib import Path

# ─── Config ─────────────────────────────────────────────────────────────────

CONTENT_DIR = Path(__file__).parent.parent / "content"

DOD_DISCLAIMER = (
    "*The appearance of U.S. Department of Defense (DoD) visual information "
    "does not imply or constitute DoD endorsement.*"
)

# Indicators that an image is from DoD/US military (requires disclaimer)
DOD_INDICATORS = [
    "dod", "dvids", "department of defense", "u.s. navy", "u.s. army",
    "u.s. air force", "u.s. marine", "pentagon", "master sgt", "petty officer",
    "staff sgt", "senior airman", "lance cpl", "nara", "national archives",
    "public domain", "us navy", "us army", "us air force",
]

# Known PAID / rights-managed sources — NEVER use without license
FORBIDDEN_SOURCES = [
    "getty images", "gettyimages", "shutterstock", "alamy", "corbis",
    "ap photo", "associated press photo", "reuters/", "afp/", "magnum photos",
    "getty/", "istock", "adobe stock",
]

# Accepted free licenses
FREE_LICENSES = [
    "public domain", "cc0", "cc by", "cc-by", "us government",
    "u.s. government", "dod", "nasa", "wikimedia", "commons.wikimedia",
    "no known copyright", "creative commons",
]

# ─── Checks ─────────────────────────────────────────────────────────────────

def check_post(filepath: Path) -> list[dict]:
    issues = []
    content = filepath.read_text(encoding="utf-8")
    rel_path = filepath.relative_to(CONTENT_DIR.parent)

    # 1. Check cover image exists in front matter
    has_cover_fm = bool(re.search(r'^cover:\s*".+?"', content, re.MULTILINE))

    # 2. Check for cover image attribution section
    has_caption = bool(re.search(
        r'\*(?:Cover image|Titelbild|Imagen de portada|Обложка|تصویر جلد|صورة الغلاف):',
        content, re.IGNORECASE
    ))
    has_source = bool(re.search(
        r'\*(?:Source|Quelle|Fuente|Источник|منبع|المصدر):',
        content, re.IGNORECASE
    ))

    if has_cover_fm and not has_caption:
        issues.append({
            "file": str(rel_path),
            "severity": "ERROR",
            "message": "Missing cover image caption"
        })
    if has_cover_fm and not has_source:
        issues.append({
            "file": str(rel_path),
            "severity": "ERROR",
            "message": "Missing cover image source attribution"
        })

    # 3. Check for forbidden paid sources
    content_lower = content.lower()
    for forbidden in FORBIDDEN_SOURCES:
        if forbidden in content_lower:
            issues.append({
                "file": str(rel_path),
                "severity": "CRITICAL",
                "message": f"Potentially rights-managed source detected: '{forbidden}' — verify license before publishing"
            })

    # 4. Check DoD images have disclaimer
    is_dod = any(ind in content_lower for ind in DOD_INDICATORS[:10])  # First 10 are strong DoD signals
    has_disclaimer = DOD_DISCLAIMER.lower()[:40] in content_lower
    if is_dod and not has_disclaimer:
        issues.append({
            "file": str(rel_path),
            "severity": "WARNING",
            "message": "DoD image detected but missing non-endorsement disclaimer"
        })

    # 5. Check if license is identified
    has_license = any(lic in content_lower for lic in FREE_LICENSES)
    if has_cover_fm and has_source and not has_license:
        issues.append({
            "file": str(rel_path),
            "severity": "WARNING",
            "message": "License not clearly stated in image attribution"
        })

    return issues


def add_dod_disclaimer(filepath: Path) -> bool:
    """Auto-add DoD disclaimer after source line if missing."""
    content = filepath.read_text(encoding="utf-8")
    content_lower = content.lower()

    is_dod = any(ind in content_lower for ind in DOD_INDICATORS[:10])
    has_disclaimer = DOD_DISCLAIMER.lower()[:40] in content_lower

    if not is_dod or has_disclaimer:
        return False

    # Add disclaimer after the Source line
    new_content = re.sub(
        r'(\*(?:Source|Quelle|Fuente|Источник|منبع|المصدر):[^\n]+\*)',
        r'\1\n\n' + DOD_DISCLAIMER,
        content,
        flags=re.IGNORECASE,
        count=1
    )

    if new_content != content:
        filepath.write_text(new_content, encoding="utf-8")
        return True
    return False


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    fix_dod = "--fix-dod" in sys.argv
    all_issues = []
    fixed_files = []

    # Scan all index.md files in all language posts
    posts = list(CONTENT_DIR.glob("*/posts/*/index.md"))
    posts += list(CONTENT_DIR.glob("*/prophecy/index.md"))

    print(f"🔍 Checking {len(posts)} files...\n")

    for post in sorted(posts):
        issues = check_post(post)
        all_issues.extend(issues)

        if fix_dod:
            if add_dod_disclaimer(post):
                fixed_files.append(post)

    # ── Report ──
    if all_issues:
        # Group by severity
        criticals = [i for i in all_issues if i["severity"] == "CRITICAL"]
        errors    = [i for i in all_issues if i["severity"] == "ERROR"]
        warnings  = [i for i in all_issues if i["severity"] == "WARNING"]

        if criticals:
            print("🚨 CRITICAL (potential copyright violation):")
            for i in criticals:
                print(f"   {i['file']}: {i['message']}")
            print()

        if errors:
            print("❌ ERRORS (missing attribution):")
            for i in errors:
                print(f"   {i['file']}: {i['message']}")
            print()

        if warnings:
            print("⚠️  WARNINGS:")
            for i in warnings:
                print(f"   {i['file']}: {i['message']}")
            print()

        print(f"Summary: {len(criticals)} critical, {len(errors)} errors, {len(warnings)} warnings")
    else:
        print("✅ All clear — no rights issues detected.")

    if fixed_files:
        print(f"\n🔧 Auto-fixed DoD disclaimer in {len(fixed_files)} files:")
        for f in fixed_files:
            print(f"   {f.relative_to(CONTENT_DIR.parent)}")

    return 1 if any(i["severity"] in ("CRITICAL", "ERROR") for i in all_issues) else 0


if __name__ == "__main__":
    sys.exit(main())

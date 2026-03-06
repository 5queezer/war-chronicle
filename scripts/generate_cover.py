#!/usr/bin/env python3
"""
War Chronicle — AI Cover Image Generator
Uses Google Gemini Imagen 3 (gemini-2.5-flash-image) for image generation.
"""

import os, sys, argparse, base64, re
from pathlib import Path

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

DAILY_THEMES = {
    "iran": "Persian architectural silhouettes, mosque domes and minarets against a burning sky",
    "israel": "Mediterranean coastline, Iron Dome radar silhouettes, strategic tension",
    "usa": "Naval carrier group silhouette on dark waters, aircraft contrails",
    "hormus": "Strait of Hormuz, tanker ships, strategic chokepoint, nautical chart overlay",
    "nuclear": "Abstract energy symbols, cooling towers, dark industrial aesthetic",
    "ceasefire": "Two silhouetted figures at a negotiating table, dramatic backlight",
    "default": "Abstract geopolitical conflict map, strategic arrows, war room aesthetic",
}

PROMPT_TEMPLATE = """Dramatic abstract geopolitical artwork. Dark cinematic atmosphere. No text, no words, no letters anywhere.
{theme_hint}
Middle Eastern landscape silhouettes, fire and smoke on the horizon, no people visible,
symbolic and powerful, digital painting style, dark palette with amber and crimson accents, high contrast.
1200x627 pixels, photorealistic."""

def pick_theme(title: str) -> str:
    for keyword, theme in DAILY_THEMES.items():
        if keyword in title.lower():
            return theme
    return DAILY_THEMES["default"]

def read_title_from_post(post_dir: Path) -> str:
    index = post_dir / "index.md"
    if index.exists():
        content = index.read_text()
        m = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
        if m:
            return m.group(1).strip()
    return post_dir.name

def generate_image(title: str, output_path: Path) -> bool:
    import urllib.request, json
    theme_hint = pick_theme(title)
    prompt = PROMPT_TEMPLATE.format(theme_hint=theme_hint)
    print(f"  Prompt theme: {theme_hint[:60]}...")

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]}
    }).encode()

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY}"
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.loads(r.read())
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

    # Extract image
    try:
        parts = resp["candidates"][0]["content"]["parts"]
        for part in parts:
            if "inlineData" in part:
                img_data = base64.b64decode(part["inlineData"]["data"])
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(img_data)
                print(f"  ✅ Saved: {output_path} ({len(img_data)//1024}KB)")
                return True
        print(f"  ERROR: No image in response: {resp}")
    except Exception as e:
        print(f"  ERROR parsing response: {e}\n  Response: {str(resp)[:300]}")
    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--post-dir", help="Path to single post directory")
    parser.add_argument("--all", action="store_true", help="Generate for all EN posts")
    args = parser.parse_args()

    base = Path("/root/war-chronicle/content/en/posts")

    if args.post_dir:
        post_dir = Path(args.post_dir)
        title = read_title_from_post(post_dir)
        print(f"Generating cover for: {title}")
        generate_image(title, post_dir / "cover.jpg")
    elif args.all:
        posts = sorted(base.glob("*/"))
        for post_dir in posts:
            if (post_dir / "index.md").exists():
                title = read_title_from_post(post_dir)
                cover = post_dir / "cover.jpg"
                if cover.exists():
                    print(f"  SKIP (exists): {post_dir.name}")
                    continue
                print(f"Generating: {post_dir.name} → {title}")
                generate_image(title, cover)
    else:
        print("Use --post-dir <path> or --all")

if __name__ == "__main__":
    main()

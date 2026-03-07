#!/usr/bin/env python3
"""
Add hyperlinks to all source citations in War Chronicle posts (Day 1-9, all languages).
"""

import os
import re
import glob

# Mapping of source names to URLs for inline citations *(Source)*
INLINE_SOURCE_MAP = {
    "Reuters": "https://www.reuters.com/world/middle-east/",
    "Associated Press": "https://apnews.com/hub/iran",
    "AP": "https://apnews.com/hub/iran",
    "AFP": "https://www.afp.com/en/news-hub",
    "Al Jazeera": "https://www.aljazeera.com/tag/iran-israel-war/",
    "Haaretz": "https://www.haaretz.com/",
    "Times of Israel": "https://www.timesofisrael.com/",
    "Pentagon Press Briefing": "https://www.defense.gov/News/Transcripts/",
    "Pentagon": "https://www.defense.gov/News/Transcripts/",
    "Defense.gov": "https://www.defense.gov/News/Transcripts/",
    "State Department": "https://www.state.gov",
    "CENTCOM": "https://www.centcom.mil",
    "IDF Spokesperson Unit": "https://www.idf.il/en/mini-sites/idf-spokesperson-unit/",
    "IDF": "https://www.idf.il/en/mini-sites/idf-spokesperson-unit/",
    "IRNA": "https://en.irna.ir/",
    "TASS": "https://tass.com/",
    "RT": "https://www.rt.com/",
    "IAEA": "https://www.iaea.org/newscenter/news",
    "UN": "https://news.un.org/en/",
    "IEA": "https://www.iea.org",
    "Wall Street Journal": "https://www.wsj.com/",
    "Bloomberg": "https://www.bloomberg.com/",
    "Washington Post": "https://www.washingtonpost.com/",
    "New York Times": "https://www.nytimes.com/",
    "BBC": "https://www.bbc.com/news/world/middle_east",
    "Guardian": "https://www.theguardian.com/world/iran",
    "Truth Social": "https://truthsocial.com/@realDonaldTrump",
    # FA-specific Telegram channels
    "BRICS News": "https://t.me/s/brics_news",
    "Intel Slava Z": "https://t.me/s/intelslava",
    "Megatron": "https://t.me/s/MegatronOfficial",
    "Uncut News": "https://t.me/s/UncutNews_official",
}

# For Sources section — updated URLs (some were short/wrong in original)
SOURCES_SECTION_REPLACEMENTS = [
    # Reuters
    (r'\[Reuters\]\(https://www\.reuters\.com\)',
     '[Reuters](https://www.reuters.com/world/middle-east/)'),
    # IDF short URL
    (r'\[IDF Spokesperson Unit\]\(https://www\.idf\.il/en/\)',
     '[IDF Spokesperson Unit](https://www.idf.il/en/mini-sites/idf-spokesperson-unit/)'),
    (r'\[IDF\]\(https://www\.idf\.il/en/\)',
     '[IDF](https://www.idf.il/en/mini-sites/idf-spokesperson-unit/)'),
    # Pentagon (already correct in most but some have short URL)
    (r'\[Pentagon\]\(https://www\.defense\.gov\)',
     '[Pentagon](https://www.defense.gov/News/Transcripts/)'),
    # IRNA missing trailing slash
    (r'\[IRNA\]\(https://en\.irna\.ir\)',
     '[IRNA](https://en.irna.ir/)'),
    # TASS missing trailing slash
    (r'\[TASS\]\(https://tass\.com\)',
     '[TASS](https://tass.com/)'),
    # AFP
    (r'\[AFP\]\(https://www\.afp\.com\)',
     '[AFP](https://www.afp.com/en/news-hub)'),
    # Times of Israel
    (r'\[Times of Israel\]\(https://www\.timesofisrael\.com\)',
     '[Times of Israel](https://www.timesofisrael.com/)'),
    # Bloomberg trailing slash
    (r'\[Bloomberg\]\(https://www\.bloomberg\.com\)',
     '[Bloomberg](https://www.bloomberg.com/)'),
    # Washington Post
    (r'\[Washington Post\]\(https://www\.washingtonpost\.com\)',
     '[Washington Post](https://www.washingtonpost.com/)'),
    # IEA
    (r'\[IEA \(International Energy Agency\)\]\(https://www\.iea\.org\)',
     '[IEA (International Energy Agency)](https://www.iea.org/)'),
    # State Department
    (r'\[State Department\]\(https://www\.state\.gov\)',
     '[State Department](https://www.state.gov/)'),
    # CENTCOM
    (r'\[CENTCOM\]\(https://www\.centcom\.mil\)',
     '[CENTCOM](https://www.centcom.mil/)'),
]


def make_linked_source(name, url):
    """Return markdown link for a source name."""
    return f'[{name}]({url})'


def replace_inline_citations(text):
    """
    Replace *(SourceName)* with *([SourceName](URL))* for known sources.
    Skip prophetic/literary attributions.
    """
    def replacer(m):
        inner = m.group(1)  # e.g. "Reuters" or "Pentagon Press Briefing"

        # Skip prophetic/literary citations (contain year or "Bible" etc.)
        if any(skip in inner for skip in [
            'Irlmaier', 'Hildegard', 'Bible', 'ESV', '~1', 'Scripture',
            'Prophecies', 'Scivias', 'Book III', 'Vision'
        ]):
            return m.group(0)  # leave unchanged

        # Handle compound citations like "BRICS News / Intel Slava Z"
        if ' / ' in inner:
            parts = inner.split(' / ')
            linked_parts = []
            for part in parts:
                part = part.strip()
                if part in INLINE_SOURCE_MAP:
                    linked_parts.append(f'[{part}]({INLINE_SOURCE_MAP[part]})')
                else:
                    linked_parts.append(part)
            return f'*({" / ".join(linked_parts)})*'

        # Single source
        if inner in INLINE_SOURCE_MAP:
            url = INLINE_SOURCE_MAP[inner]
            return f'*([{inner}]({url}))*'

        return m.group(0)  # leave unchanged if not in map

    # Match *(SourceName)* — but NOT already-linked ones like *([Source](url))*
    # Pattern: *( followed by content that doesn't start with [
    pattern = r'\*\(([^\[\)][^\)]*)\)\*'
    return re.sub(pattern, replacer, text)


def fix_sources_section(text):
    """Fix URLs in the ## Sources / ## Quellen / etc. section."""
    for pattern, replacement in SOURCES_SECTION_REPLACEMENTS:
        text = re.sub(pattern, replacement, text)
    return text


def process_file(filepath):
    """Process a single markdown file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()

    text = original
    text = replace_inline_citations(text)
    text = fix_sources_section(text)

    if text != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        return True
    return False


def main():
    base_dir = '/root/war-chronicle/content'
    languages = ['en', 'de', 'es', 'ru', 'fa']

    total_changed = 0

    for lang in languages:
        posts_dir = os.path.join(base_dir, lang, 'posts')
        if not os.path.exists(posts_dir):
            print(f"[SKIP] {posts_dir} does not exist")
            continue

        md_files = glob.glob(os.path.join(posts_dir, '*/index.md'))
        md_files.sort()

        lang_changed = 0
        for filepath in md_files:
            changed = process_file(filepath)
            if changed:
                lang_changed += 1
                day = os.path.basename(os.path.dirname(filepath))
                print(f"[{lang.upper()}] Updated: {day}")
            else:
                day = os.path.basename(os.path.dirname(filepath))
                print(f"[{lang.upper()}] No changes: {day}")

        total_changed += lang_changed
        print(f"  → {lang.upper()}: {lang_changed} files updated")

    print(f"\nTotal files updated: {total_changed}")


if __name__ == '__main__':
    main()

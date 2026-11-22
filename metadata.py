"""YouTube SEO metadata: title derivation, tag extraction, chapters,
description writer. Qt-free."""

from __future__ import annotations

#==============================================================================
# ── METADATA — SEO title/description/tags/chapters (Qt-free)
#    (merged from studio/metadata.py in the v2.5 ten-file edition)
#==============================================================================

"""YouTube SEO metadata generator (Qt-free).

Builds upload-ready metadata (title, description with chapters, tags and
hashtags) for an exported typing video and writes it next to the output:

    <output_base>.description.txt   paste into the YouTube description box
    <output_base>.metadata.json     full metadata (also useful for automation)

Chapters are generated from the branding timeline when intro/outro cards are
enabled (0:00 Intro / Coding / Outro) - YouTube requires at least three
entries starting at 0:00, which the intro+typing+outro structure satisfies.
"""

import json
import os
import re
from collections import Counter
from typing import Dict, Iterable, List, Optional, Tuple

from config import INTRO_DURATION, OUTRO_DURATION

# ------------------------------------------------------------------ stopwords
# Programming keywords + generic words that make poor tags.
_STOPWORDS = frozenset("""
def return import from as if elif else for while try except finally with lambda
yield raise class pass break continue global nonlocal assert del in is not and or
none true false self async await match case print len range str int float list
dict set tuple type isinstance super staticmethod classmethod property exception
function const let var new extends implements interface public private protected
static void boolean string number object class enum export default this super
null undefined async await typeof instanceof package struct impl fn pub use mut
match mod crate where move ref unsafe dyn trait loop crate func defer go chan
select switch case break default package include define using namespace template
typename public private virtual override friend operator sizeof typedef
the a an and or of to in on for with is are was were be been it its this that
code video typing watch subscribe like comment share channel shorts youtube
python javascript typescript java code programming coding learn tutorial
""".split())


def derive_title(source_name: str) -> str:
    """Turn a source file name into a human title.

    "sorting_algorithms.py" -> "Sorting Algorithms"
    "my-cool-script.js"     -> "My Cool Script"
    "custom_code.py"        -> "Custom Code"
    """
    base = os.path.splitext(os.path.basename(str(source_name)))[0]
    base = re.sub(r"[_\-\s]+", " ", base).strip()
    if not base or base.lower() in ("custom code", "custom_code", "preview", "untitled"):
        return "Watch Me Code"
    words = base.split()
    titled = []
    for wd in words:
        titled.append(wd[0].upper() + wd[1:] if wd else wd)
    out = " ".join(titled)
    return out[:64].strip() or "Watch Me Code"


def _split_identifier(ident: str) -> Iterable[str]:
    """Split snake_case / camelCase identifiers into words."""
    for part in re.split(r"[_\-\s]+", ident):
        if not part:
            continue
        # camelCase -> camel Case, foo2Bar -> foo2 Bar
        for w in re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])", part):
            yield w.lower()


def extract_tags(code: str, lang: str, limit: int = 18) -> List[str]:
    """Frequency-ranked, filtered keywords from the source code."""
    counts: Counter = Counter()
    for ident in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", code or ""):
        for word in _split_identifier(ident):
            if len(word) < 3 or word in _STOPWORDS or word.isdigit():
                continue
            counts[word] += 1
    tags = [w for w, _ in counts.most_common(limit - 6)]
    generic = [lang, "coding", "programming", "learn to code", "developer",
               "software engineer", "typing video", "coding shorts"]
    out: List[str] = []
    for tag in tags + generic:
        if tag and tag not in out:
            out.append(tag)
        if len(out) >= limit:
            break
    return out


def format_chapter_time(sec: float) -> str:
    sec = max(0, int(round(sec)))
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def build_chapters(typing_duration: float, lead: float = 0.0,
                   tail: float = 0.0) -> List[Tuple[str, str]]:
    """Chapter list from the branding timeline (needs all 3 segments)."""
    if lead <= 0 or tail <= 0 or typing_duration <= 0:
        return []
    return [
        ("0:00", "Intro"),
        (format_chapter_time(lead), "Coding"),
        (format_chapter_time(lead + typing_duration), "Outro"),
    ]


def build_metadata(config, source_names: Optional[List[str]] = None,
                   typing_duration: float = 0.0,
                   lead: float = 0.0, tail: float = 0.0,
                   frame_size: Optional[Tuple[int, int]] = None) -> Dict:
    """Assemble the full metadata dict for one exported video."""
    names = [n for n in (source_names or []) if n and n != "custom_code.py"]
    first = names[0] if names else "custom_code.py"
    title = derive_title(first)

    vertical = bool(frame_size and frame_size[1] > frame_size[0])
    is_shorts = vertical

    lang = "code"
    if config is not None:
        try:
            from config import EXT_TO_LANGUAGE
            lang = EXT_TO_LANGUAGE.get(
                os.path.splitext(first)[1].lower(), "code")
        except Exception:
            lang = "code"

    code = ""
    if config is not None:
        code = getattr(config, "custom_code", "") or ""
    tags = extract_tags(code, lang if lang != "code" else "coding")

    chapters = build_chapters(typing_duration, lead, tail)

    hook = (f"Watch {title} typed in real time - syntax highlighted, with "
            "satisfying mechanical keyboard sounds.")
    lines: List[str] = [title, "", hook, ""]
    if chapters:
        lines.append("Chapters:")
        lines.extend(f"{stamp} {name}" for stamp, name in chapters)
        lines.append("")
    lines.append("Subscribe for more coding videos - new typing videos every week!")
    lines.append("")
    hashtags = ["#coding", "#programming"]
    if is_shorts:
        hashtags.insert(0, "#shorts")
    if lang and lang != "code":
        hashtags.append(f"#{lang}")
    lines.append(" ".join(hashtags[:5]))
    description = "\n".join(lines).strip() + "\n"

    return {
        "title": title,
        "description": description,
        "tags": tags,
        "hashtags": hashtags,
        "chapters": [{"time": stamp, "name": name} for stamp, name in chapters],
        "is_shorts": is_shorts,
        "category": "Education",
        "privacy": "public",
        "made_for_kids": False,
        "language": lang,
        "source_files": names or [first],
    }


def render_description(meta: Dict) -> str:
    return meta.get("description", "")


def write_metadata_files(config, output_path: str,
                         source_names: Optional[List[str]] = None,
                         typing_duration: float = 0.0,
                         lead: float = 0.0, tail: float = 0.0,
                         frame_size: Optional[Tuple[int, int]] = None) -> List[str]:
    """Write <base>.description.txt and <base>.metadata.json next to the mp4.

    Respects ``config.write_metadata``; never raises. Returns written paths.
    """
    if config is None or not getattr(config, "write_metadata", True):
        return []
    base = os.path.splitext(str(output_path))[0]
    if not base or base.endswith("_frames"):
        return []
    try:
        meta = build_metadata(config, source_names, typing_duration, lead, tail,
                              frame_size)
        desc_path = base + ".description.txt"
        json_path = base + ".metadata.json"
        with open(desc_path, "w", encoding="utf-8") as f:
            f.write(render_description(meta))
        payload = dict(meta)
        payload["output"] = str(output_path)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return [desc_path, json_path]
    except Exception:
        from config import logger
        logger.error("Failed to write metadata files", exc_info=True)
        return []

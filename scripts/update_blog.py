#!/usr/bin/env python3
"""Refresh the BLOG-POSTS block in index.html from the drumandbytes.com RSS feed. Run from repo root."""

from __future__ import annotations

import html
import pathlib
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

INDEX = pathlib.Path("index.html")

RSS_URL = "https://drumandbytes.com/rss/"
BLOG_POSTS = 4
GENERATED_NOTE = "<!-- updated by .github/workflows/update-blog.yml -->"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "maris-popens-eu-bot",
            "Accept": "application/rss+xml, application/xml;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def build_blog_block() -> str:
    root = ET.fromstring(fetch(RSS_URL))
    items = root.findall("./channel/item")[:BLOG_POSTS]
    if not items:
        raise RuntimeError("no <item> entries in RSS feed")

    lines = ["        " + GENERATED_NOTE]
    for item in items:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if not title or not link:
            raise RuntimeError(f"RSS item missing title/link: {title!r} {link!r}")
        pub = (item.findtext("pubDate") or "").strip()
        try:
            stamp = f"{parsedate_to_datetime(pub):%Y-%m}"
        except (TypeError, ValueError):
            stamp = ""
        lines.append(
            '        <li><a href="{link}" target="_blank" rel="noopener">'
            '<span class="k">{stamp}</span><span class="v">{title}</span></a></li>'.format(
                link=html.escape(link, quote=True),
                title=html.escape(title),
                stamp=html.escape(stamp),
            )
        )
    return "\n".join(lines)


def replace_block(text: str, key: str, body: str) -> str:
    start, end = f"<!-- {key}:START -->", f"<!-- {key}:END -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if not pattern.search(text):
        raise RuntimeError(f"markers for {key} not found in {INDEX}")
    return pattern.sub(f"{start}\n{body}\n        {end}", text)


def main() -> int:
    original = INDEX.read_text()
    updated = replace_block(original, "BLOG-POSTS", build_blog_block())
    if updated == original:
        print("index.html already up to date")
        return 0
    INDEX.write_text(updated)
    print("index.html updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())

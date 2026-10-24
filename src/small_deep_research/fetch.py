from __future__ import annotations

import html
import re
import urllib.request
from typing import Callable

from .search import UA

Fetcher = Callable[[str], str]


def html_to_text(page: str) -> str:
    page = re.sub(r"(?is)<(script|style|noscript|svg|nav|footer|header)[^>]*>.*?</\1>", " ", page)
    page = re.sub(r"(?i)<br\s*/?>|</p>|</h[1-6]>|</li>|</div>", "\n", page)
    text = html.unescape(re.sub(r"<[^>]+>", " ", page))
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    return "\n".join(ln.strip() for ln in text.split("\n") if ln.strip())


def http_fetch(url: str, timeout: float = 20.0, max_bytes: int = 2_000_000) -> str:
    if not url.startswith(("http://", "https://")):
        raise ValueError("only http(s) URLs are fetched")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        ctype = r.headers.get("Content-Type", "")
        raw = r.read(max_bytes).decode(r.headers.get_content_charset() or "utf-8", "replace")
    return html_to_text(raw) if "html" in ctype or "<html" in raw[:500].lower() else raw

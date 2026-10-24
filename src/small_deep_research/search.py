from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Protocol

UA = "small-deep-research/0.0.1 (+https://github.com/Kimjinyoung0529/small-deep-research)"


@dataclass
class SearchHit:
    title: str
    url: str
    snippet: str = ""


class SearchBackend(Protocol):
    def search(self, query: str, k: int = 5) -> list[SearchHit]: ...


def _get(url: str, timeout: float = 20.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode(r.headers.get_content_charset() or "utf-8", "replace")


def _strip(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


class SearxngSearch:
    """SearXNG instance with JSON output enabled (settings.yml: search.formats includes json)."""

    def __init__(self, base_url: str, timeout: float = 20.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def search(self, query: str, k: int = 5) -> list[SearchHit]:
        q = urllib.parse.urlencode({"q": query, "format": "json"})
        data = json.loads(_get(f"{self.base_url}/search?{q}", self.timeout))
        return [SearchHit(r.get("title", ""), r["url"], r.get("content", "")) for r in data.get("results", []) if r.get("url")][:k]


class DuckDuckGoHTMLSearch:
    """Scrapes html.duckduckgo.com. Unofficial; may break or be rate-limited. Prefer SearXNG for anything serious."""

    def __init__(self, timeout: float = 20.0):
        self.timeout = timeout

    @staticmethod
    def parse(page: str, k: int = 5) -> list[SearchHit]:
        hits: list[SearchHit] = []
        links = re.findall(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', page, re.S)
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', page, re.S)
        for i, (href, title) in enumerate(links):
            href = html.unescape(href)
            if "uddg=" in href:
                href = urllib.parse.unquote(urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("uddg", [href])[0])
            if href.startswith("//"):
                href = "https:" + href
            if not href.startswith("http"):
                continue
            hits.append(SearchHit(_strip(title), href, _strip(snippets[i]) if i < len(snippets) else ""))
            if len(hits) >= k:
                break
        return hits

    def search(self, query: str, k: int = 5) -> list[SearchHit]:
        return self.parse(_get("https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query}), self.timeout), k)

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from . import prompts as P
from .budget import Budget, BudgetExceeded, estimate_tokens
from .fetch import Fetcher, http_fetch
from .llm import LLM
from .search import SearchBackend, SearchHit


@dataclass
class Source:
    n: int
    title: str
    url: str
    notes: list[str] = field(default_factory=list)


@dataclass
class ResearchResult:
    question: str
    report_md: str
    sources: list[Source]
    queries: list[str]
    budget: dict
    stopped_by: str | None = None


def parse_queries(text: str, limit: int) -> list[str]:
    m = re.search(r"\[.*?\]", text, re.S)
    if m:
        try:
            arr = json.loads(m.group(0))
            out = [str(x).strip() for x in arr if str(x).strip()]
            if out:
                return out[:limit]
        except json.JSONDecodeError:
            pass
    lines = [re.sub(r"^[\s\-\*\d\.\)\"']+|[\"',]+$", "", ln).strip() for ln in text.splitlines()]
    return [ln for ln in lines if ln and not ln.startswith(("[", "]"))][:limit]


def parse_notes(text: str, k: int) -> list[str]:
    if text.strip() in ("없음", "없음.", "NONE", ""):
        return []
    out = []
    for ln in text.splitlines():
        ln = re.sub(r"^[\s\-\*•\d\.\)]+", "", ln).strip()
        if ln and ln not in ("없음", "없음."):
            out.append(ln)
    return out[:k]


class ResearchEngine:
    def __init__(self, llm: LLM, search: SearchBackend, fetcher: Fetcher = http_fetch, budget: Budget | None = None,
                 queries_per_round: int = 3, hits_per_query: int = 3, page_chars: int = 4000, notes_per_page: int = 5):
        self.llm = llm
        self.search = search
        self.fetch = fetcher
        self.budget = budget or Budget()
        self.qpr = queries_per_round
        self.hpq = hits_per_query
        self.page_chars = page_chars
        self.npp = notes_per_page

    # --- llm wrapper with token accounting ---
    def _ask(self, system: str, user: str, max_tokens: int = 512) -> str:
        cost = estimate_tokens(system) + estimate_tokens(user) + max_tokens
        if cost > self.budget.tokens_left():
            raise BudgetExceeded("max_tokens")
        out = self.llm.chat([{"role": "system", "content": system}, {"role": "user", "content": user}], max_tokens=max_tokens)
        self.budget.use_tokens(estimate_tokens(system) + estimate_tokens(user) + estimate_tokens(out))
        return out

    def _notes_block(self, sources: list[Source]) -> str:
        return "\n".join(f"[{s.n}] {s.title}\n" + "\n".join(f"- {x}" for x in s.notes) for s in sources if s.notes) or "(없음)"

    def run(self, question: str) -> ResearchResult:
        b = self.budget
        sources: list[Source] = []
        seen: set[str] = set()
        used_queries: list[str] = []
        stopped_by = None
        try:
            queue = parse_queries(self._ask(P.PLAN_SYS, P.PLAN_USER.format(question=question, n=self.qpr), 200), self.qpr) or [question]
            while queue and b.can_step():
                query = queue.pop(0)
                if query in used_queries:
                    continue
                b.use_step()
                used_queries.append(query)
                try:
                    hits: list[SearchHit] = self.search.search(query, self.hpq)
                except Exception as e:  # network/backends are flaky; keep going
                    b.log.append(f"search failed: {query!r}: {e}")
                    hits = []
                for h in hits:
                    if h.url in seen or not b.can_fetch():
                        continue
                    seen.add(h.url)
                    try:
                        text = self.fetch(h.url)
                    except Exception as e:
                        b.log.append(f"fetch failed: {h.url}: {e}")
                        text = h.snippet
                    b.use_page()
                    if not text:
                        continue
                    raw = self._ask(P.NOTES_SYS, P.NOTES_USER.format(question=question, title=h.title, text=text[: self.page_chars], k=self.npp), 300)
                    notes = parse_notes(raw, self.npp)
                    if notes:
                        sources.append(Source(len(sources) + 1, h.title or h.url, h.url, notes))
                if not queue and b.can_step() and sources:
                    ans = self._ask(P.REFINE_SYS, P.REFINE_USER.format(question=question, notes=self._notes_block(sources)), 120)
                    if "DONE" not in ans.upper():
                        queue = [q for q in parse_queries(ans, self.qpr) if q not in used_queries]
            if not b.can_step() and queue:
                stopped_by = "max_steps"
        except BudgetExceeded as e:
            stopped_by = str(e)

        report, report_cut = self._report(question, sources)
        if report_cut and not stopped_by:
            stopped_by = "max_tokens"
        return ResearchResult(question, report, sources, used_queries, b.summary(), stopped_by)

    def _report(self, question: str, sources: list[Source]) -> tuple[str, bool]:
        cut = False
        if not sources:
            body = "## 요약\n\n근거로 쓸 자료를 찾지 못했어요. 검색 백엔드나 예산 설정을 확인해 주세요."
        else:
            try:
                body = self._ask(P.REPORT_SYS, P.REPORT_USER.format(question=question, notes=self._notes_block(sources)), 1200)
            except BudgetExceeded:
                cut = True
                body = "## 요약\n\n토큰 예산이 부족해 종합 보고서를 쓰지 못했어요. 아래는 모은 메모예요.\n\n" + self._notes_block(sources)
            valid = {str(s.n) for s in sources}
            body = re.sub(r"\[(\d+)\]", lambda m: m.group(0) if m.group(1) in valid else "", body)
        refs = "\n".join(f"{s.n}. [{s.title}]({s.url})" for s in sources)
        return f"# {question}\n\n{body.strip()}\n\n## 출처\n\n{refs or '(없음)'}\n", cut

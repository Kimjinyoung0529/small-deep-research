from __future__ import annotations

import argparse
import json
import sys

from .budget import Budget
from .engine import ResearchEngine
from .fetch import http_fetch
from .llm import OpenAICompatLLM
from .search import DuckDuckGoHTMLSearch, SearxngSearch


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="small-deep-research", description="작은 모델용 딥 리서치 / small-model deep research")
    p.add_argument("question")
    p.add_argument("--llm-url", default="http://127.0.0.1:8081/v1", help="OpenAI-compatible base URL")
    p.add_argument("--model", default="local")
    p.add_argument("--api-key", default=None)
    p.add_argument("--searxng", default=None, help="SearXNG base URL (JSON enabled). Default: DuckDuckGo HTML")
    p.add_argument("--max-steps", type=int, default=3)
    p.add_argument("--max-pages", type=int, default=6)
    p.add_argument("--max-tokens", type=int, default=20000)
    p.add_argument("--json", action="store_true", help="print JSON instead of markdown")
    p.add_argument("-o", "--out", default=None)
    a = p.parse_args(argv)

    search = SearxngSearch(a.searxng) if a.searxng else DuckDuckGoHTMLSearch()
    eng = ResearchEngine(OpenAICompatLLM(a.llm_url, a.model, a.api_key), search, http_fetch,
                         budget=Budget(a.max_steps, a.max_pages, a.max_tokens))
    r = eng.run(a.question)
    if a.json:
        out = json.dumps({"question": r.question, "report_md": r.report_md, "queries": r.queries, "budget": r.budget,
                          "stopped_by": r.stopped_by, "sources": [s.__dict__ for s in r.sources]}, ensure_ascii=False, indent=2)
    else:
        out = r.report_md
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(out)
    else:
        sys.stdout.write(out + "\n")
    print(f"[budget] {r.budget} stopped_by={r.stopped_by}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

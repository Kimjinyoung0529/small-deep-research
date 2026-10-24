import json

from small_deep_research import Budget, ResearchEngine
from small_deep_research.engine import parse_notes, parse_queries
from small_deep_research.fetch import html_to_text
from small_deep_research.search import DuckDuckGoHTMLSearch, SearchHit


class FakeLLM:
    def __init__(self, refine="DONE"):
        self.calls = []
        self.refine = refine

    def chat(self, messages, max_tokens=512, temperature=0.2):
        sys_ = messages[0]["content"]
        self.calls.append(sys_)
        if "계획" in sys_:
            return '["서울 인구", "서울 면적"]'
        if "사실만" in sys_:
            return "없음" if "광고" in messages[1]["content"] else "- 서울 인구는 약 930만 명이다\n- 출처 자료 기준"
        if "점검" in sys_:
            return self.refine
        return "## 요약\n\n서울 인구는 약 930만 명이에요 [1]. 면적 자료도 있어요 [2]. 엉터리 번호 [99]."


class FakeSearch:
    def __init__(self):
        self.queries = []

    def search(self, q, k=5):
        self.queries.append(q)
        base = len(self.queries) * 10
        return [SearchHit(f"문서{base + i}", f"https://ex.com/{base + i}", "snip") for i in range(k)]


def fetch_ok(url):
    return "광고 페이지" if url.endswith("2") else f"본문 {url}"


def test_full_loop_cites_and_numbers_sources():
    eng = ResearchEngine(FakeLLM(), FakeSearch(), fetch_ok, Budget(max_steps=3, max_pages=10, max_tokens=50000), hits_per_query=3)
    r = eng.run("서울 인구는?")
    assert r.queries == ["서울 인구", "서울 면적"]
    assert r.sources and [s.n for s in r.sources] == list(range(1, len(r.sources) + 1))
    assert "## 출처" in r.report_md and "1. [문서10](https://ex.com/10)" in r.report_md
    assert "[99]" not in r.report_md  # invalid citations stripped
    assert r.stopped_by is None


def test_page_budget_respected():
    eng = ResearchEngine(FakeLLM(), FakeSearch(), fetch_ok, Budget(max_steps=5, max_pages=2, max_tokens=50000))
    r = eng.run("q")
    assert eng.budget.pages == 2
    assert len(r.sources) <= 2


def test_step_budget_and_refine_queries():
    llm = FakeLLM(refine='["추가1", "추가2"]')
    s = FakeSearch()
    eng = ResearchEngine(llm, s, fetch_ok, Budget(max_steps=3, max_pages=50, max_tokens=100000))
    r = eng.run("q")
    assert len(s.queries) == 3 and s.queries[2] == "추가1"
    assert r.stopped_by == "max_steps"


def test_token_budget_falls_back_without_crash():
    eng = ResearchEngine(FakeLLM(), FakeSearch(), fetch_ok, Budget(max_steps=3, max_pages=10, max_tokens=1500))
    r = eng.run("서울 인구는?")
    assert r.stopped_by == "max_tokens"
    assert r.report_md.startswith("# 서울 인구는?")


def test_failures_are_tolerated():
    class BadSearch:
        def search(self, q, k=5):
            raise OSError("down")

    eng = ResearchEngine(FakeLLM(), BadSearch(), fetch_ok, Budget())
    r = eng.run("q")
    assert r.sources == [] and "찾지 못했어요" in r.report_md
    assert any("search failed" in x for x in eng.budget.log)


def test_fetch_failure_uses_snippet():
    def bad_fetch(url):
        raise OSError("nope")

    r = ResearchEngine(FakeLLM(), FakeSearch(), bad_fetch, Budget(max_steps=1, max_pages=1)).run("q")
    assert len(r.sources) == 1


def test_parsers():
    assert parse_queries('계획: ["a", "b", "c", "d"]', 3) == ["a", "b", "c"]
    assert parse_queries("1. 첫째\n2. 둘째", 5) == ["첫째", "둘째"]
    assert parse_notes("없음", 5) == []
    assert parse_notes("- 하나\n* 둘\n3. 셋", 2) == ["하나", "둘"]


def test_html_to_text_and_ddg_parse():
    t = html_to_text("<html><script>x()</script><p>안녕&amp;하세요</p><div>둘째</div></html>")
    assert "x()" not in t and "안녕&하세요" in t and "둘째" in t
    page = ('<a rel="nofollow" class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fa.com%2Fx&amp;rut=1">A <b>t</b></a>'
            '<a class="result__snippet" href="#">스니펫</a>')
    hits = DuckDuckGoHTMLSearch.parse(page)
    assert hits[0].url == "https://a.com/x" and hits[0].title == "A t" and hits[0].snippet == "스니펫"


def test_cli_with_mocks(monkeypatch, capsys):
    from small_deep_research import cli

    monkeypatch.setattr(cli, "OpenAICompatLLM", lambda *a, **k: FakeLLM())
    monkeypatch.setattr(cli, "DuckDuckGoHTMLSearch", lambda: FakeSearch())
    monkeypatch.setattr(cli, "http_fetch", fetch_ok)
    assert cli.main(["서울 인구는?", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["sources"] and "## 출처" in data["report_md"]

# small-deep-research

작은 로컬 모델(llama.cpp 등)로 돌리는 **딥 리서치 엔진의 최소 뼈대**예요. AETHERION 오픈소스 6번 프로젝트예요.
A **minimal skeleton** of a deep-research engine designed for small local models. Part of the AETHERION OSS suite.

> 상태: **뼈대(v0.0.1)**. 품질 벤치마크는 아직 하지 않았어요. 보고서 품질은 쓰는 모델과 검색 백엔드에 크게 좌우돼요.
> Status: **skeleton (v0.0.1)**. No quality benchmarks have been run; report quality depends heavily on the model and search backend.

## 동작 방식 / How it works

```
계획(plan) → 검색(search) → 가져오기(fetch) → 메모 추출(notes) → [부족하면 추가 검색] → 인용 보고서(report)
```

- **LLM 교체 가능**: OpenAI 호환 `/v1/chat/completions`면 무엇이든 (llama.cpp `llama-server`, vLLM, Ollama…).
- **검색 교체 가능**: SearXNG(JSON 출력 켜진 인스턴스) 또는 DuckDuckGo HTML(비공식 스크래핑, 깨질 수 있음). `search(query, k)`만 구현하면 직접 붙일 수 있어요.
- **예산 제한**: `max_steps`(검색 횟수), `max_pages`(가져올 페이지 수), `max_tokens`(추정 토큰). 넘으면 멈추고, 모은 메모까지로 보고서를 써요.
- **한국어 우선 프롬프트**: 작은 모델이 따르기 쉽게 짧고 딱딱하게 썼어요.
- **번호 붙은 출처**: 보고서 본문에 `[1]` 형식 인용, 끝에 `## 출처` 목록. 없는 번호의 인용은 자동으로 지워요.
- 의존성 없음(표준 라이브러리만).

Pluggable OpenAI-compatible LLM, pluggable search (SearXNG / DuckDuckGo HTML / your own), budget limits on steps/pages/estimated tokens, Korean-first prompts, markdown report with numbered sources. Zero runtime dependencies.

## 사용법 / Usage

```bash
pip install -e .
# llama.cpp 서버가 127.0.0.1:8081 에 떠 있다고 가정 / assumes llama-server on :8081
small-deep-research "2026년 한국 최저임금은 얼마야?" --max-steps 3 --max-pages 6
small-deep-research "질문" --searxng http://localhost:8888 --json -o out.json
```

```python
from small_deep_research import Budget, ResearchEngine
from small_deep_research.llm import OpenAICompatLLM
from small_deep_research.search import SearxngSearch

eng = ResearchEngine(OpenAICompatLLM("http://127.0.0.1:8081/v1"), SearxngSearch("http://localhost:8888"),
                     budget=Budget(max_steps=3, max_pages=6, max_tokens=20000))
print(eng.run("질문").report_md)
```

## 한계 / Limitations (솔직하게)

- 토큰 수는 글자 수 기반 **추정치**예요(정확한 토크나이저 아님).
- 작은 모델은 JSON 형식을 자주 어겨요. 파서가 대충 복구하지만 완벽하지 않아요.
- 인용 번호가 실제로 그 문장을 뒷받침하는지는 검증하지 않아요(번호 범위만 확인).
- 자바스크립트로 그려지는 페이지, PDF는 아직 못 읽어요.
- DuckDuckGo HTML 스크래핑은 비공식이라 차단·변경될 수 있어요.

## 개발 / Development

```bash
pip install -e ".[dev]" && ruff check . && pytest -q
```
테스트는 가짜 LLM·검색·fetch로 돌아서 네트워크나 모델이 필요 없어요. Tests use mocked LLM/search/fetch — no network or model needed.

## 라이선스 / License

Apache-2.0 © AETHERION 팀

"""Korean-first prompts. Kept short on purpose: small models follow short, rigid instructions better."""

PLAN_SYS = (
    "너는 리서치 계획을 세우는 도우미야. 사용자의 질문에 답하려면 무엇을 검색해야 하는지 "
    "웹 검색어를 정해. 반드시 JSON 배열(문자열 목록)만 출력해. 설명은 쓰지 마."
)
PLAN_USER = "질문: {question}\n검색어 최대 {n}개를 JSON 배열로만 출력해. 예: [\"검색어1\", \"검색어2\"]"

NOTES_SYS = (
    "너는 자료에서 사실만 뽑아내는 도우미야. 질문과 관련된 사실만 짧은 글머리표(- )로 적어. "
    "자료에 없는 내용은 절대 지어내지 마. 관련 내용이 없으면 '없음' 한 단어만 출력해."
)
NOTES_USER = "질문: {question}\n출처 제목: {title}\n출처 본문(일부):\n{text}\n\n관련 사실(최대 {k}줄):"

REFINE_SYS = (
    "너는 리서치 진행을 점검하는 도우미야. 지금까지 모은 메모로 질문에 충분히 답할 수 있으면 "
    "DONE 한 단어만 출력해. 부족하면 추가 검색어를 JSON 배열로만 출력해."
)
REFINE_USER = "질문: {question}\n지금까지의 메모:\n{notes}\n\n출력(DONE 또는 JSON 배열):"

REPORT_SYS = (
    "너는 리서치 보고서를 쓰는 도우미야. 아래 번호가 붙은 메모만 근거로 한국어 마크다운 보고서를 써. "
    "문장마다 근거 출처 번호를 [1], [2]처럼 붙여. 메모에 없는 사실은 쓰지 마. "
    "근거가 부족한 부분은 '확인되지 않음'이라고 솔직하게 적어. 출처 목록은 쓰지 마(프로그램이 붙임)."
)
REPORT_USER = "질문: {question}\n\n메모:\n{notes}\n\n보고서(제목은 '## 요약'으로 시작):"

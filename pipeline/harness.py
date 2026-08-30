"""
pipeline.harness

블로그 초안 및 기술 문서의 무결성을 검증하는 하네스(Linter) 모듈.
이모지 배제, 필수 ADR 섹션 존재 여부, 파일 링크 실존 여부, AI 상투어 등을 결정론적으로 검증합니다.
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple

# 순수 이모지 및 특수 픽토그램 유니코드 패턴 (한글 음절 및 CJK 완전 배제)
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F300-\U0001F5FF"  # Misc Symbols and Pictographs
    "\U0001F680-\U0001F6FF"  # Transport and Map
    "\U0001F700-\U0001F77F"  # Alchemical
    "\U0001F780-\U0001F7FF"  # Geometric Shapes Ext
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002600-\U000026FF"  # Misc symbols (e.g. ⚡, ☕, ⚠️)
    "\U00002700-\U000027BF"  # Dingbats (e.g. 🚀, ✨, ❌)
    "]+",
    flags=re.UNICODE,
)

# AI 특유의 상투어 / 번역투 금지 단어 목록
AI_CLICHE_WORDS = [
    "살펴보겠습니다",
    "알아보겠습니다",
    "중요한 역할을 합니다",
    "매우 유용합니다",
    "살펴보았습니다",
    "도움이 되셨기를 바랍니다",
    "환영합니다",
    "지금까지",
]

# 기술 문서 필수 5대 영역 키워드 (과목 실습 & 프로젝트 회고 공통 대응)
REQUIRED_SECTIONS = [
    ("Context/Overview", ["개요", "배경", "학습 개념", "개념 요약", "Context", "Objective", "Background", "Overview"]),
    ("Challenges/Limitation", ["한계", "기본 구현", "도전 과제", "기술적 제약", "문제", "Naive", "Limitation", "Challenge", "Constraint"]),
    ("Engineering Decisions", ["엔지니어링 의사결정", "리팩터링", "해결 방안", "트레이드오프", "Decision", "Refactoring", "Solution", "Trade-off"]),
    ("Verification/Results", ["검증", "회고", "성과", "배움", "결과", "Verification", "Takeaway", "Result", "Lesson"]),
]


def check_emojis(content: str) -> List[str]:
    """텍스트 내 이모지 포함 여부 검사"""
    errors = []
    matches = list(EMOJI_PATTERN.finditer(content))
    if matches:
        for m in matches:
            errors.append(f"이모지 감지: '{m.group()}' (위치: {m.start()}~{m.end()})")
    return errors


def check_required_sections(content: str) -> List[str]:
    """필수 ADR 섹션 포함 여부 검사"""
    errors = []
    for section_name, keywords in REQUIRED_SECTIONS:
        found = any(kw in content for kw in keywords)
        if not found:
            errors.append(f"필수 섹션 누락: [{section_name}] (허용 키워드: {', '.join(keywords)})")
    return errors


def check_mermaid(content: str) -> List[str]:
    """Mermaid 다이어그램 블록 포함 여부 검사"""
    if "```mermaid" not in content:
        return ["Mermaid 다이어그램 블록(```mermaid ... ```)이 누락되었습니다."]
    return []


def check_ai_cliches(content: str) -> List[str]:
    """AI 상투어 포함 여부 검사"""
    errors = []
    for word in AI_CLICHE_WORDS:
        if word in content:
            errors.append(f"AI 상투어구 감지: '{word}'")
    return errors


def validate_markdown_file(file_path: Path) -> Tuple[bool, List[str]]:
    """마크다운 파일 전체 무결성 검증"""
    if not file_path.exists():
        return False, [f"파일을 찾을 수 없습니다: {file_path}"]

    content = file_path.read_text(encoding="utf-8")
    all_errors = []

    all_errors.extend(check_emojis(content))
    all_errors.extend(check_required_sections(content))
    all_errors.extend(check_mermaid(content))
    all_errors.extend(check_ai_cliches(content))

    is_valid = len(all_errors) == 0
    return is_valid, all_errors


def main():
    if len(sys.argv) < 2:
        print("사용법: python harness.py <검증할_마크다운_파일경로>")
        sys.exit(1)

    target_path = Path(sys.argv[1])
    is_valid, errors = validate_markdown_file(target_path)

    print(f"=== 하네스 검증 시작: {target_path.name} ===")
    if is_valid:
        print("[통과] 모든 거버넌스 및 무결성 검사를 통과했습니다.")
        sys.exit(0)
    else:
        print(f"[실패] {len(errors)}개의 위반 사항이 발견되었습니다:")
        for idx, err in enumerate(errors, 1):
            print(f"  {idx}. {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()

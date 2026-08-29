"""
pipeline.generate_draft

부트캠프의 다중 과목(agent_core, network_zt 등) 디렉토리에서
실습 코드와 주석을 인제스트하고, Google Gemini API를 호출하여
AGENTS.md 및 ADR 규격을 준수하는 기술 블로그 초안을 생성하는 모듈입니다.
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import google.generativeai as genai
from pipeline.harness import validate_markdown_file

# 과목별 메타데이터 매핑
COURSE_CATALOG = {
    "agent_core": {
        "prefix": "c01",
        "course_name": "1과목 AI·자동화 기초",
        "category": "AI·보안 자동화",
        "default_tags": ["Python", "Security Automation", "Flask", "Schedule"],
    },
    "network_zt": {
        "prefix": "c02",
        "course_name": "2과목 네트워크·ZT 운영 기초",
        "category": "네트워크·Zero Trust",
        "default_tags": ["Network", "Zero Trust", "Firewall", "Security"],
    },
}


def scan_target_directories(repo_root: Path) -> List[Tuple[str, str, Path]]:
    """생성 대상이 되는 (course_id, day_id, day_dir_path) 목록 탐색"""
    targets = []
    for course_id, info in COURSE_CATALOG.items():
        course_dir = repo_root / course_id
        if not course_dir.exists() or not course_dir.is_dir():
            continue

        # day01 ~ day08 폴더 스캔
        for item in sorted(course_dir.iterdir()):
            if item.is_dir() and item.name.startswith("day"):
                day_id = item.name
                targets.append((course_id, day_id, item))
    return targets


def collect_code_context(day_dir: Path) -> str:
    """해당 일차 디렉토리 내의 모든 코드, 주석, 데이터 파일 구조 인제스트"""
    context_chunks = []

    # 파이썬 코드 파일 수집
    py_files = sorted(day_dir.glob("*.py"))
    for py_file in py_files:
        content = py_file.read_text(encoding="utf-8")
        context_chunks.append(f"### 파일명: {py_file.name}\n```python\n{content}\n```\n")

    # logs 데이터 파일 목록 수집
    logs_dir = day_dir / "logs"
    if logs_dir.exists() and logs_dir.is_dir():
        log_files = [f.name for f in logs_dir.iterdir() if f.is_file()]
        context_chunks.append(f"### 참조 데이터 파일 (logs/):\n- {', '.join(log_files)}\n")

    return "\n".join(context_chunks)


def build_system_prompt() -> str:
    """AGENTS.md 및 im-not-ai 기반 시스템 프롬프트 구성"""
    return """당신은 보안 자동화 엔지니어링 블로그의 전문 테크니컬 라이터입니다.
지원자가 직접 작성하고 리팩터링한 코드와 주석을 인제스트하여, 고품질 기술 의사결정 기록(ADR) 포스트를 작성합니다.

[엄격한 거버넌스 규칙]
1. 이모지(Emoji) 및 특수 아이콘 기호는 본문, 제목, 코드 블록 어디에도 절대 사용하지 마십시오. 강조는 표준 마크다운 문법만 사용합니다.
2. AI 특유의 상투어구('살펴보겠습니다', '중요한 역할을 합니다', '매우 유용합니다', '지금까지' 등)와 영문 번역투를 완전히 배제하고, 시니어 엔지니어의 담백하고 엄밀한 한국어로 서술하십시오.
3. 단순 파이썬 기초 문법 나열을 금지합니다. '기본 구현의 한계점'과 '작성자가 주석으로 고민하고 해결한 엔지니어링 의사결정'을 명확히 대조하십시오.
4. Mermaid 다이어그램(```mermaid ... ```)을 필수로 1개 이상 포함하여 시스템 동작 흐름을 시각화하십시오.

[필수 마크다운 구조]
반드시 다음 Frontmatter와 5개 섹션 구조를 정확히 지켜서 마크다운을 출력하십시오.

---
title: "포스트 제목"
slug: "cXX-course-dayYY-주제"
description: "한두 줄 요약"
pubDate: YYYY-MM-DD
tags: ["태그1", "태그2"]
category: "카테고리명"
status: "published"
---

## 1. 개요 및 학습 맥락 (Context & Objective)
- 해당 일차의 핵심 보안/자동화 주제 및 해결 과제 서술

## 2. 기본 구현의 한계점 (Limitation of Naive Approach)
- 강의 예시 수준의 단순 구현이 가진 구조적, 보안적, I/O 측면의 한계 분석

## 3. 엔지니어링 의사결정 및 리팩터링 (Engineering Decisions)
- 작성자가 코드와 주석에서 고민한 질문과 해답(Q&A)을 바탕으로 구체적인 리팩터링 근거 서술
- 핵심 코드 스니펫 포함

## 4. 시스템 아키텍처 흐름도 (Mermaid Diagram)
- 전체 동작을 보여주는 Mermaid 시퀀스 또는 플로우차트 다이어그램

## 5. 검증 및 회고 (Verification & Takeaway)
- 동작 검증 결과 및 컴퓨터공학적 배움 요약
"""


def generate_draft_with_gemini(
    course_id: str,
    day_id: str,
    day_dir: Path,
    api_key: str,
    model_name: str = "gemini-1.5-flash",
) -> str:
    """Gemini API를 호출하여 블로그 마크다운 생성"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=build_system_prompt(),
    )

    course_info = COURSE_CATALOG.get(course_id, {})
    code_context = collect_code_context(day_dir)

    user_prompt = f"""[학습 정보]
- 과목: {course_info.get('course_name', course_id)}
- 일차: {day_id}
- 카테고리: {course_info.get('category', '보안 자동화')}
- 기본 태그: {', '.join(course_info.get('default_tags', []))}
- 현재 날짜: {datetime.now().strftime('%Y-%m-%d')}
- 추천 Slug 접두사: {course_info.get('prefix', 'c01')}-{course_id.replace('_', '-')}-{day_id}

[소스코드 및 주석 컨텍스트]
{code_context}

위 소스코드와 주석에 담긴 문제의식을 바탕으로, 지정된 규칙과 Frontmatter를 완벽히 준수하는 기술 블로그 마크다운을 생성하십시오. 마크다운 본문만 출력하고 기타 안내 문구는 생략하십시오."""

    response = model.generate_content(user_prompt)
    raw_text = response.text.strip()

    # 코드 블록 감싸기(```markdown ... ```) 제거 처리
    if raw_text.startswith("```markdown"):
        raw_text = raw_text[len("```markdown"):].strip()
    if raw_text.startswith("```"):
        raw_text = raw_text[len("```"):].strip()
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3].strip()

    return raw_text


def process_single_target(
    course_id: str,
    day_id: str,
    day_dir: Path,
    output_dir: Path,
    api_key: Optional[str] = None,
) -> bool:
    """단일 일차에 대한 초고 생성 및 하네스 검증 실행"""
    course_info = COURSE_CATALOG.get(course_id, {})
    prefix = course_info.get("prefix", "c01")
    target_slug = f"{prefix}-{course_id.replace('_', '-')}-{day_id}"
    output_file = output_dir / f"{target_slug}.md"

    # 이미 파일이 존재하는 경우 스킵 (Day 05의 경우 기존 생성본 호환)
    if output_file.exists():
        print(f"[스킵] 이미 초고가 존재합니다: {output_file.name}")
        return True

    # Day 05 기존 파일이 다른 이름으로 존재하는지 체크
    if day_id == "day05" and (output_dir / "day05-event-driven-pipeline.md").exists():
        print(f"[스킵] Day05 초고가 이미 존재합니다.")
        return True

    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        print(f"[오류] GEMINI_API_KEY 환경변수가 설정되지 않아 {day_id} 생성을 진행할 수 없습니다.")
        return False

    print(f"[생성 중] {course_info.get('course_name')} {day_id} 초고 생성 시작...")
    try:
        content = generate_draft_with_gemini(course_id, day_id, day_dir, api_key)
        output_file.write_text(content, encoding="utf-8")

        # 하네스 검증
        is_valid, errors = validate_markdown_file(output_file)
        if not is_valid:
            print(f"[경고] 생성된 파일이 하네스 검증을 통과하지 못했습니다: {output_file.name}")
            for err in errors:
                print(f"  - {err}")
            return False

        print(f"[완료] 초고 생성 및 하네스 검증 통과: {output_file.name}")
        return True
    except Exception as e:
        print(f"[실패] {day_id} 생성 중 예외 발생: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="DevLog 초고 자동 생성기")
    parser.add_argument("--auto", action="store_true", help="미작성된 모든 dayXX 자동 탐색 및 생성")
    parser.add_argument("--course", type=str, help="특정 과목 지정 (예: agent_core)")
    parser.add_argument("--day", type=str, help="특정 일차 지정 (예: day05)")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    output_dir = repo_root / "docs" / "posts"
    output_dir.mkdir(parents=True, exist_ok=True)

    targets = scan_target_directories(repo_root)

    if args.day:
        course = args.course or "agent_core"
        target_dir = repo_root / course / args.day
        if not target_dir.exists():
            print(f"[오류] 지정한 디렉토리가 존재하지 않습니다: {target_dir}")
            sys.exit(1)
        success = process_single_target(course, args.day, target_dir, output_dir)
        sys.exit(0 if success else 1)

    if args.auto:
        all_success = True
        for course_id, day_id, day_dir in targets:
            success = process_single_target(course_id, day_id, day_dir, output_dir)
            if not success:
                all_success = False
        sys.exit(0 if all_success else 1)

    print("사용법:")
    print("  python pipeline/generate_draft.py --auto")
    print("  python pipeline/generate_draft.py --course agent_core --day day05")


if __name__ == "__main__":
    main()

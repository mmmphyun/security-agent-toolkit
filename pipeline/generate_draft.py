"""
pipeline.generate_draft

1. 부트캠프 과목(agent_core, network_zt 등) 실습 코드 및 주석 인제스트
   - *llm*.py 존재 여부에 따라 '페어 프로그래밍 대조' vs '단독 리팩터링' 모드 자동 분기
   - 학습 개념 요약(1번) 및 전체 산출물 파이프라인(2번) 공식 탑재
2. 자율 프로젝트 디렉토리(projects/**) 내의 비정형 기술/회고 메모 인제스트
3. Google Gemini API를 호출하여 이모지 0개, 괄호 영단어 번역투 0개의 고품질 기술 블로그 초안을 생성합니다.
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import google.generativeai as genai
from pipeline.harness import validate_markdown_file

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


def get_available_gemini_model() -> str:
    """사용 가능한 최신 Gemini 모델 우선순위 선택"""
    preferred_models = [
        "models/gemini-3.6-flash",
        "gemini-3.6-flash",
        "models/gemini-2.5-flash",
        "gemini-2.5-flash",
        "models/gemini-1.5-flash",
        "gemini-1.5-flash",
        "models/gemini-1.5-pro",
        "gemini-1.5-pro",
    ]
    try:
        available = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        print(f"[정보] 사용 가능한 모델 목록: {available}")
        for pref in preferred_models:
            for avail in available:
                if pref == avail or avail.endswith(pref.replace("models/", "")):
                    return avail
        if available:
            return available[0]
    except Exception as e:
        print(f"[경고] 모델 목록 조회 실패: {e}")
    return "models/gemini-3.6-flash"


def scan_course_targets(repo_root: Path) -> List[Tuple[str, str, Path]]:
    """과목 실습 (course_id, day_id, day_dir_path) 탐색"""
    targets = []
    for course_id in COURSE_CATALOG.keys():
        course_dir = repo_root / course_id
        if not course_dir.exists() or not course_dir.is_dir():
            continue

        for item in sorted(course_dir.iterdir()):
            if item.is_dir() and item.name.startswith("day"):
                targets.append((course_id, item.name, item))
    return targets


def scan_project_targets(repo_root: Path) -> List[Tuple[str, str, Path]]:
    """자율 프로젝트 메모 (project_name, note_slug, note_file_path) 탐색"""
    targets = []
    projects_dir = repo_root / "projects"
    if not projects_dir.exists() or not projects_dir.is_dir():
        return targets

    for proj_dir in sorted(projects_dir.iterdir()):
        if not proj_dir.is_dir():
            continue
        project_name = proj_dir.name
        for md_file in sorted(proj_dir.glob("*.md")):
            if md_file.name.lower() == "readme.md":
                continue
            note_slug = md_file.stem
            targets.append((project_name, note_slug, md_file))
    return targets


def collect_course_context(day_dir: Path) -> Tuple[str, bool]:
    """과목 일차 코드, 주석 인제스트 및 llm 파일 존재 여부 반환"""
    chunks = []
    py_files = sorted(day_dir.glob("*.py"))
    has_llm = any("llm" in f.name.lower() for f in py_files)

    for py_file in py_files:
        content = py_file.read_text(encoding="utf-8")
        filename = py_file.name

        role_desc = "실습 코드"
        if "연습" in filename or "practice" in filename:
            role_desc = "작성자가 당일 수업 6교시에 고민하여 직접 완성한 코드 (Student's Original Implementation)"
        elif "llm" in filename:
            role_desc = "작성자의 코드를 바탕으로 AI(LLM)와 페어 프로그래밍을 통해 최적화/모범 구조를 도출한 코드 (AI-Assisted Optimization)"

        chunks.append(f"### 파일명: {filename} [{role_desc}]\n```python\n{content}\n```\n")

    logs_dir = day_dir / "logs"
    if logs_dir.exists() and logs_dir.is_dir():
        log_files = [f.name for f in logs_dir.iterdir() if f.is_file()]
        chunks.append(f"### 참조 데이터 파일 (logs/):\n- {', '.join(log_files)}\n")

    return "\n".join(chunks), has_llm


def build_course_system_prompt(has_llm: bool) -> str:
    """과목 실습용 시스템 프롬프트 (llm 파일 유무에 따라 모드 분기)"""
    rules_file = Path(__file__).resolve().parent / "rules" / "humanize_rules.md"
    humanize_guide = rules_file.read_text(encoding="utf-8") if rules_file.exists() else ""

    pair_programming_guide = ""
    if has_llm:
        pair_programming_guide = """
[페어 프로그래밍 서술 지침: llm 파일 감지됨]
- '연습' 파일은 내가 수업 중에 직접 작성한 6교시 최종 구현이고, 'llm' 파일은 AI 페어 프로그래머에게 검토를 요청하여 도출한 최적화 결과입니다.
- "내가 혼자 다 짰다"고 거짓말하지 말고, "내 코드의 한계점을 분석하고 AI와의 협업을 통해 어떤 설계 원칙을 적용했는지"를 정직한 시각으로 대조 서술하십시오.
"""
    else:
        pair_programming_guide = """
[단독 엔지니어링 서술 지침: llm 파일 없음]
- 인위적인 AI 페어 프로그래밍을 날조하지 마십시오.
- 작성자가 코드와 주석에서 고민한 질문과 해답(Q&A)을 바탕으로, 기본 구현 대비 스스로 어떤 구조적 개선과 리팩터링을 진행했는지를 서술하십시오.
"""

    return f"""당신은 보안 자동화 엔지니어링 블로그의 전문 테크니컬 라이터입니다.
지원자가 작성한 코드와 주석을 인제스트하여, 학습 개념과 전체 산출물 흐름, 엔지니어링 의사결정이 완벽히 담긴 기술 의사결정 기록(ADR) 포스트를 작성합니다.

[한국어 휴머나이징 룰북]
{humanize_guide}

[엄격한 거버넌스 및 표현 규칙]
1. 이모지(Emoji) 및 특수 아이콘 기호 절대 금지.
2. 불필요한 일반 단어 괄호 영단어 병기 금지:
   - 금지: 손상(Broken), 부작용(Side-Effect), 접근(Approach), 구조(Structure), 예외(Exception) 등
   - 허용: 공식 컴퓨터공학/보안 대문자 약어(IDS, IPS, SIEM, SOAR, SRP, CSV, JSON, OOM, AST, API 등)
3. AI 특유의 상투어구('살펴보겠습니다', '중요한 역할을 합니다', '매우 유용합니다', '지금까지' 등) 배제.
{pair_programming_guide}
4. Mermaid 다이어그램(```mermaid ... ```)을 2번 섹션에 필수로 1개 이상 포함하여 시스템 동작 흐름을 시각화하십시오.

[필수 마크다운 구조]
---
title: "포스트 제목"
slug: "cXX-course-dayYY-주제"
description: "한두 줄 요약"
pubDate: YYYY-MM-DD
tags: ["태그1", "태그2"]
category: "카테고리명"
status: "published"
---

## 1. 오늘의 학습 개념 요약 (Core Concepts)
- 오늘 다룬 핵심 기술/이론의 배경 및 동작 원리를 본인의 언어로 명쾌하게 설명

## 2. 전체 산출물 파이프라인 구조 (Deliverables & Workflow)
- 오늘 실습으로 도출된 파일들이 유기적으로 결합되어 완성한 최종 시스템/데이터 흐름 개괄
- 전체 시스템 아키텍처 다이어그램 (Mermaid)

## 3. 기본 구현의 한계점 (Limitation of Naive Approach)
- 단순 구현 또는 초기 작성 코드가 가진 성능, 예외 처리, I/O 측면의 한계 분석

## 4. 엔지니어링 의사결정 및 리팩터링 (Engineering Decisions)
- 구체적인 리팩터링 및 설계 의사결정 근거 서술 (코드 스니펫 대조 포함)

## 5. 검증 및 회고 (Verification & Takeaway)
- 동작 검증 결과 및 실무 관점의 배움 요약
"""


def build_project_system_prompt() -> str:
    """자율 프로젝트 메모용 시스템 프롬프트"""
    rules_file = Path(__file__).resolve().parent / "rules" / "humanize_rules.md"
    humanize_guide = rules_file.read_text(encoding="utf-8") if rules_file.exists() else ""

    return f"""당신은 시니어 소프트웨어 엔지니어 관점의 기술 블로그 아티클 라이터입니다.
작성자가 자유롭게 작성한 프로젝트 메모, 설계 의도, 트러블슈팅 기록, 또는 협업 마찰 해결 과정을 분석하여,
깊이 있고 프로페셔널한 기술 분석 및 프로젝트 회고록 포스트를 작성합니다.

[한국어 휴머나이징 룰북]
{humanize_guide}

[엄격한 거버넌스 및 표현 규칙]
1. 이모지(Emoji) 및 특수 아이콘 기호 절대 금지.
2. 불필요한 일반 단어 괄호 영단어 병기 금지 (단, 공식 대문자 약어는 허용).
3. 메모의 성격(아키텍처 트레이드오프 / 개발 트러블슈팅 / DevOps 운영 이슈 / 이해관계자 협업 및 요구사항 충돌 해결 등)을 스스로 파악하여 가장 알맞은 전문적 어조로 전개할 것.
4. 협업 마찰이나 비즈니스 충돌을 다룰 경우, 감정적 대립이 아닌 '이해관계자 간의 우선순위 불일치 분석 ➔ 객관적 데이터와 프로토타입 기반 설득 ➔ 합의 도출'이라는 성숙한 엔지니어링 협업 프레임워크로 서술할 것.
5. 시스템 구조나 문제 해결 흐름을 보여주는 Mermaid 다이어그램(```mermaid ... ```)을 필수로 1개 이상 포함할 것.

[필수 마크다운 구조]
---
title: "프로젝트 분석/회고 제목"
slug: "proj-프로젝트명-주제슬러그"
description: "한두 줄 요약"
pubDate: YYYY-MM-DD
tags: ["Project", "프로젝트명", "주제태그"]
category: "프로젝트 분석 & 회고"
status: "published"
---

## 1. 개요 및 배경 (Context & Problem Definition)
## 2. 핵심 도전 과제 및 기술적 제약 (Core Challenges & Constraints)
## 3. 엔지니어링 의사결정 및 해결 방안 (Engineering Decisions & Trade-offs)
## 4. 시스템 아키텍처 및 워크플로우 (Mermaid Diagram)
## 5. 성과 및 회고 (Results & Lessons Learned)
"""


def clean_markdown_fences(raw_text: str) -> str:
    """코드 블록 감싸기 제거"""
    text = raw_text.strip()
    if text.startswith("```markdown"):
        text = text[len("```markdown"):].strip()
    if text.startswith("```"):
        text = text[len("```"):].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text


def process_course_target(course_id: str, day_id: str, day_dir: Path, output_dir: Path, api_key: str) -> bool:
    """과목 실습 초고 생성"""
    course_info = COURSE_CATALOG.get(course_id, {})
    prefix = course_info.get("prefix", "c01")
    target_slug = f"{prefix}-{course_id.replace('_', '-')}-{day_id}"
    output_file = output_dir / f"{target_slug}.md"

    if output_file.exists():
        print(f"[스킵] 과목 초고 이미 존재: {output_file.name}")
        return True

    print(f"[생성 중] {course_info.get('course_name')} {day_id} 초고 생성...")
    try:
        code_context, has_llm = collect_course_context(day_dir)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=get_available_gemini_model(),
            system_instruction=build_course_system_prompt(has_llm),
        )

        user_prompt = f"""[학습 정보]
- 과목: {course_info.get('course_name', course_id)}
- 일차: {day_id}
- 카테고리: {course_info.get('category', 'AI·보안 자동화')}
- 기본 태그: {', '.join(course_info.get('default_tags', []))}
- 현재 날짜: {datetime.now().strftime('%Y-%m-%d')}
- 추천 Slug: {target_slug}
- 페어 프로그래밍 모드: {'활성화 (llm 파일 감지됨)' if has_llm else '비활성화 (단독 리팩터링 모드)'}

[소스코드 및 주석 컨텍스트]
{code_context}

위 코드를 바탕으로 Frontmatter와 5대 섹션 구조(개념 요약, 산출물 파이프라인, 한계점, 의사결정, 검증 및 회고)를 완벽히 준수하는 마크다운 본문만 출력하십시오."""

        response = model.generate_content(user_prompt)
        content = clean_markdown_fences(response.text)
        output_file.write_text(content, encoding="utf-8")

        is_valid, errors = validate_markdown_file(output_file)
        if not is_valid:
            print(f"[경고] 하네스 검증 실패: {output_file.name}")
            for err in errors:
                print(f"  - {err}")
            return False

        print(f"[완료] 과목 초고 생성 성공: {output_file.name}")
        return True
    except Exception as e:
        print(f"[실패] 과목 생성 중 예외: {e}")
        return False


def process_project_target(project_name: str, note_slug: str, note_file: Path, output_dir: Path, api_key: str) -> bool:
    """자율 프로젝트 메모 초고 생성"""
    target_slug = f"proj-{project_name.replace('_', '-')}-{note_slug.replace('_', '-')}"
    output_file = output_dir / f"{target_slug}.md"

    if output_file.exists():
        print(f"[스킵] 프로젝트 초고 이미 존재: {output_file.name}")
        return True

    print(f"[생성 중] 프로젝트 [{project_name}] - {note_slug} 초고 생성...")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=get_available_gemini_model(),
            system_instruction=build_project_system_prompt(),
        )

        note_content = note_file.read_text(encoding="utf-8")
        user_prompt = f"""[프로젝트 정보]
- 프로젝트 식별자: {project_name}
- 메모 파일명: {note_file.name}
- 카테고리: 프로젝트 분석 & 회고
- 추천 Slug: {target_slug}
- 현재 날짜: {datetime.now().strftime('%Y-%m-%d')}

[작성자 메모 원본]
{note_content}

위 메모를 바탕으로 시니어 엔지니어링 관점의 기술 블로그 아티클을 작성하십시오. Frontmatter와 마크다운 본문만 출력하십시오."""

        response = model.generate_content(user_prompt)
        content = clean_markdown_fences(response.text)
        output_file.write_text(content, encoding="utf-8")

        is_valid, errors = validate_markdown_file(output_file)
        if not is_valid:
            print(f"[경고] 하네스 검증 실패: {output_file.name}")
            for err in errors:
                print(f"  - {err}")
            return False

        print(f"[완료] 프로젝트 초고 생성 성공: {output_file.name}")
        return True
    except Exception as e:
        print(f"[실패] 프로젝트 생성 중 예외: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="DevLog 초고 통합 자동 생성기")
    parser.add_argument("--auto", action="store_true", help="과목 및 프로젝트 미작성 전체 자동 스캔/생성")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    output_dir = repo_root / "docs" / "posts"
    output_dir.mkdir(parents=True, exist_ok=True)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[오류] GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    genai.configure(api_key=api_key)

    course_targets = scan_course_targets(repo_root)
    project_targets = scan_project_targets(repo_root)

    print(f"=== 스캔 결과: 과목 실습 {len(course_targets)}건, 프로젝트 메모 {len(project_targets)}건 ===")

    all_success = True
    for course_id, day_id, day_dir in course_targets:
        if not process_course_target(course_id, day_id, day_dir, output_dir, api_key):
            all_success = False

    for project_name, note_slug, note_file in project_targets:
        if not process_project_target(project_name, note_slug, note_file, output_dir, api_key):
            all_success = False

    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()

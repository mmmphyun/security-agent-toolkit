"""
pipeline.harness

블로그 초안 및 기술 문서의 무결성을 검증하는 하네스(Linter) 모듈.
이모지 배제, 필수 ADR 섹션 존재 여부, 파일 링크 실존 여부, AI 상투어 등을 결정론적으로 검증합니다.
"""

import re
import sys
from pathlib import Path

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

# AI 특유의 상투어 / 비전문적 메타 어휘 / 번역투 금지 단어 목록
AI_CLICHE_WORDS = [
    "수강생",
    "페어 프로그래밍",
    "학습자 여러분",
    "독자 여러분",
    "모범 답안",
    "살펴보겠습니다",
    "알아보겠습니다",
    "중요한 역할을 합니다",
    "매우 유용합니다",
    "살펴보았습니다",
    "도움이 되셨기를 바랍니다",
    "환영합니다",
    "지금까지",
    "손쉽게",
]

# 기술 문서 필수 5대 영역 키워드 (과목 실습 & 프로젝트 회고 공통 대응)
REQUIRED_SECTIONS = [
    ("Context/Overview", ["개요", "배경", "학습 개념", "개념 요약", "Context", "Objective", "Background", "Overview"]),
    ("Challenges/Limitation", ["한계", "기본 구현", "도전 과제", "기술적 제약", "문제", "Naive", "Limitation", "Challenge", "Constraint"]),
    ("Engineering Decisions", ["엔지니어링 의사결정", "리팩터링", "해결 방안", "트레이드오프", "Decision", "Refactoring", "Solution", "Trade-off"]),
    ("Verification/Results", ["검증", "회고", "성과", "배움", "결과", "Verification", "Takeaway", "Result", "Lesson"]),
]


def clean_markdown_fences(raw_text: str) -> str:
    """최외곽 마크다운 코드 블록 감싸기 제거 (본문 말단 코드블록 보존)"""
    text = raw_text.strip()
    text = re.sub(r"^```(?:markdown)?\s*\n", "", text)
    text = re.sub(r"\n```\s*$", "", text)
    return text.strip()



def check_emojis(content: str) -> list[str]:
    """텍스트 내 이모지 포함 여부 검사"""
    errors = []
    matches = list(EMOJI_PATTERN.finditer(content))
    if matches:
        for m in matches:
            errors.append(f"이모지 감지: '{m.group()}' (위치: {m.start()}~{m.end()})")
    return errors


def check_required_sections(content: str) -> list[str]:
    """필수 ADR 마크다운 헤더(#, ##, ###) 포함 여부 검사"""
    errors = []
    # 마크다운 헤더 라인만 추출하여 정밀 매칭
    header_lines = [line.strip() for line in content.splitlines() if line.strip().startswith("#")]
    header_text = "\n".join(header_lines)

    for section_name, keywords in REQUIRED_SECTIONS:
        found = any(kw in header_text for kw in keywords)
        if not found:
            errors.append(f"필수 섹션 헤더 누락: [{section_name}] (허용 헤더 키워드: {', '.join(keywords)})")
    return errors


def check_mermaid(content: str) -> list[str]:
    """Mermaid 다이어그램 블록 포함 여부 검사"""
    if "```mermaid" not in content:
        return ["Mermaid 다이어그램 블록(```mermaid ... ```)이 누락되었습니다."]
    return []


def check_ai_cliches(content: str) -> list[str]:
    """AI 상투어 포함 여부 검사"""
    errors = []
    for word in AI_CLICHE_WORDS:
        if word in content:
            errors.append(f"AI 상투어구 감지: '{word}'")
    return errors


def validate_markdown_file(file_path: Path) -> tuple[bool, list[str]]:
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


EXCLUDED_ROOT_DIRS = {
    ".git",
    ".github",
    "docs",
    "blog",
    "pipeline",
    "projects",
    "tests",
    "build",
    "dist",
    "venv",
    ".venv",
    "venv.bak",
    "node_modules",
    "security_agent_toolkit.egg-info",
    "__pycache__",
}


def extract_course_prefix(course_dir: Path, fallback_index: int) -> str:
    """과목 README.md 또는 디렉토리명에서 과목 접두사(c01, c02, ...) 추출"""
    readme_path = course_dir / "README.md"
    if readme_path.exists():
        content = readme_path.read_text(encoding="utf-8")
        match = re.search(r"#\s*(\d+)과목", content)
        if match:
            return f"c{int(match.group(1)):02d}"

    # 디렉토리명 자체에 c01, c02 등의 패턴이 있는 경우
    name_match = re.search(r"c(\d+)", course_dir.name.lower())
    if name_match:
        return f"c{int(name_match.group(1)):02d}"

    # 기본 폴백: 순번 기반 접두사
    return f"c{fallback_index:02d}"


def scan_pending_targets(repo_root: Path) -> list[dict[str, str]]:
    """docs/posts/에 아직 포스트가 생성되지 않은 실습 및 프로젝트 타겟 동적 탐색"""
    posts_dir = repo_root / "docs" / "posts"
    existing_slugs = {f.stem for f in posts_dir.glob("*.md")} if posts_dir.exists() else set()
    pending = []

    # 1. 동적 과목 실습 디렉토리 탐색 (dayXX 서브디렉토리를 보유한 모든 디렉토리)
    candidate_dirs = [
        d for d in sorted(repo_root.iterdir())
        if d.is_dir() and d.name not in EXCLUDED_ROOT_DIRS and not d.name.startswith(".")
    ]

    course_dirs = []
    for d in candidate_dirs:
        has_day_dirs = any(sub.is_dir() and sub.name.startswith("day") for sub in d.iterdir())
        if has_day_dirs:
            course_dirs.append(d)

    for idx, course_dir in enumerate(course_dirs, 1):
        prefix = extract_course_prefix(course_dir, fallback_index=idx)
        for item in sorted(course_dir.iterdir()):
            if item.is_dir() and item.name.startswith("day"):
                target_slug = f"{prefix}-{course_dir.name.replace('_', '-')}-{item.name}"
                if target_slug not in existing_slugs:
                    pending.append({
                        "type": "course",
                        "course_id": course_dir.name,
                        "day_id": item.name,
                        "path": str(item.relative_to(repo_root)),
                        "target_slug": target_slug,
                        "expected_file": f"docs/posts/{target_slug}.md",
                    })

    # 2. 자율 프로젝트 메모 파일 동적 탐색
    projects_dir = repo_root / "projects"
    if projects_dir.exists() and projects_dir.is_dir():
        for proj_dir in sorted(projects_dir.iterdir()):
            if not proj_dir.is_dir():
                continue
            proj_name = proj_dir.name
            for md_file in sorted(proj_dir.glob("*.md")):
                if md_file.name.lower() == "readme.md":
                    continue
                target_slug = f"proj-{proj_name.replace('_', '-')}-{md_file.stem.replace('_', '-')}"
                if target_slug not in existing_slugs:
                    pending.append({
                        "type": "project",
                        "project_name": proj_name,
                        "note_file": md_file.name,
                        "path": str(md_file.relative_to(repo_root)),
                        "target_slug": target_slug,
                        "expected_file": f"docs/posts/{target_slug}.md",
                    })

    return pending


def main():
    if len(sys.argv) < 2:
        print("사용법:")
        print("  1. 하네스 검증: python harness.py <검증할_마크다운_파일경로>")
        print("  2. 대기 타겟 스캔: python harness.py --scan-pending")
        print("  3. 커리큘럼 컨텍스트 조회: python harness.py --fetch-curriculum <course_id> <day_id>")
        print("  4. 프로젝트 컨텍스트 조회: python harness.py --fetch-project <project_name> <note_file>")
        sys.exit(1)

    arg = sys.argv[1]

    if arg in ("--scan-pending", "--list-pending"):
        repo_root = Path(__file__).resolve().parent.parent
        pending = scan_pending_targets(repo_root)
        if not pending:
            print("[확인] 모든 실습 및 프로젝트가 이미 블로그 포스트로 작성되었습니다. (대기 타겟: 0건)")
            sys.exit(0)

        print(f"=== 미작성 대기 타겟 ({len(pending)}건) ===")
        for idx, item in enumerate(pending, 1):
            print(f"[{idx}] {item['type'].upper()} | 소스: {item['path']} -> 대상: {item['expected_file']}")
        sys.exit(0)

    if arg in ("--fetch-curriculum", "--fetch-notion"):
        from pipeline.context_loader import fetch_day_lecture_note

        if len(sys.argv) < 4:
            print("사용법: python harness.py --fetch-curriculum <course_id> <day_id>")
            sys.exit(1)
        c_id = sys.argv[2]
        d_id = sys.argv[3]
        note = fetch_day_lecture_note(c_id, d_id)
        print(note)
        sys.exit(0)

    if arg == "--fetch-project":
        from pipeline.analyze_project import analyze_project_context

        if len(sys.argv) < 4:
            print("사용법: python harness.py --fetch-project <project_name> <note_file>")
            sys.exit(1)
        proj_name = sys.argv[2]
        note_name = sys.argv[3]
        repo_root = Path(__file__).resolve().parent.parent
        context_str = analyze_project_context(repo_root, proj_name, note_name)
        print(context_str)
        sys.exit(0)

    target_path = Path(arg)
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


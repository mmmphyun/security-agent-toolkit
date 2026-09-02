"""
pipeline.harness

블로그 초안 및 기술 문서의 무결성을 검증하는 하네스(Linter) 모듈.
이모지 배제, 필수 ADR 섹션 존재 여부, 파일 링크 실존 여부, AI 상투어 등을 결정론적으로 검증합니다.
"""

import json
import re
import sys
from pathlib import Path

import yaml

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



import json

# 기본 내장 공인 약어 및 CS 용어 화이트리스트 (설정 파일 누락 시 fallback)
DEFAULT_WHITELIST = {
    "API", "LLM", "JSON", "JSONL", "JSON Schema", "DB", "R2", "CDN", "SSOT", "HITL", "OIDC", "STS",
    "SPOF", "TTL", "GCP", "AWS", "REST", "mTLS", "eBPF", "Wasm", "gVisor", "OS", "UI",
    "CLI", "IP", "TCP", "UDP", "HTTP", "HTTPS", "TLS", "SSL", "SQL", "NoSQL", "AST",
    "CI", "CD", "PR", "SOC", "SIEM", "SOAR", "XDR", "EDR", "IDS", "IPS", "WAF", "CVE",
    "CWE", "OWASP", "PoC", "LRU", "LFU", "OOM", "CPU", "RAM", "SSD", "HDD", "IO", "I/O",
    "FIFO", "DNS", "SSH", "FTP", "SMTP", "VPN", "VPC", "NAT", "IAM", "RBAC", "ABAC",
    "RTT", "Zero Trust", "Keep-Alive", "Fail-Open", "Fail-Safe", "Circuit Breaker",
    "K8s", "Kubernetes", "Docker", "Redis", "Kafka", "RabbitMQ", "PostgreSQL", "MySQL",
    "MongoDB", "Elasticsearch", "SQLite", "FastAPI", "Flask", "Django", "Express",
    "NestJS", "Next.js", "React", "Vue", "Astro", "Pydantic", "SQLAlchemy", "Aiohttp",
    "Requests", "Pytest", "Part 1", "Part 2", "Part 3", "v1", "v2", "v3",
}

# 대문자 2~6자리 순수 기술 약어 패턴 (예: JWT, AES, RSA, RFC 등 자동 허용)
ACRONYM_PATTERN = re.compile(r"^[A-Z0-9]{2,6}$")


def load_whitelist() -> set[str]:
    """pipeline/config/whitelist.json에서 확장 화이트리스트 로드"""
    config_file = Path(__file__).resolve().parent / "config" / "whitelist.json"
    whitelist = set(DEFAULT_WHITELIST)
    if config_file.exists():
        try:
            data = json.loads(config_file.read_text(encoding="utf-8"))
            for key in ("abbreviations", "frameworks_and_tools"):
                if key in data and isinstance(data[key], list):
                    whitelist.update(data[key])
        except (json.JSONDecodeError, OSError):
            pass
    return whitelist


# 주의가 필요한 AI 양산형 복합 대구 패턴 (Soft Warning 대상)
AI_COMPLEX_CLICHE_PATTERNS = [
    re.compile(r"뿐만 아니라.+도.+을 통해"),
    re.compile(r"뿐만 아니라.+도.+를 통해"),
    re.compile(r"바탕으로.+통해.+수 있습니다"),
    re.compile(r"통해.+바탕으로.+수 있습니다"),
]


def strip_code_blocks(content: str) -> str:
    """코드 블록(```...```) 및 인라인 코드(`...`)를 제거한 순수 마크다운 텍스트 반환"""
    text_without_blocks = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
    text_without_inline = re.sub(r"`[^`\n]+`", "", text_without_blocks)
    return text_without_inline


def check_emojis(content: str) -> list[str]:
    """텍스트 내 이모지 포함 여부 검사"""
    errors = []
    matches = list(EMOJI_PATTERN.finditer(content))
    if matches:
        for m in matches:
            errors.append(f"이모지 감지: '{m.group()}' (위치: {m.start()}~{m.end()})")
    return errors


def is_allowed_english(text: str, whitelist: set[str]) -> bool:
    """영단어가 공인 약어, 화이트리스트, 또는 정규식 약어 패턴에 부합하는지 검증"""
    stripped = text.strip()
    if stripped in whitelist or ACRONYM_PATTERN.match(stripped):
        return True

    # 공백이나 특수문자로 구분된 복합 토큰 분할 검사
    tokens = [t.strip() for t in re.split(r"[\s\-\/\&]+", stripped) if t.strip()]
    return bool(tokens and all(t in whitelist or ACRONYM_PATTERN.match(t) for t in tokens))


def check_parentheses_english(content: str) -> list[str]:
    """한글 뒤 불필요한 영단어 괄호 병기(예: 경보(Alert), 도구(Tool)) 검출 (하드 에러)"""
    errors = []
    pure_text = strip_code_blocks(content)
    whitelist = load_whitelist()

    pattern = re.compile(r"([가-힣]+)\s*\(([A-Za-z0-9\s_\-\/\.\&]+)\)")
    for match in pattern.finditer(pure_text):
        hangul_word = match.group(1)
        english_inside = match.group(2).strip()

        if is_allowed_english(english_inside, whitelist):
            continue

        errors.append(
            f"불필요한 괄호 내 영어 병기 감지: '{match.group()}' (한글: '{hangul_word}', 괄호: '{english_inside}'). "
            f"공인 약어가 아닌 영단어 번역투 병기를 제거하고 순수 한국어로 기술하십시오."
        )
    return errors


def check_required_sections(content: str) -> list[str]:
    """필수 ADR 마크다운 헤더(#, ##, ###) 포함 여부 검사"""
    errors = []
    header_lines = [line.strip() for line in content.splitlines() if line.strip().startswith("#")]
    header_text = "\n".join(header_lines)

    for section_name, keywords in REQUIRED_SECTIONS:
        found = any(kw in header_text for kw in keywords)
        if not found:
            errors.append(f"필수 섹션 헤더 누락: [{section_name}] (허용 헤더 키워드: {', '.join(keywords)})")
    return errors


def check_mermaid(content: str) -> list[str]:
    """Mermaid 다이어그램 블록 존재 및 런타임 구문 유효성 검사"""
    mermaid_blocks = re.findall(r"```mermaid\s*\n(.*?)\n```", content, re.DOTALL)
    if not mermaid_blocks:
        return ["Mermaid 다이어그램 블록(```mermaid ... ```)이 누락되었습니다."]

    errors = []
    valid_diagram_types = (
        "flowchart", "graph", "sequenceDiagram", "classDiagram",
        "stateDiagram", "erDiagram", "gantt", "pie", "mindmap"
    )

    for idx, block in enumerate(mermaid_blocks, 1):
        lines = [line.strip() for line in block.strip().splitlines() if line.strip() and not line.strip().startswith("%%")]
        if not lines:
            errors.append(f"Mermaid 블록 #{idx}의 내용이 비어 있습니다.")
            continue

        first_line = lines[0]
        if not any(first_line.startswith(dtype) for dtype in valid_diagram_types):
            errors.append(f"Mermaid 블록 #{idx}: 유효하지 않은 다이어그램 선언입니다 ('{first_line}'). flowchart, sequenceDiagram 등으로 시작해야 합니다.")

        for line_no, line in enumerate(lines, 1):
            unquoted_labels = re.findall(r"\|([^\"\|\n]*[\(\)\{\}\[\]\/][^\"\|\n]*)\|", line)
            if unquoted_labels:
                for bad_label in unquoted_labels:
                    errors.append(f"Mermaid 블록 #{idx} L{line_no}: 엣지 라벨 '{bad_label.strip()}'에 특수문자/괄호가 포함되어 있으나 큰따옴표로 감싸지 않았습니다 (예: |\"{bad_label.strip()}\"| 형태로 수정 필요).")

            if re.search(r"(\w+)\s*&\s*(\w+)\s*(-->|-->\||-.->)", line):
                errors.append(f"Mermaid 블록 #{idx} L{line_no}: '&' 다중 노드 연결자('{line}')는 브라우저 렌더러에서 깨질 수 있습니다. 개별 간선(A --> C, B --> C)으로 분리하십시오.")

            if line.count("[") != line.count("]") or line.count("{") != line.count("}"):
                errors.append(f"Mermaid 블록 #{idx} L{line_no}: 괄호([]) 또는 중괄호({{}})의 열림/닫힘 쌍이 일치하지 않습니다 ('{line}').")

    return errors


def check_code_paths(content: str, current_file: Path) -> list[str]:
    """코드 블록 주석이나 설명에 명시된 파일 경로가 실제 레포지토리 또는 캐시 레포에 존재하는지 검증"""
    errors = []
    repo_root = current_file.resolve().parent.parent.parent

    # 코드 블록 내부의 파일 경로 주석 패턴 탐색 (예: # ... (src/bot/cogs/sync.py), // path/to/file 등)
    code_blocks = re.findall(r"```(?:\w+)?\s*\n(.*?)\n```", content, re.DOTALL)
    for block in code_blocks:
        first_few_lines = "\n".join(block.strip().splitlines()[:3])
        # 주석 형태의 파일 경로 매칭 (src/..., agent_core/..., projects/...)
        matched_paths = re.findall(r"(?:#|//|\*)\s*.*?([a-zA-Z0-9_\-\./\\]+\.(?:py|ts|js|tsx|jsx|go|rs|java|json|yaml|yml))", first_few_lines)
        for raw_path in matched_paths:
            clean_path = raw_path.strip().replace("\\", "/")
            if "/" not in clean_path or clean_path.startswith("http") or clean_path.startswith("."):
                continue

            # 로컬 레포지토리 내 확인
            local_exists = (repo_root / clean_path).exists()
            # 캐시된 원격 프로젝트 레포지토리 내 확인 (.cache/repos/*/<clean_path>)
            cache_exists = False
            cache_repos_dir = repo_root / ".cache" / "repos"
            if cache_repos_dir.exists():
                for repo_dir in cache_repos_dir.iterdir():
                    if repo_dir.is_dir() and (repo_dir / clean_path).exists():
                        cache_exists = True
                        break

            if not local_exists and not cache_exists:
                errors.append(
                    f"존재하지 않는 가상 소스코드 경로 감지: '{clean_path}'. "
                    f"실제 레포지토리에 존재하는 원본 파일 경로를 사용하거나 가상 코드 창작을 배제하십시오."
                )
    return errors


def check_ai_cliches(content: str) -> tuple[list[str], list[str]]:
    """AI 상투어(하드 에러) 및 복합 대구 패턴(소프트 경고) 검사"""
    hard_errors = []
    soft_warnings = []

    pure_text = strip_code_blocks(content)

    for word in AI_CLICHE_WORDS:
        if word in pure_text:
            hard_errors.append(f"금지된 AI 상투어구 감지: '{word}'")

    for pattern in AI_COMPLEX_CLICHE_PATTERNS:
        matches = list(pattern.finditer(pure_text))
        if matches:
            for m in matches:
                soft_warnings.append(f"기계적 복합 대구 의심 패턴: '{m.group()}' (자연스러운 문맥인지 자가 검토 권장)")

    return hard_errors, soft_warnings


def scan_all_topics(repo_root: Path) -> list[dict]:
    """기존 발행된 모든 블로그 포스트의 핵심 H2/H3 엔지니어링 의사결정 및 트러블슈팅 주제 색인 목록 추출"""
    posts_dir = repo_root / "docs" / "posts"
    topics_ledger = []
    if not posts_dir.exists():
        return topics_ledger

    standard_exclude = [
        "개념 요약", "한계점", "엔지니어링 의사결정", "검증 및 회고",
        "동작 검증", "확장 로드맵", "구조", "Context", "Limitation", "Decision", "Takeaway"
    ]

    for md_file in sorted(posts_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        title_m = re.search(r"^title:\s*[\"']?(.*?)[\"']?$", content, re.MULTILINE)
        title = title_m.group(1) if title_m else md_file.stem

        # 실제 기술적 의사결정 및 문제 해결 H3/H2 헤딩만 추출
        headings = []
        for line in content.splitlines():
            line_s = line.strip()
            if line_s.startswith("### ") or (line_s.startswith("## ") and not line_s.startswith("# ")):
                h_text = re.sub(r"^#{2,3}\s*", "", line_s).strip()
                if h_text and len(h_text) > 3:
                    if not any(ex in h_text for ex in standard_exclude):
                        headings.append(h_text)

        topics_ledger.append({
            "slug": md_file.stem,
            "file": md_file.name,
            "title": title,
            "topics": headings
        })
    return topics_ledger


def check_duplicate_topics(content: str, current_file: Path) -> list[str]:
    """신규 포스트의 H3 주제가 기존 포스트와 중복되는지 검사하고 인용 권장 알림 생성"""
    warnings = []
    repo_root = current_file.resolve().parent.parent.parent
    existing_ledger = scan_all_topics(repo_root)

    current_headings = []
    for line in content.splitlines():
        line_s = line.strip()
        if line_s.startswith("### "):
            h_text = re.sub(r"^###\s*", "", line_s).strip()
            if h_text and len(h_text) > 4:
                current_headings.append(h_text)

    for current_h in current_headings:
        # 단어 토큰 분리 (2글자 이상 키워드)
        current_keywords = set(re.findall(r"[가-힣a-zA-Z0-9]{3,}", current_h))
        if not current_keywords:
            continue

        for prev in existing_ledger:
            if prev["slug"] == current_file.stem:
                continue

            for prev_h in prev["topics"]:
                prev_keywords = set(re.findall(r"[가-힣a-zA-Z0-9]{3,}", prev_h))
                overlap = current_keywords.intersection(prev_keywords)
                # 3개 이상의 핵심 기술 키워드가 겹치고, 본문에 해당 이전 포스트 링크가 없는 경우
                if len(overlap) >= 3 or (len(overlap) >= 2 and current_h == prev_h):
                    if prev["slug"] not in content and prev["file"] not in content:
                        warnings.append(
                            f"중복 주제 검토 권장: '{current_h}' 주제는 이미 [{prev['slug']}]({prev['title']})에서 다루었습니다. "
                            f"내용 중복 서술 대신 이전 포스트 링크([링크](/security-agent-toolkit/blog/{prev['slug']}/)) 인용 및 당일 신규 아키텍처(Delta) 중심으로 작성을 권장합니다."
                        )
    return warnings


def validate_markdown_file(file_path: Path) -> tuple[bool, list[str], list[str]]:
    """마크다운 파일 전체 무결성 검증 (하드 에러와 소프트 경고 분리)"""
    if not file_path.exists():
        return False, [f"파일을 찾을 수 없습니다: {file_path}"], []

    content = file_path.read_text(encoding="utf-8")
    hard_errors = []
    soft_warnings = []

    hard_errors.extend(check_emojis(content))
    hard_errors.extend(check_parentheses_english(content))
    hard_errors.extend(check_required_sections(content))
    hard_errors.extend(check_mermaid(content))
    hard_errors.extend(check_code_paths(content, file_path))

    cliche_errors, cliche_warnings = check_ai_cliches(content)
    hard_errors.extend(cliche_errors)
    soft_warnings.extend(cliche_warnings)

    topic_warnings = check_duplicate_topics(content, file_path)
    soft_warnings.extend(topic_warnings)

    is_valid = len(hard_errors) == 0
    return is_valid, hard_errors, soft_warnings


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

                # Frontmatter 내 status: draft 또는 draft: true 선언 시 대기 타겟에서 배제
                try:
                    content = md_file.read_text(encoding="utf-8").lstrip("\ufeff \t\r\n")
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            fm = yaml.safe_load(parts[1])
                            if isinstance(fm, dict):
                                if fm.get("draft") is True or fm.get("ignore") is True:
                                    continue
                                if str(fm.get("status", "")).lower() in ("draft", "ignore", "wip"):
                                    continue
                except Exception:
                    pass

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

    if arg == "--scan-topics":
        repo_root = Path(__file__).resolve().parent.parent
        ledger = scan_all_topics(repo_root)
        print(f"=== 발행된 블로그 포스트 및 핵심 주제 색인 ({len(ledger)}건) ===")
        for item in ledger:
            print(f"• [{item['slug']}] {item['title']}")
            for t in item['topics']:
                print(f"    - {t}")
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
    is_valid, hard_errors, soft_warnings = validate_markdown_file(target_path)

    print(f"=== 하네스 검증 시작: {target_path.name} ===")
    if soft_warnings:
        print(f"[알림] {len(soft_warnings)}건의 권장 스타일 검토 항목이 있습니다:")
        for idx, warn in enumerate(soft_warnings, 1):
            print(f"  (i) {warn}")

    if is_valid:
        print("[통과] 모든 거버넌스 및 무결성 검사를 통과했습니다.")
        sys.exit(0)
    else:
        print(f"[실패] {len(hard_errors)}개의 필수 거버넌스 위반 사항이 발견되었습니다:")
        for idx, err in enumerate(hard_errors, 1):
            print(f"  {idx}. {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()


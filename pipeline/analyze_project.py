"""
pipeline.analyze_project

자율 프로젝트 레포지토리 심층 분석 및 회고 인제스트 파이프라인.
메모 파일(projects/<project_name>/<note_slug>.md)의 선언형 Frontmatter(repo URL/로컬 경로)를 파싱하고,
exploring-codebases 및 searching-codebases 프로토콜에 따라 프로젝트 아키텍처와 핵심 소스코드를 추출합니다.
"""

import contextlib
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

# 배제 디렉토리 및 파일 확장자
EXCLUDED_DIRS = {
    ".git",
    ".github",
    ".cache",
    ".astro",
    ".idea",
    ".vscode",
    "node_modules",
    "venv",
    ".venv",
    "dist",
    "build",
    "__pycache__",
    "coverage",
    ".pytest_cache",
    ".ruff_cache",
}

EXCLUDED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".svg",
    ".webp",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".bin",
    ".pyc",
    ".class",
    ".lock",
    ".wasm",
    ".whl",
}

SOURCE_EXTENSIONS = {
    ".py",
    ".ts",
    ".js",
    ".tsx",
    ".jsx",
    ".go",
    ".rs",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".sh",
    ".ps1",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".sql",
    ".html",
    ".css",
}


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """마크다운 본문에서 Frontmatter를 안전하게 추출 (BOM/공백 무시 및 Graceful Fallback)"""
    cleaned = content.lstrip("\ufeff \t\r\n")
    if not cleaned.startswith("---"):
        return {}, content

    parts = cleaned.split("---", 2)
    if len(parts) < 3:
        return {}, content

    try:
        data = yaml.safe_load(parts[1])
        return (data, parts[2].strip()) if isinstance(data, dict) else ({}, parts[2].strip())
    except Exception:  # noqa: BLE001
        return {}, parts[2].strip()


def is_excluded_dir(dir_name: str) -> bool:
    """디렉토리가 배제 대상인지 확인"""
    return dir_name in EXCLUDED_DIRS or dir_name.endswith(".egg-info")


def resolve_repository(repo_uri: str | None, project_name: str, cache_root: Path) -> Path | None:
    """원격 Git clone/reset 또는 로컬 경로를 탐색하여 대상 레포지토리의 유효한 Path 반환"""
    if not repo_uri or not str(repo_uri).strip():
        return None

    repo_str = str(repo_uri).strip()

    # 1. 원격 Git URL 처리 (HTTP/HTTPS/SSH)
    if repo_str.startswith(("http://", "https://", "git@", "ssh://")):
        repo_cache_dir = cache_root / "repos" / project_name
        repo_cache_dir.parent.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"

        if (repo_cache_dir / ".git").exists():
            # 멱등적 최신화: fetch 후 reset (충돌 방지)
            with contextlib.suppress(Exception):
                subprocess.run(
                    ["git", "-C", str(repo_cache_dir), "fetch", "--depth", "1", "origin"],
                    env=env,
                    capture_output=True,
                    timeout=30,
                    check=False,
                )
                subprocess.run(
                    ["git", "-C", str(repo_cache_dir), "reset", "--hard", "FETCH_HEAD"],
                    env=env,
                    capture_output=True,
                    timeout=10,
                    check=False,
                )
            return repo_cache_dir

        try:
            res = subprocess.run(
                ["git", "clone", "--depth", "1", repo_str, str(repo_cache_dir)],
                env=env,
                capture_output=True,
                timeout=45,
                check=False,
            )
            if res.returncode == 0 and repo_cache_dir.exists():
                return repo_cache_dir
        except Exception:  # noqa: BLE001
            return None

        return None

    # 2. 로컬 파일 시스템 경로 처리
    local_path = Path(repo_str).resolve()
    return local_path if local_path.exists() and local_path.is_dir() else None


def extract_tech_stack(repo_dir: Path) -> list[str]:
    """[Phase 1] 주요 설정 파일 및 키워드 기반 기술 스택 자동 식별"""
    stacks = []
    config_maps = [
        ("pyproject.toml", "Python (pyproject.toml)", ["fastapi", "flask", "django", "ruff"]),
        ("requirements.txt", "Python (requirements.txt)", ["fastapi", "flask", "django"]),
        ("package.json", "Node.js / npm", ["astro", "next", "react", "typescript", "vue"]),
        ("go.mod", "Go (go.mod)", []),
        ("Cargo.toml", "Rust (Cargo.toml)", []),
        ("Dockerfile", "Docker", []),
        ("docker-compose.yml", "Docker Compose", []),
    ]

    kw_display_map = {
        "fastapi": "FastAPI",
        "flask": "Flask",
        "django": "Django",
        "ruff": "Ruff",
        "astro": "Astro",
        "next": "Next.js",
        "react": "React",
        "typescript": "TypeScript",
        "vue": "Vue",
    }

    for fname, label, sub_kws in config_maps:
        fpath = repo_dir / fname
        if fpath.exists():
            stacks.append(label)
            if sub_kws:
                content = fpath.read_text(encoding="utf-8", errors="ignore").lower()
                for kw in sub_kws:
                    if kw in content:
                        stacks.append(kw_display_map.get(kw, kw.capitalize()))

    return sorted(dict.fromkeys(stacks)) if stacks else ["스택 미식별 (일반 스크립트 또는 문서)"]


def extract_readme(repo_dir: Path, max_lines: int = 100) -> str:
    """[Phase 1] README 파일 내용 추출 (상위 라인 제한)"""
    readme_path = next(
        (p for p in repo_dir.iterdir() if p.is_file() and p.name.lower().startswith("readme")),
        None,
    )
    if readme_path:
        with contextlib.suppress(Exception):
            lines = readme_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            if len(lines) > max_lines:
                return "\n".join(lines[:max_lines]) + f"\n\n...(총 {len(lines)}줄 중 상위 {max_lines}줄 발췌)"
            return "\n".join(lines)
    return "(README 파일을 찾을 수 없습니다.)"


def generate_directory_tree(repo_dir: Path, max_depth: int = 2) -> str:
    """[Phase 1] 2-depth 디렉토리 트리 구조 생성 (배제 디렉토리 적용)"""
    lines = [f"{repo_dir.name}/"]

    def walk_tree(current_dir: Path, depth: int, prefix: str):
        if depth > max_depth:
            return

        with contextlib.suppress(Exception):
            entries = sorted(
                [
                    e for e in current_dir.iterdir()
                    if not e.name.startswith(".") and not is_excluded_dir(e.name)
                    and (e.is_dir() or e.suffix.lower() not in EXCLUDED_EXTENSIONS)
                ],
                key=lambda x: (not x.is_dir(), x.name.lower()),
            )

            for i, entry in enumerate(entries):
                is_last = (i == len(entries) - 1)
                connector = "└── " if is_last else "├── "
                child_prefix = "    " if is_last else "│   "

                if entry.is_dir():
                    lines.append(f"{prefix}{connector}{entry.name}/")
                    walk_tree(entry, depth + 1, prefix + child_prefix)
                else:
                    lines.append(f"{prefix}{connector}{entry.name}")

    walk_tree(repo_dir, 1, "")
    return "\n".join(lines)


def extract_git_commits(repo_dir: Path, max_count: int = 10) -> list[str]:
    """[Phase 1] 최근 Git 커밋 로그 추출"""
    if not (repo_dir / ".git").exists():
        return ["(Git 히스토리가 존재하지 않는 로컬 디렉토리입니다.)"]

    try:
        res = subprocess.run(
            ["git", "-C", str(repo_dir), "log", f"-n{max_count}", "--oneline"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip().splitlines()
    except Exception:  # noqa: BLE001
        return ["(Git 커밋 로그 조회 중 오류가 발생했습니다.)"]

    return ["(Git 커밋 로그를 조회할 수 없습니다.)"]


def extract_keywords_from_note(note_text: str) -> list[str]:
    """[Phase 2] 사견 메모에서 핵심 심볼, 파일명, 함수명, 아키텍처 키워드 추출"""
    keywords = set()
    # 백틱, 데코레이터, 함수/클래스명, 파일 경로 통합 추출
    patterns = re.findall(
        r"`([^`]+)`|(@[\w\.]+)|(?:def|class|async def)\s+(\w+)|([\w\-\./\\]+\.(?:py|ts|js|tsx|jsx|go|rs|yml|yaml|toml|json|md))",
        note_text,
    )
    for group in patterns:
        for item in group:
            if item and len(item.strip()) >= 3 and not item.startswith("-"):
                clean = item.strip().replace("\\", "/")
                keywords.add(clean)
                if "/" in clean:
                    keywords.add(Path(clean).name)

    return sorted(keywords)


def collect_target_source_files(repo_dir: Path) -> list[Path]:
    """레포지토리 내에서 분석 대상이 되는 유효한 소스코드 파일 수집"""
    source_files = []
    for root, dirs, files in os.walk(repo_dir):
        dirs[:] = [d for d in dirs if not is_excluded_dir(d) and not d.startswith(".")]
        root_path = Path(root)
        for fname in files:
            if not fname.startswith(".") and (
                Path(fname).suffix.lower() in SOURCE_EXTENSIONS or fname in ("Dockerfile", "Makefile")
            ):
                source_files.append(root_path / fname)
    return source_files


def find_and_slice_code_snippets(
    repo_dir: Path,
    keywords: list[str],
    max_files: int = 8,
    max_lines_per_file: int = 300,
) -> list[dict[str, str]]:
    """[Phase 2] 사견 키워드와 매칭되는 핵심 소스코드 파일을 최대 8개, 파일당 300줄 이내로 선별 슬라이싱"""
    source_files = collect_target_source_files(repo_dir)
    if not source_files:
        return []

    scored_files: list[tuple[int, Path, str]] = []

    for file_path in source_files:
        try:
            rel_path = str(file_path.relative_to(repo_dir)).replace("\\", "/")
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        score = sum(15 for kw in keywords if kw in rel_path)
        score += sum(2 for kw in keywords if kw in content)
        if file_path.name in ("main.py", "app.py", "index.ts", "server.py", "cli.py", "harness.py"):
            score += 5

        if score > 0:
            scored_files.append((score, file_path, content))

    scored_files.sort(key=lambda x: x[0], reverse=True)

    results = []
    for _, fpath, content in scored_files[:max_files]:
        rel_path = str(fpath.relative_to(repo_dir)).replace("\\", "/")
        lines = content.splitlines()

        if len(lines) <= max_lines_per_file:
            sliced_code = "\n".join(lines)
            summary_info = f"{rel_path} (전체 {len(lines)}줄)"
        else:
            sliced_code = "\n".join(lines[:max_lines_per_file])
            summary_info = f"{rel_path} (총 {len(lines)}줄 중 상위 {max_lines_per_file}줄 슬라이싱)"

        ext = fpath.suffix.lstrip(".")
        lang_map = {"py": "python", "ts": "typescript", "js": "javascript"}
        lang = lang_map.get(ext, ext if ext else "text")

        results.append({
            "path": rel_path,
            "info": summary_info,
            "lang": lang,
            "code": sliced_code,
        })

    return results


def resolve_project_paths(repo_root: Path, project_name: str, note_file: str | None = None) -> tuple[str, Path]:
    """CLI 인자 형태(프로젝트명+파일명 또는 전체 마크다운 파일 경로)를 유연하게 해석"""
    if note_file is None:
        # 단일 경로로 인자가 들어온 경우 (예: projects/devlog-agent-pipeline/01_note.md)
        p = (repo_root / project_name).resolve() if not Path(project_name).is_absolute() else Path(project_name)
        if p.exists() and p.is_file():
            p_name = p.parent.name
            return p_name, p

    # 일반적인 형태: project_name, note_file
    note_path = repo_root / "projects" / project_name / (note_file or "")
    if not note_path.exists():
        # note_file에 이미 projects/ 경로가 포함된 경우 폴백
        alt_path = repo_root / (note_file or "")
        if alt_path.exists():
            note_path = alt_path

    return project_name, note_path


def analyze_project_context(repo_root: Path, project_name: str, note_file: str | None = None) -> str:
    """
    지정된 프로젝트 메모와 연결된 레포지토리를 인제스트하여
    3단 표준 마크다운 규약에 맞춘 최종 컨텍스트 텍스트를 생성합니다.
    """
    proj_name, note_path = resolve_project_paths(repo_root, project_name, note_file)
    if not note_path.exists():
        return f"[오류] 프로젝트 메모 파일을 찾을 수 없습니다: {note_path}"

    note_raw = note_path.read_text(encoding="utf-8")
    frontmatter, note_body = parse_frontmatter(note_raw)

    repo_uri = frontmatter.get("repo")
    cache_root = repo_root / ".cache"
    target_repo_path = resolve_repository(repo_uri, proj_name, cache_root)

    output_blocks = [
        "### 1. 프로젝트 프로파일 및 아키텍처 뼈대 (README, Tech Stack, Tree, Commits)\n",
    ]

    if target_repo_path and target_repo_path.exists():
        tech_stacks = extract_tech_stack(target_repo_path)
        readme_content = extract_readme(target_repo_path, max_lines=100)
        tree_content = generate_directory_tree(target_repo_path, max_depth=2)
        commit_logs = extract_git_commits(target_repo_path, max_count=10)

        output_blocks.append(f"- **연결된 레포지토리:** `{repo_uri}` (로컬 경로: `{target_repo_path}`)")
        output_blocks.append(f"- **식별된 기술 스택:** {', '.join(tech_stacks)}")
        if frontmatter.get("topic"):
            output_blocks.append(f"- **메모 토픽:** {frontmatter.get('topic')}")
        if frontmatter.get("tags"):
            output_blocks.append(f"- **태그:** {frontmatter.get('tags')}")

        output_blocks.append(f"\n#### [README 요약]\n```markdown\n{readme_content}\n```\n")
        output_blocks.append(f"#### [디렉토리 뼈대 맵 (2-Depth)]\n```text\n{tree_content}\n```\n")
        output_blocks.append(f"#### [최근 Git 커밋 로그]\n```text\n{chr(10).join(commit_logs)}\n```\n")
    else:
        output_blocks.append("> [!NOTE]")
        output_blocks.append("> 연결된 원격/로컬 레포지토리가 없거나 접근할 수 없어 순수 작성자 메모 기반 모드로 동작합니다.\n")
        if frontmatter.get("topic"):
            output_blocks.append(f"- **메모 토픽:** {frontmatter.get('topic')}")
        if frontmatter.get("tags"):
            output_blocks.append(f"- **태그:** {frontmatter.get('tags')}\n")

    output_blocks.append("\n### 2. 작성자 사견 및 설계 회고 메모 원본\n")
    output_blocks.append(note_body)
    output_blocks.append("\n\n### 3. 사견 매핑 핵심 소스코드 스니펫\n")

    if target_repo_path and target_repo_path.exists():
        keywords = extract_keywords_from_note(note_raw)
        snippets = find_and_slice_code_snippets(
            target_repo_path,
            keywords,
            max_files=8,
            max_lines_per_file=300,
        )

        if snippets:
            for snip in snippets:
                output_blocks.append(f"#### `{snip['path']}` ({snip['info']})")
                output_blocks.append(f"```{snip['lang']}\n{snip['code']}\n```\n")
        else:
            output_blocks.append("(사견 메모의 키워드와 직접 매핑되는 소스코드가 없습니다.)\n")
    else:
        output_blocks.append("(레포지토리가 연결되지 않아 소스코드 스니펫을 추출하지 않았습니다.)\n")

    return "\n".join(output_blocks)


def main():
    if len(sys.argv) < 2:
        print("사용법:")
        print("  1. python pipeline/analyze_project.py <project_name> <note_file>")
        print("  2. python pipeline/analyze_project.py <note_file_path>")
        print("예시: python pipeline/analyze_project.py devlog-agent-pipeline 01_architecture_and_tradeoffs.md")
        sys.exit(1)

    repo_root = Path(__file__).resolve().parent.parent
    if len(sys.argv) == 2:
        context_text = analyze_project_context(repo_root, sys.argv[1])
    else:
        context_text = analyze_project_context(repo_root, sys.argv[1], sys.argv[2])

    print(context_text)


if __name__ == "__main__":
    main()

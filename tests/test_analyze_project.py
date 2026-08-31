import tempfile
import unittest
from pathlib import Path

from pipeline.analyze_project import (
    analyze_project_context,
    collect_target_source_files,
    extract_keywords_from_note,
    extract_tech_stack,
    find_and_slice_code_snippets,
    generate_directory_tree,
    is_excluded_dir,
    parse_frontmatter,
    resolve_repository,
)


class TestAnalyzeProject(unittest.TestCase):
    def test_parse_frontmatter_valid(self):
        content = """---
repo: "https://github.com/test/repo"
topic: "아키텍처 분석"
tags: ["Security", "FastAPI"]
---

# 프로젝트 메모 본문
"""
        fm, body = parse_frontmatter(content)
        self.assertEqual(fm.get("repo"), "https://github.com/test/repo")
        self.assertEqual(fm.get("topic"), "아키텍처 분석")
        self.assertEqual(fm.get("tags"), ["Security", "FastAPI"])
        self.assertIn("# 프로젝트 메모 본문", body)

    def test_parse_frontmatter_graceful_fallback(self):
        # Frontmatter가 없는 순수 마크다운
        content_no_fm = "# 순수 마크다운 본문\n내용입니다."
        fm, body = parse_frontmatter(content_no_fm)
        self.assertEqual(fm, {})
        self.assertEqual(body, content_no_fm)

        # 빈 repo 필드
        content_empty_repo = """---
repo: ""
topic: "단독 메모"
---
# 본문
"""
        fm, body = parse_frontmatter(content_empty_repo)
        self.assertEqual(fm.get("repo"), "")
        self.assertEqual(fm.get("topic"), "단독 메모")

        # UTF-8 BOM 포함 마크다운
        content_bom = "\ufeff---\nrepo: 'https://github.com/test/repo'\ntopic: 'BOM 테스트'\n---\n# 본문"
        fm_bom, body_bom = parse_frontmatter(content_bom)
        self.assertEqual(fm_bom.get("topic"), "BOM 테스트")
        self.assertEqual(body_bom, "# 본문")

    def test_is_excluded_dir(self):
        self.assertTrue(is_excluded_dir(".git"))
        self.assertTrue(is_excluded_dir("node_modules"))
        self.assertTrue(is_excluded_dir(".venv"))
        self.assertTrue(is_excluded_dir("__pycache__"))
        self.assertTrue(is_excluded_dir("my_pkg.egg-info"))
        self.assertFalse(is_excluded_dir("src"))
        self.assertFalse(is_excluded_dir("pipeline"))

    def test_resolve_repository_local(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            resolved = resolve_repository(str(tmp_path), "test_proj", tmp_path / ".cache")
            self.assertIsNotNone(resolved)
            self.assertEqual(resolved, tmp_path)

        # 존재하지 않는 경로
        resolved_none = resolve_repository("C:/invalid/non_existent_path_12345", "test_proj", Path(".cache"))
        self.assertIsNone(resolved_none)

        # 빈 문자열
        self.assertIsNone(resolve_repository("", "test_proj", Path(".cache")))
        self.assertIsNone(resolve_repository(None, "test_proj", Path(".cache")))

    def test_extract_tech_stack_and_tree(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            (repo_path / "pyproject.toml").write_text("[project]\ndependencies=['fastapi']\n", encoding="utf-8")
            (repo_path / "Dockerfile").write_text("FROM python:3.10", encoding="utf-8")
            (repo_path / "README.md").write_text("# Test Repo\nREADME 본문 내용입니다.", encoding="utf-8")

            # 배제 대상 디렉토리 및 파일 생성
            (repo_path / ".git").mkdir()
            (repo_path / ".git" / "config").write_text("git config", encoding="utf-8")
            (repo_path / "node_modules").mkdir()
            (repo_path / "node_modules" / "dummy.js").write_text("dummy", encoding="utf-8")
            (repo_path / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n")

            # 유효 디렉토리 및 파일
            src_dir = repo_path / "src"
            src_dir.mkdir()
            (src_dir / "main.py").write_text("print('hello')", encoding="utf-8")

            tech = extract_tech_stack(repo_path)
            self.assertTrue(any("Python" in t for t in tech))
            self.assertIn("FastAPI", tech)
            self.assertIn("Docker", tech)

            tree = generate_directory_tree(repo_path, max_depth=2)
            self.assertIn("src/", tree)
            self.assertIn("main.py", tree)
            self.assertNotIn(".git", tree)
            self.assertNotIn("node_modules", tree)
            self.assertNotIn("image.png", tree)

            valid_sources = collect_target_source_files(repo_path)
            self.assertEqual(len(valid_sources), 3)  # pyproject.toml, Dockerfile, main.py

    def test_token_budget_and_file_limit(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)

            # 10개의 파이썬 파일 생성 (350줄짜리 1개 포함)
            for i in range(10):
                file_lines = [f"# Line {j}" for j in range(350 if i == 0 else 50)]
                (repo_path / f"module_{i}.py").write_text("\n".join(file_lines), encoding="utf-8")

            keywords = ["module"]
            snippets = find_and_slice_code_snippets(
                repo_path,
                keywords,
                max_files=8,
                max_lines_per_file=300,
            )

            # 최대 8개 파일 선별 검증
            self.assertLessEqual(len(snippets), 8)

            # 파일당 300줄 슬라이싱 제한 검증
            for snip in snippets:
                lines = snip["code"].splitlines()
                self.assertLessEqual(len(lines), 300)

    def test_extract_keywords_from_note(self):
        note = """
## 4. 인제스터 탐색 힌트 (Key Modules & Functions)
- **핵심 파일:** `src/core/scanner.py`, `workers/task_queue.py`
- **주요 함수/클래스:** `AsyncVulnerabilityScanner`, `@app.task`, `handle_packet_stream`
def test_handler():
    pass
"""
        keywords = extract_keywords_from_note(note)
        self.assertIn("src/core/scanner.py", keywords)
        self.assertIn("scanner.py", keywords)
        self.assertIn("AsyncVulnerabilityScanner", keywords)
        self.assertIn("@app.task", keywords)
        self.assertIn("handle_packet_stream", keywords)
        self.assertIn("test_handler", keywords)

    def test_analyze_project_context_3_sections(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)
            proj_dir = root_path / "projects" / "sample-proj"
            proj_dir.mkdir(parents=True)

            note_file = proj_dir / "01_test_note.md"
            note_file.write_text("""---
repo: ""
topic: "순수 메모 테스트"
---
# 프로젝트 개요
순수 텍스트 메모입니다.
""", encoding="utf-8")

            result = analyze_project_context(root_path, "sample-proj", "01_test_note.md")
            self.assertIn("### 1. 프로젝트 프로파일 및 아키텍처 뼈대", result)
            self.assertIn("### 2. 작성자 사견 및 설계 회고 메모 원본", result)
            self.assertIn("### 3. 사견 매핑 핵심 소스코드 스니펫", result)
            self.assertIn("순수 텍스트 메모입니다.", result)

            # 단일 경로 인자 형태 테스트
            result_single = analyze_project_context(root_path, "projects/sample-proj/01_test_note.md")
            self.assertIn("### 1. 프로젝트 프로파일 및 아키텍처 뼈대", result_single)
            self.assertIn("순수 텍스트 메모입니다.", result_single)


if __name__ == "__main__":
    unittest.main()

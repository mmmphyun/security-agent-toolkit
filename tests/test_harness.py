import unittest
from pathlib import Path

from pipeline.harness import (
    check_ai_cliches,
    check_emojis,
    check_mermaid,
    check_required_sections,
    clean_markdown_fences,
    scan_pending_targets,
)


class TestPipelineHarness(unittest.TestCase):
    def test_clean_markdown_fences(self):
        # 래퍼 제거 및 끝단 코드블록 보존 검증
        wrapped_text = "```markdown\n## 1. 개요\n```python\nprint('hello')\n```\n```"
        cleaned = clean_markdown_fences(wrapped_text)
        self.assertTrue(cleaned.startswith("## 1. 개요"))
        self.assertTrue(cleaned.endswith("```"))
        self.assertIn("```python\nprint('hello')\n```", cleaned)

    def test_emoji_detection(self):
        self.assertEqual(len(check_emojis("정상적인 기술 문서 본문")), 0)
        self.assertGreater(len(check_emojis("이모지 포함 🚀")), 0)

    def test_required_sections(self):
        sample_doc = """
## 1. 학습 개념 요약
## 2. 기본 구현의 한계점
## 3. 엔지니어링 의사결정 및 리팩터링
## 4. 검증 및 회고
"""
        self.assertEqual(len(check_required_sections(sample_doc)), 0)

    def test_mermaid_check(self):
        self.assertEqual(len(check_mermaid("```mermaid\ngraph TD;\nA-->B;\n```")), 0)
        self.assertGreater(len(check_mermaid("다이어그램 없음")), 0)

    def test_ai_cliches(self):
        self.assertEqual(len(check_ai_cliches("담백한 기술 문서")), 0)
        self.assertGreater(len(check_ai_cliches("지금부터 자세히 살펴보겠습니다")), 0)
        self.assertGreater(len(check_ai_cliches("수강생 구현과 AI 페어 프로그래밍")), 0)
        self.assertGreater(len(check_ai_cliches("학습자 여러분을 위한 모범 답안")), 0)

    def test_scan_pending_targets(self):
        repo_root = Path(__file__).resolve().parent.parent
        pending = scan_pending_targets(repo_root)
        self.assertIsInstance(pending, list)
        # 이미 작성된 day01~day05는 제외되어야 함
        self.assertFalse(any(item["target_slug"] == "c01-agent-core-day01" for item in pending))
        # 반환된 항목의 구조 유효성 검증
        for item in pending:
            self.assertIn("type", item)
            self.assertIn("target_slug", item)
            self.assertIn("expected_file", item)



if __name__ == "__main__":
    unittest.main()

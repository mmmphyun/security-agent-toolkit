"""
pipeline.context_loader

커리큘럼 허브에서 과목/일차별 메인 목표 및 세부 교시(Sub-lessons) 실습 명세를
실시간으로 인제스트하여 에이전트에게 제공하는 컨텍스트 로더 모듈.
"""

import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv

# 프로젝트 루트의 .env 로드
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)

CURRICULUM_HUB_PAGE_ID = os.getenv("CURRICULUM_HUB_PAGE_ID") or os.getenv("NOTION_HUB_PAGE_ID") or ""
NOTION_API_URL = "https://www.notion.so/api/v3/loadPageChunk"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


def load_notion_blocks(page_id: str) -> dict:
    """원격 엔드포인트를 호출하여 해당 페이지의 블록 딕셔너리 반환"""
    if not page_id:
        return {}
    clean_id = page_id.replace("-", "")
    formatted_id = (
        f"{clean_id[:8]}-{clean_id[8:12]}-{clean_id[12:16]}-{clean_id[16:20]}-{clean_id[20:]}"
    )
    payload = {
        "page": {"id": formatted_id},
        "limit": 100,
        "cursor": {"stack": []},
        "chunkNumber": 0,
        "verticalColumns": False,
    }
    resp = requests.post(NOTION_API_URL, json=payload, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json().get("recordMap", {}).get("block", {})


def extract_block_text(val: dict) -> str:
    """단일 블록에서 텍스트 추출"""
    props = val.get("properties", {})
    title_chunks = props.get("title", [])
    text_parts = []
    for chunk in title_chunks:
        if isinstance(chunk, list) and len(chunk) > 0:
            text_parts.append(str(chunk[0]))
    return "".join(text_parts).strip()


def parse_page_content_blocks(page_id: str, blocks: dict) -> list[str]:
    """블록 딕셔너리를 마크다운 텍스트 라인 리스트로 변환"""
    lines = []
    for bid, binfo in blocks.items():
        if bid == page_id:
            continue
        val = binfo.get("value", {}).get("value", {})
        btype = val.get("type")
        text = extract_block_text(val)
        if not text:
            continue

        if btype == "header":
            lines.append(f"\n# {text}\n")
        elif btype == "sub_header":
            lines.append(f"\n## {text}\n")
        elif btype == "sub_sub_header":
            lines.append(f"\n### {text}\n")
        elif btype == "numbered_list":
            lines.append(f"1. {text}")
        elif btype == "bulleted_list":
            lines.append(f"- {text}")
        elif btype == "code":
            lines.append(f"```python\n{text}\n```")
        elif btype == "quote":
            lines.append(f"> {text}")
        elif btype == "toggle":
            lines.append(f"<details><summary>{text}</summary></details>")
        elif btype != "page":
            lines.append(text)
    return lines


def build_curriculum_catalog() -> dict:
    """메인 허브를 파싱하여 과목/일차별 페이지 ID 맵 구축"""
    if not CURRICULUM_HUB_PAGE_ID:
        return {}

    blocks = load_notion_blocks(CURRICULUM_HUB_PAGE_ID)
    catalog = {}
    current_course_id = None

    course_dir_hints = {
        "1과목": "agent_core",
        "2과목": "network_zt",
        "3과목": "access_control",
        "4과목": "anomaly_detection",
        "5과목": "soar_response",
    }

    for bid, binfo in blocks.items():
        val = binfo.get("value", {}).get("value", {})
        btype = val.get("type")
        text = extract_block_text(val)
        if not text:
            continue

        if btype in ("header", "sub_header"):
            for k, dir_name in course_dir_hints.items():
                if k in text:
                    current_course_id = dir_name
                    if current_course_id not in catalog:
                        catalog[current_course_id] = {
                            "course_name": text,
                            "days": {},
                        }
                    break

        elif btype == "page" and current_course_id:
            day_match = re.search(r"Day\s*(\d+)", text, re.IGNORECASE)
            if day_match:
                day_num = int(day_match.group(1))
                day_key = f"day{day_num:02d}"
                catalog[current_course_id]["days"][day_key] = {
                    "title": text,
                    "page_id": bid,
                }

    return catalog


def fetch_day_lecture_note(course_id: str, day_id: str, fetch_sub_lessons: bool = True) -> str:
    """특정 과목/일차의 커리큘럼 본문 및 세부 교시 명세를 재귀적으로 추출"""
    if not CURRICULUM_HUB_PAGE_ID:
        return "[알림] CURRICULUM_HUB_PAGE_ID 환경변수가 설정되지 않아 로컬 코드 컨텍스트만 사용합니다."

    catalog = build_curriculum_catalog()
    course_info = catalog.get(course_id)
    if not course_info:
        return f"[알림] 커리큘럼 허브에서 과목({course_id}) 정보를 찾을 수 없습니다."

    day_info = course_info.get("days", {}).get(day_id)
    if not day_info:
        return f"[알림] 커리큘럼 허브에서 {course_id} - {day_id} 일차를 찾을 수 없습니다."

    page_id = day_info["page_id"]
    page_title = day_info["title"]
    day_blocks = load_notion_blocks(page_id)

    output = [f"# [{course_info['course_name']}] {page_title}\n"]
    output.extend(parse_page_content_blocks(page_id, day_blocks))

    # 하위 세부 교시(1교시~6교시, 실습자료 등) 탐색 및 재귀 인제스트
    if fetch_sub_lessons:
        child_sub_pages = []
        for bid, binfo in day_blocks.items():
            if bid == page_id:
                continue
            val = binfo.get("value", {}).get("value", {})
            btype = val.get("type")
            title = extract_block_text(val)
            if btype == "page" and ("교시" in title or "실습" in title or "과제" in title):
                child_sub_pages.append((bid, title))

        if child_sub_pages:
            output.append("\n\n---\n## [세부 교시별 강의 본문 및 실습 명세]")
            for cid, ctitle in child_sub_pages:
                output.append(f"\n### {ctitle}\n")
                try:
                    sub_blocks = load_notion_blocks(cid)
                    sub_lines = parse_page_content_blocks(cid, sub_blocks)
                    output.extend(sub_lines)
                except Exception as e:  # noqa: BLE001
                    output.append(f"(세부 교시 내용 로드 실패: {e})")

    return "\n".join(output)


if __name__ == "__main__":
    import sys
    c_id = sys.argv[1] if len(sys.argv) > 1 else "agent_core"
    d_id = sys.argv[2] if len(sys.argv) > 2 else "day06"
    print(f"=== 커리큘럼 컨텍스트 인제스트: {c_id} / {d_id} ===")
    note = fetch_day_lecture_note(c_id, d_id, fetch_sub_lessons=True)
    print(f"총 추출된 글자 수: {len(note):,}자")
    print(note[:1500])

"""
notifier.py - 분석 결과 전송/저장
Slack 웹훅, Notion 페이지, 파일 저장 담당
"""
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

import config
from formatter import format_telegram, format_blog, format_slack, format_notion_blocks


class NotificationResult:
    """알림 전송 결과 추적"""

    def __init__(self):
        self.results: Dict[str, Dict] = {}

    def add(self, channel: str, success: bool, detail: str = ""):
        self.results[channel] = {"success": success, "detail": detail}
        status = "OK" if success else "FAIL"
        print(f"[Notifier] {channel}: {status} {detail}")

    def summary(self) -> str:
        total = len(self.results)
        ok = sum(1 for r in self.results.values() if r["success"])
        return f"{ok}/{total} 채널 전송 성공"


def save_to_files(
    result: Dict[str, Any],
    output_dir: str = None,
    date_str: str = None,
) -> Dict[str, str]:
    """
    텔레그램/블로그/JSON 결과를 파일로 저장

    Returns:
        저장된 파일 경로 딕셔너리
    """
    kst = timezone(timedelta(hours=9))
    if not date_str:
        date_str = datetime.now(kst).strftime("%Y년 %m월 %d일")
    file_date = datetime.now(kst).strftime("%Y%m%d")

    output_path = Path(output_dir or config.OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)

    saved = {}

    # 텔레그램 포맷
    telegram_text = format_telegram(result, date_str)
    telegram_file = output_path / f"{file_date}_telegram.txt"
    telegram_file.write_text(telegram_text, encoding="utf-8")
    saved["telegram"] = str(telegram_file)
    print(f"[Notifier] 텔레그램 파일 저장: {telegram_file}")

    # 블로그 포맷
    blog_text = format_blog(result, date_str)
    blog_file = output_path / f"{file_date}_blog.txt"
    blog_file.write_text(blog_text, encoding="utf-8")
    saved["blog"] = str(blog_file)
    print(f"[Notifier] 블로그 파일 저장: {blog_file}")

    # JSON 원본
    if config.SAVE_JSON_RESULT:
        json_file = output_path / f"{file_date}_result.json"
        json_file.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        saved["json"] = str(json_file)
        print(f"[Notifier] JSON 저장: {json_file}")

    return saved


def send_to_slack(
    result: Dict[str, Any],
    date_str: str = None,
    webhook_url: str = None,
) -> bool:
    """Slack 웹훅으로 브리핑 전송"""
    webhook_url = webhook_url or config.SLACK_WEBHOOK_URL
    if not webhook_url:
        print("[Notifier] Slack: SLACK_WEBHOOK_URL 미설정, 건너뜀")
        return False

    try:
        import requests
    except ImportError:
        print("[Notifier] Slack: requests 미설치 (pip install requests)")
        return False

    payload = format_slack(result, date_str)

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"},
        )
        if response.status_code == 200:
            print("[Notifier] Slack 전송 완료")
            return True
        else:
            print(f"[Notifier] Slack 오류: HTTP {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"[Notifier] Slack 전송 실패: {e}")
        return False


def create_notion_page(
    result: Dict[str, Any],
    date_str: str = None,
    notion_token: str = None,
    parent_page_id: str = None,
) -> Optional[str]:
    """
    Notion에 새 페이지 생성하고 페이지 URL 반환

    Args:
        result: 분석 결과
        date_str: 날짜 문자열
        notion_token: Notion integration 토큰
        parent_page_id: 부모 페이지 ID

    Returns:
        생성된 Notion 페이지 URL (실패 시 None)
    """
    notion_token = notion_token or config.NOTION_TOKEN
    parent_page_id = parent_page_id or config.NOTION_PAGE_ID

    if not notion_token:
        print("[Notifier] Notion: NOTION_TOKEN 미설정, 건너뜀")
        return None
    if not parent_page_id:
        print("[Notifier] Notion: NOTION_PAGE_ID 미설정, 건너뜀")
        return None

    try:
        import requests
    except ImportError:
        print("[Notifier] Notion: requests 미설치 (pip install requests)")
        return None

    kst = timezone(timedelta(hours=9))
    if not date_str:
        date_str = datetime.now(kst).strftime("%Y년 %m월 %d일")

    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    # 페이지 블록 내용
    children = format_notion_blocks(result, date_str)

    # 최대 100개 블록 (Notion API 제한)
    children = children[:100]

    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "icon": {"type": "emoji", "emoji": "📊"},
        "properties": {
            "title": {
                "title": [
                    {"type": "text", "text": {"content": f"일일 브리핑 | {date_str}"}}
                ]
            }
        },
        "children": children,
    }

    try:
        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=payload,
            timeout=30,
        )

        if response.status_code == 200:
            page_data = response.json()
            page_id = page_data.get("id", "").replace("-", "")
            page_url = page_data.get("url", f"https://www.notion.so/{page_id}")
            print(f"[Notifier] Notion 페이지 생성 완료: {page_url}")
            return page_url
        else:
            error_body = response.text[:300]
            print(f"[Notifier] Notion 오류: HTTP {response.status_code} - {error_body}")
            return None

    except Exception as e:
        print(f"[Notifier] Notion 페이지 생성 실패: {e}")
        return None


def notify_all(
    result: Dict[str, Any],
    date_str: str = None,
    output_dir: str = None,
) -> NotificationResult:
    """
    모든 채널에 결과 전송/저장

    Returns:
        NotificationResult 객체
    """
    kst = timezone(timedelta(hours=9))
    if not date_str:
        date_str = datetime.now(kst).strftime("%Y년 %m월 %d일")

    nr = NotificationResult()

    # 1. 파일 저장 (항상 실행)
    try:
        saved = save_to_files(result, output_dir, date_str)
        nr.add("file", True, f"→ {', '.join(saved.values())}")
    except Exception as e:
        nr.add("file", False, str(e))

    # 2. Slack
    if config.SLACK_WEBHOOK_URL:
        ok = send_to_slack(result, date_str)
        nr.add("slack", ok)
    else:
        print("[Notifier] Slack: 미설정, 건너뜀")

    # 3. Notion
    if config.NOTION_TOKEN and config.NOTION_PAGE_ID:
        page_url = create_notion_page(result, date_str)
        nr.add("notion", page_url is not None, page_url or "")
    else:
        print("[Notifier] Notion: 미설정, 건너뜀")

    return nr

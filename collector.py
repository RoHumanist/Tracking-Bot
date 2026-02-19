"""
collector.py - 텔레그램 메시지 수집기
Telethon 라이브러리로 지정 채널에서 메시지 수집
"""
import asyncio
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Optional

import config


def parse_manual_messages(text: str) -> List[Dict]:
    """
    수동으로 붙여넣은 텍스트를 메시지 리스트로 파싱

    지원 형식:
    1. [채널: name] timestamp | 내용
    2. 날짜/시간 줄 이후 내용 (텔레그램 앱 복사 형식)
    3. 일반 텍스트 (채널 구분 없음)
    """
    messages = []
    lines = text.strip().split("\n")

    # 형식 1: [채널: name] 패턴
    channel_pattern = re.compile(r"^\[채널:\s*(.+?)\]\s*(.+?)?\|\s*(.+)$")
    # 형식 2: 날짜 패턴 (YYYY-MM-DD HH:MM)
    datetime_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})")

    current_channel = "manual_input"
    current_date = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")
    buffer = []

    for line in lines:
        line = line.strip()
        if not line:
            if buffer:
                messages.append({
                    "channel": current_channel,
                    "date": current_date,
                    "text": " ".join(buffer),
                    "message_id": len(messages) + 1,
                })
                buffer = []
            continue

        m = channel_pattern.match(line)
        if m:
            if buffer:
                messages.append({
                    "channel": current_channel,
                    "date": current_date,
                    "text": " ".join(buffer),
                    "message_id": len(messages) + 1,
                })
                buffer = []
            current_channel = m.group(1).strip()
            current_date = m.group(2).strip() if m.group(2) else current_date
            text = m.group(3).strip()
            if text:
                messages.append({
                    "channel": current_channel,
                    "date": current_date,
                    "text": text,
                    "message_id": len(messages) + 1,
                })
        else:
            buffer.append(line)

    # 남은 버퍼 처리
    if buffer:
        messages.append({
            "channel": current_channel,
            "date": current_date,
            "text": " ".join(buffer),
            "message_id": len(messages) + 1,
        })

    return [m for m in messages if m["text"].strip()]


def load_messages_from_file(file_path: str) -> List[Dict]:
    """파일에서 메시지 로드"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    text = path.read_text(encoding="utf-8")
    messages = parse_manual_messages(text)
    print(f"[Collector] 파일에서 {len(messages)}개 메시지 로드: {file_path}")
    return messages


def load_messages_from_stdin() -> List[Dict]:
    """표준 입력에서 메시지 로드"""
    print("[Collector] 메시지를 붙여넣고 Enter 두 번 + Ctrl+D:")
    try:
        text = sys.stdin.read()
    except KeyboardInterrupt:
        return []

    messages = parse_manual_messages(text)
    print(f"[Collector] {len(messages)}개 메시지 파싱 완료")
    return messages


def get_demo_messages() -> List[Dict]:
    """데모용 샘플 메시지 반환"""
    return parse_manual_messages(config.DEMO_MESSAGES)


async def collect_telegram_messages(
    channels: Optional[List[str]] = None,
    hours_back: int = None,
) -> List[Dict]:
    """
    Telethon으로 텔레그램 채널 메시지 수집

    Args:
        channels: 수집할 채널 목록 (None이면 config 사용)
        hours_back: 몇 시간 전까지 수집 (None이면 config 사용)

    Returns:
        메시지 딕셔너리 리스트
    """
    try:
        from telethon import TelegramClient
        from telethon.tl.types import Message
    except ImportError:
        raise ImportError("Telethon 미설치. pip install telethon 실행 필요")

    if not config.TELEGRAM_API_ID or not config.TELEGRAM_API_HASH:
        raise ValueError("TELEGRAM_API_ID, TELEGRAM_API_HASH 환경변수 설정 필요")

    channels = channels or config.TELEGRAM_CHANNELS
    hours_back = hours_back or config.TELEGRAM_HOURS_BACK

    if not channels:
        raise ValueError("수집할 채널이 지정되지 않았습니다. TELEGRAM_CHANNELS 설정 필요")

    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    all_messages = []

    async with TelegramClient(
        "tracking_bot_session",
        config.TELEGRAM_API_ID,
        config.TELEGRAM_API_HASH,
    ) as client:
        # 전화번호로 로그인 (최초 1회만 인증 필요)
        if config.TELEGRAM_PHONE:
            await client.start(phone=config.TELEGRAM_PHONE)
        else:
            await client.start()

        for channel in channels:
            try:
                print(f"[Collector] 수집 중: {channel}")
                entity = await client.get_entity(channel)
                channel_name = getattr(entity, "title", channel) or channel

                async for message in client.iter_messages(entity, limit=200):
                    if not isinstance(message, Message):
                        continue
                    if not message.text:
                        continue
                    if message.date < cutoff_time:
                        break

                    kst = timezone(timedelta(hours=9))
                    msg_date = message.date.astimezone(kst)

                    all_messages.append({
                        "channel": channel_name,
                        "date": msg_date.strftime("%Y-%m-%d %H:%M"),
                        "text": message.text.strip(),
                        "message_id": message.id,
                        "views": getattr(message, "views", 0),
                        "forwards": getattr(message, "forwards", 0),
                    })

                print(f"[Collector] {channel_name}: 메시지 수집 완료")
                await asyncio.sleep(1)  # rate limit 방지

            except Exception as e:
                print(f"[Collector] 경고 - {channel} 수집 실패: {e}")
                continue

    # 날짜 기준 정렬
    all_messages.sort(key=lambda x: x["date"])
    print(f"[Collector] 총 {len(all_messages)}개 메시지 수집 완료")
    return all_messages


def format_messages_for_analysis(messages: List[Dict]) -> str:
    """메시지 리스트를 분석용 텍스트로 변환"""
    lines = []
    for msg in messages:
        channel = msg.get("channel", "unknown")
        date = msg.get("date", "")
        text = msg.get("text", "").strip()
        if text:
            lines.append(f"[채널: {channel}] {date} | {text}")
    return "\n\n".join(lines)


def collect_messages(mode: str, file_path: Optional[str] = None) -> List[Dict]:
    """
    모드에 따라 메시지 수집 (동기 래퍼)

    Args:
        mode: 'auto', 'file', 'stdin', 'demo'
        file_path: mode='file'일 때 파일 경로
    """
    if mode == "demo":
        print("[Collector] 데모 모드: 샘플 메시지 사용")
        return get_demo_messages()

    elif mode == "file":
        if not file_path:
            raise ValueError("파일 경로를 지정해주세요 (--file 옵션)")
        return load_messages_from_file(file_path)

    elif mode == "stdin":
        return load_messages_from_stdin()

    elif mode == "auto":
        return asyncio.run(collect_telegram_messages())

    else:
        raise ValueError(f"지원하지 않는 모드: {mode}")

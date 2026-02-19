"""
formatter.py - 분석 결과를 다양한 포맷으로 변환
텔레그램, 블로그(네이버), Slack, Notion 블록 형식 지원
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

import config


def _get_sentiment_emoji(sentiment: str) -> str:
    return {"positive": "📈", "negative": "📉", "neutral": "➡️"}.get(sentiment, "➡️")


def _get_importance_emoji(importance: str) -> str:
    return {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(importance, "⚪")


def format_telegram(result: Dict[str, Any], date_str: str = None) -> str:
    """
    텔레그램 채널용 마크다운 포맷
    최대 4096자 제한 준수
    """
    kst = timezone(timedelta(hours=9))
    if not date_str:
        date_str = datetime.now(kst).strftime("%Y년 %m월 %d일")

    meta = result.get("_meta", {})
    sentiment = result.get("market_sentiment", "neutral")
    sentiment_emoji = _get_sentiment_emoji(sentiment)

    lines = []
    lines.append(f"📊 *일일 브리핑* | {date_str}")
    lines.append("")

    # 요약
    summary = result.get("summary", "")
    if summary:
        lines.append(f"_{summary}_")
        lines.append("")

    # 주요 주제
    topics = result.get("topics", [])
    if topics:
        lines.append("*📌 주요 이슈*")
        for topic in topics:
            imp_emoji = _get_importance_emoji(topic.get("importance", "low"))
            title = topic.get("title", "")
            content = topic.get("content", "")
            tags = topic.get("tags", [])
            tag_str = " ".join(f"#{t}" for t in tags[:3]) if tags else ""

            lines.append(f"\n{imp_emoji} *{title}*")
            lines.append(content)
            if tag_str:
                lines.append(tag_str)

    lines.append("")

    # 주요 수치
    numbers = result.get("key_numbers", [])
    if numbers:
        lines.append("*📊 주요 수치*")
        for num in numbers[:4]:
            label = num.get("label", "")
            value = num.get("value", "")
            context = num.get("context", "")
            lines.append(f"• {label}: *{value}* ({context})")
        lines.append("")

    # 시장 감성
    reason = result.get("sentiment_reason", "")
    lines.append(f"{sentiment_emoji} *시장 감성*: {sentiment.upper()}")
    if reason:
        lines.append(reason)
    lines.append("")

    # 키워드
    keywords = result.get("top_keywords", [])
    if keywords:
        kw_str = " · ".join(keywords[:5])
        lines.append(f"🔑 *키워드*: {kw_str}")
        lines.append("")

    # 액션 아이템
    actions = result.get("action_items", [])
    if actions:
        lines.append("✅ *주목 포인트*")
        for action in actions[:3]:
            lines.append(f"• {action}")
        lines.append("")

    # 푸터
    msg_count = meta.get("message_count", 0)
    channel_count = meta.get("channel_count", 0)
    lines.append(f"_채널 {channel_count}개, 메시지 {msg_count}건 분석 | Tracking Bot_")

    text = "\n".join(lines)

    # 4096자 초과 시 자르기
    if len(text) > config.TELEGRAM_MAX_LENGTH:
        text = text[:config.TELEGRAM_MAX_LENGTH - 20] + "\n\n_(내용 생략)_"

    return text


def format_blog(result: Dict[str, Any], date_str: str = None) -> str:
    """
    네이버 블로그용 텍스트 포맷 (HTML 없이 순수 텍스트)
    """
    kst = timezone(timedelta(hours=9))
    if not date_str:
        date_str = datetime.now(kst).strftime("%Y년 %m월 %d일")

    meta = result.get("_meta", {})
    sentiment = result.get("market_sentiment", "neutral")
    keywords = result.get("top_keywords", [])
    tag_str = ", ".join(keywords[:5]) if keywords else "AI, 테크, 트렌드"

    lines = []

    # 블로그 헤더
    lines.append(config.BLOG_HEADER_TEMPLATE.format(
        date=date_str,
        tags=tag_str,
    ).strip())
    lines.append("")
    lines.append("=" * 50)
    lines.append(f"  {date_str} 일일 정보 브리핑")
    lines.append("=" * 50)
    lines.append("")

    # 요약
    summary = result.get("summary", "")
    if summary:
        lines.append("[ 오늘의 요약 ]")
        lines.append("")
        lines.append(summary)
        lines.append("")

    # 시장 감성
    sentiment_label = {"positive": "긍정적", "negative": "부정적", "neutral": "중립적"}.get(
        sentiment, "중립적"
    )
    reason = result.get("sentiment_reason", "")
    lines.append(f"▶ 오늘의 시장 분위기: {sentiment_label}")
    if reason:
        lines.append(f"  {reason}")
    lines.append("")

    # 주요 이슈
    topics = result.get("topics", [])
    if topics:
        lines.append("[ 주요 이슈 ]")
        lines.append("")
        for i, topic in enumerate(topics, 1):
            title = topic.get("title", "")
            content = topic.get("content", "")
            importance = topic.get("importance", "low")
            tags = topic.get("tags", [])
            sources = topic.get("sources", [])

            imp_label = {"high": "★★★", "medium": "★★☆", "low": "★☆☆"}.get(importance, "★☆☆")

            lines.append(f"{i}. {title}  {imp_label}")
            lines.append("-" * 40)
            lines.append(content)
            if sources:
                lines.append(f"  출처: {', '.join(sources)}")
            if tags:
                lines.append(f"  태그: {' '.join(f'#{t}' for t in tags)}")
            lines.append("")

    # 주요 수치
    numbers = result.get("key_numbers", [])
    if numbers:
        lines.append("[ 주요 수치 ]")
        lines.append("")
        for num in numbers:
            label = num.get("label", "")
            value = num.get("value", "")
            context = num.get("context", "")
            lines.append(f"  • {label}: {value}")
            if context:
                lines.append(f"    → {context}")
        lines.append("")

    # 주목 포인트
    actions = result.get("action_items", [])
    if actions:
        lines.append("[ 주목 포인트 ]")
        lines.append("")
        for action in actions:
            lines.append(f"  ▷ {action}")
        lines.append("")

    # 키워드
    if keywords:
        lines.append("[ 오늘의 키워드 ]")
        lines.append("")
        lines.append("  " + "  |  ".join(keywords[:5]))
        lines.append("")

    # 푸터
    msg_count = meta.get("message_count", 0)
    channel_count = meta.get("channel_count", 0)
    lines.append("=" * 50)
    lines.append(f"채널 {channel_count}개, 메시지 {msg_count}건 분석")
    lines.append("자동 생성 | Tracking Bot")
    lines.append("=" * 50)

    return "\n".join(lines)


def format_slack(result: Dict[str, Any], date_str: str = None) -> Dict[str, Any]:
    """
    Slack Block Kit 포맷 반환
    """
    kst = timezone(timedelta(hours=9))
    if not date_str:
        date_str = datetime.now(kst).strftime("%Y년 %m월 %d일")

    meta = result.get("_meta", {})
    sentiment = result.get("market_sentiment", "neutral")
    sentiment_emoji = _get_sentiment_emoji(sentiment)
    summary = result.get("summary", "")
    topics = result.get("topics", [])
    keywords = result.get("top_keywords", [])

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📊 일일 브리핑 | {date_str}",
                "emoji": True,
            },
        },
        {"type": "divider"},
    ]

    if summary:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*요약*\n{summary}"},
        })
        blocks.append({"type": "divider"})

    if topics:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*📌 주요 이슈*"},
        })
        for topic in topics[:4]:
            imp_emoji = _get_importance_emoji(topic.get("importance", "low"))
            title = topic.get("title", "")
            content = topic.get("content", "")
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{imp_emoji} *{title}*\n{content}",
                },
            })

    blocks.append({"type": "divider"})

    # 통계 필드
    fields = [
        {"type": "mrkdwn", "text": f"*시장 감성*\n{sentiment_emoji} {sentiment.upper()}"},
        {"type": "mrkdwn", "text": f"*분석 메시지*\n{meta.get('message_count', 0)}건"},
    ]
    if keywords:
        fields.append({
            "type": "mrkdwn",
            "text": f"*키워드*\n{', '.join(keywords[:3])}",
        })

    blocks.append({"type": "section", "fields": fields})

    return {
        "username": "Tracking Bot",
        "icon_emoji": ":bar_chart:",
        "channel": config.SLACK_CHANNEL,
        "blocks": blocks,
        "text": f"일일 브리핑 | {date_str}",  # 알림 fallback 텍스트
    }


def format_notion_blocks(result: Dict[str, Any], date_str: str = None) -> List[Dict]:
    """
    Notion API Block 객체 리스트 반환
    """
    kst = timezone(timedelta(hours=9))
    if not date_str:
        date_str = datetime.now(kst).strftime("%Y년 %m월 %d일")

    meta = result.get("_meta", {})
    summary = result.get("summary", "")
    topics = result.get("topics", [])
    numbers = result.get("key_numbers", [])
    actions = result.get("action_items", [])
    keywords = result.get("top_keywords", [])
    sentiment = result.get("market_sentiment", "neutral")
    sentiment_emoji = _get_sentiment_emoji(sentiment)

    def heading(text: str, level: int = 2) -> Dict:
        return {
            "object": "block",
            "type": f"heading_{level}",
            f"heading_{level}": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            },
        }

    def paragraph(text: str) -> Dict:
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            },
        }

    def bullet(text: str) -> Dict:
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            },
        }

    def divider() -> Dict:
        return {"object": "block", "type": "divider", "divider": {}}

    def callout(text: str, emoji: str = "📌") -> Dict:
        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": text}}],
                "icon": {"type": "emoji", "emoji": emoji},
            },
        }

    blocks = []

    # 요약
    if summary:
        blocks.append(callout(summary, "💡"))
        blocks.append(divider())

    # 시장 감성
    reason = result.get("sentiment_reason", "")
    sentiment_text = f"시장 감성: {sentiment.upper()}"
    if reason:
        sentiment_text += f"\n{reason}"
    blocks.append(callout(sentiment_text, sentiment_emoji))
    blocks.append(divider())

    # 주요 이슈
    if topics:
        blocks.append(heading("📌 주요 이슈", 2))
        for topic in topics:
            title = topic.get("title", "")
            content = topic.get("content", "")
            importance = topic.get("importance", "low")
            tags = topic.get("tags", [])
            sources = topic.get("sources", [])
            imp_emoji = _get_importance_emoji(importance)

            blocks.append(heading(f"{imp_emoji} {title}", 3))
            blocks.append(paragraph(content))
            if sources:
                blocks.append(paragraph(f"출처: {', '.join(sources)}"))
            if tags:
                blocks.append(paragraph(f"태그: {' '.join(f'#{t}' for t in tags)}"))
        blocks.append(divider())

    # 주요 수치
    if numbers:
        blocks.append(heading("📊 주요 수치", 2))
        for num in numbers:
            label = num.get("label", "")
            value = num.get("value", "")
            context = num.get("context", "")
            blocks.append(bullet(f"{label}: {value} ({context})"))
        blocks.append(divider())

    # 액션 아이템
    if actions:
        blocks.append(heading("✅ 주목 포인트", 2))
        for action in actions:
            blocks.append(bullet(action))
        blocks.append(divider())

    # 키워드
    if keywords:
        blocks.append(heading("🔑 키워드", 2))
        blocks.append(paragraph(" · ".join(keywords)))
        blocks.append(divider())

    # 메타 정보
    msg_count = meta.get("message_count", 0)
    channel_count = meta.get("channel_count", 0)
    analyzed_at = meta.get("analyzed_at", "")
    blocks.append(
        paragraph(
            f"채널 {channel_count}개, 메시지 {msg_count}건 분석 | {analyzed_at} | Tracking Bot"
        )
    )

    return blocks

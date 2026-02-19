"""
config.py - 모든 설정과 프롬프트 관리
환경변수 또는 직접 수정으로 설정
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional

# ────────────────────────────────────────────
# API Keys & Tokens (환경변수 우선, 없으면 직접 입력)
# ────────────────────────────────────────────

# Anthropic Claude API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Telegram API (my.telegram.org에서 발급)
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0") or "0")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE", "")  # +821012345678 형식

# 수집할 텔레그램 채널/그룹 목록 (username 또는 chat_id)
TELEGRAM_CHANNELS: List[str] = [
    ch.strip()
    for ch in os.getenv("TELEGRAM_CHANNELS", "").split(",")
    if ch.strip()
] or [
    # 기본값 예시 - 실제 채널로 교체
    # "channel_username",
    # "-1001234567890",
]

# 수집 시간 범위 (시간 단위, 기본 24시간)
TELEGRAM_HOURS_BACK = int(os.getenv("TELEGRAM_HOURS_BACK", "24"))

# Slack
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#daily-briefing")

# Notion
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID", "")  # 부모 페이지 ID

# ────────────────────────────────────────────
# Claude 모델 설정
# ────────────────────────────────────────────

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4-5")
CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "4096"))
CLAUDE_TEMPERATURE = float(os.getenv("CLAUDE_TEMPERATURE", "0.3"))

# ────────────────────────────────────────────
# 출력 파일 설정
# ────────────────────────────────────────────

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")
SAVE_RAW_MESSAGES = os.getenv("SAVE_RAW_MESSAGES", "true").lower() == "true"
SAVE_JSON_RESULT = os.getenv("SAVE_JSON_RESULT", "true").lower() == "true"

# ────────────────────────────────────────────
# 분석 프롬프트 설정
# ────────────────────────────────────────────

SYSTEM_PROMPT = """당신은 텔레그램 채널 메시지를 분석하여 핵심 인사이트를 추출하는 전문 분석가입니다.

역할:
- 다양한 채널의 메시지를 종합하여 오늘의 주요 트렌드와 이슈를 파악합니다
- 중복 내용은 제거하고 가장 중요한 정보만 선별합니다
- 한국 독자를 위해 맥락을 충분히 설명합니다
- 사실과 의견을 명확히 구분합니다

출력 원칙:
- 간결하고 명확하게 작성합니다
- 전문 용어는 괄호 안에 설명을 덧붙입니다
- 중요도 순서로 정렬합니다
"""

ANALYSIS_PROMPT_TEMPLATE = """다음은 오늘 수집된 텔레그램 채널 메시지들입니다.

수집 일시: {date}
채널 수: {channel_count}
메시지 수: {message_count}

=== 메시지 내용 ===
{messages}
===================

위 메시지들을 분석하여 다음 형식의 JSON으로 응답해주세요:

{{
  "summary": "전체 내용을 2-3문장으로 요약",
  "topics": [
    {{
      "title": "주제명",
      "importance": "high/medium/low",
      "content": "상세 내용 (2-4문장)",
      "sources": ["채널명1", "채널명2"],
      "tags": ["태그1", "태그2"]
    }}
  ],
  "key_numbers": [
    {{
      "label": "수치 레이블",
      "value": "수치값",
      "context": "맥락 설명"
    }}
  ],
  "action_items": ["주목할 액션 아이템1", "아이템2"],
  "market_sentiment": "positive/neutral/negative",
  "sentiment_reason": "감성 판단 이유",
  "top_keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"]
}}

JSON만 응답하세요. 다른 텍스트는 포함하지 마세요."""

# ────────────────────────────────────────────
# 포맷 설정
# ────────────────────────────────────────────

TELEGRAM_MAX_LENGTH = 4096  # 텔레그램 메시지 최대 길이
BLOG_MIN_LENGTH = 500       # 블로그 최소 길이

# 텔레그램 출력 템플릿
TELEGRAM_HEADER = "📊 *일일 브리핑* | {date}"
TELEGRAM_FOOTER = "\n\n_자동 생성 | Tracking Bot_"

# 블로그 출력 헤더
BLOG_HEADER_TEMPLATE = """제목: {date} 일일 정보 브리핑

카테고리: 정보/트렌드
태그: {tags}

"""

# Notion 데이터베이스 프로퍼티 매핑 (데이터베이스 사용 시)
NOTION_PROPERTIES = {
    "title_prop": "Name",
    "date_prop": "Date",
    "sentiment_prop": "Sentiment",
    "tags_prop": "Tags",
}


# ────────────────────────────────────────────
# 데모 모드 샘플 데이터
# ────────────────────────────────────────────

DEMO_MESSAGES = """[채널: tech_news]
2024-01-15 09:30 | OpenAI, GPT-5 출시 임박 - 내부 테스트 단계 진입. 이전 버전 대비 추론 능력 40% 향상, 멀티모달 기능 대폭 강화될 예정.

[채널: crypto_signals]
2024-01-15 10:15 | 비트코인 ETF 순유입 역대 최고치 경신. 블랙록 IBIT 하루 유입액 $650M 돌파. 기관 수요 지속 증가세.

[채널: startup_kr]
2024-01-15 11:00 | 네이버, 하이퍼클로바X 기업용 API 공개. 월 구독 방식으로 제공, 카카오와 본격 경쟁 구도 형성.

[채널: ai_research]
2024-01-15 11:45 | 구글 딥마인드, 단백질 구조 예측 정확도 99.9% 달성 발표. 신약 개발 기간 대폭 단축 전망. Nature 게재 예정.

[채널: tech_news]
2024-01-15 13:20 | 애플, 2025년 AR 글래스 출시 재확인. 비전프로 OS 업데이트로 개발자 생태계 확장 중. 삼성과 협력설 부인.

[채널: startup_kr]
2024-01-15 14:30 | 카카오, AI 비서 '카나나' 베타 서비스 시작. 카카오톡 내 통합으로 일상 업무 자동화 지원. 초기 반응 긍정적.

[채널: crypto_signals]
2024-01-15 15:00 | 이더리움 2.0 스테이킹 수익률 4.2% 기록. 총 스테이킹 물량 3,200만 ETH 돌파. DeFi TVL도 반등세.

[채널: ai_research]
2024-01-15 16:15 | MIT, LLM 추론 비용 80% 절감 기술 공개. 양자화와 증류 기법 결합한 새 방식. 오픈소스 공개 예정."""


def validate_config() -> dict:
    """설정 유효성 검사, 경고 메시지 반환"""
    warnings = []
    errors = []

    if not ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY 미설정 - Claude API 사용 불가")

    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        warnings.append("Telegram API 미설정 - 자동 수집 불가 (수동 모드는 가능)")

    if not SLACK_WEBHOOK_URL:
        warnings.append("SLACK_WEBHOOK_URL 미설정 - Slack 알림 비활성화")

    if not NOTION_TOKEN or not NOTION_PAGE_ID:
        warnings.append("Notion 설정 미완료 - Notion 페이지 생성 비활성화")

    return {"errors": errors, "warnings": warnings}

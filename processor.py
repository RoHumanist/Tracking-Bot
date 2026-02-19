"""
processor.py - Claude API로 메시지 분석
수집된 메시지를 Claude에게 보내 구조화된 JSON 결과 반환
"""
import json
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

import config
from collector import format_messages_for_analysis


def _clean_json_response(text: str) -> str:
    """Claude 응답에서 JSON만 추출"""
    # ```json ... ``` 코드블록 처리
    code_block = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if code_block:
        return code_block.group(1).strip()

    # 중괄호로 시작하는 JSON 찾기
    json_match = re.search(r"\{[\s\S]+\}", text)
    if json_match:
        return json_match.group(0).strip()

    return text.strip()


def analyze_messages(
    messages: List[Dict],
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Claude API로 메시지 분석

    Args:
        messages: 수집된 메시지 리스트
        dry_run: True이면 API 호출 없이 더미 결과 반환

    Returns:
        분석 결과 딕셔너리
    """
    if not messages:
        raise ValueError("분석할 메시지가 없습니다")

    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)

    # 채널 목록 추출
    channels = list({m.get("channel", "unknown") for m in messages})

    # 분석용 텍스트 생성
    message_text = format_messages_for_analysis(messages)

    # 프롬프트 완성
    prompt = config.ANALYSIS_PROMPT_TEMPLATE.format(
        date=now.strftime("%Y년 %m월 %d일 %H:%M"),
        channel_count=len(channels),
        message_count=len(messages),
        messages=message_text,
    )

    if dry_run:
        print("[Processor] Dry-run 모드: 더미 결과 반환")
        return _get_dummy_result(now, channels, len(messages))

    if not config.ANTHROPIC_API_KEY:
        raise ValueError(
            "ANTHROPIC_API_KEY 미설정. .env 파일 또는 환경변수를 확인해주세요."
        )

    try:
        import anthropic
    except ImportError:
        raise ImportError("anthropic 미설치. pip install anthropic 실행 필요")

    print(f"[Processor] Claude 분석 시작 ({len(messages)}개 메시지, 모델: {config.CLAUDE_MODEL})")

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    try:
        response = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=config.CLAUDE_MAX_TOKENS,
            system=config.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = response.content[0].text
        print(f"[Processor] 응답 수신 ({len(raw_text)} chars)")

        # JSON 파싱
        json_text = _clean_json_response(raw_text)
        result = json.loads(json_text)

        # 메타데이터 추가
        result["_meta"] = {
            "analyzed_at": now.isoformat(),
            "message_count": len(messages),
            "channel_count": len(channels),
            "channels": channels,
            "model": config.CLAUDE_MODEL,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }

        print("[Processor] 분석 완료")
        return result

    except json.JSONDecodeError as e:
        print(f"[Processor] JSON 파싱 오류: {e}")
        print(f"[Processor] 원본 응답:\n{raw_text[:500]}...")
        # JSON 파싱 실패 시 텍스트로 감싸서 반환
        return {
            "summary": raw_text[:500],
            "topics": [],
            "key_numbers": [],
            "action_items": [],
            "market_sentiment": "neutral",
            "sentiment_reason": "파싱 오류로 감성 분석 불가",
            "top_keywords": [],
            "_meta": {
                "analyzed_at": now.isoformat(),
                "message_count": len(messages),
                "channel_count": len(channels),
                "channels": channels,
                "parse_error": str(e),
            },
        }

    except Exception as e:
        raise RuntimeError(f"Claude API 오류: {e}") from e


def _get_dummy_result(now: datetime, channels: List[str], msg_count: int) -> Dict[str, Any]:
    """데모/드라이런용 더미 분석 결과"""
    return {
        "summary": (
            "오늘 AI 기술 분야에서 주목할 만한 발표들이 이어졌습니다. "
            "OpenAI의 GPT-5 출시 임박 소식과 구글 딥마인드의 단백질 구조 예측 성과가 "
            "큰 관심을 받았으며, 국내에서는 네이버와 카카오의 AI 서비스 경쟁이 본격화되고 있습니다."
        ),
        "topics": [
            {
                "title": "GPT-5 출시 임박",
                "importance": "high",
                "content": (
                    "OpenAI가 GPT-5의 내부 테스트를 시작했다는 소식이 전해졌습니다. "
                    "이전 버전 대비 추론 능력이 40% 향상되고 멀티모달 기능이 대폭 강화될 예정입니다. "
                    "출시 시기는 구체적으로 밝혀지지 않았으나 수 주 내로 예상됩니다."
                ),
                "sources": ["tech_news"],
                "tags": ["AI", "OpenAI", "GPT-5", "LLM"],
            },
            {
                "title": "비트코인 ETF 순유입 역대 최고",
                "importance": "high",
                "content": (
                    "블랙록 IBIT ETF의 하루 순유입액이 $650M을 돌파하며 역대 최고치를 경신했습니다. "
                    "기관 투자자들의 수요가 지속적으로 증가하고 있어 시장에 긍정적인 신호로 해석됩니다."
                ),
                "sources": ["crypto_signals"],
                "tags": ["비트코인", "ETF", "기관투자", "블랙록"],
            },
            {
                "title": "국내 AI 서비스 경쟁 본격화",
                "importance": "medium",
                "content": (
                    "네이버가 하이퍼클로바X 기업용 API를 공개하고, 카카오는 AI 비서 '카나나' 베타를 시작했습니다. "
                    "양사의 AI 서비스가 동시에 시장에 진입하며 국내 AI 생태계 경쟁이 심화될 전망입니다."
                ),
                "sources": ["startup_kr"],
                "tags": ["네이버", "카카오", "AI", "한국"],
            },
            {
                "title": "구글 딥마인드 단백질 구조 예측 99.9% 달성",
                "importance": "medium",
                "content": (
                    "구글 딥마인드가 단백질 구조 예측 정확도 99.9%를 달성했다고 발표했습니다. "
                    "이 성과는 Nature에 게재될 예정이며, 신약 개발 기간을 대폭 단축할 것으로 기대됩니다."
                ),
                "sources": ["ai_research"],
                "tags": ["딥마인드", "바이오", "단백질", "신약"],
            },
        ],
        "key_numbers": [
            {"label": "블랙록 IBIT 일일 순유입", "value": "$650M+", "context": "역대 최고치 경신"},
            {"label": "GPT-5 추론 능력 향상", "value": "40%", "context": "이전 버전 대비"},
            {"label": "단백질 구조 예측 정확도", "value": "99.9%", "context": "구글 딥마인드"},
            {"label": "이더리움 스테이킹 물량", "value": "3,200만 ETH", "context": "역대 최고"},
        ],
        "action_items": [
            "GPT-5 출시 일정 모니터링 - API 비용 및 성능 변화 주목",
            "블랙록 IBIT ETF 자금 흐름 지속 추적",
            "네이버/카카오 AI API 베타 신청 검토",
            "딥마인드 논문 Nature 게재 후 상세 내용 확인",
        ],
        "market_sentiment": "positive",
        "sentiment_reason": (
            "AI 기술 발전과 기관 자금 유입이 동시에 확인되며 전반적으로 긍정적인 흐름입니다."
        ),
        "top_keywords": ["AI", "GPT-5", "비트코인ETF", "네이버", "딥마인드"],
        "_meta": {
            "analyzed_at": now.isoformat(),
            "message_count": msg_count,
            "channel_count": len(channels),
            "channels": channels,
            "model": "demo_mode",
            "input_tokens": 0,
            "output_tokens": 0,
        },
    }

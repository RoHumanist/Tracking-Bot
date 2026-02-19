#!/usr/bin/env python3
"""
main.py - Tracking Bot 메인 진입점

실행 모드:
  python main.py --demo              # 샘플 데이터로 전체 파이프라인 테스트
  python main.py --file msgs.txt     # 파일에서 메시지 읽기
  python main.py --stdin             # 표준 입력에서 메시지 읽기
  python main.py                     # Telegram API 자동 수집

환경변수 설정:
  ANTHROPIC_API_KEY   - Claude API 키 (필수)
  TELEGRAM_API_ID     - Telegram API ID (자동 모드 필수)
  TELEGRAM_API_HASH   - Telegram API Hash (자동 모드 필수)
  TELEGRAM_PHONE      - Telegram 전화번호 (자동 모드 필수)
  TELEGRAM_CHANNELS   - 수집할 채널, 쉼표 구분
  SLACK_WEBHOOK_URL   - Slack 웹훅 URL (선택)
  NOTION_TOKEN        - Notion integration 토큰 (선택)
  NOTION_PAGE_ID      - Notion 부모 페이지 ID (선택)
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path


def load_env_file(env_file: str = ".env"):
    """간단한 .env 파일 로더 (python-dotenv 없이 동작)"""
    env_path = Path(env_file)
    if not env_path.exists():
        return

    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tracking Bot - 텔레그램 채널 분석 + Notion/Slack/블로그 브리핑",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--demo",
        action="store_true",
        help="샘플 데이터로 전체 파이프라인 테스트 (API 키 없이 동작)",
    )
    mode_group.add_argument(
        "--file",
        metavar="PATH",
        help="메시지가 담긴 텍스트 파일 경로",
    )
    mode_group.add_argument(
        "--stdin",
        action="store_true",
        help="표준 입력에서 메시지 읽기",
    )

    parser.add_argument(
        "--output",
        metavar="DIR",
        default="./output",
        help="출력 디렉토리 (기본: ./output)",
    )
    parser.add_argument(
        "--env",
        metavar="FILE",
        default=".env",
        help=".env 파일 경로 (기본: .env)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Claude API 호출 없이 더미 결과로 테스트",
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="현재 설정 상태 출력 후 종료",
    )

    return parser.parse_args()


def print_banner():
    print("=" * 55)
    print("  Tracking Bot - 일일 채널 브리핑 자동화")
    print("=" * 55)


def print_config_status():
    """설정 상태 출력"""
    import config

    validation = config.validate_config()

    print("\n[ 설정 상태 ]")
    print(f"  Claude 모델    : {config.CLAUDE_MODEL}")
    print(f"  API Key        : {'설정됨' if config.ANTHROPIC_API_KEY else '미설정 !'}")
    print(f"  Telegram API   : {'설정됨' if config.TELEGRAM_API_ID else '미설정'}")
    print(f"  채널 목록      : {config.TELEGRAM_CHANNELS or '없음'}")
    print(f"  Slack Webhook  : {'설정됨' if config.SLACK_WEBHOOK_URL else '미설정'}")
    print(f"  Notion Token   : {'설정됨' if config.NOTION_TOKEN else '미설정'}")
    print(f"  Notion Page ID : {'설정됨' if config.NOTION_PAGE_ID else '미설정'}")
    print(f"  출력 디렉토리  : {config.OUTPUT_DIR}")

    if validation["errors"]:
        print("\n  [ 오류 ]")
        for e in validation["errors"]:
            print(f"    ✗ {e}")

    if validation["warnings"]:
        print("\n  [ 경고 ]")
        for w in validation["warnings"]:
            print(f"    ! {w}")

    print()


def run_pipeline(
    mode: str,
    file_path: str = None,
    output_dir: str = None,
    dry_run: bool = False,
) -> bool:
    """
    전체 파이프라인 실행

    1. 메시지 수집
    2. Claude 분석
    3. 파일/Slack/Notion 전송

    Returns:
        True: 성공, False: 실패
    """
    from collector import collect_messages
    from processor import analyze_messages
    from notifier import notify_all

    kst = timezone(timedelta(hours=9))
    date_str = datetime.now(kst).strftime("%Y년 %m월 %d일")

    # ── STEP 1: 메시지 수집 ──────────────────────────
    print(f"\n[1/3] 메시지 수집 ({mode} 모드)")
    try:
        messages = collect_messages(mode, file_path)
    except Exception as e:
        print(f"[ERROR] 메시지 수집 실패: {e}")
        return False

    if not messages:
        print("[ERROR] 수집된 메시지가 없습니다.")
        return False

    print(f"      → {len(messages)}개 메시지 수집 완료")

    # ── STEP 2: Claude 분석 ──────────────────────────
    print(f"\n[2/3] Claude 분석 시작")
    is_demo = mode == "demo" or dry_run
    try:
        result = analyze_messages(messages, dry_run=is_demo)
    except Exception as e:
        print(f"[ERROR] 분석 실패: {e}")
        return False

    print(f"      → {len(result.get('topics', []))}개 주제 추출 완료")

    # ── STEP 3: 결과 전송/저장 ────────────────────────
    print(f"\n[3/3] 결과 전송/저장")
    nr = notify_all(result, date_str, output_dir)
    print(f"\n      → {nr.summary()}")

    return True


def main():
    print_banner()

    # .env 파일 로드
    args = parse_args()
    load_env_file(args.env)

    # 설정 보기 모드
    if args.show_config:
        print_config_status()
        return

    import config

    # 모드 결정
    if args.demo:
        mode = "demo"
        file_path = None
        print(f"\n모드: 데모 (샘플 데이터 사용, Claude API {'호출 안 함' if args.dry_run else '호출'})")
    elif args.file:
        mode = "file"
        file_path = args.file
        print(f"\n모드: 파일 ({args.file})")
    elif args.stdin:
        mode = "stdin"
        file_path = None
        print("\n모드: 표준 입력")
    else:
        mode = "auto"
        file_path = None
        print("\n모드: 텔레그램 자동 수집")

    # 설정 간단 출력
    print_config_status()

    # 파이프라인 실행
    success = run_pipeline(
        mode=mode,
        file_path=file_path,
        output_dir=args.output,
        dry_run=args.dry_run,
    )

    if success:
        print("\n파이프라인 완료.")
        print(f"출력 파일: {args.output}/")
        sys.exit(0)
    else:
        print("\n파이프라인 실패. 위 오류 메시지를 확인해주세요.")
        sys.exit(1)


if __name__ == "__main__":
    main()

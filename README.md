# Tracking Bot

텔레그램 채널 메시지를 수집 → Claude AI로 분석 → Notion 페이지 생성 + 텔레그램/블로그용 텍스트 출력.

## 실행 모드

| 명령어 | 용도 |
|--------|------|
| `python main.py --demo` | API 키 없이 파이프라인 테스트 |
| `python main.py --file messages.txt` | 텍스트 파일에서 메시지 읽어 처리 |
| `python main.py --stdin` | 터미널에 직접 붙여넣기 |
| `python main.py` | Telegram API로 자동 수집 → 분석 → 전송 |

## 출력물

- `output/YYYYMMDD_telegram.txt` → 텔레그램 채널 복붙용
- `output/YYYYMMDD_blog.txt` → 네이버 블로그 복붙용
- Notion 페이지 자동 생성 (토큰 설정 시)
- Slack 메시지 (웹훅 설정 시)

## 빠른 시작

### 1. 설치

```bash
git clone <repo-url>
cd Tracking-Bot
pip install -r requirements.txt
```

### 2. 환경변수 설정

```bash
cp .env.example .env
# .env 파일을 열어 ANTHROPIC_API_KEY 등 입력
```

### 3. 데모 테스트

```bash
python main.py --demo
```

샘플 데이터로 전체 파이프라인(수집→분석→저장)을 테스트합니다. `ANTHROPIC_API_KEY` 없이도 동작합니다.

### 4. 파일 모드 (가장 빠른 실제 사용법)

```
텔레그램 앱에서 채널 메시지 복사
→ messages.txt에 붙여넣기
→ python main.py --file messages.txt
```

`ANTHROPIC_API_KEY`만 있으면 바로 결과가 나옵니다.

## 환경변수 상세

| 변수 | 필수 | 설명 |
|------|------|------|
| `ANTHROPIC_API_KEY` | ✅ | Claude API 키 |
| `TELEGRAM_API_ID` | auto 모드 | my.telegram.org에서 발급 |
| `TELEGRAM_API_HASH` | auto 모드 | my.telegram.org에서 발급 |
| `TELEGRAM_PHONE` | auto 모드 | +821012345678 형식 |
| `TELEGRAM_CHANNELS` | auto 모드 | 채널명, 쉼표 구분 |
| `SLACK_WEBHOOK_URL` | 선택 | Slack 웹훅 URL |
| `NOTION_TOKEN` | 선택 | Notion integration 토큰 |
| `NOTION_PAGE_ID` | 선택 | 브리핑 저장할 페이지 ID |

## 파일 입력 형식

```
[채널: tech_news] 2024-01-15 09:30 | OpenAI, GPT-5 출시 임박...

[채널: crypto_signals] 2024-01-15 10:15 | 비트코인 ETF 순유입 최고치...
```

또는 형식 없이 일반 텍스트로도 붙여넣기 가능합니다.

## Notion 설정

1. [Notion Integrations](https://www.notion.so/my-integrations)에서 새 integration 생성
2. 토큰 복사 → `NOTION_TOKEN` 설정
3. 브리핑을 저장할 Notion 페이지에서 integration 연결 (Share → Invite)
4. 페이지 URL에서 ID 추출: `notion.so/.../{32자리-ID}` → `NOTION_PAGE_ID` 설정

## 파일 구조

```
Tracking-Bot/
├── main.py          # 진입점 (3가지 모드)
├── config.py        # 모든 설정 + 프롬프트
├── collector.py     # 메시지 수집 (Telegram/파일/stdin)
├── processor.py     # Claude API 분석
├── formatter.py     # 출력 포맷 (텔레그램/블로그/Slack/Notion)
├── notifier.py      # 전송/저장 (Slack/Notion/파일)
├── requirements.txt
├── .env.example
└── .github/
    └── workflows/
        └── daily-briefing.yml  # GitHub Actions 자동화
```

## GitHub Actions 자동화

`daily-briefing.yml`을 활성화하면 매일 오전 8시(KST)에 자동 실행됩니다.

GitHub 레포 → Settings → Secrets에 환경변수를 저장하면 됩니다.

> **참고**: Telegram 자동 수집(`--auto`)은 세션 파일이 필요해 GitHub Actions에서 직접 사용하기 어렵습니다. 서버에서 cron으로 실행하거나 `--file` 모드와 결합하는 것을 권장합니다.

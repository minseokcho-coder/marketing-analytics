"""마케팅 성과 분석 Slack 리포트 모듈"""
import os
import sys
from datetime import datetime

# 상위 디렉토리 import 허용
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "")

# ──────────────────────────────────────────────
# 2025 하반기 vs 2026.01 마케팅 성과 데이터
# 분기점: 2026년 1월 9일
# ──────────────────────────────────────────────

PERFORMANCE_DATA = {
    "pivot_date": "2026-01-09",
    "period_before": "2025 Q4 (10-11월)",
    "period_after": "2026년 1월 (분기점 이후)",

    # ── Before (2025 Q4) ──
    "before": {
        "monthly_sends": 1_915_571,
        "view_rate": 65.1,
        "click_rate": 7.9,
        "signup_rate": 1.4,
        "auth_rate": 50.5,
        "roas": 92.0,
    },

    # ── After (2026.01) ──
    "after": {
        "total_cost": 77_000_000,
        "total_sends": 1_362_014,
        "total_views": 913_106,
        "total_clicks": 148_828,
        "total_signups": 37_340,
        "total_auths": 21_215,
        "view_rate": 67.04,
        "click_rate": 10.93,
        "signup_rate": 2.74,
        "auth_rate": 56.82,
        "roas": 126.07,
        # 종소세 사업자
        "jongso_valid": 266,
        "jongso_valid_amount": 1_371_373_454,
        "jongso_apply": 135,
        "jongso_apply_amount": 779_047_476,
        "jongso_apply_rate": 50.75,
        # 프리/근로
        "free_apply": 1_702,
        "free_apply_amount": 2_991_890_424,
        # 종부세
        "jongbu_valid": 767,
        "jongbu_valid_amount": 3_095_798_181,
        "jongbu_apply": 330,
        "jongbu_apply_amount": 1_089_996_772,
        # 양도세
        "yangdo_valid": 720,
        "yangdo_valid_amount": 6_480_588_639,
        "yangdo_apply": 350,
        "yangdo_apply_amount": 2_602_330_238,
        # CAC
        "cac_signup": 2_062,
        "cac_auth": 3_630,
        "cac_valid": 51_782,
        "cac_apply": 113_235,
        # 통합 EPA
        "total_epa": 97_073_694,
    },

    # ── 하락 기여도 분석 ──
    "contribution": [
        {"indicator": "평균환급액(신청)", "change": -19.74, "contribution": 25.37, "rank": 1},
        {"indicator": "클릭율", "change": -17.21, "contribution": 22.11, "rank": 2},
        {"indicator": "가입율", "change": -17.04, "contribution": 21.90, "rank": 3},
        {"indicator": "신청율", "change": -10.40, "contribution": 13.37, "rank": 4},
        {"indicator": "기경정비율", "change": -8.96, "contribution": 11.51, "rank": 5},
        {"indicator": "열람율", "change": -2.45, "contribution": 3.14, "rank": 6},
        {"indicator": "유효고객율", "change": -2.02, "contribution": 2.60, "rank": 7},
    ],

    # ── 일별 상세 (2026.01) ──
    "daily_jan2026": [
        {"date": "01/06", "sends": 194794, "view_rate": 65.81, "signup_rate": 2.23, "auth_rate": 55.34, "signups": 4335},
        {"date": "01/08", "sends": 199939, "view_rate": 66.47, "signup_rate": 2.29, "auth_rate": 56.98, "signups": 4582},
        {"date": "01/13", "sends": 191617, "view_rate": 67.18, "signup_rate": 3.15, "auth_rate": 57.73, "signups": 6032},
        {"date": "01/15", "sends": 200206, "view_rate": 68.60, "signup_rate": 3.42, "auth_rate": 58.65, "signups": 6846},
        {"date": "01/19", "sends": 194637, "view_rate": 68.04, "signup_rate": 3.24, "auth_rate": 57.91, "signups": 6313},
        {"date": "01/20", "sends": 177952, "view_rate": 67.63, "signup_rate": 3.23, "auth_rate": 52.17, "signups": 5749},
        {"date": "01/22", "sends": 202869, "view_rate": 65.63, "signup_rate": 1.72, "auth_rate": 58.94, "signups": 3483},
    ],
}


def _fmt_won(amount: int) -> str:
    """원 단위를 억/만 단위로 포맷"""
    if amount >= 100_000_000:
        return f"{amount / 100_000_000:.1f}억"
    if amount >= 10_000:
        return f"{amount / 10_000:.0f}만"
    return f"{amount:,}"


def _change_emoji(before: float, after: float) -> str:
    diff = after - before
    if diff > 0:
        return f":arrow_up: +{diff:.1f}%p"
    if diff < 0:
        return f":arrow_down: {diff:.1f}%p"
    return "→ 동일"


def build_summary_blocks() -> list:
    """핵심 요약 리포트 블록"""
    d = PERFORMANCE_DATA
    b = d["before"]
    a = d["after"]
    today = datetime.now().strftime("%Y년 %m월 %d일")

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "마케팅 성과 분석 리포트",
                "emoji": True,
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f":calendar: {today} | 분기점: *2026.01.09* | 비교: 2025 Q4 vs 2026.01",
                }
            ],
        },
        {"type": "divider"},
        # ── KPI 요약 ──
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*:bar_chart: 핵심 KPI (Before vs After 분기점)*",
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*총 집행 비용*\n{_fmt_won(a['total_cost'])}"},
                {"type": "mrkdwn", "text": f"*총 발송*\n{a['total_sends']:,}"},
                {"type": "mrkdwn", "text": f"*ROAS*\n{a['roas']}% {_change_emoji(b['roas'], a['roas'])}"},
                {"type": "mrkdwn", "text": f"*통합 EPA*\n{_fmt_won(a['total_epa'])}"},
            ],
        },
        {"type": "divider"},
        # ── 전환율 비교 ──
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*:chart_with_upwards_trend: 주요 전환율 변화 (Q4 -> 1월)*",
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*열람율*\n{b['view_rate']}% → {a['view_rate']}% {_change_emoji(b['view_rate'], a['view_rate'])}"},
                {"type": "mrkdwn", "text": f"*클릭율*\n{b['click_rate']}% → {a['click_rate']}% {_change_emoji(b['click_rate'], a['click_rate'])}"},
                {"type": "mrkdwn", "text": f"*가입율*\n{b['signup_rate']}% → {a['signup_rate']}% {_change_emoji(b['signup_rate'], a['signup_rate'])}"},
                {"type": "mrkdwn", "text": f"*인증율*\n{b['auth_rate']}% → {a['auth_rate']}% {_change_emoji(b['auth_rate'], a['auth_rate'])}"},
            ],
        },
        {"type": "divider"},
        # ── 채널별 성과 ──
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*:moneybag: 채널별 EPA / 신청 성과 (2026.01)*",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f":one: *종소세 (사업자)*: 유효 {a['jongso_valid']}명 | 신청 {a['jongso_apply']}명 ({a['jongso_apply_rate']}%) | 신청환급 {_fmt_won(a['jongso_apply_amount'])}\n"
                    f":two: *프리/근로*: 신청 {a['free_apply']:,}명 | 신청환급 {_fmt_won(a['free_apply_amount'])}\n"
                    f":three: *종부세*: 유효 {a['jongbu_valid']}명 | 신청 {a['jongbu_apply']}명 | 유효환급 {_fmt_won(a['jongbu_valid_amount'])}\n"
                    f":four: *양도세*: 유효 {a['yangdo_valid']}명 | 신청 {a['yangdo_apply']}명 | 유효환급 {_fmt_won(a['yangdo_valid_amount'])}"
                ),
            },
        },
        {"type": "divider"},
        # ── 하락 기여도 ──
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*:warning: 하락 기여도 TOP 3 (EPA 감소 요인)*",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n".join(
                    f"{c['rank']}. *{c['indicator']}*: {c['change']:+.1f}% (기여도 {c['contribution']:.1f}%)"
                    for c in d["contribution"][:3]
                ),
            },
        },
        {"type": "divider"},
        # ── CAC ──
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*:receipt: CAC (고객획득비용)*",
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*가입 CAC*\n{a['cac_signup']:,}원"},
                {"type": "mrkdwn", "text": f"*인증 CAC*\n{a['cac_auth']:,}원"},
                {"type": "mrkdwn", "text": f"*유효 CAC*\n{a['cac_valid']:,}원"},
                {"type": "mrkdwn", "text": f"*신청 CAC*\n{a['cac_apply']:,}원"},
            ],
        },
        {"type": "divider"},
        # ── 핵심 인사이트 ──
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*:bulb: 핵심 인사이트*\n\n"
                    ":white_check_mark: *개선 지표*: 열람율(+1.9%p), 클릭율(+3.0%p), 가입율(+1.3%p), ROAS(+34.1%p)\n"
                    ":x: *하락 지표*: 유효고객율(-4.4%p), 발송 모수 축소(-28.9%)\n"
                    ":new: *신규 성과*: 프리/근로 EPA 29.9억, 종부세 유효환급 30.9억, 양도세 유효환급 64.8억\n"
                    ":dart: *우선 과제*: 클릭율 A/B 테스트, 랜딩 UX 개선, 타겟 세그먼트 최적화"
                ),
            },
        },
        # ── 푸터 ──
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": ":robot_face: _PM Scraper Bot 마케팅 분석 | 데이터 소스: KakaoTalk TMS 캠페인_",
                }
            ],
        },
    ]
    return blocks


def send_marketing_report(channel: str = None, test_mode: bool = False) -> bool:
    """마케팅 성과 분석 리포트를 Slack으로 전송"""
    blocks = build_summary_blocks()
    text = "마케팅 성과 분석 리포트 - 2025 Q4 vs 2026.01 (분기점: 1/9)"

    if test_mode:
        print("=" * 60)
        print("[테스트 모드] 마케팅 리포트 미리보기")
        print("=" * 60)
        for block in blocks:
            if block.get("type") == "header":
                print(f"\n### {block['text']['text']}")
            elif block.get("type") == "section":
                if "fields" in block:
                    for f in block["fields"]:
                        print(f"  {f['text']}")
                elif "text" in block:
                    print(f"  {block['text']['text']}")
            elif block.get("type") == "divider":
                print("-" * 40)
            elif block.get("type") == "context":
                for el in block.get("elements", []):
                    print(f"  {el.get('text', '')}")
        print("=" * 60)
        return True

    if not SLACK_BOT_TOKEN:
        print("SLACK_BOT_TOKEN이 설정되지 않았습니다.")
        return False

    target_channel = channel or SLACK_CHANNEL
    if not target_channel:
        print("SLACK_CHANNEL이 설정되지 않았습니다.")
        return False

    try:
        client = WebClient(token=SLACK_BOT_TOKEN)
        client.chat_postMessage(
            channel=target_channel,
            blocks=blocks,
            text=text,
            unfurl_links=False,
            unfurl_media=False,
        )
        print(f"마케팅 리포트 전송 성공 → {target_channel}")
        return True
    except SlackApiError as e:
        print(f"마케팅 리포트 전송 실패: {e.response['error']}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="마케팅 성과 분석 Slack 리포트")
    parser.add_argument("--test", action="store_true", help="테스트 모드 (콘솔 출력만)")
    parser.add_argument("--channel", type=str, help="전송할 Slack 채널 ID")
    args = parser.parse_args()

    send_marketing_report(channel=args.channel, test_mode=args.test)

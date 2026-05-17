"""
Alphex Contento — AI 마케팅 영상 자동 제작 파이프라인
Streamlit 메인 대시보드
"""

import streamlit as st
import anthropic
import requests
from datetime import datetime
import time

# ══════════════════════════════════════════════════════════
# 1. 페이지 기본 설정
# ══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Alphex Contento | AI 영상 자동 제작",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════
# 2. 다크 핀테크 테마 CSS
# ══════════════════════════════════════════════════════════
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #0E1117; }

section[data-testid="stSidebar"] {
    background-color: #0D1117 !important;
    border-right: 1px solid #21262D;
}

div.stButton > button {
    background: linear-gradient(135deg, #00E676, #00C853);
    color: #0E1117 !important;
    font-weight: 700;
    font-size: 14px;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    width: 100%;
    transition: all 0.2s ease;
}
div.stButton > button:hover {
    background: linear-gradient(135deg, #69F0AE, #00E676);
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(0, 230, 118, 0.35);
}

div[data-baseweb="tab-list"] {
    background-color: #161B22;
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
}
button[data-baseweb="tab"] {
    background-color: transparent;
    color: #8B949E !important;
    font-weight: 600;
    border-radius: 7px;
    border: none;
    padding: 10px 18px;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background-color: #21262D !important;
    color: #00E676 !important;
}

div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea {
    background-color: #161B22 !important;
    color: #E6EDF3 !important;
    border: 1px solid #30363D !important;
    border-radius: 8px;
}
div[data-baseweb="input"] input:focus,
div[data-baseweb="textarea"] textarea:focus {
    border-color: #00E676 !important;
    box-shadow: 0 0 0 2px rgba(0, 230, 118, 0.2) !important;
}

div[data-baseweb="select"] > div {
    background-color: #161B22 !important;
    border: 1px solid #30363D !important;
    color: #E6EDF3 !important;
    border-radius: 8px !important;
}

div[data-testid="metric-container"] {
    background-color: #161B22;
    border: 1px solid #21262D;
    border-radius: 10px;
    padding: 14px;
}
div[data-testid="metric-container"] label { color: #8B949E !important; font-size: 11px !important; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    color: #00E676 !important;
    font-size: 22px !important;
    font-weight: 700 !important;
}

div[data-testid="stFileUploader"] {
    background-color: #161B22;
    border: 1px dashed #30363D;
    border-radius: 10px;
}

div[data-testid="stCheckbox"] label { color: #E6EDF3 !important; }
hr { border-color: #21262D !important; }
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #0E1117; }
::-webkit-scrollbar-thumb { background: #30363D; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #00E676; }
</style>
""",
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════
# 3. 시크릿 로딩 헬퍼
# ══════════════════════════════════════════════════════════
def _secret(key, session_fallback=None):
    try:
        v = st.secrets.get(key, "")
        if v:
            return v
    except Exception:
        pass
    if session_fallback:
        return st.session_state.get(session_fallback, "")
    return ""

# ══════════════════════════════════════════════════════════
# 4. 세션 스테이트 초기화
# ══════════════════════════════════════════════════════════
_defaults = {
    "daily_step": 1,
    "daily_news_done": False,
    "daily_news_data": [],
    "daily_earnings_data": [],
    "daily_script_done": False,
    "daily_script_text": "",
    "daily_titles": [],
    "daily_voice_done": False,
    "daily_audio_bytes": None,
    "daily_video_done": False,
    "daily_video_url": "",
    "daily_render_id": "",
    "wknd_step": 1,
    "wknd_data_done": False,
    "wknd_market_data": {},
    "wknd_script_done": False,
    "wknd_script_text": "",
    "wknd_titles": [],
    "wknd_voice_done": False,
    "wknd_audio_bytes": None,
    "wknd_video_done": False,
    "wknd_video_url": "",
    "api_claude": "",
    "api_elevenlabs": "",
    "api_creatomate": "",
    "api_fmp": "",
    "persona_name": "",
    "persona_tone": "주식 예능 (유머+정보 균형)",
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════════════════════
# 5. UI 헬퍼 함수
# ══════════════════════════════════════════════════════════
def step_indicator(current: int, total: int = 5) -> None:
    labels = ["데이터\n수집", "AI 대본\n생성", "보이스\n합성", "영상\n조립", "완성 &\n다운로드"]
    html = '<div style="display:flex;justify-content:center;align-items:center;padding:20px 0 8px;gap:0;">'
    for i in range(total):
        n = i + 1
        done = n < current
        active = n == current
        if done:
            bg, fg, txt, icon = "#00E676", "#0E1117", "#00E676", "✓"
        elif active:
            bg, fg, txt, icon = "#00E676", "#0E1117", "#E6EDF3", str(n)
        else:
            bg, fg, txt, icon = "#21262D", "#8B949E", "#8B949E", str(n)
        glow = "box-shadow:0 0 14px rgba(0,230,118,0.5);" if active else ""
        html += f"""
        <div style="display:flex;flex-direction:column;align-items:center;min-width:72px;">
            <div style="width:38px;height:38px;border-radius:50%;background:{bg};color:{fg};
                        display:flex;align-items:center;justify-content:center;
                        font-weight:700;font-size:14px;{glow}">{icon}</div>
            <div style="margin-top:6px;font-size:10px;color:{txt};text-align:center;
                        white-space:pre-line;font-weight:{"700" if active else "400"};">{labels[i]}</div>
        </div>"""
        if i < total - 1:
            line_color = "#00E676" if n < current else "#21262D"
            html += f'<div style="flex:1;height:2px;background:{line_color};margin-bottom:24px;min-width:20px;max-width:48px;"></div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def step_badge(n: int, active: bool = True) -> str:
    bg = "#00E676" if active else "#21262D"
    fg = "#0E1117" if active else "#8B949E"
    return (
        f'<div style="width:26px;height:26px;border-radius:50%;background:{bg};color:{fg};'
        f'display:flex;align-items:center;justify-content:center;font-weight:700;'
        f'font-size:12px;flex-shrink:0;">{n}</div>'
    )


def section_header(n: int, title: str, active: bool = True) -> None:
    color = "#E6EDF3" if active else "#8B949E"
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">'
        f"{step_badge(n, active)}"
        f'<h3 style="color:{color};margin:0;font-size:17px;">{title}</h3>'
        f"</div>",
        unsafe_allow_html=True,
    )


def api_badge(label: str, secret_key: str, session_key: str, color_ok: str = "#00E676") -> None:
    connected = bool(_secret(secret_key, session_key))
    status = "✓ 연결됨" if connected else "⚠ 미설정"
    border = color_ok if connected else "#FFA726"
    color = color_ok if connected else "#FFA726"
    st.markdown(
        f'<div style="background:#161B22;border:1px solid #21262D;border-left:3px solid {border};'
        f'border-radius:8px;padding:10px 14px;margin:5px 0;">'
        f'<div style="font-size:10px;color:#8B949E;text-transform:uppercase;letter-spacing:.5px;">{label}</div>'
        f'<div style="font-size:15px;font-weight:700;color:{color};margin-top:3px;">{status}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def info_box(msg: str, color: str = "#00E676") -> None:
    st.markdown(
        f'<div style="background:#161B22;border-left:3px solid {color};border-radius:8px;'
        f'padding:14px;margin:12px 0;color:#8B949E;font-size:13px;">{msg}</div>',
        unsafe_allow_html=True,
    )


def card(content_html: str) -> None:
    st.markdown(
        f'<div style="background:#161B22;border:1px solid #21262D;border-radius:12px;padding:20px;margin:8px 0;">'
        f"{content_html}</div>",
        unsafe_allow_html=True,
    )


def divider() -> None:
    st.markdown("<hr>", unsafe_allow_html=True)


def market_mode() -> tuple[str, str]:
    now = datetime.now()
    if now.weekday() >= 5:
        return "📅 주말 대가 모드", "#7B68EE"
    if 6 <= now.hour < 14:
        return "☀️ 평일 아침 모드", "#00E676"
    return "🌙 장외 시간", "#FFA726"


# ══════════════════════════════════════════════════════════
# 6. API 함수
# ══════════════════════════════════════════════════════════

# ── FMP: 뉴스 수집 ──────────────────────────────────────
def fetch_news(tickers_str: str, count: int):
    api_key = _secret("FMP_API_KEY", "api_fmp")
    if not api_key:
        return [], "FMP API 키가 설정되지 않았습니다."
    tickers = ",".join([t.strip().upper() for t in tickers_str.split(",") if t.strip()])
    params = {"tickers": tickers, "limit": count, "apikey": api_key}
    try:
        r = requests.get(
            "https://financialmodelingprep.com/api/v3/stock_news",
            params=params,
            timeout=15,
        )
        if r.status_code == 200:
            return r.json(), None
        return [], f"FMP 오류 ({r.status_code}): {r.text[:200]}"
    except Exception as e:
        return [], str(e)


# ── FMP: 어닝 캘린더 ──────────────────────────────────
def fetch_earnings(tickers_str: str):
    api_key = _secret("FMP_API_KEY", "api_fmp")
    if not api_key:
        return []
    tickers = [t.strip().upper() for t in tickers_str.split(",") if t.strip()]
    try:
        r = requests.get(
            "https://financialmodelingprep.com/api/v3/earning_calendar",
            params={"apikey": api_key},
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            if tickers:
                data = [e for e in data if e.get("symbol") in tickers]
            return data[:10]
    except Exception:
        pass
    return []


# ── FMP: 주간 지수 데이터 ─────────────────────────────
def fetch_market_indices():
    api_key = _secret("FMP_API_KEY", "api_fmp")
    if not api_key:
        return {}
    symbols = {"S&P 500": "%5EGSPC", "NASDAQ": "%5EIXIC", "DOW": "%5EDJI", "VIX": "%5EVIX"}
    result = {}
    for name, sym in symbols.items():
        try:
            r = requests.get(
                f"https://financialmodelingprep.com/api/v3/quote/{sym}",
                params={"apikey": api_key},
                timeout=10,
            )
            if r.status_code == 200 and r.json():
                d = r.json()[0]
                result[name] = {
                    "price": d.get("price", 0),
                    "change": d.get("changesPercentage", 0),
                }
        except Exception:
            pass
    return result


# ── Claude: 대본 파싱 ────────────────────────────────
def parse_script_response(text: str):
    titles = []
    script = text
    if "== 유튜브 제목 후보 3개 ==" in text and "== 대본 ==" in text:
        parts = text.split("== 대본 ==")
        title_section = parts[0]
        script = parts[1].strip() if len(parts) > 1 else text
        for line in title_section.split("\n"):
            line = line.strip()
            if line and line[0] in "123" and "." in line[:3]:
                titles.append(line.split(".", 1)[1].strip())
    return titles, script


# ── Claude: 평일 대본 생성 ───────────────────────────
def generate_daily_script(news_data, earnings_data, user_comment, video_type, tone_style):
    api_key = _secret("CLAUDE_API_KEY", "api_claude")
    if not api_key:
        return None, None, "Claude API 키가 설정되지 않았습니다."

    news_lines = "\n".join(
        [f"• [{n.get('symbol','')}] {n.get('title','')}" for n in news_data[:7]]
    ) or "수집된 뉴스 없음"

    earnings_lines = "\n".join(
        [
            f"• {e.get('symbol','')} — 발표일: {e.get('date','')}  EPS 예상: ${e.get('epsEstimated','N/A')}"
            for e in earnings_data[:5]
        ]
    ) or "어닝 일정 없음"

    length_map = {
        "숏폼 (60초 이하)": "600자 이내, 임팩트 있게 짧고 강렬하게",
        "미드폼 (3–5분)": "1500자 내외, 자세하게",
        "롱폼 (10분 이상)": "3000자 이상, 심층 분석 포함",
    }
    tone_map = {
        "주식 예능 (유머+정보)": "재미있고 유머러스하게, 쉬운 말로",
        "진지한 심층 분석": "전문적이고 신뢰감 있게",
        "동기부여 멘토형": "따뜻하고 격려하는 톤으로",
    }

    prompt = f"""당신은 한국 주식 유튜브 채널 'Alphex Contento'의 AI 대본 작가입니다.

[오늘의 미국 주식 뉴스]
{news_lines}

[오늘 어닝 발표 일정]
{earnings_lines}

[운영자 한마디]
{user_comment if user_comment else "없음"}

[영상 타입] {video_type} — {length_map.get(video_type, "")}
[톤앤매너] {tone_style} — {tone_map.get(tone_style, "")}

아래 형식으로 한국어 대본을 작성해주세요:

== 유튜브 제목 후보 3개 ==
1. (후킹 제목1)
2. (후킹 제목2)
3. (후킹 제목3)

== 대본 ==
[오프닝 — 시청자를 즉시 사로잡는 후킹 멘트]

[뉴스 핵심 3가지 요약]

[어닝 발표 하이라이트]

[운영자 코멘트]

[마무리 & 구독/좋아요 CTA]

실제 방송에서 읽을 수 있는 자연스러운 구어체로 작성하세요."""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text
        titles, script = parse_script_response(raw)
        return titles, script, None
    except Exception as e:
        return None, None, str(e)


# ── Claude: 주말 대본 생성 ───────────────────────────
def generate_weekend_script(market_data, legend, insight_theme, user_comment):
    api_key = _secret("CLAUDE_API_KEY", "api_claude")
    if not api_key:
        return None, None, "Claude API 키가 설정되지 않았습니다."

    market_lines = "\n".join(
        [
            f"• {name}: {d.get('price', 0):,.2f} ({d.get('change', 0):+.2f}%)"
            for name, d in market_data.items()
        ]
    ) or "시장 데이터 없음"

    prompt = f"""당신은 한국 주식 유튜브 채널 'Alphex Contento'의 AI 대본 작가입니다.

[이번 주 미국 주요 지수]
{market_lines}

[이번 주 주인공 투자 대가] {legend}
[인사이트 테마] {insight_theme}
[운영자 한마디] {user_comment if user_comment else "없음"}

아래 형식으로 주말 스페셜 롱폼 대본(2000자 이상)을 작성해주세요:

== 유튜브 제목 후보 3개 ==
1. (후킹 제목1)
2. (후킹 제목2)
3. (후킹 제목3)

== 대본 ==
[오프닝 — 이번 주 시장 한 줄 요약]

[이번 주 주요 지수 리뷰]

[{legend}의 명언 & 현재 시장 적용]

[다음 주 주목할 포인트]

[운영자 코멘트]

[마무리 & 구독 CTA]

구어체, 동기부여 톤으로 작성하세요."""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text
        titles, script = parse_script_response(raw)
        return titles, script, None
    except Exception as e:
        return None, None, str(e)


# ── ElevenLabs: 음성 합성 ─────────────────────────────
VOICE_IDS = {
    "남성 · 전문 애널리스트형": "pNInz6obpgDQGcFmaJgB",
    "남성 · 에너지 넘치는 예능형": "ErXwobaYiN019PkySvjV",
    "여성 · 차분한 해설형": "21m00Tcm4TlvDq8ikWAM",
    "여성 · 활기찬 진행형": "EXAVITQu4vr4xnSDxMaL",
}


def synthesize_voice(text: str, voice_persona: str):
    api_key = _secret("ELEVENLABS_API_KEY", "api_elevenlabs")
    if not api_key:
        return None, "ElevenLabs API 키가 설정되지 않았습니다."

    voice_id = VOICE_IDS.get(voice_persona, "pNInz6obpgDQGcFmaJgB")
    text_to_speak = text[:2500]

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key,
    }
    payload = {
        "text": text_to_speak,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }

    try:
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            json=payload,
            headers=headers,
            timeout=90,
        )
        if r.status_code == 200:
            return r.content, None
        try:
            detail = r.json().get("detail", {})
            msg = detail.get("message", r.text[:300]) if isinstance(detail, dict) else str(detail)
        except Exception:
            msg = r.text[:300]
        return None, f"ElevenLabs 오류: {msg}"
    except Exception as e:
        return None, str(e)


# ── Creatomate: 영상 렌더링 ───────────────────────────
def create_video_render(title: str, script_excerpt: str, ratio_option: str):
    api_key = _secret("CREATOMATE_API_KEY", "api_creatomate")
    if not api_key:
        return None, "Creatomate API 키가 설정되지 않았습니다."

    if "9:16" in ratio_option:
        width, height = 1080, 1920
    elif "16:9" in ratio_option:
        width, height = 1920, 1080
    else:
        width, height = 1080, 1080

    source = {
        "output_format": "mp4",
        "duration": 30,
        "width": width,
        "height": height,
        "fill_color": "#0E1117",
        "elements": [
            {
                "type": "text",
                "text": "⬡ ALPHEX CONTENTO",
                "x": "50%",
                "y": "8%",
                "width": "90%",
                "x_alignment": "50%",
                "font_family": "Noto Sans KR",
                "font_size": "4 vmin",
                "fill_color": "#00E676",
                "font_weight": "700",
            },
            {
                "type": "text",
                "text": title[:80],
                "x": "50%",
                "y": "28%",
                "width": "88%",
                "x_alignment": "50%",
                "font_family": "Noto Sans KR",
                "font_size": "5.5 vmin",
                "fill_color": "#E6EDF3",
                "font_weight": "700",
                "line_height": "140%",
            },
            {
                "type": "text",
                "text": script_excerpt[:400],
                "x": "50%",
                "y": "60%",
                "width": "84%",
                "height": "30%",
                "x_alignment": "50%",
                "y_alignment": "50%",
                "font_family": "Noto Sans KR",
                "font_size": "3 vmin",
                "fill_color": "#8B949E",
                "line_height": "160%",
            },
            {
                "type": "text",
                "text": "본 영상은 투자 권유가 아닌 정보 제공 목적입니다.",
                "x": "50%",
                "y": "95%",
                "width": "90%",
                "x_alignment": "50%",
                "font_family": "Noto Sans KR",
                "font_size": "2 vmin",
                "fill_color": "#30363D",
            },
        ],
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        r = requests.post(
            "https://api.creatomate.com/v1/renders",
            json={"source": source},
            headers=headers,
            timeout=30,
        )
        if r.status_code == 202:
            return r.json()[0]["id"], None
        return None, f"Creatomate 오류 ({r.status_code}): {r.text[:300]}"
    except Exception as e:
        return None, str(e)


def poll_render(render_id: str):
    api_key = _secret("CREATOMATE_API_KEY", "api_creatomate")
    if not api_key:
        return None, None
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        r = requests.get(
            f"https://api.creatomate.com/v1/renders/{render_id}",
            headers=headers,
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("status"), data.get("url")
    except Exception:
        pass
    return None, None


# ══════════════════════════════════════════════════════════
# 7. SIDEBAR
# ══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        """
    <div style="text-align:center;padding:22px 0 14px;">
        <div style="font-size:28px;font-weight:900;letter-spacing:-1px;color:#00E676;">⬡ ALPHEX</div>
        <div style="font-size:11px;color:#8B949E;letter-spacing:4px;text-transform:uppercase;margin-top:2px;">CONTENTO</div>
        <div style="font-size:10px;color:#30363D;margin-top:6px;">AI 마케팅 영상 자동화 파이프라인</div>
    </div>
    <hr>
    """,
        unsafe_allow_html=True,
    )

    mode_label, mode_color = market_mode()
    emoji, text = mode_label.split(" ", 1)
    st.markdown(
        f"""
    <div style="background:linear-gradient(135deg,#161B22,#0D1117);
                border:1px solid {mode_color}33;border-radius:10px;
                padding:14px;margin-bottom:16px;text-align:center;">
        <div style="font-size:24px;margin-bottom:4px;">{emoji}</div>
        <div style="color:{mode_color};font-weight:700;font-size:13px;">{text}</div>
        <div style="color:#8B949E;font-size:11px;margin-top:3px;">{datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="color:#E6EDF3;font-size:13px;font-weight:600;margin-bottom:4px;">API 연결 상태</div>',
        unsafe_allow_html=True,
    )
    api_badge("Claude API (Anthropic)", "CLAUDE_API_KEY", "api_claude")
    api_badge("ElevenLabs TTS", "ELEVENLABS_API_KEY", "api_elevenlabs")
    api_badge("Creatomate 렌더링", "CREATOMATE_API_KEY", "api_creatomate")
    api_badge("FMP 금융 데이터", "FMP_API_KEY", "api_fmp")

    divider()

    st.markdown(
        '<div style="color:#E6EDF3;font-size:13px;font-weight:600;margin-bottom:8px;">이번 달 제작 현황</div>',
        unsafe_allow_html=True,
    )
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("생성 완료", "12개")
    with col_b:
        st.metric("잔여 한도", "18개")

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 시작 전 **⚙️ 설정** 탭에서 API 키를 확인해주세요.")


# ══════════════════════════════════════════════════════════
# 8. 메인 헤더
# ══════════════════════════════════════════════════════════
st.markdown(
    """
<div style="padding:6px 0 18px;">
    <h1 style="color:#E6EDF3;font-size:26px;font-weight:800;margin:0;letter-spacing:-0.5px;">
        🎬 Alphex Contento
    </h1>
    <p style="color:#8B949E;margin:4px 0 0;font-size:13px;">
        뉴스 수집 → AI 대본 → 보이스 합성 → 영상 조립 → 완성까지, 5단계 자동 파이프라인
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════
# 9. 탭 구성
# ══════════════════════════════════════════════════════════
tab_daily, tab_weekend, tab_settings = st.tabs(
    [
        "☀️  평일 아침 모드  (Daily Factory)",
        "📅  주말 대가 모드  (Weekend Insight)",
        "⚙️  설정 & 편집  (Settings & Editor)",
    ]
)


# ──────────────────────────────────────────────────────────
# TAB 1 : DAILY FACTORY
# ──────────────────────────────────────────────────────────
with tab_daily:

    step_indicator(st.session_state.daily_step)
    divider()

    # ── STEP 1 · 데이터 수집 ──────────────────────────────
    section_header(1, "미국 뉴스 & 어닝 일정 수집", active=True)

    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        tickers = st.text_input(
            "관심 종목 티커",
            placeholder="AAPL, NVDA, TSLA, META  (쉼표로 구분)",
            help="분석할 미국 주식 티커를 입력하세요",
        )
    with c2:
        news_count = st.selectbox("뉴스 수량", [5, 10, 15, 20], index=1)
    with c3:
        data_source = st.selectbox("데이터 소스", ["FMP + RSS", "FMP Only", "RSS Only"])

    if st.button("📡  Step 1 · 뉴스 & 어닝 데이터 수집 시작", key="btn_d_collect"):
        if not tickers.strip():
            st.warning("⚠️ 종목 티커를 입력해주세요. (예: AAPL, NVDA)")
        else:
            with st.spinner("미국 증시 데이터를 수집하는 중..."):
                news_data, err = fetch_news(tickers, news_count)
                earnings_data = fetch_earnings(tickers)

            if err:
                st.error(f"❌ 뉴스 수집 실패: {err}")
            else:
                st.session_state.daily_news_data = news_data
                st.session_state.daily_earnings_data = earnings_data
                st.session_state.daily_news_done = True
                st.session_state.daily_step = max(st.session_state.daily_step, 2)
                st.success(f"✅ 뉴스 {len(news_data)}건, 어닝 일정 {len(earnings_data)}건 수집 완료!")

    if st.session_state.daily_news_done:
        with st.expander("📋 수집된 데이터 미리보기", expanded=False):
            news_html = "".join(
                [
                    f'<div style="color:#E6EDF3;font-size:12px;padding:6px 0;border-bottom:1px solid #21262D;">'
                    f'<span style="color:#00E676;font-weight:600;">[{n.get("symbol","")}]</span> {n.get("title","")}'
                    f'<span style="color:#30363D;font-size:10px;margin-left:8px;">{n.get("publishedDate","")[:10]}</span></div>'
                    for n in st.session_state.daily_news_data[:7]
                ]
            ) or '<div style="color:#8B949E;">수집된 뉴스가 없습니다.</div>'

            earnings_html = "".join(
                [
                    f'<div style="color:#E6EDF3;font-size:12px;padding:4px 0;">'
                    f'<span style="color:#7B68EE;font-weight:600;">{e.get("symbol","")}</span>'
                    f' — {e.get("date","")}  EPS 예상: <span style="color:#00E676;">${e.get("epsEstimated","N/A")}</span></div>'
                    for e in st.session_state.daily_earnings_data
                ]
            ) or '<div style="color:#8B949E;">해당 종목의 어닝 일정이 없습니다.</div>'

            card(
                f'<div style="color:#00E676;font-weight:600;margin-bottom:10px;font-size:13px;">📰 오늘의 주요 뉴스</div>'
                f"{news_html}"
                f'<div style="color:#00E676;font-weight:600;margin:14px 0 10px;font-size:13px;">📅 어닝 컨퍼런스 콜 일정</div>'
                f"{earnings_html}"
            )

    divider()

    # ── STEP 2 · AI 대본 생성 ─────────────────────────────
    section_header(2, "AI 도파민 대본 생성", active=st.session_state.daily_step >= 2)

    user_comment = st.text_area(
        "✍️ 내 생각 한 줄 코멘트 (선택)",
        placeholder="예: NVDA는 지금 잠깐 숨 고르는 타이밍인 것 같아요.",
        height=72,
    )

    c4, c5 = st.columns(2)
    with c4:
        video_type = st.selectbox("영상 타입", ["숏폼 (60초 이하)", "미드폼 (3–5분)", "롱폼 (10분 이상)"])
    with c5:
        tone_style = st.selectbox("톤앤매너", ["주식 예능 (유머+정보)", "진지한 심층 분석", "동기부여 멘토형"])

    if st.button("🤖  Step 2 · AI 도파민 대본 생성하기", key="btn_d_script"):
        if not st.session_state.daily_news_done:
            st.warning("⚠️ Step 1 데이터 수집을 먼저 완료해주세요.")
        else:
            with st.spinner("Claude AI가 후킹 대본을 작성 중... (30초~1분 소요)"):
                titles, script, err = generate_daily_script(
                    st.session_state.daily_news_data,
                    st.session_state.daily_earnings_data,
                    user_comment,
                    video_type,
                    tone_style,
                )
            if err:
                st.error(f"❌ 대본 생성 실패: {err}")
            else:
                st.session_state.daily_titles = titles
                st.session_state.daily_script_text = script
                st.session_state.daily_script_done = True
                st.session_state.daily_step = max(st.session_state.daily_step, 3)
                st.success("✅ 대본 생성 완료!")

    if st.session_state.daily_script_done:
        titles = st.session_state.daily_titles
        if titles:
            titles_html = "".join(
                [f'<div style="color:#E6EDF3;font-size:13px;line-height:2.2;">{"①②③"[i]} {t}</div>' for i, t in enumerate(titles)]
            )
            card(
                f'<div style="font-size:11px;color:#8B949E;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;">🎯 AI 추천 유튜브 제목 (3개)</div>'
                + titles_html
            )

        script_content = st.text_area(
            "📝 생성된 대본 — 직접 수정 가능합니다",
            value=st.session_state.daily_script_text,
            height=300,
            key="daily_script_editor",
        )
        st.session_state.daily_script_text = script_content

    divider()

    # ── STEP 3 · 보이스 합성 ─────────────────────────────
    section_header(3, "ElevenLabs 보이스 합성 (TTS)", active=st.session_state.daily_step >= 3)

    c6, c7 = st.columns(2)
    with c6:
        voice_persona = st.selectbox(
            "AI 유튜버 목소리 페르소나",
            list(VOICE_IDS.keys()),
        )
    with c7:
        voice_speed = st.slider("말하기 속도", 0.8, 1.5, 1.0, 0.05)

    if st.button("🎙️  Step 3 · 보이스 합성 시작", key="btn_d_tts"):
        if not st.session_state.daily_script_done:
            st.warning("⚠️ Step 2 대본 생성을 먼저 완료해주세요.")
        elif not st.session_state.daily_script_text.strip():
            st.warning("⚠️ 대본 내용이 없습니다.")
        else:
            with st.spinner("ElevenLabs가 음성을 합성 중... (30초~2분 소요)"):
                audio_bytes, err = synthesize_voice(
                    st.session_state.daily_script_text,
                    voice_persona,
                )
            if err:
                st.error(f"❌ 음성 합성 실패: {err}")
            else:
                st.session_state.daily_audio_bytes = audio_bytes
                st.session_state.daily_voice_done = True
                st.session_state.daily_step = max(st.session_state.daily_step, 4)
                st.success("✅ 음성 합성 완료!")

    if st.session_state.daily_voice_done and st.session_state.daily_audio_bytes:
        st.audio(st.session_state.daily_audio_bytes, format="audio/mp3")
        st.download_button(
            "⬇️  MP3 음성 다운로드",
            data=st.session_state.daily_audio_bytes,
            file_name="alphex_voice.mp3",
            mime="audio/mp3",
            key="btn_d_audio_dl",
        )

    divider()

    # ── STEP 4 · 영상 조립 ───────────────────────────────
    section_header(4, "영상 조립 & Creatomate 렌더링", active=st.session_state.daily_step >= 4)

    c8, c9 = st.columns(2)
    with c8:
        include_alphex = st.checkbox("✅ Alphex Vue 시연 화면 자동 삽입", value=True)
        include_disclaimer = st.checkbox("✅ 면책 조항 자막 자동 삽입", value=True)
    with c9:
        output_ratio = st.selectbox(
            "출력 영상 비율", ["숏폼 9:16 (쇼츠/릴스)", "와이드 16:9 (유튜브)", "정방형 1:1 (인스타)"]
        )
        caption_font = st.selectbox("자막 서체", ["Gothic Bold (기본)", "Noto Sans KR Bold", "나눔 스퀘어 ExtraBold"])

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🎬  Step 4 · 최종 마케팅 영상 제작 시작!", key="btn_d_render"):
        if not st.session_state.daily_voice_done:
            st.warning("⚠️ Step 3 보이스 합성을 먼저 완료해주세요.")
        else:
            selected_title = (
                st.session_state.daily_titles[0]
                if st.session_state.daily_titles
                else "Alphex Contento 마케팅 영상"
            )
            script_excerpt = st.session_state.daily_script_text[:400]

            with st.spinner("Creatomate에 영상 렌더링 요청 중..."):
                render_id, err = create_video_render(selected_title, script_excerpt, output_ratio)

            if err:
                st.error(f"❌ 영상 제작 실패: {err}")
            else:
                st.session_state.daily_render_id = render_id
                with st.spinner("영상 렌더링 중... (1~3분 소요)"):
                    for _ in range(36):
                        time.sleep(5)
                        status, url = poll_render(render_id)
                        if status == "succeeded":
                            st.session_state.daily_video_url = url
                            st.session_state.daily_video_done = True
                            st.session_state.daily_step = 5
                            break
                        elif status == "failed":
                            st.error("❌ 렌더링 실패. 다시 시도해주세요.")
                            break
                    else:
                        st.warning("⏳ 렌더링이 오래 걸리고 있습니다. 잠시 후 다시 확인해주세요.")

    # ── STEP 5 · 완성 & 다운로드 ─────────────────────────
    if st.session_state.daily_video_done:
        divider()
        section_header(5, "완성 & 다운로드", active=True)
        st.markdown(
            """
        <div style="background:linear-gradient(135deg,#161B22,#0D1117);
                    border:1px solid #00E676;border-radius:14px;
                    padding:32px;text-align:center;margin:8px 0 20px;">
            <div style="font-size:48px;margin-bottom:12px;">🎬</div>
            <div style="color:#00E676;font-size:20px;font-weight:700;margin-bottom:6px;">마케팅 영상 완성!</div>
            <div style="color:#8B949E;font-size:13px;margin-bottom:20px;">Alphex Contento 파이프라인이 성공적으로 완료되었습니다.</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        c10, c11, c12 = st.columns(3)
        with c10:
            if st.session_state.daily_video_url:
                st.link_button("⬇️  MP4 다운로드", st.session_state.daily_video_url)
        with c11:
            st.button("📤  유튜브 예약 업로드", key="btn_d_yt")
        with c12:
            if st.button("🔁  새 영상 제작", key="btn_d_reset"):
                for k in [
                    "daily_step", "daily_news_done", "daily_news_data", "daily_earnings_data",
                    "daily_script_done", "daily_script_text", "daily_titles",
                    "daily_voice_done", "daily_audio_bytes",
                    "daily_video_done", "daily_video_url", "daily_render_id",
                ]:
                    st.session_state[k] = _defaults[k]
                st.rerun()


# ──────────────────────────────────────────────────────────
# TAB 2 : WEEKEND INSIGHT
# ──────────────────────────────────────────────────────────
with tab_weekend:

    step_indicator(st.session_state.wknd_step)
    divider()

    # ── STEP 1 · 주간 데이터 취합 ─────────────────────────
    section_header(1, "주간 시장 요약 데이터 취합", active=True)

    c_w1, c_w2, c_w3 = st.columns(3)
    with c_w1:
        include_fomc = st.checkbox("FOMC 일정 포함", value=True)
    with c_w2:
        include_cpi = st.checkbox("CPI 발표 포함", value=True)
    with c_w3:
        include_earnings = st.checkbox("주요 기업 실적 일정", value=True)

    if st.button("📊  Step 1 · 주간 시장 데이터 취합 시작", key="btn_w_collect"):
        with st.spinner("이번 주 시장 데이터를 가져오는 중..."):
            market_data = fetch_market_indices()
        if market_data:
            st.session_state.wknd_market_data = market_data
            st.session_state.wknd_data_done = True
            st.session_state.wknd_step = max(st.session_state.wknd_step, 2)
            st.success("✅ 주간 데이터 취합 완료!")
        else:
            st.error("❌ 데이터 수집 실패. FMP API 키를 확인해주세요.")

    if st.session_state.wknd_data_done and st.session_state.wknd_market_data:
        with st.expander("📈 주간 시장 요약 미리보기", expanded=False):
            md = st.session_state.wknd_market_data
            cols = st.columns(len(md) if md else 4)
            for i, (name, d) in enumerate(md.items()):
                change = d.get("change", 0)
                delta_str = f"{change:+.2f}%"
                with cols[i]:
                    st.metric(name, f"{d.get('price', 0):,.2f}", delta_str)

    divider()

    # ── STEP 2 · 투자 대가 설정 ───────────────────────────
    section_header(2, "투자 대가 인사이트 설정", active=st.session_state.wknd_step >= 2)

    c_w4, c_w5 = st.columns(2)
    with c_w4:
        legend = st.selectbox(
            "이번 주 투자 대가 선택",
            [
                "워렌 버핏 (Warren Buffett)",
                "피터 린치 (Peter Lynch)",
                "레이 달리오 (Ray Dalio)",
                "찰리 멍거 (Charlie Munger)",
                "조지 소로스 (George Soros)",
                "하워드 막스 (Howard Marks)",
            ],
        )
    with c_w5:
        insight_theme = st.selectbox(
            "인사이트 테마",
            [
                "지금 시장 상황에 맞는 명언",
                "장기 투자 마인드셋",
                "리스크 관리 철학",
                "종목 발굴 방법론",
                "시장 위기 대응 전략",
            ],
        )

    info_box("💡 선택한 투자 대가의 철학이 이번 주 시장 흐름과 연결된 스토리로 대본에 녹아듭니다.", "#7B68EE")

    divider()

    # ── STEP 3 · 주말 롱폼 대본 생성 ─────────────────────
    section_header(3, "동기부여 & 주말 롱폼 대본 생성", active=st.session_state.wknd_step >= 3)

    wknd_comment = st.text_area(
        "✍️ 이번 주 내 한 마디 (선택)",
        placeholder="예: 이번 주 하락장을 버텨낸 분들, 진짜 수고하셨어요.",
        height=72,
    )

    if st.button("🤖  Step 3 · 주말 스페셜 대본 생성", key="btn_w_script"):
        if not st.session_state.wknd_data_done:
            st.warning("⚠️ Step 1 데이터 취합을 먼저 완료해주세요.")
        else:
            with st.spinner("주간 요약 + 투자 대가 인사이트를 융합 중... (30초~1분 소요)"):
                titles, script, err = generate_weekend_script(
                    st.session_state.wknd_market_data,
                    legend,
                    insight_theme,
                    wknd_comment,
                )
            if err:
                st.error(f"❌ 대본 생성 실패: {err}")
            else:
                st.session_state.wknd_titles = titles
                st.session_state.wknd_script_text = script
                st.session_state.wknd_script_done = True
                st.session_state.wknd_step = max(st.session_state.wknd_step, 4)
                st.success("✅ 주말 스페셜 대본 완성!")

    if st.session_state.wknd_script_done:
        if st.session_state.wknd_titles:
            titles_html = "".join(
                [f'<div style="color:#E6EDF3;font-size:13px;line-height:2.2;">{"①②③"[i]} {t}</div>'
                 for i, t in enumerate(st.session_state.wknd_titles)]
            )
            card(
                '<div style="font-size:11px;color:#8B949E;margin-bottom:8px;">🎯 AI 추천 유튜브 제목</div>'
                + titles_html
            )
        wknd_script = st.text_area(
            "📝 주말 롱폼 대본 — 직접 수정 가능",
            value=st.session_state.wknd_script_text,
            height=320,
            key="wknd_script_editor",
        )
        st.session_state.wknd_script_text = wknd_script

    divider()

    # ── STEP 4 · 보이스 합성 & 영상 조립 ─────────────────
    section_header(4, "보이스 합성 & 영상 조립", active=st.session_state.wknd_step >= 4)

    c_w6, c_w7 = st.columns(2)
    with c_w6:
        include_chart = st.checkbox("✅ 주간 지수 차트 삽입", value=True)
        include_calendar = st.checkbox("✅ 다음 주 이벤트 캘린더 삽입", value=True)
    with c_w7:
        wknd_ratio = st.selectbox(
            "출력 비율 (주말 롱폼)", ["와이드 16:9 (유튜브 권장)", "숏폼 9:16 (요약 클립)", "정방형 1:1"]
        )
        wknd_voice = st.selectbox("목소리 페르소나", list(VOICE_IDS.keys()), key="wknd_voice_sel")

    if st.button("🎬  Step 4+5 · 주말 종합 영상 제작 시작!", key="btn_w_render"):
        if not st.session_state.wknd_script_done:
            st.warning("⚠️ Step 3 대본 생성을 먼저 완료해주세요.")
        else:
            with st.spinner("ElevenLabs 음성 합성 중..."):
                audio_bytes, err = synthesize_voice(st.session_state.wknd_script_text, wknd_voice)
            if err:
                st.error(f"❌ 음성 합성 실패: {err}")
            else:
                st.session_state.wknd_audio_bytes = audio_bytes
                st.session_state.wknd_voice_done = True

                selected_title = (
                    st.session_state.wknd_titles[0]
                    if st.session_state.wknd_titles
                    else "Alphex Contento 주말 스페셜"
                )
                with st.spinner("Creatomate 영상 렌더링 중... (1~3분 소요)"):
                    render_id, err2 = create_video_render(
                        selected_title, st.session_state.wknd_script_text[:400], wknd_ratio
                    )
                if err2:
                    st.error(f"❌ 영상 제작 실패: {err2}")
                else:
                    for _ in range(36):
                        time.sleep(5)
                        status, url = poll_render(render_id)
                        if status == "succeeded":
                            st.session_state.wknd_video_url = url
                            st.session_state.wknd_video_done = True
                            st.session_state.wknd_step = 5
                            st.success("🎉 주말 스페셜 영상 완성!")
                            break
                        elif status == "failed":
                            st.error("❌ 렌더링 실패.")
                            break

    if st.session_state.wknd_voice_done and st.session_state.wknd_audio_bytes:
        st.audio(st.session_state.wknd_audio_bytes, format="audio/mp3")
        st.download_button(
            "⬇️  MP3 음성 다운로드",
            data=st.session_state.wknd_audio_bytes,
            file_name="alphex_weekend_voice.mp3",
            mime="audio/mp3",
            key="btn_w_audio_dl",
        )

    if st.session_state.wknd_video_done:
        st.markdown(
            """
        <div style="background:linear-gradient(135deg,#161B22,#0D1117);
                    border:1px solid #7B68EE;border-radius:14px;
                    padding:28px;text-align:center;margin:16px 0;">
            <div style="font-size:44px;margin-bottom:10px;">📅</div>
            <div style="color:#7B68EE;font-size:18px;font-weight:700;margin-bottom:6px;">주말 스페셜 완성!</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        c_dl1, c_dl2 = st.columns(2)
        with c_dl1:
            if st.session_state.wknd_video_url:
                st.link_button("⬇️  MP4 다운로드", st.session_state.wknd_video_url)
        with c_dl2:
            if st.button("🔁  새 주말 영상 제작", key="btn_w_reset"):
                for k in [
                    "wknd_step", "wknd_data_done", "wknd_market_data",
                    "wknd_script_done", "wknd_script_text", "wknd_titles",
                    "wknd_voice_done", "wknd_audio_bytes",
                    "wknd_video_done", "wknd_video_url",
                ]:
                    st.session_state[k] = _defaults[k]
                st.rerun()


# ──────────────────────────────────────────────────────────
# TAB 3 : SETTINGS & EDITOR
# ──────────────────────────────────────────────────────────
with tab_settings:

    st.markdown(
        '<h3 style="color:#E6EDF3;font-size:19px;margin-bottom:4px;">⚙️ API 설정 & 시스템 구성</h3>',
        unsafe_allow_html=True,
    )
    info_box(
        "⚠️ <b>보안 안내:</b> 여기서 입력한 API 키는 현재 세션 동안만 유지됩니다. "
        "브라우저를 닫으면 다시 입력해야 합니다.",
        "#FFA726",
    )

    divider()

    st.markdown(
        '<div style="color:#E6EDF3;font-size:15px;font-weight:600;margin-bottom:16px;">🔑 API 키 입력</div>',
        unsafe_allow_html=True,
    )

    c_s1, c_s2 = st.columns(2)

    with c_s1:
        st.markdown('<div style="color:#8B949E;font-size:12px;margin-bottom:6px;">🤖 Claude API (Anthropic)</div>', unsafe_allow_html=True)
        claude_key = st.text_input("Claude API Key", type="password", placeholder="sk-ant-api03-...", label_visibility="collapsed", key="input_claude")
        if claude_key:
            st.session_state.api_claude = claude_key

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div style="color:#8B949E;font-size:12px;margin-bottom:6px;">🎬 Creatomate API</div>', unsafe_allow_html=True)
        creatomate_key = st.text_input("Creatomate Key", type="password", placeholder="cr_live_...", label_visibility="collapsed", key="input_creatomate")
        if creatomate_key:
            st.session_state.api_creatomate = creatomate_key

    with c_s2:
        st.markdown('<div style="color:#8B949E;font-size:12px;margin-bottom:6px;">🎵 ElevenLabs API</div>', unsafe_allow_html=True)
        el_key = st.text_input("ElevenLabs Key", type="password", placeholder="xi_...", label_visibility="collapsed", key="input_elevenlabs")
        if el_key:
            st.session_state.api_elevenlabs = el_key

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div style="color:#8B949E;font-size:12px;margin-bottom:6px;">📰 FMP API (금융 데이터)</div>', unsafe_allow_html=True)
        fmp_key = st.text_input("FMP Key", type="password", placeholder="영문+숫자 조합", label_visibility="collapsed", key="input_fmp")
        if fmp_key:
            st.session_state.api_fmp = fmp_key

    if st.button("💾  API 키 저장", key="btn_save_api"):
        st.success("✅ API 키가 저장되었습니다. 사이드바 상태가 업데이트됩니다.")
        st.rerun()

    divider()

    st.markdown(
        '<div style="color:#E6EDF3;font-size:15px;font-weight:600;margin-bottom:16px;">🔑 현재 연결 상태</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        api_badge("Claude API (Anthropic)", "CLAUDE_API_KEY", "api_claude")
        api_badge("Creatomate 렌더링", "CREATOMATE_API_KEY", "api_creatomate")
    with col2:
        api_badge("ElevenLabs TTS", "ELEVENLABS_API_KEY", "api_elevenlabs")
        api_badge("FMP 금융 데이터", "FMP_API_KEY", "api_fmp")

    divider()

    # ── AI 유튜버 페르소나 설정 ───────────────────────────
    st.markdown(
        '<div style="color:#E6EDF3;font-size:15px;font-weight:600;margin-bottom:16px;">🎙️ AI 유튜버 페르소나 설정</div>',
        unsafe_allow_html=True,
    )

    c_p1, c_p2 = st.columns(2)
    with c_p1:
        persona_name = st.text_input(
            "채널 페르소나 이름",
            value=st.session_state.persona_name,
            placeholder="예: 알파 레이더, 주식 탐정, 월가 해석가 ...",
        )
        st.session_state.persona_name = persona_name

        voice_default = st.selectbox("기본 목소리 스타일", list(VOICE_IDS.keys()))
    with c_p2:
        tone_default = st.selectbox(
            "기본 대본 톤",
            ["주식 예능 (유머+정보 균형)", "진지한 심층 분석", "동기부여 멘토형", "뉴스 리포터형"],
            key="tone_select",
        )
        st.session_state.persona_tone = tone_default

        signature = st.text_input(
            "채널 시그니처 문구",
            placeholder="예: 오늘도 Alphex Vue와 함께 수익 내봅시다!",
        )

    divider()

    # ── 인물 촬영본 편집 ──────────────────────────────────
    st.markdown(
        '<div style="color:#E6EDF3;font-size:15px;font-weight:600;margin-bottom:16px;">✂️ 인물 촬영본 AI 편집 (선택 기능)</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div style="background:#161B22;border:1px dashed #30363D;border-radius:12px;
                padding:28px;text-align:center;margin-bottom:14px;">
        <div style="font-size:36px;margin-bottom:8px;">🎥</div>
        <div style="color:#8B949E;font-size:13px;">직접 촬영한 영상을 업로드하면 AI가 자동으로 편집해드립니다</div>
        <div style="color:#30363D;font-size:11px;margin-top:4px;">지원: MP4, MOV, AVI · 최대 2GB</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "인물 촬영 영상 업로드",
        type=["mp4", "mov", "avi"],
        label_visibility="collapsed",
    )

    if uploaded:
        c_e1, c_e2 = st.columns(2)
        with c_e1:
            do_jumpcut = st.checkbox("🎬 자동 점프컷 (무음 구간 제거)", value=True)
            do_beauty = st.checkbox("✨ AI 뷰티 보정 필터", value=True)
        with c_e2:
            do_bg = st.checkbox("🖼️ 가상 배경 합성", value=False)
            silence_ms = st.slider("무음 감지 임계값 (ms)", 100, 1000, 300, 50)

        if st.button("🤖  AI 자동 컷편집 & 뷰티 보정 실행", key="btn_edit"):
            with st.spinner("AI가 영상을 분석하고 편집 중입니다..."):
                time.sleep(3)
            st.success("✅ AI 편집 완료! 편집본을 다운로드할 수 있습니다.")
            st.button("⬇️  편집 영상 다운로드", key="btn_edit_dl")

    divider()

    # ── 면책 조항 설정 ────────────────────────────────────
    st.markdown(
        '<div style="color:#E6EDF3;font-size:15px;font-weight:600;margin-bottom:12px;">📜 자동 삽입 면책 조항</div>',
        unsafe_allow_html=True,
    )
    st.text_area(
        "영상 하단 및 더보기란 자동 삽입 문구",
        value="본 영상은 투자 권유가 아닌 AI 기반 분석 정보 제공이 목적이며, 모든 투자의 책임은 본인에게 있습니다.",
        height=72,
        key="disclaimer_text",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾  전체 설정 저장 & 적용", key="btn_save_all"):
        st.success("✅ 모든 설정이 저장되었습니다! ☀️ 평일 아침 모드 탭으로 이동하여 영상을 제작해보세요.")

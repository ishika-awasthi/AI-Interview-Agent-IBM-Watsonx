"""
AI Interview Trainer — Streamlit UI.

Usage:
    streamlit run app.py

Requires a .env file in the project root with:
    WATSONX_API_KEY=<your IBM Cloud IAM API key>
    WATSONX_PROJECT_ID=<your WatsonX project UUID>
    WATSONX_URL=https://us-south.ml.cloud.ibm.com
"""

import html
import json
import logging
import re

import streamlit as st
from dotenv import load_dotenv

from models.watsonx_client import build_client, generate
from utils.text_utils import clean_response
from prompts.interview_prompt import (
    build_question_prompt,
    build_evaluation_prompt,
)

load_dotenv()

logger = logging.getLogger(__name__)

# ── page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Interview Trainer",
    page_icon="🎓",
    layout="wide",
)

# ── global styling ─────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;900&family=Inter:wght@300;400;500;600&display=swap');

    /* ── CSS Variables ─────────────────────────────────────────── */
    :root {
        --bg-base:    #030c16;
        --bg-surface: #071b28;
        --bg-card:    rgba(255,255,255,0.05);
        --border:     rgba(56,189,248,0.18);
        --ocean:      #38bdf8;
        --ocean-deep: #0891b2;
        --ocean-glow: rgba(8,145,178,0.45);
        --neon:       #67e8f9;
        --text:       #e2e8f0;
        --text-soft:  #94a3b8;
        --text-muted: #64748b;
        --green:      #34d399;
        --amber:      #fbbf24;
        --red:        #f87171;
        --success-bg: rgba(52,211,153,0.12);
        --warn-bg:    rgba(251,191,36,0.12);
        --info-bg:    rgba(56,189,248,0.12);
    }

    /* ── Reset & Base ───────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: var(--bg-base) !important;
        color: var(--text) !important;
    }
    h1,h2,h3,h4,h5 { font-family: 'Poppins', sans-serif; color: var(--text) !important; }

    .stApp {
        background: radial-gradient(ellipse at 20% 0%, rgba(8,145,178,0.15) 0%, transparent 60%),
                    radial-gradient(ellipse at 80% 100%, rgba(14,165,233,0.10) 0%, transparent 60%),
                    var(--bg-base) !important;
        min-height: 100vh;
    }

    /* Streamlit text overrides */
    .stApp p, .stApp span, .stApp label, .stApp li,
    .stApp .stMarkdown, .stMarkdown p, .stCaption,
    [data-testid="stCaptionContainer"] p {
        color: var(--text) !important;
    }

    /* Hide Streamlit chrome */
    #MainMenu, footer, header { visibility: hidden; }

    /* ── Animated Hero ─────────────────────────────────────────── */
    @keyframes gradientShift {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes fadeSlideDown {
        from { opacity: 0; transform: translateY(-18px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(12px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 20px var(--ocean-glow), 0 0 60px rgba(8,145,178,0.2); }
        50%       { box-shadow: 0 0 35px var(--ocean-glow), 0 0 90px rgba(8,145,178,0.35); }
    }
    @keyframes shimmer {
        0%   { background-position: -200% center; }
        100% { background-position: 200% center; }
    }
    @keyframes scoreReveal {
        from { opacity: 0; transform: scale(0.85); }
        to   { opacity: 1; transform: scale(1); }
    }

    .app-hero {
        background: linear-gradient(270deg, #0c4a6e, #0891b2, #06b6d4, #0ea5e9, #0c4a6e);
        background-size: 400% 400%;
        animation: gradientShift 8s ease infinite, fadeSlideDown 0.6s ease both;
        border-radius: 20px;
        padding: 32px 36px;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 22px;
        border: 1px solid rgba(56,189,248,0.3);
        position: relative;
        overflow: hidden;
    }
    .app-hero::before {
        content: '';
        position: absolute; inset: 0;
        background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, transparent 60%);
        pointer-events: none;
    }
    .app-hero .hero-icon { font-size: 52px; line-height: 1; filter: drop-shadow(0 4px 12px rgba(0,0,0,0.4)); }
    .app-hero .hero-title { font-size: 30px; font-weight: 900; color: #fff !important; margin: 0; letter-spacing: -0.5px; }
    .app-hero .hero-sub   { font-size: 14px; color: rgba(255,255,255,0.82) !important; margin-top: 4px; }
    .hero-badge {
        display: inline-flex; align-items: center; gap: 6px;
        background: rgba(255,255,255,0.15);
        border: 1px solid rgba(255,255,255,0.25);
        border-radius: 20px; padding: 4px 12px;
        font-size: 12px; font-weight: 600; color: #fff !important;
        margin-top: 10px; backdrop-filter: blur(4px);
    }

    /* ── Stepper ────────────────────────────────────────────────── */
    .stepper { display: flex; gap: 6px; margin: 20px 0 4px 0; animation: fadeIn 0.5s ease both; }
    .step {
        flex: 1; text-align: center; padding: 10px 6px; border-radius: 12px;
        font-size: 12px; font-weight: 600;
        color: var(--text-muted) !important;
        background: var(--bg-card);
        border: 1px solid rgba(255,255,255,0.07);
        backdrop-filter: blur(8px);
        transition: all 0.3s ease;
    }
    .step.active {
        color: #fff !important;
        background: linear-gradient(120deg, var(--ocean-deep), #06b6d4);
        border-color: transparent;
        animation: pulse-glow 2.5s ease-in-out infinite;
    }
    .step.done {
        color: var(--green) !important;
        background: rgba(52,211,153,0.1);
        border-color: rgba(52,211,153,0.25);
    }

    /* ── Glass Cards ────────────────────────────────────────────── */
    .glass-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 24px 28px;
        backdrop-filter: blur(16px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.35);
        animation: fadeIn 0.5s ease both;
    }
    .glass-card h4 { color: var(--text) !important; font-size: 16px; font-weight: 700; margin-bottom: 10px; }

    /* ── Radio topics ───────────────────────────────────────────── */
    div[role="radiogroup"] label {
        border: 1.5px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        margin-bottom: 8px !important;
        background: rgba(255,255,255,0.04) !important;
        transition: all 0.2s ease;
        backdrop-filter: blur(8px);
    }
    div[role="radiogroup"] label p { color: var(--text) !important; font-weight: 500; }
    div[role="radiogroup"] label:hover {
        border-color: var(--ocean) !important;
        background: rgba(56,189,248,0.1) !important;
        transform: translateX(4px);
    }

    /* ── Text Area ──────────────────────────────────────────────── */
    .stTextArea textarea {
        background: rgba(255,255,255,0.05) !important;
        border: 1.5px solid rgba(56,189,248,0.25) !important;
        border-radius: 14px !important;
        color: var(--text) !important;
        font-size: 15px !important;
        line-height: 1.7 !important;
        transition: border-color 0.2s ease;
    }
    .stTextArea textarea:focus { border-color: var(--ocean) !important; }
    .stTextArea textarea::placeholder { color: var(--text-muted) !important; }
    .stTextArea label p { color: var(--text) !important; font-weight: 600; }

    /* ── Select/Number inputs ───────────────────────────────────── */
    .stSelectbox select, .stNumberInput input {
        background: rgba(255,255,255,0.06) !important;
        border: 1.5px solid rgba(56,189,248,0.25) !important;
        border-radius: 10px !important;
        color: var(--text) !important;
    }

    /* ── Buttons ────────────────────────────────────────────────── */
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        padding: 0.7rem 1.4rem !important;
        transition: all 0.2s ease !important;
        border: 1.5px solid rgba(255,255,255,0.12) !important;
        background: rgba(255,255,255,0.06) !important;
        color: var(--text) !important;
        backdrop-filter: blur(8px);
    }
    .stButton > button:hover {
        border-color: var(--ocean) !important;
        background: rgba(56,189,248,0.12) !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(8,145,178,0.25) !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--ocean-deep), #06b6d4) !important;
        border: none !important;
        color: #fff !important;
        box-shadow: 0 6px 20px rgba(8,145,178,0.4) !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 30px rgba(8,145,178,0.55) !important;
        opacity: 0.95;
    }
    .stButton > button:active { transform: scale(0.97) !important; }

    /* ── Question Card ──────────────────────────────────────────── */
    .q-card {
        background: rgba(56,189,248,0.08);
        border: 1px solid rgba(56,189,248,0.25);
        border-left: 4px solid var(--ocean);
        border-radius: 16px;
        padding: 22px 26px;
        animation: fadeIn 0.5s ease both;
        position: relative;
        overflow: hidden;
    }
    .q-card::before {
        content: '';
        position: absolute;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: linear-gradient(135deg, rgba(56,189,248,0.04) 0%, transparent 60%);
        pointer-events: none;
    }
    .q-tag {
        display: inline-flex; align-items: center; gap: 6px;
        font-size: 11px; font-weight: 700; letter-spacing: 0.06em;
        color: var(--ocean) !important;
        background: rgba(8,145,178,0.15);
        border: 1px solid rgba(8,145,178,0.3);
        border-radius: 20px; padding: 3px 12px; margin-bottom: 14px;
        text-transform: uppercase;
    }
    .q-text {
        font-size: 17px; line-height: 1.75;
        color: var(--text) !important;
        font-weight: 400;
    }

    /* ── Progress Bar ───────────────────────────────────────────── */
    .progress-wrap { margin: 16px 0 6px 0; }
    .progress-label {
        display: flex; justify-content: space-between;
        font-size: 13px; font-weight: 600;
        color: var(--text-soft) !important;
        margin-bottom: 8px;
    }
    .progress-track {
        height: 6px; border-radius: 6px;
        background: rgba(255,255,255,0.08);
        overflow: hidden;
    }
    .progress-fill {
        height: 100%; border-radius: 6px;
        background: linear-gradient(90deg, var(--ocean-deep), #06b6d4, var(--ocean));
        background-size: 200% 100%;
        animation: shimmer 2s linear infinite;
        transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* Score card rules now defined near end of stylesheet (ring-based). */

    /* ── Feedback Cards ─────────────────────────────────────────── */
    .fb-card {
        border-radius: 14px; padding: 18px 22px; margin-bottom: 12px;
        animation: fadeIn 0.5s ease both;
        border: 1px solid;
    }
    .fb-card.strengths { background: var(--success-bg); border-color: rgba(52,211,153,0.2); }
    .fb-card.weaknesses { background: var(--warn-bg); border-color: rgba(251,191,36,0.2); }
    .fb-card.ideal { background: var(--info-bg); border-color: rgba(56,189,248,0.2); }
    .fb-title { font-weight: 700; font-size: 14px; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
    .fb-body { font-size: 14.5px; line-height: 1.7; color: var(--text-soft) !important; }

    /* ── Info Panel ─────────────────────────────────────────────── */
    .info-panel {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px; padding: 22px 24px;
        font-size: 14px; line-height: 1.9;
        color: var(--text-soft) !important;
        animation: fadeIn 0.6s ease 0.2s both;
    }
    .info-panel .rule-head { font-weight: 700; font-size: 13px; color: var(--ocean) !important; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; display: block; }

    /* ── Summary Dashboard ──────────────────────────────────────── */
    .summary-header {
        text-align: center; padding: 32px 20px 24px;
        background: linear-gradient(135deg, rgba(8,145,178,0.15), rgba(14,165,233,0.08));
        border: 1px solid rgba(56,189,248,0.2); border-radius: 20px;
        margin-bottom: 24px; animation: fadeIn 0.6s ease both;
    }
    .grade-badge {
        display: inline-block;
        font-size: 72px; font-weight: 900; font-family: 'Poppins',sans-serif;
        background: linear-gradient(135deg, var(--ocean), #67e8f9);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        line-height: 1; margin-bottom: 8px;
    }
    .grade-label { font-size: 18px; color: var(--text-soft) !important; }

    .avg-bar-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; animation: fadeIn 0.5s ease both; }
    .avg-bar-label { width: 160px; font-size: 13px; font-weight: 600; color: var(--text-soft) !important; text-align: right; flex-shrink: 0; }
    .avg-bar-track { flex: 1; height: 10px; border-radius: 10px; background: rgba(255,255,255,0.08); overflow: hidden; }
    .avg-bar-fill { height: 100%; border-radius: 10px; transition: width 1s cubic-bezier(0.4,0,0.2,1); }
    .avg-bar-val { width: 42px; font-size: 13px; font-weight: 700; color: var(--text) !important; flex-shrink: 0; }

    .q-accordion {
        border: 1px solid rgba(255,255,255,0.08); border-radius: 14px;
        margin-bottom: 10px; overflow: hidden;
        animation: fadeIn 0.4s ease both;
    }
    .q-acc-header {
        display: flex; align-items: center; justify-content: space-between;
        padding: 14px 18px;
        background: rgba(255,255,255,0.04);
        cursor: pointer; font-weight: 600; font-size: 14px;
        color: var(--text) !important;
    }
    .q-acc-body { padding: 16px 18px; background: rgba(255,255,255,0.02); font-size: 14px; color: var(--text-soft) !important; }

    /* Streamlit expander dark styling */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
        color: var(--text) !important;
    }
    .streamlit-expanderContent {
        background: rgba(255,255,255,0.02) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-top: none !important;
    }

    /* Metric text override */
    [data-testid="stMetricValue"] { color: var(--text) !important; }
    [data-testid="stMetricLabel"] { color: var(--text-soft) !important; }

    /* Word count caption */
    .wc-caption { font-size: 12px; color: var(--text-muted) !important; margin-top: 4px; }

    /* ── Ocean floor backdrop ───────────────────────────────────── */
    .ocean-floor {
        position: fixed;
        left: 0; right: 0; bottom: 0;
        height: 220px;
        z-index: 0;
        opacity: 0.6;
        pointer-events: none;
    }

    /* ── Mega title ─────────────────────────────────────────────── */
    .mega-title {
        position: relative; z-index: 1;
        text-align: center;
        font-family: 'Poppins', sans-serif;
        font-weight: 900;
        font-size: 44px;
        letter-spacing: 1px;
        margin: 8px 0 2px 0;
        background: linear-gradient(90deg, var(--ocean-deep), var(--neon), var(--ocean-deep));
        background-size: 200% auto;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: shimmer 6s linear infinite;
        filter: drop-shadow(0 0 24px rgba(8,145,178,0.55));
    }
    .mega-subtitle {
        position: relative; z-index: 1;
        text-align: center;
        font-size: 13px;
        color: var(--text-soft) !important;
        margin-bottom: 4px;
        letter-spacing: 0.02em;
    }

    /* ── Ocean nav bar ──────────────────────────────────────────── */
    .ocean-nav {
        position: relative; z-index: 1;
        display: flex; align-items: center; justify-content: space-between;
        gap: 16px;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(56,189,248,0.15);
        border-radius: 16px;
        padding: 12px 22px;
        margin: 18px 0 4px 0;
        backdrop-filter: blur(14px);
        box-shadow: 0 8px 28px rgba(0,0,0,0.35);
        flex-wrap: wrap;
    }
    .nav-brand { display: flex; align-items: center; gap: 10px; }
    .nav-logo {
        width: 38px; height: 38px; border-radius: 50%;
        background: linear-gradient(135deg, var(--ocean-deep), #06b6d4);
        display: flex; align-items: center; justify-content: center;
        font-size: 17px; flex-shrink: 0;
        box-shadow: 0 0 16px rgba(8,145,178,0.55);
    }
    .nav-title-line {
        font-family: 'Poppins', sans-serif; font-weight: 700;
        font-size: 12px; line-height: 1.25;
        color: #fff !important; letter-spacing: 0.03em;
    }
    .nav-links { display: flex; align-items: center; gap: 22px; flex-wrap: wrap; }
    .nav-link {
        font-size: 13px; font-weight: 600;
        color: var(--text-muted) !important;
        padding-bottom: 4px;
        border-bottom: 2px solid transparent;
        transition: all 0.2s ease;
    }
    .nav-link.active { color: var(--ocean) !important; border-bottom-color: var(--ocean); }
    .nav-link.done { color: var(--green) !important; }
    .nav-user { display: flex; align-items: center; gap: 10px; }
    .nav-avatar {
        width: 30px; height: 30px; border-radius: 50%;
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(56,189,248,0.3);
        display: flex; align-items: center; justify-content: center;
        font-size: 12px; font-weight: 700;
        color: var(--ocean) !important;
    }
    .nav-username { font-size: 13px; font-weight: 600; color: var(--text-soft) !important; }
    .nav-bell { font-size: 14px; opacity: 0.8; }

    /* ── Page shell (wraps all main content in one rounded card) ─── */
    .block-container {
        position: relative; z-index: 1;
        border: 1px solid rgba(56,189,248,0.12);
        border-radius: 26px;
        padding: 28px 34px 34px !important;
        background: rgba(255,255,255,0.015);
        box-shadow: 0 24px 70px rgba(0,0,0,0.45);
    }

    /* ── Score rings ────────────────────────────────────────────── */
    .score-grid { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 8px; }
    .score-card {
        flex: 1; min-width: 140px;
        border-radius: 18px; padding: 18px 14px;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(56,189,248,0.12);
        text-align: center;
        display: flex; flex-direction: column; align-items: center; gap: 10px;
        animation: scoreReveal 0.5s ease both;
    }
    .score-ring-label {
        font-size: 11px; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.05em; color: var(--text-soft) !important;
    }
    .ring-wrap { position: relative; width: 100px; height: 100px; }
    .score-ring { width: 100px; height: 100px; transform: rotate(-90deg); }
    .ring-bg { fill: none; stroke: rgba(255,255,255,0.08); stroke-width: 9; }
    .ring-fill {
        fill: none; stroke-width: 9; stroke-linecap: round;
        transition: stroke-dashoffset 1s cubic-bezier(0.4,0,0.2,1);
    }
    .ring-value {
        position: absolute; inset: 0;
        display: flex; align-items: center; justify-content: center;
        font-size: 20px; font-weight: 900; font-family: 'Poppins',sans-serif;
        color: #fff !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── helpers ───────────────────────────────────────────────────────────────────


def safe_html(text: str) -> str:
    """Escape model-generated text for safe embedding in HTML blocks."""
    return html.escape(text or "").replace("\n", "<br>")


FEEDBACK_LABELS: list[str] = [
    "Overall Score", "Technical Accuracy", "Clarity", "Completeness",
    "Strengths", "Weaknesses", "Ideal Answer",
]


def parse_feedback(feedback: str) -> dict[str, str]:
    """Parse a structured feedback string into a label-to-value mapping.

    Scans each line for a known label prefix (e.g. ``"Overall Score:"``),
    collects the value that follows, and handles multi-line values by
    buffering continuation lines.

    Args:
        feedback: Raw text returned by the model after evaluation.

    Returns:
        A dict mapping each recognised label to its value string.
    """
    parsed: dict[str, str] = {}
    current_label: str | None = None
    buffer: list[str] = []
    for raw_line in feedback.splitlines():
        line = raw_line.strip()
        matched = False
        for lbl in FEEDBACK_LABELS:
            if line.lower().startswith(lbl.lower() + ":"):
                if current_label:
                    parsed[current_label] = " ".join(buffer).strip()
                current_label = lbl
                buffer = [line[len(lbl) + 1:].strip()]
                matched = True
                break
        if not matched and current_label and line:
            buffer.append(line)
    if current_label:
        parsed[current_label] = " ".join(buffer).strip()
    return parsed


def score_fraction(value: str) -> float:
    """Convert a score string such as ``'8/10'`` to a fraction in [0, 1].

    Accepts formats like ``'8/10'``, ``'8'``, or ``'8.5 / 10'``.
    Returns ``0.0`` when the string cannot be parsed.
    Assumes a denominator of 10 when none is present.
    """
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:/\s*(\d+(?:\.\d+)?))?", value or "")
    if not match:
        return 0.0
    num = float(match.group(1))
    denom = float(match.group(2)) if match.group(2) else 10.0
    return max(0.0, min(1.0, num / denom)) if denom else 0.0


def score_display(value: str) -> str:
    """Extract a short 'N/10'-style label from a score string for compact display.

    Model output for a score field sometimes includes trailing rationale text
    on the same line (e.g. ``'6/10 The candidate correctly identifies...'``).
    This pulls out just the leading numeric score/denominator so UI elements
    like the score ring never have to render a full sentence. Falls back to
    '—' when no numeric score can be found.
    """
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:/\s*(\d+(?:\.\d+)?))?", value or "")
    if not match:
        return "—"
    num = match.group(1)
    denom = match.group(2) or "10"
    return f"{num}/{denom}"


def score_gradient(fraction: float) -> str:
    """Return a CSS linear-gradient string coloured by performance tier.

    - >= 0.75 → green  (strong)
    - >= 0.50 → amber  (fair)
    - <  0.50 → red    (needs work)
    """
    if fraction >= 0.75:
        return "linear-gradient(135deg, #059669, #10b981)"
    if fraction >= 0.50:
        return "linear-gradient(135deg, #d97706, #f59e0b)"
    return "linear-gradient(135deg, #dc2626, #ef4444)"


def bar_color(fraction: float) -> str:
    """Return a CSS linear-gradient for a horizontal progress bar.

    Colour tiers mirror score_gradient (green / amber / red).
    """
    if fraction >= 0.75:
        return "linear-gradient(90deg, #059669, #34d399)"
    if fraction >= 0.50:
        return "linear-gradient(90deg, #d97706, #fbbf24)"
    return "linear-gradient(90deg, #dc2626, #f87171)"


_RING_RADIUS: int = 46
_RING_CIRCUMFERENCE: float = 2 * 3.14159265 * _RING_RADIUS  # ≈ 289.03


def ring_stops(fraction: float) -> tuple[str, str]:
    """Return ``(start_colour, end_colour)`` hex strings for the score ring gradient.

    Colour tiers mirror score_gradient (green / amber / red).
    """
    if fraction >= 0.75:
        return "#059669", "#34d399"
    if fraction >= 0.50:
        return "#d97706", "#fbbf24"
    return "#dc2626", "#f87171"


_ring_uid_counter: int = 0


def render_score_card(label: str, value: str, uid: str = "") -> str:
    """Render an SVG ring-score card as an HTML string.

    Generates a unique gradient ID per call to avoid SVG defs collisions
    when multiple cards are rendered on the same page.

    Args:
        label: Display label shown above the ring (e.g. ``"Overall Score"``).
        value: Raw score string (e.g. ``"8/10"``); parsed by score_fraction().
        uid:   Optional caller-supplied prefix for the gradient ID.

    Returns:
        A self-contained HTML snippet for one score card.
    """
    global _ring_uid_counter
    _ring_uid_counter += 1
    frac = score_fraction(value)
    c1, c2 = ring_stops(frac)
    grad_id = f"ringGrad{uid}{_ring_uid_counter}"
    offset = _RING_CIRCUMFERENCE * (1 - frac)
    return (
        f'<div class="score-card">'
        f'<div class="score-ring-label">{label}</div>'
        f'<div class="ring-wrap">'
        f'<svg class="score-ring" viewBox="0 0 100 100">'
        f'<defs>'
        f'<linearGradient id="{grad_id}" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="{c1}"/>'
        f'<stop offset="100%" stop-color="{c2}"/>'
        f'</linearGradient>'
        f'</defs>'
        f'<circle class="ring-bg" cx="50" cy="50" r="{_RING_RADIUS}"/>'
        f'<circle class="ring-fill" cx="50" cy="50" r="{_RING_RADIUS}" '
        f'stroke="url(#{grad_id})" '
        f'stroke-dasharray="{_RING_CIRCUMFERENCE:.2f}" '
        f'stroke-dashoffset="{offset:.2f}"/>'
        f'</svg>'
        f'<div class="ring-value">{safe_html(score_display(value))}</div>'
        f'</div>'
        f'</div>'
    )


def compute_grade(avg_overall: float) -> tuple[str, str]:
    """Return (letter_grade, message) based on avg overall score out of 10."""
    if avg_overall >= 8.5:
        return "A+", "Outstanding performance — interview-ready! 🚀"
    if avg_overall >= 7.5:
        return "A", "Excellent — very strong candidate! 🌟"
    if avg_overall >= 6.5:
        return "B+", "Great job — minor areas to polish! 💪"
    if avg_overall >= 5.5:
        return "B", "Good effort — keep practising! 📈"
    if avg_overall >= 4.5:
        return "C", "Fair start — review the weak areas! 📚"
    return "D", "Needs more preparation — don't give up! 🎯"


# ── Constants ─────────────────────────────────────────────────────────────────

TOTAL_QUESTIONS: int = 5
ANSWER_BOX_HEIGHT: int = 200

TOPIC_OPTIONS = {
    "🐍  Python": "Python",
    "🤖  Machine Learning": "Machine Learning",
    "🧑‍💼  HR & Behavioural": "HR",
    "☁️  Cloud & DevOps": "Cloud and DevOps",
    "🗄️  Data Structures & Algorithms": "Data Structures and Algorithms",
}


# ── Session-state initialisation ──────────────────────────────────────────────


def _init_state() -> None:
    """Initialise all session-state keys with their default values.

    Called once at startup; skips keys that already exist so re-runs
    after a Streamlit rerun do not reset in-progress session data.
    """
    defaults: dict[str, object] = {
        "stage": "start",
        "model": None,
        "current_q": 0,           # 1-indexed when in session
        "question": "",
        "asked_questions": [],
        "history": [],            # list of {question, answer, feedback_data}
        "feedback_data": {},
        "role": "Python",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


_init_state()

# ── Ocean floor backdrop (fixed decorative illustration) ────────────────────

st.markdown(
    """
    <div class="ocean-floor">
        <svg viewBox="0 0 1440 220" preserveAspectRatio="none" style="width:100%;height:100%;display:block;">
            <path d="M0,220 L0,150 Q100,120 180,155 T380,148 L420,220 Z" fill="#04121c" opacity="0.9"/>
            <path d="M480,220 L505,165 Q600,125 685,158 Q745,180 805,155 L850,220 Z" fill="#051826" opacity="0.85"/>
            <path d="M980,220 L1015,135 Q1110,92 1195,142 Q1258,175 1330,152 L1440,175 L1440,220 Z" fill="#04141f" opacity="0.9"/>
            <path d="M0,178 Q360,148 720,178 T1440,178 L1440,220 L0,220 Z" fill="rgba(8,145,178,0.25)"/>
            <path d="M0,196 Q360,168 720,196 T1440,196 L1440,220 L0,220 Z" fill="rgba(56,189,248,0.15)"/>
            <circle cx="220" cy="120" r="2" fill="#67e8f9" opacity="0.8"/>
            <circle cx="640" cy="100" r="1.6" fill="#38bdf8" opacity="0.7"/>
            <circle cx="980" cy="132" r="2" fill="#67e8f9" opacity="0.6"/>
            <circle cx="1240" cy="88" r="1.6" fill="#38bdf8" opacity="0.8"/>
            <circle cx="90" cy="90" r="1.4" fill="#67e8f9" opacity="0.5"/>
        </svg>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Mega title ────────────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="mega-title">AI INTERVIEW TRAINER</div>
    <div class="mega-subtitle">Powered by IBM Granite on WatsonX &nbsp;·&nbsp; 5-Question Sessions &nbsp;·&nbsp; Instant AI Feedback</div>
    """,
    unsafe_allow_html=True,
)

# ── Nav bar (brand + stage links + user) ────────────────────────────────────

_stage_order  = ["start", "question", "feedback", "summary"]
_stage_labels = ["Choose Topic", "Answer Questions", "Review Feedback", "Final Summary"]
_current_idx  = _stage_order.index(st.session_state.stage) if st.session_state.stage in _stage_order else 1

nav_links_html = ""
for i, label in enumerate(_stage_labels):
    cls = "active" if i == _current_idx else ("done" if i < _current_idx else "")
    nav_links_html += f'<span class="nav-link {cls}">{label}</span>'

st.markdown(
    f"""
    <div class="ocean-nav">
        <div class="nav-brand">
            <div class="nav-logo">🌊</div>
            <div>
                <div class="nav-title-line">AI INTERVIEW</div>
                <div class="nav-title-line">TRAINER</div>
            </div>
        </div>
        <div class="nav-links">{nav_links_html}</div>
        <div class="nav-user">
            <div class="nav-avatar">IA</div>
            <span class="nav-username">Ishika A.</span>
            <span class="nav-bell">🔔</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")


# ══════════════════════════════════════════════════════════════════════════════
# STAGE: start
# ══════════════════════════════════════════════════════════════════════════════

if st.session_state.stage == "start":
    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown(
            """
            <div class="glass-card">
                <h4>🎯 Pick your interview track</h4>
                <p style="color:var(--text-soft);font-size:14px;margin-bottom:16px;">
                    5 questions · AI-scored · Full session summary
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        display_choice = st.radio(
            "Topic", list(TOPIC_OPTIONS.keys()), label_visibility="collapsed"
        )
        role = TOPIC_OPTIONS[display_choice]
        st.write("")

        if st.button("🚀  Start Interview Session", type="primary", use_container_width=True):
            # Cache model across sessions
            if st.session_state.model is None:
                with st.spinner("🔗 Connecting to IBM WatsonX …"):
                    try:
                        st.session_state.model = build_client()
                    except ValueError:
                        st.error("⚠️ Configuration error: one or more WatsonX credentials are missing. Check your .env file.")
                        st.stop()
                    except Exception:
                        logger.exception("Unexpected error while connecting to WatsonX.")
                        st.error("⚠️ Something went wrong while connecting. Please try again.")
                        st.stop()

            with st.spinner("✨ Generating Question 1 …"):
                try:
                    prompt = build_question_prompt(role, 1, [], total=TOTAL_QUESTIONS)
                    raw = generate(st.session_state.model, prompt)
                    question = clean_response(raw) if raw else ""
                    if not question.strip():
                        st.error("⚠️ The model returned an empty response. Please wait a moment and try again.")
                    else:
                        st.session_state.question = question
                        st.session_state.role = role
                        st.session_state.current_q = 1
                        st.session_state.asked_questions = [question]
                        st.session_state.history = []
                        st.session_state.stage = "question"
                        st.rerun()
                except FileNotFoundError:
                    st.error("⚠️ A prompt template file is missing. Please contact support.")
                except RuntimeError as exc:
                    st.error(f"⚠️ {exc}")
                except Exception:
                    logger.exception("Unexpected error generating question 1.")
                    st.error("⚠️ Something went wrong. Please try again.")


    with right:
        st.markdown(
            """
            <div class="info-panel">
                <div><span class="rule-head">&#x1F4CB; Session Format</span></div>
                <div>You will answer <strong style="color:#38bdf8;">5 interview questions</strong> in sequence.
                Each is evaluated immediately by IBM Granite AI.</div>
                <br>
                <div><span class="rule-head">&#x1F4CA; Scoring Dimensions</span></div>
                <div>Each answer is graded across four dimensions:<br>
                &nbsp;&nbsp;&bull; <strong style="color:#38bdf8;">Overall Score</strong> /10<br>
                &nbsp;&nbsp;&bull; <strong style="color:#38bdf8;">Technical Accuracy</strong> /10<br>
                &nbsp;&nbsp;&bull; <strong style="color:#38bdf8;">Clarity</strong> /10<br>
                &nbsp;&nbsp;&bull; <strong style="color:#38bdf8;">Completeness</strong> /10</div>
                <br>
                <div><span class="rule-head">&#x1F3C6; Final Dashboard</span></div>
                <div>After all 5 questions you receive a full dashboard:<br>
                &nbsp;&nbsp;&bull; Average score per dimension<br>
                &nbsp;&nbsp;&bull; Overall session grade (A+ &rarr; D)<br>
                &nbsp;&nbsp;&bull; Per-question breakdown<br>
                &nbsp;&nbsp;&bull; Downloadable JSON report</div>
                <br>
                <div><span class="rule-head">&#x1F4A1; Tips</span></div>
                <div>Answer in your own words &nbsp;&middot;&nbsp; Be specific &nbsp;&middot;&nbsp; Quality &gt; length</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# STAGE: question
# ══════════════════════════════════════════════════════════════════════════════

elif st.session_state.stage == "question":
    role = st.session_state.get("role", "Python")
    q_num = st.session_state.current_q
    _q = st.session_state.get("question", "").strip()

    # ── Progress bar ──────────────────────────────────────────────
    pct = int(((q_num - 1) / TOTAL_QUESTIONS) * 100)
    st.markdown(
        f"""
        <div class="progress-wrap">
            <div class="progress-label">
                <span>Question {q_num} of {TOTAL_QUESTIONS}</span>
                <span>{pct}% complete</span>
            </div>
            <div class="progress-track">
                <div class="progress-fill" style="width:{pct}%;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not _q:
        st.error("⚠️ No question loaded — please restart the session.")
    else:
        st.markdown(
            f"""
            <div class="q-card">
                <div class="q-tag">&#x2736; {role.upper()} &nbsp;&middot;&nbsp; QUESTION {q_num}/{TOTAL_QUESTIONS}</div>
                <div class="q-text">{safe_html(_q)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    answer = st.text_area(
        "Your Answer",
        height=ANSWER_BOX_HEIGHT,
        key="answer_input",
        placeholder="Type your answer here — be specific and use your own words …",
    )

    word_count = len(answer.split()) if answer.strip() else 0
    st.markdown(f'<p class="wc-caption">&#x1F4DD; {word_count} word{"s" if word_count != 1 else ""}</p>', unsafe_allow_html=True)
    st.write("")

    col_sub, col_skip = st.columns([3, 1])
    with col_sub:
        if st.button("✅  Submit Answer", type="primary", use_container_width=True):
            if not answer.strip():
                st.warning("Please enter your answer before submitting.")
            else:
                with st.spinner(f"🤖 Evaluating your answer …"):
                    try:
                        eval_prompt = build_evaluation_prompt(role, _q, answer.strip())
                        raw_feedback = generate(st.session_state.model, eval_prompt)
                        feedback_text = clean_response(raw_feedback)
                        st.session_state.feedback_data = parse_feedback(feedback_text)
                        st.session_state.history.append({
                            "question": _q,
                            "answer": answer.strip(),
                            "feedback_data": st.session_state.feedback_data,
                        })
                        st.session_state.stage = "feedback"
                        st.rerun()
                    except FileNotFoundError:
                        st.error("⚠️ A prompt template file is missing. Please contact support.")
                    except RuntimeError as exc:
                        st.error(f"⚠️ {exc}")
                    except Exception:
                        logger.exception("Unexpected error evaluating answer for Q%s.", q_num)
                        st.error("⚠️ Something went wrong. Please try again.")

    with col_skip:
        if st.button("⏭ Skip", use_container_width=True):
            st.session_state.history.append({
                "question": _q,
                "answer": "(skipped)",
                "feedback_data": {},
            })
            # Advance to next question or summary
            next_q = q_num + 1
            if next_q > TOTAL_QUESTIONS:
                st.session_state.stage = "summary"
            else:
                with st.spinner(f"✨ Loading Question {next_q} …"):
                    try:
                        prompt = build_question_prompt(role, next_q, st.session_state.asked_questions, total=TOTAL_QUESTIONS)
                        raw = generate(st.session_state.model, prompt)
                        question = clean_response(raw)
                        st.session_state.question = question
                        st.session_state.current_q = next_q
                        st.session_state.asked_questions.append(question)
                        st.session_state.stage = "question"
                    except FileNotFoundError:
                        st.error("⚠️ A prompt template file is missing. Please contact support.")
                    except RuntimeError as exc:
                        st.error(f"⚠️ {exc}")
                    except Exception:
                        logger.exception("Unexpected error loading question %s (skip path).", next_q)
                        st.error("⚠️ Something went wrong. Please try again.")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STAGE: feedback
# ══════════════════════════════════════════════════════════════════════════════

elif st.session_state.stage == "feedback":
    role = st.session_state.get("role", "Python")
    q_num = st.session_state.current_q
    _q = st.session_state.get("question", "").strip()
    data = st.session_state.feedback_data

    # Progress bar
    pct = int((q_num / TOTAL_QUESTIONS) * 100)
    st.markdown(
        f"""
        <div class="progress-wrap">
            <div class="progress-label">
                <span>Feedback for Question {q_num} of {TOTAL_QUESTIONS}</span>
                <span>{pct}% complete</span>
            </div>
            <div class="progress-track">
                <div class="progress-fill" style="width:{pct}%;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Question recap
    st.markdown(
        f"""
        <div class="q-card">
            <div class="q-tag">&#x2736; {role.upper()} &nbsp;&middot;&nbsp; QUESTION {q_num}/{TOTAL_QUESTIONS}</div>
            <div class="q-text">{safe_html(_q)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    st.markdown("#### 📊 Your Score")

    score_labels = ["Overall Score", "Technical Accuracy", "Clarity", "Completeness"]
    cards_html = '<div class="score-grid">'
    for lbl in score_labels:
        cards_html += render_score_card(lbl, data.get(lbl, "—"))
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

    st.write("")

    # Narrative feedback
    for lbl, (icon, css_cls, color) in {
        "Strengths":    ("&#x2705;", "strengths",  "#34d399"),
        "Weaknesses":   ("&#x26A0;", "weaknesses", "#fbbf24"),
        "Ideal Answer": ("&#x1F4A1;", "ideal",      "#38bdf8"),
    }.items():
        st.markdown(
            f"""
            <div class="fb-card {css_cls}">
                <div class="fb-title" style="color:{color};">{icon} {lbl}</div>
                <div class="fb-body">{safe_html(data.get(lbl, "—"))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    next_q = q_num + 1
    if next_q > TOTAL_QUESTIONS:
        if st.button("🏁  View Final Summary", type="primary", use_container_width=True):
            st.session_state.stage = "summary"
            st.rerun()
    else:
        if st.button(f"➡️  Next Question ({next_q}/{TOTAL_QUESTIONS})", type="primary", use_container_width=True):
            with st.spinner(f"✨ Generating Question {next_q} …"):
                try:
                    prompt = build_question_prompt(
                        role, next_q, st.session_state.asked_questions, total=TOTAL_QUESTIONS
                    )
                    raw = generate(st.session_state.model, prompt)
                    question = clean_response(raw)
                    if not question.strip():
                        st.error("⚠️ The model returned an empty response. Please click Next again.")
                    else:
                        st.session_state.question = question
                        st.session_state.current_q = next_q
                        st.session_state.asked_questions.append(question)
                        st.session_state.stage = "question"
                        st.rerun()
                except FileNotFoundError:
                    st.error("⚠️ A prompt template file is missing. Please contact support.")
                except RuntimeError as exc:
                    st.error(f"⚠️ {exc}")
                except Exception:
                    logger.exception("Unexpected error generating question %s.", next_q)
                    st.error("⚠️ Something went wrong. Please try again.")


# ══════════════════════════════════════════════════════════════════════════════
# STAGE: summary
# ══════════════════════════════════════════════════════════════════════════════

elif st.session_state.stage == "summary":
    role = st.session_state.get("role", "Python")
    history = st.session_state.history

    # ── Compute averages ──────────────────────────────────────────
    score_labels = ["Overall Score", "Technical Accuracy", "Clarity", "Completeness"]
    avgs: dict[str, float] = {}
    for lbl in score_labels:
        vals = [
            score_fraction(item["feedback_data"].get(lbl, "0")) * 10
            for item in history
            if item["feedback_data"]
        ]
        avgs[lbl] = sum(vals) / len(vals) if vals else 0.0

    avg_overall = avgs.get("Overall Score", 0.0)
    grade, grade_msg = compute_grade(avg_overall)

    # ── Summary header ────────────────────────────────────────────
    st.markdown(
        f"""
        <div class="summary-header">
            <div class="grade-badge">{grade}</div>
            <div style="font-size:22px;font-weight:700;color:#e2e8f0;margin-bottom:4px;">{grade_msg}</div>
            <div class="grade-label">{role} Session &nbsp;·&nbsp; {len(history)} Questions Answered</div>
            <div style="margin-top:12px;font-size:28px;font-weight:900;font-family:'Poppins',sans-serif;
                        background:linear-gradient(135deg,#38bdf8,#67e8f9);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                {avg_overall:.1f} / 10
            </div>
            <div style="font-size:13px;color:#64748b;margin-top:4px;">Average Overall Score</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Average score bars ────────────────────────────────────────
    st.markdown("#### 📈 Average Scores by Dimension")
    for lbl in score_labels:
        val = avgs[lbl]
        frac = val / 10.0
        color = bar_color(frac)
        st.markdown(
            f"""
            <div class="avg-bar-row">
                <div class="avg-bar-label">{lbl}</div>
                <div class="avg-bar-track">
                    <div class="avg-bar-fill" style="width:{frac*100:.0f}%;background:{color};"></div>
                </div>
                <div class="avg-bar-val">{val:.1f}/10</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    # ── Per-question breakdown ────────────────────────────────────
    st.markdown("#### 🗂️ Question-by-Question Breakdown")
    for i, item in enumerate(history, start=1):
        fd = item.get("feedback_data", {})
        overall_val = fd.get("Overall Score", "—")
        frac = score_fraction(overall_val)
        color_dot = "#34d399" if frac >= 0.75 else ("#fbbf24" if frac >= 0.50 else "#f87171")

        with st.expander(
            f"Q{i}  ·  {item['question'][:80]}{'…' if len(item['question']) > 80 else ''}  —  Overall: {score_display(overall_val)}"
        ):
            if not fd:
                st.markdown('<p style="color:var(--text-muted);">(Skipped)</p>', unsafe_allow_html=True)
            else:
                # Mini score row
                mini_html = '<div class="score-grid" style="margin-bottom:14px;">'
                for lbl in score_labels:
                    mini_html += render_score_card(lbl, fd.get(lbl, "—"))
                mini_html += "</div>"
                st.markdown(mini_html, unsafe_allow_html=True)

                st.markdown("**Your Answer:**")
                st.markdown(
                    f'<p style="color:var(--text-soft);font-size:14px;line-height:1.7;">{safe_html(item.get("answer",""))}</p>',
                    unsafe_allow_html=True,
                )

                for lbl, (icon, css_cls, color) in {
                    "Strengths":    ("&#x2705;",  "strengths",  "#34d399"),
                    "Weaknesses":   ("&#x26A0;",  "weaknesses", "#fbbf24"),
                    "Ideal Answer": ("&#x1F4A1;", "ideal",      "#38bdf8"),
                }.items():
                    if fd.get(lbl):
                        st.markdown(
                            f"""
                            <div class="fb-card {css_cls}" style="margin-top:10px;">
                                <div class="fb-title" style="color:{color};">{icon} {lbl}</div>
                                <div class="fb-body">{safe_html(fd.get(lbl,""))}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

    st.write("")

    # ── Download report ───────────────────────────────────────────
    report = {
        "role": role,
        "total_questions": TOTAL_QUESTIONS,
        "grade": grade,
        "average_overall": round(avg_overall, 2),
        "average_scores": {k: round(v, 2) for k, v in avgs.items()},
        "questions": [
            {
                "q_num": i + 1,
                "question": item["question"],
                "answer": item["answer"],
                "scores": {
                    lbl: item["feedback_data"].get(lbl, "—")
                    for lbl in score_labels
                },
                "strengths":   item["feedback_data"].get("Strengths", ""),
                "weaknesses":  item["feedback_data"].get("Weaknesses", ""),
                "ideal_answer": item["feedback_data"].get("Ideal Answer", ""),
            }
            for i, item in enumerate(history)
        ],
    }
    report_json = json.dumps(report, indent=2, ensure_ascii=False)

    dl_col, restart_col = st.columns([1, 1], gap="medium")
    with dl_col:
        st.download_button(
            label="⬇️  Download Full Report (JSON)",
            data=report_json,
            file_name=f"interview_{role.replace(' ','_').lower()}_report.json",
            mime="application/json",
            use_container_width=True,
        )
    with restart_col:
        if st.button("🔄  Start New Session", type="primary", use_container_width=True):
            for key in ["stage", "current_q", "question", "asked_questions",
                        "history", "feedback_data", "role"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

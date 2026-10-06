import sqlite3
from datetime import date, timedelta
from html import escape

import pandas as pd
import streamlit as st


# --------------------------------------------------
# App configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Job Tracker",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed",
)


DB = "jobs.db"

STATUSES = [
    "To Apply",
    "Applied",
    "Interview",
    "Offer",
    "Rejected",
    "Withdrawn",
]

STATUS_EMOJI = {
    "To Apply": "🟡",
    "Applied": "🔵",
    "Interview": "🟣",
    "Offer": "🟢",
    "Rejected": "🔴",
    "Withdrawn": "⚫",
}

# RGB triplets used for rgba() in the timeline and status accents
STATUS_RGB = {
    "To Apply": "245, 158, 11",
    "Applied": "59, 130, 246",
    "Interview": "139, 92, 246",
    "Offer": "34, 197, 94",
    "Rejected": "239, 68, 68",
    "Withdrawn": "148, 163, 184",
}


# --------------------------------------------------
# Styling  (dark navy glass, blue glow)
# --------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Urbanist:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        color-scheme: dark;

        --text: #F1F5FF;
        --text-dim: rgba(200, 216, 255, 0.76);
        --text-faint: rgba(170, 192, 240, 0.52);

        --accent: #7DB2FF;
        --blue: #3B82F6;
        --blue-glow: #2F7BFF;
        --cyan: #5EE7F5;

        --glass: linear-gradient(
            145deg,
            rgba(120, 170, 255, 0.16) 0%,
            rgba(60, 100, 200, 0.07) 55%,
            rgba(120, 170, 255, 0.10) 100%
        );
        --glass-soft: linear-gradient(
            145deg,
            rgba(120, 170, 255, 0.10),
            rgba(60, 100, 200, 0.04)
        );

        /* INPUT FIELD: solid dark so the light text is always readable */
        --field: #08122B;
        --field-border: rgba(125, 178, 255, 0.28);

        --border: rgba(140, 185, 255, 0.20);
        --border-strong: rgba(150, 195, 255, 0.40);
        --shadow: 0 12px 38px rgba(2, 6, 25, 0.55);
        --inner-light: inset 0 1px 0 rgba(200, 225, 255, 0.22);
    }

    html, body, .stApp, [class*="css"] {
        font-family: 'Urbanist', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: var(--text);
    }

    /* ---------- Dark glassy background with blue orbs ---------- */
    .stApp {
        background:
            radial-gradient(34rem 26rem at 8% 6%, rgba(47, 123, 255, 0.34), transparent 65%),
            radial-gradient(30rem 24rem at 96% 14%, rgba(56, 160, 255, 0.22), transparent 65%),
            radial-gradient(36rem 28rem at 4% 96%, rgba(30, 90, 220, 0.30), transparent 62%),
            radial-gradient(32rem 26rem at 100% 100%, rgba(40, 110, 255, 0.24), transparent 64%),
            linear-gradient(160deg, #030814 0%, #06112B 40%, #081A44 70%, #040B1E 100%);
        background-attachment: fixed;
    }

    .block-container {
        max-width: 1080px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { background: transparent !important; }

    div[data-testid="stVerticalBlock"] {
        gap: 0.6rem;
    }

    p, label, span, li {
        color: var(--text);
    }

    /* ---------- Header ---------- */
    .app-header {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        padding: 0 0 16px;
        margin-bottom: 6px;
        border-bottom: 1px solid var(--border);
    }

    .app-eyebrow {
        display: flex;
        align-items: center;
        gap: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        font-weight: 500;
        letter-spacing: 0.22em;
        color: var(--accent);
    }

    .app-eyebrow .dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--cyan);
        box-shadow: 0 0 12px rgba(94, 231, 245, 0.9);
    }

    .app-title {
        margin: 6px 0 0;
        padding: 0;
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1.12;
        color: #FFFFFF;
        text-shadow: 0 0 28px rgba(47, 123, 255, 0.55);
    }

    .app-title span {
        background: linear-gradient(90deg, #7DB2FF, #5EE7F5);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }

    /* ---------- Expanders (Add job + notes) ---------- */
    div[data-testid="stExpander"] {
        border: 1px solid var(--border) !important;
        border-radius: 18px;
        background: var(--glass) !important;
        backdrop-filter: blur(24px) saturate(150%);
        -webkit-backdrop-filter: blur(24px) saturate(150%);
        box-shadow: var(--shadow), var(--inner-light);
        overflow: hidden;
    }

    div[data-testid="stExpander"] details,
    div[data-testid="stExpander"] details > div {
        background: transparent !important;
        border: none !important;
    }

    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] details > summary {
        background: transparent !important;
        padding: 0.6rem 1rem;
        color: var(--text) !important;
        font-weight: 600;
        font-size: 0.92rem;
    }

    div[data-testid="stExpander"] summary *,
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] summary span {
        color: var(--text) !important;
        background: transparent !important;
    }

    div[data-testid="stExpander"] summary:hover,
    div[data-testid="stExpander"] summary:hover * {
        color: #FFFFFF !important;
    }

    div[data-testid="stExpander"] summary svg {
        color: var(--text-dim) !important;
        fill: var(--text-dim) !important;
    }

    div[data-testid="stForm"] {
        border: none !important;
        background: transparent !important;
        padding: 0.25rem 0.25rem 0;
    }

    /* Notes expander inside a job card: lighter, nested glass */
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stExpander"] {
        border-radius: 12px;
        background: rgba(120, 170, 255, 0.06) !important;
        box-shadow: none;
        backdrop-filter: none;
        -webkit-backdrop-filter: none;
    }

    /* ---------- Labels ---------- */
    label,
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label,
    .stDateInput label,
    .stMultiSelect label,
    div[data-testid="stWidgetLabel"] p {
        color: var(--text-dim) !important;
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.02em;
    }

    /* ---------- Inputs (text, textarea, date) ----------
       Solid dark background + bright text = always readable. */
    div[data-baseweb="input"],
    div[data-baseweb="textarea"],
    div[data-baseweb="base-input"] {
        background-color: var(--field) !important;
        border-radius: 12px !important;
        border: 1px solid var(--field-border) !important;
        transition: border-color 0.18s ease, box-shadow 0.18s ease;
    }

    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="base-input"] > div {
        background-color: var(--field) !important;
        border: none !important;
    }

    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="textarea"]:focus-within,
    div[data-baseweb="base-input"]:focus-within {
        border-color: rgba(125, 178, 255, 0.95) !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.28), 0 0 18px rgba(47, 123, 255, 0.35);
    }

    input, textarea {
        background-color: var(--field) !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        caret-color: var(--cyan);
        font-size: 0.92rem !important;
        font-weight: 500;
    }

    /* Chrome autofill would otherwise paint a light background */
    input:-webkit-autofill,
    input:-webkit-autofill:hover,
    input:-webkit-autofill:focus,
    textarea:-webkit-autofill {
        -webkit-box-shadow: 0 0 0 1000px #08122B inset !important;
        -webkit-text-fill-color: #FFFFFF !important;
        caret-color: var(--cyan);
    }

    input::placeholder, textarea::placeholder {
        color: rgba(170, 192, 240, 0.50) !important;
        -webkit-text-fill-color: rgba(170, 192, 240, 0.50) !important;
        opacity: 1;
        font-weight: 400;
    }

    div[data-testid="InputInstructions"],
    div[data-testid="InputInstructions"] * {
        color: var(--text-faint) !important;
        background: transparent !important;
        font-size: 0.68rem !important;
    }

    /* ---------- Selectbox / Multiselect ---------- */
    div[data-baseweb="select"] > div {
        background-color: var(--field) !important;
        border: 1px solid var(--field-border) !important;
        border-radius: 12px !important;
        transition: border-color 0.18s ease, box-shadow 0.18s ease;
    }

    div[data-baseweb="select"] > div:focus-within {
        border-color: rgba(125, 178, 255, 0.95) !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.28), 0 0 18px rgba(47, 123, 255, 0.35);
    }

    div[data-baseweb="select"] div,
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] input {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-size: 0.88rem;
    }

    div[data-baseweb="select"] svg {
        color: var(--text-dim) !important;
        fill: var(--text-dim) !important;
    }

    span[data-baseweb="tag"] {
        background: rgba(59, 130, 246, 0.30) !important;
        border: 1px solid rgba(125, 178, 255, 0.45);
        border-radius: 999px;
    }

    span[data-baseweb="tag"] span,
    span[data-baseweb="tag"] svg {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        fill: #FFFFFF !important;
        font-size: 0.74rem;
        font-weight: 500;
    }

    /* Dropdown menus */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    div[data-baseweb="popover"] ul,
    ul[data-baseweb="menu"] {
        background: #0A1736 !important;
        border-radius: 14px;
    }

    div[data-baseweb="popover"] > div {
        border: 1px solid var(--border-strong);
        box-shadow: 0 16px 40px rgba(2, 6, 25, 0.65), 0 0 24px rgba(47, 123, 255, 0.18);
    }

    li[role="option"],
    li[role="option"] * {
        background: transparent !important;
        color: var(--text) !important;
        font-size: 0.86rem;
    }

    li[role="option"]:hover,
    li[aria-selected="true"] {
        background: rgba(59, 130, 246, 0.28) !important;
    }

    /* Date picker calendar */
    div[data-baseweb="calendar"],
    div[data-baseweb="calendar"] * {
        background-color: #0A1736 !important;
        color: var(--text) !important;
    }

    div[data-baseweb="calendar"] button:hover,
    div[data-baseweb="calendar"] [aria-selected="true"] {
        background-color: rgba(59, 130, 246, 0.65) !important;
    }

    /* ---------- Metrics (glass cards) ---------- */
    div[data-testid="stMetric"] {
        position: relative;
        padding: 14px 18px;
        border: 1px solid var(--border);
        border-radius: 18px;
        background: var(--glass);
        backdrop-filter: blur(24px) saturate(150%);
        -webkit-backdrop-filter: blur(24px) saturate(150%);
        box-shadow: var(--shadow), var(--inner-light);
        overflow: hidden;
    }

    div[data-testid="stMetric"]::after {
        content: "";
        position: absolute;
        right: -30px;
        top: -30px;
        width: 110px;
        height: 110px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(47, 123, 255, 0.38), transparent 70%);
        pointer-events: none;
    }

    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] * {
        color: var(--text-dim) !important;
        font-size: 0.72rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] * {
        color: #FFFFFF !important;
        font-size: 2.1rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
        line-height: 1.1;
        text-shadow: 0 0 18px rgba(47, 123, 255, 0.55);
    }

    /* ---------- Section labels ---------- */
    .section-label {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: 20px 0 6px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: var(--text-faint);
    }

    .section-label span {
        color: var(--text-dim);
    }

    .section-label .hint {
        letter-spacing: 0.02em;
        text-transform: none;
        font-family: 'Urbanist', sans-serif;
        font-size: 0.78rem;
        color: var(--text-faint);
    }

    /* ---------- Caption ---------- */
    div[data-testid="stCaptionContainer"],
    div[data-testid="stCaptionContainer"] * {
        color: var(--text-faint) !important;
        font-size: 0.78rem !important;
    }

    /* ---------- Timeline ---------- */
    .tl-wrap {
        border: 1px solid var(--border);
        border-radius: 18px;
        background: var(--glass);
        backdrop-filter: blur(24px) saturate(150%);
        -webkit-backdrop-filter: blur(24px) saturate(150%);
        box-shadow: var(--shadow), var(--inner-light);
        overflow-x: auto;
        padding: 12px 16px 14px;
    }

    .tl-inner {
        min-width: 640px;
    }

    .tl-row {
        display: grid;
        grid-template-columns: 150px 1fr;
        align-items: center;
        column-gap: 12px;
    }

    .tl-axis-row {
        padding-bottom: 8px;
        border-bottom: 1px solid var(--border);
        margin-bottom: 4px;
    }

    .tl-axis {
        position: relative;
        height: 16px;
    }

    .tl-tick {
        position: absolute;
        top: 0;
        transform: translateX(-50%);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.64rem;
        color: var(--text-faint);
        white-space: nowrap;
    }

    .tl-tick.first { transform: translateX(0); }
    .tl-tick.last { transform: translateX(-100%); }

    .tl-name {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-size: 0.86rem;
        font-weight: 600;
        color: var(--text);
        padding: 6px 0;
    }

    .tl-name small {
        display: block;
        margin-top: -2px;
        font-size: 0.7rem;
        font-weight: 400;
        color: var(--text-faint);
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .tl-track {
        position: relative;
        height: 30px;
        background-image: repeating-linear-gradient(
            90deg,
            rgba(140, 185, 255, 0.12) 0,
            rgba(140, 185, 255, 0.12) 1px,
            transparent 1px,
            transparent var(--grid, 14.28%)
        );
        border-radius: 4px;
    }

    .tl-bar {
        position: absolute;
        left: 0;
        top: 50%;
        height: 4px;
        transform: translateY(-50%);
        border-radius: 3px;
    }

    .tl-marker {
        position: absolute;
        top: 50%;
        width: 11px;
        height: 11px;
        transform: translate(-50%, -50%);
        border-radius: 50%;
    }

    .tl-label {
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        padding-left: 12px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.64rem;
        white-space: nowrap;
    }

    .tl-label.flip {
        padding-left: 0;
        padding-right: 12px;
        transform: translate(-100%, -50%);
    }

    .tl-today {
        position: absolute;
        top: -2px;
        bottom: -2px;
        width: 0;
        border-left: 1px dashed rgba(94, 231, 245, 0.75);
        z-index: 2;
    }

    .tl-today-tag {
        position: absolute;
        top: -17px;
        transform: translateX(-50%);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.58rem;
        letter-spacing: 0.12em;
        color: var(--cyan);
    }

    .tl-overdue-note {
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid var(--border);
        display: flex;
        gap: 14px;
        flex-wrap: wrap;
        font-size: 0.72rem;
        color: var(--text-faint);
    }

    .tl-key {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        color: var(--text-dim);
    }

    .tl-key i {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
    }

    /* ---------- Job card container (glass) ---------- */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.job-card) {
        position: relative;
        border: 1px solid var(--border) !important;
        border-radius: 18px !important;
        background: var(--glass) !important;
        backdrop-filter: blur(24px) saturate(150%);
        -webkit-backdrop-filter: blur(24px) saturate(150%);
        box-shadow: var(--shadow), var(--inner-light);
        padding: 14px 18px 14px 20px !important;
        transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.job-card):hover {
        border-color: var(--border-strong) !important;
        transform: translateY(-1px);
        box-shadow: var(--shadow), var(--inner-light), 0 0 26px rgba(47, 123, 255, 0.20);
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.job-card) > div {
        gap: 0.55rem;
    }

    .job-card {
        position: relative;
    }

    .job-card::before {
        content: "";
        position: absolute;
        left: -20px;
        top: 2px;
        bottom: 2px;
        width: 3px;
        border-radius: 3px;
        background: rgb(var(--rgb));
        box-shadow: 0 0 12px rgba(var(--rgb), 0.65);
    }

    .job-top {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
    }

    .company {
        color: #FFFFFF;
        font-size: 1.08rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        line-height: 1.25;
    }

    .role {
        margin-top: 1px;
        color: var(--text-dim);
        font-size: 0.88rem;
    }

    .pill {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        flex-shrink: 0;
        padding: 3px 11px;
        border-radius: 999px;
        border: 1px solid rgba(var(--rgb), 0.50);
        background: rgba(var(--rgb), 0.20);
        color: rgb(var(--rgb-light));
        font-size: 0.74rem;
        font-weight: 600;
        letter-spacing: 0.01em;
        white-space: nowrap;
    }

    .job-meta {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 6px 14px;
        margin-top: 9px;
    }

    .deadline-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: var(--text-dim);
    }

    .deadline-chip.overdue { color: #FF8FA0; }
    .deadline-chip.soon { color: #FCD34D; }
    .deadline-chip.today { color: #FCD34D; }

    .tags {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: 10px;
    }

    .tag {
        padding: 2px 10px;
        border-radius: 999px;
        border: 1px solid var(--border);
        background: rgba(120, 170, 255, 0.10);
        color: #E4EDFF;
        font-size: 0.72rem;
        font-weight: 500;
    }

    .tag.empty-tag {
        color: var(--text-faint);
        background: transparent;
        border-style: dashed;
    }

    /* ---------- Buttons ---------- */
    .stButton > button,
    .stLinkButton > a,
    .stFormSubmitButton > button {
        min-height: 36px;
        padding: 0.25rem 0.9rem;
        border-radius: 999px;
        border: 1px solid var(--border-strong);
        background: rgba(120, 170, 255, 0.12);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        color: var(--text) !important;
        font-size: 0.84rem;
        font-weight: 600;
        box-shadow: var(--inner-light);
        transition: all 0.18s ease;
    }

    .stButton > button:hover,
    .stLinkButton > a:hover {
        border-color: rgba(160, 200, 255, 0.7);
        background: rgba(120, 170, 255, 0.24);
        color: #fff !important;
        box-shadow: var(--inner-light), 0 0 16px rgba(47, 123, 255, 0.35);
    }

    .stButton > button p,
    .stLinkButton > a p {
        color: inherit !important;
        font-size: 0.84rem;
    }

    .stButton > button[kind="secondary"]:hover {
        border-color: rgba(255, 120, 140, 0.7);
        background: rgba(239, 68, 68, 0.22);
        color: #FFD3DA !important;
        box-shadow: none;
    }

    button[kind="primary"],
    button[kind="primaryFormSubmit"] {
        background: linear-gradient(100deg, #1D4ED8 0%, #2F7BFF 55%, #5EB5FF 100%) !important;
        color: #fff !important;
        border: 1px solid rgba(190, 220, 255, 0.45) !important;
        box-shadow: 0 8px 26px rgba(47, 123, 255, 0.55), var(--inner-light);
    }

    button[kind="primary"] p,
    button[kind="primaryFormSubmit"] p {
        color: #fff !important;
    }

    button[kind="primary"]:hover,
    button[kind="primaryFormSubmit"]:hover {
        background: linear-gradient(100deg, #2B5FE8 0%, #4A90FF 55%, #7CC4FF 100%) !important;
        border-color: rgba(210, 232, 255, 0.65) !important;
    }

    /* ---------- Alerts ---------- */
    div[data-testid="stAlert"] {
        background: var(--glass);
        border: 1px solid var(--border);
        border-radius: 12px;
        color: var(--text);
    }

    div[data-testid="stAlert"] * {
        color: var(--text) !important;
    }

    /* ---------- Notes text ---------- */
    div[data-testid="stExpander"] .stMarkdown p,
    div[data-testid="stExpander"] div[data-testid="stText"] {
        color: var(--text-dim) !important;
        font-size: 0.86rem;
    }

    /* ---------- Empty state ---------- */
    .empty {
        padding: 36px 20px;
        margin-top: 14px;
        border: 1px dashed var(--border-strong);
        border-radius: 18px;
        background: var(--glass-soft);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        text-align: center;
        color: var(--text-dim);
    }

    .empty h3 {
        margin: 0 0 4px;
        padding: 0;
        color: #FFFFFF;
        font-size: 1.1rem;
        font-weight: 700;
    }

    .empty p {
        margin: 0;
        font-size: 0.9rem;
        color: var(--text-dim);
    }

    /* ---------- Footer ---------- */
    .app-footer {
        text-align: center;
        margin-top: 36px;
        color: var(--text-faint);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.66rem;
        letter-spacing: 0.12em;
    }

    /* ---------- Scrollbars ---------- */
    ::-webkit-scrollbar { height: 8px; width: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(140, 185, 255, 0.30);
        border-radius: 8px;
    }

    /* ---------- Mobile ---------- */
    @media (max-width: 640px) {
        .block-container {
            padding: 1.1rem 0.9rem 3rem;
        }

        .app-title {
            font-size: 1.5rem;
        }

        div[data-testid="stMetricValue"],
        div[data-testid="stMetricValue"] * {
            font-size: 1.6rem !important;
        }

        .job-top {
            flex-direction: column;
            gap: 8px;
        }

        .tl-row {
            grid-template-columns: 110px 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Database functions
# --------------------------------------------------

def connect():
    conn = sqlite3.connect(DB)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            skills TEXT,
            deadline TEXT,
            status TEXT NOT NULL DEFAULT 'To Apply',
            url TEXT,
            notes TEXT
        )
        """
    )

    return conn


def add_job(company, role, skills, deadline, status, url, notes):
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO jobs
            (company, role, skills, deadline, status, url, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company,
                role,
                skills,
                str(deadline),
                status,
                url,
                notes,
            ),
        )


def update_status(job_id, status):
    with connect() as conn:
        conn.execute(
            """
            UPDATE jobs
            SET status = ?
            WHERE id = ?
            """,
            (status, job_id),
        )


def delete_job(job_id):
    with connect() as conn:
        conn.execute(
            """
            DELETE FROM jobs
            WHERE id = ?
            """,
            (job_id,),
        )


def load_jobs():
    with connect() as conn:
        return pd.read_sql_query(
            """
            SELECT *
            FROM jobs
            ORDER BY
                CASE
                    WHEN deadline IS NULL OR deadline = '' THEN 1
                    ELSE 0
                END,
                deadline ASC,
                id DESC
            """,
            conn,
        )


# --------------------------------------------------
# UI helpers
# --------------------------------------------------

# Lighter tints of each status color for text on glass surfaces
STATUS_RGB_LIGHT = {
    "To Apply": "252, 211, 77",
    "Applied": "165, 205, 255",
    "Interview": "212, 198, 255",
    "Offer": "134, 239, 172",
    "Rejected": "255, 175, 175",
    "Withdrawn": "214, 222, 235",
}


def status_rgb(status_name):
    return STATUS_RGB.get(status_name, "148, 163, 184")


def status_rgb_light(status_name):
    return STATUS_RGB_LIGHT.get(status_name, "214, 222, 235")


def build_timeline(frame, today_date):
    """Build a compact HTML/CSS deadline timeline from jobs with deadlines."""
    rows = frame[frame["deadline_date"].notna()].copy()

    if rows.empty:
        return ""

    rows = rows.sort_values(
        by=["deadline_date", "id"],
        ascending=[True, False],
    )

    earliest = min(rows["deadline_date"].min(), today_date)
    latest = max(rows["deadline_date"].max(), today_date)

    # Padding so markers and labels never touch the edges
    start = earliest - timedelta(days=1)
    end = latest + timedelta(days=3)

    total_days = max((end - start).days, 1)

    def pct(day):
        return ((day - start).days / total_days) * 100

    # Axis ticks (about 6 evenly spaced labels)
    tick_count = 6
    ticks_html = ""
    for i in range(tick_count + 1):
        offset_days = round(total_days * i / tick_count)
        tick_day = start + timedelta(days=offset_days)
        position = (offset_days / total_days) * 100

        extra_class = ""
        if i == 0:
            extra_class = " first"
        elif i == tick_count:
            extra_class = " last"

        ticks_html += (
            f'<div class="tl-tick{extra_class}" style="left:{position:.2f}%">'
            f'{tick_day.strftime("%b")} {tick_day.day}</div>'
        )

    today_pos = pct(today_date)
    grid_step = 100 / tick_count

    rows_html = ""
    for _, job in rows.iterrows():
        job_status = str(job["status"])
        rgb = status_rgb(job_status)
        rgb_light = status_rgb_light(job_status)

        deadline_day = job["deadline_date"]
        days_left = job["days_left"]
        overdue = days_left < 0

        company_text = escape(str(job["company"]))
        role_text = escape(str(job["role"]))

        marker_pos = pct(deadline_day)

        if overdue:
            bar_start = marker_pos
            bar_width = max(today_pos - marker_pos, 0)
            bar_style = (
                f"left:{bar_start:.2f}%;width:{bar_width:.2f}%;"
                "background:repeating-linear-gradient(90deg,"
                "rgba(255,110,130,0.75) 0,rgba(255,110,130,0.75) 4px,"
                "transparent 4px,transparent 7px);"
            )
            marker_style = (
                f"left:{marker_pos:.2f}%;"
                "background:#FF5C77;"
                "box-shadow:0 0 0 3px rgba(255,92,119,0.28);"
            )
            label_color = "#FF8FA0"
            label_text = f"{abs(int(days_left))}d overdue"
        else:
            bar_style = (
                f"left:{pct(today_date):.2f}%;"
                f"width:{max(marker_pos - pct(today_date), 0):.2f}%;"
                f"background:linear-gradient(90deg,"
                f"rgba({rgb},0.2),rgba({rgb},0.85));"
            )
            marker_style = (
                f"left:{marker_pos:.2f}%;"
                f"background:rgb({rgb});"
                f"box-shadow:0 0 0 3px rgba({rgb},0.28);"
            )
            label_color = f"rgb({rgb_light})"

            if days_left == 0:
                label_text = "today"
            elif days_left == 1:
                label_text = "1d"
            else:
                label_text = f"{int(days_left)}d"

        # Flip label to the left of the marker if near the right edge
        flip_class = " flip" if marker_pos > 82 else ""

        rows_html += (
            '<div class="tl-row">'
            f'<div class="tl-name" title="{company_text} · {role_text}">'
            f'{company_text}<small>{role_text}</small></div>'
            f'<div class="tl-track" style="--grid:{grid_step:.4f}%">'
            f'<div class="tl-bar" style="{bar_style}"></div>'
            f'<div class="tl-marker" style="{marker_style}"></div>'
            f'<div class="tl-label{flip_class}" '
            f'style="left:{marker_pos:.2f}%;color:{label_color}">'
            f'{label_text}</div>'
            '</div>'
            '</div>'
        )

    today_line = (
        f'<div class="tl-today" style="left:{today_pos:.2f}%">'
        f'<div class="tl-today-tag">TODAY</div></div>'
    )

    return (
        '<div class="tl-wrap"><div class="tl-inner">'
        '<div class="tl-row tl-axis-row">'
        '<div></div>'
        f'<div class="tl-axis">{ticks_html}</div>'
        '</div>'
        '<div style="position:relative;">'
        '<div class="tl-row" style="position:absolute;inset:0;'
        'pointer-events:none;">'
        '<div></div>'
        f'<div style="position:relative;">{today_line}</div>'
        '</div>'
        f'{rows_html}'
        '</div>'
        '<div class="tl-overdue-note">'
        '<span class="tl-key"><i style="background:#FF5C77"></i>Overdue</span>'
        '<span class="tl-key"><i style="background:rgb(245,158,11)"></i>'
        'Upcoming (colored by status)</span>'
        '<span class="tl-key"><i style="background:#5EE7F5"></i>Today</span>'
        '</div>'
        '</div></div>'
    )


# --------------------------------------------------
# Header
# --------------------------------------------------

st.markdown(
    '<div class="app-header"><div>'
    '<div class="app-eyebrow"><span class="dot"></span>JOB TRACKER</div>'
    '<h1 class="app-title">Find it. Track it., '
    '<span> Land it.</span></h1>'
    '</div></div>',
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Add a job
# --------------------------------------------------

with st.expander("＋ Add a new job", expanded=False):
    with st.form("add_job_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        company = col1.text_input(
            "Company *",
            placeholder="Google, Amazon, Deloitte...",
        )

        role = col2.text_input(
            "Role *",
            placeholder="Data Analyst, Software Engineer...",
        )

        col3, col4 = st.columns(2)

        deadline = col3.date_input(
            "Application deadline",
            value=date.today(),
        )

        status = col4.selectbox(
            "Current status",
            STATUSES,
            index=0,
        )

        skills = st.text_input(
            "Skills",
            placeholder="Python, SQL, Excel, Power BI...",
        )

        url = st.text_input(
            "Job URL",
            placeholder="https://example.com/job",
        )

        notes = st.text_area(
            "Notes",
            placeholder="Salary, recruiter name, preparation notes...",
        )

        submitted = st.form_submit_button(
            "Save job",
            use_container_width=True,
            type="primary",
        )

        if submitted:
            if not company.strip() or not role.strip():
                st.error("Company and role are required.")
            else:
                add_job(
                    company=company.strip(),
                    role=role.strip(),
                    skills=skills.strip(),
                    deadline=deadline,
                    status=status,
                    url=url.strip(),
                    notes=notes.strip(),
                )

                st.success("Job saved successfully.")
                st.rerun()


# --------------------------------------------------
# Load and prepare data
# --------------------------------------------------

df = load_jobs()

if not df.empty:
    df["deadline_date"] = pd.to_datetime(
        df["deadline"],
        errors="coerce",
    ).dt.date

    today = date.today()

    df["days_left"] = df["deadline_date"].apply(
        lambda deadline_date: (
            (deadline_date - today).days
            if pd.notna(deadline_date)
            else None
        )
    )
else:
    df["days_left"] = pd.Series(dtype="float")


# --------------------------------------------------
# Empty state
# --------------------------------------------------

if df.empty:
    st.markdown(
        '<div class="empty"><h3>No jobs yet</h3>'
        '<p>Click <b>＋ Add a new job</b> to add your first opportunity.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.stop()


# --------------------------------------------------
# Dashboard metrics
# --------------------------------------------------

total_jobs = len(df)

to_apply_count = int(
    (df["status"] == "To Apply").sum()
)

interview_count = int(
    (df["status"] == "Interview").sum()
)

offer_count = int(
    (df["status"] == "Offer").sum()
)

due_soon_count = int(
    (
        (df["days_left"] >= 0)
        & (df["days_left"] <= 7)
    ).sum()
)


st.write("")

metric1, metric2, metric3, metric4 = st.columns(4)

metric1.metric(
    "Total jobs",
    total_jobs,
)

metric2.metric(
    "To apply",
    to_apply_count,
)

metric3.metric(
    "Due soon",
    due_soon_count,
)

metric4.metric(
    "Interviews",
    interview_count,
)


# --------------------------------------------------
# Search and filters
# --------------------------------------------------

st.markdown(
    '<div class="section-label"><span>Filter</span></div>',
    unsafe_allow_html=True,
)

search_col, status_col = st.columns([2, 1])

search = search_col.text_input(
    "Search jobs",
    placeholder="🔍  Search company, role, or skill...",
    label_visibility="collapsed",
)

chosen_statuses = status_col.multiselect(
    "Filter by status",
    STATUSES,
    default=STATUSES,
    label_visibility="collapsed",
)

view = df[
    df["status"].isin(chosen_statuses)
].copy()


if search.strip():
    query = search.strip().lower()

    searchable_text = (
        view["company"].fillna("")
        + " "
        + view["role"].fillna("")
        + " "
        + view["skills"].fillna("")
        + " "
        + view["notes"].fillna("")
    ).str.lower()

    view = view[
        searchable_text.str.contains(
            query,
            regex=False,
            na=False,
        )
    ]


st.caption(
    f"Showing {len(view)} of {len(df)} saved jobs"
)


# --------------------------------------------------
# Deadline timeline
# --------------------------------------------------

timeline_html = build_timeline(view, today)

if timeline_html:
    st.markdown(
        '<div class="section-label"><span>Deadline timeline</span>'
        '<span class="hint">Sorted by deadline · jobs without deadlines hidden</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(timeline_html, unsafe_allow_html=True)


# --------------------------------------------------
# Display job cards
# --------------------------------------------------

st.markdown(
    '<div class="section-label"><span>Opportunities</span></div>',
    unsafe_allow_html=True,
)

if view.empty:
    st.markdown(
        '<div class="empty"><h3>No matching jobs</h3>'
        '<p>Try changing your search or status filters.</p></div>',
        unsafe_allow_html=True,
    )

else:
    for _, job in view.iterrows():
        job_status = str(job["status"])
        emoji = STATUS_EMOJI.get(job_status, "•")

        rgb = status_rgb(job_status)
        rgb_light = status_rgb_light(job_status)

        company_text = escape(
            str(job["company"])
        )

        role_text = escape(
            str(job["role"])
        )

        # Skills rendered as compact tags (escaped)
        if job["skills"]:
            raw_skills = [
                part.strip()
                for part in str(job["skills"]).split(",")
                if part.strip()
            ]
        else:
            raw_skills = []

        if raw_skills:
            skills_html = "".join(
                f'<span class="tag">{escape(skill)}</span>'
                for skill in raw_skills
            )
        else:
            skills_html = '<span class="tag empty-tag">No skills added</span>'

        deadline_class = ""

        if pd.isna(job["deadline_date"]):
            deadline_text = "No deadline"

        elif job["days_left"] < 0:
            deadline_text = (
                f"Deadline {escape(str(job['deadline']))} · overdue"
            )
            deadline_class = " overdue"

        elif job["days_left"] == 0:
            deadline_text = (
                f"Deadline {escape(str(job['deadline']))} · today"
            )
            deadline_class = " today"

        elif job["days_left"] == 1:
            deadline_text = (
                f"Deadline {escape(str(job['deadline']))} · 1 day left"
            )
            deadline_class = " soon"

        else:
            deadline_text = (
                f"Deadline {escape(str(job['deadline']))} · "
                f"{int(job['days_left'])} days left"
            )
            if job["days_left"] <= 7:
                deadline_class = " soon"

        # Single-line HTML (no blank lines / indentation) so Markdown
        # never mistakes it for a code block.
        card_html = (
            f'<div class="job-card" style="--rgb:{rgb}; --rgb-light:{rgb_light};">'
            '<div class="job-top">'
            '<div>'
            f'<div class="company">{company_text}</div>'
            f'<div class="role">{role_text}</div>'
            '</div>'
            f'<span class="pill">{emoji} {escape(job_status)}</span>'
            '</div>'
            '<div class="job-meta">'
            f'<span class="deadline-chip{deadline_class}">📅 {deadline_text}</span>'
            '</div>'
            f'<div class="tags">{skills_html}</div>'
            '</div>'
        )

        with st.container(border=True):
            st.markdown(card_html, unsafe_allow_html=True)

            action_col1, action_col2, action_col3 = st.columns(
                [1, 1.3, 3.7]
            )

            if job["url"]:
                action_col1.link_button(
                    "Open job",
                    str(job["url"]),
                    use_container_width=True,
                )

            new_status = action_col2.selectbox(
                "Update status",
                STATUSES,
                index=STATUSES.index(job_status),
                key=f"status_{job['id']}",
                label_visibility="collapsed",
            )

            if new_status != job_status:
                update_status(
                    int(job["id"]),
                    new_status,
                )

                st.rerun()

            if action_col3.button(
                "Delete",
                key=f"delete_{job['id']}",
                use_container_width=False,
            ):
                delete_job(int(job["id"]))
                st.rerun()

            if job["notes"]:
                with st.expander("View notes"):
                    st.write(str(job["notes"]))


# --------------------------------------------------
# Footer
# --------------------------------------------------

st.markdown(
    '<div class="app-footer">JOB TRACKER · KEEP YOUR SEARCH ORGANIZED</div>',
    unsafe_allow_html=True,
)
# To run the code streamlit run app.py   

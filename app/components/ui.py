"""
components/ui.py

Design tokens (colors, type) and reusable UI-rendering helpers for the
AgriSmart AI Streamlit prototype. Every page imports `inject_css()` once
and then composes its layout from the functions below, so the whole app
shares one visual language instead of default Streamlit styling.

Nothing in this file touches the ML model — it is pure presentation.
"""

from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------

COLORS = {
    "forest": "#1B4332",       # primary dark — nav, headings, hero
    "leaf": "#52B788",         # primary accent — buttons, links, healthy
    "leaf_light": "#B7E4C7",   # tints, hover states
    "soil": "#A9744F",         # secondary accent — treatment/prevention
    "sky": "#4A7C8C",          # tertiary accent — irrigation/weather
    "sand": "#F5F1E8",         # section background (alternate)
    "cream": "#FBFAF7",        # page background
    "charcoal": "#22291F",     # body text
    "amber": "#E0A458",        # moderate severity / warnings
    "red": "#C1443C",          # high severity / disease detected
    "white": "#FFFFFF",
}

HEADING_FONT = "'Space Grotesk', sans-serif"
BODY_FONT = "'Inter', sans-serif"


def inject_css() -> None:
    """Injects the shared stylesheet. Call once at the top of every page."""
    c = COLORS
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

        html, body, [class*="css"] {{
            font-family: {BODY_FONT};
            color: {c['charcoal']};
        }}

        .stApp {{
            background-color: {c['cream']};
        }}

        .block-container {{
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1100px;
        }}

        h1, h2, h3, h4 {{
            font-family: {HEADING_FONT};
            color: {c['forest']};
            letter-spacing: -0.01em;
        }}

        section[data-testid="stSidebar"] {{
            background-color: {c['forest']};
        }}
        section[data-testid="stSidebar"] * {{
            color: {c['cream']} !important;
        }}
        section[data-testid="stSidebar"] .stMarkdown p {{
            color: {c['leaf_light']} !important;
        }}

        /* Buttons */
        .stButton > button, .stDownloadButton > button {{
            background-color: {c['leaf']};
            color: {c['forest']};
            border: none;
            border-radius: 8px;
            padding: 0.6rem 1.4rem;
            font-weight: 600;
            font-family: {BODY_FONT};
            transition: background-color 0.15s ease;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover {{
            background-color: {c['leaf_light']};
            color: {c['forest']};
        }}

        /* Hero */
        .agri-hero {{
            background: linear-gradient(135deg, {c['forest']} 0%, #2D6A4F 100%);
            border-radius: 16px;
            padding: 3rem 2.5rem;
            margin-bottom: 2.5rem;
            color: {c['white']};
        }}
        .agri-hero h1 {{
            color: {c['white']};
            font-size: 2.4rem;
            margin-bottom: 0.4rem;
        }}
        .agri-hero p {{
            color: {c['leaf_light']};
            font-size: 1.1rem;
            max-width: 520px;
            margin-bottom: 0;
        }}

        /* Feature / step cards */
        .agri-card {{
            background-color: {c['white']};
            border-radius: 12px;
            padding: 1.4rem 1.3rem;
            height: 100%;
            border: 1px solid #E7E2D6;
        }}
        .agri-card .agri-card-icon {{
            font-size: 1.6rem;
            margin-bottom: 0.5rem;
        }}
        .agri-card h4 {{
            margin: 0 0 0.35rem 0;
            font-size: 1.05rem;
        }}
        .agri-card p {{
            font-size: 0.92rem;
            color: #4A5045;
            margin: 0;
        }}

        .agri-step-num {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background-color: {c['leaf_light']};
            color: {c['forest']};
            font-weight: 700;
            font-family: {HEADING_FONT};
            margin-bottom: 0.6rem;
        }}

        /* Diagnosis summary card */
        .agri-diagnosis {{
            background-color: {c['white']};
            border-radius: 14px;
            padding: 1.6rem;
            border-left: 6px solid {c['leaf']};
        }}
        .agri-diagnosis.is-disease {{
            border-left-color: {c['red']};
        }}
        .agri-diagnosis h2 {{
            margin: 0 0 0.2rem 0;
        }}
        .agri-diagnosis .agri-plant-label {{
            color: #6B7166;
            font-size: 0.9rem;
            margin-bottom: 0.6rem;
        }}

        /* Insight cards (irrigation / weather / sustainability / treatment) */
        .agri-insight {{
            background-color: {c['white']};
            border-radius: 12px;
            padding: 1.2rem 1.3rem;
            border-left: 5px solid var(--accent, {c['leaf']});
            margin-bottom: 0.9rem;
        }}
        .agri-insight h4 {{
            margin: 0 0 0.5rem 0;
            font-size: 1rem;
        }}
        .agri-insight ul {{
            margin: 0.4rem 0 0 0;
            padding-left: 1.1rem;
        }}
        .agri-insight li {{
            font-size: 0.92rem;
            margin-bottom: 0.2rem;
        }}
        .agri-insight p {{
            font-size: 0.92rem;
            margin: 0.2rem 0;
        }}

        /* Badges */
        .agri-badge {{
            display: inline-block;
            padding: 0.25rem 0.7rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
            font-family: {HEADING_FONT};
        }}

        /* Confidence bar */
        .agri-confidence-track {{
            background-color: #E7E2D6;
            border-radius: 999px;
            height: 10px;
            width: 100%;
            overflow: hidden;
            margin: 0.4rem 0;
        }}
        .agri-confidence-fill {{
            height: 100%;
            border-radius: 999px;
            background-color: {c['leaf']};
        }}

        /* History cards */
        .agri-history-card {{
            background-color: {c['white']};
            border-radius: 12px;
            padding: 1rem 1.2rem;
            border: 1px solid #E7E2D6;
            margin-bottom: 0.7rem;
        }}
        .agri-history-card .agri-history-meta {{
            color: #6B7166;
            font-size: 0.85rem;
        }}

        .agri-mock-note {{
            background-color: {c['sand']};
            border: 1px dashed #C9C1AC;
            border-radius: 10px;
            padding: 0.7rem 1rem;
            font-size: 0.85rem;
            color: #6B7166;
        }}

        .agri-section-title {{
            margin-top: 2.2rem;
            margin-bottom: 0.8rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Layout components
# ---------------------------------------------------------------------------

def render_hero(title: str, tagline: str) -> None:
    st.markdown(
        f"""
        <div class="agri-hero">
            <h1>{title}</h1>
            <p>{tagline}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def feature_card(icon: str, title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="agri-card">
            <div class="agri-card-icon">{icon}</div>
            <h4>{title}</h4>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def step_card(number: int, title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="agri-card">
            <div class="agri-step-num">{number}</div>
            <h4>{title}</h4>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def severity_badge(severity: str) -> str:
    """Returns an HTML badge string for a severity level (does not render)."""
    palette = {
        "Healthy": (COLORS["leaf_light"], COLORS["forest"]),
        "Mild": (COLORS["leaf_light"], COLORS["forest"]),
        "Moderate": ("#FBE8C8", "#8A5A1E"),
        "Severe": ("#F3C9C6", COLORS["red"]),
    }
    bg, fg = palette.get(severity, (COLORS["sand"], COLORS["charcoal"]))
    return f'<span class="agri-badge" style="background-color:{bg};color:{fg};">{severity}</span>'


def status_badge(status: str) -> str:
    is_healthy = status.lower().startswith("healthy")
    bg = COLORS["leaf_light"] if is_healthy else "#F3C9C6"
    fg = COLORS["forest"] if is_healthy else COLORS["red"]
    return f'<span class="agri-badge" style="background-color:{bg};color:{fg};">{status}</span>'


def diagnosis_summary(plant: str, disease: str, status: str, severity: str) -> None:
    is_disease = not status.lower().startswith("healthy")
    css_class = "agri-diagnosis is-disease" if is_disease else "agri-diagnosis"
    st.markdown(
        f"""
        <div class="{css_class}">
            <div class="agri-plant-label">Plant detected: {plant}</div>
            <h2>{disease}</h2>
            <div>{status_badge(status)}&nbsp;&nbsp;{severity_badge(severity)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def confidence_bar(confidence: float, note: str | None = None) -> None:
    """confidence is a 0-1 float."""
    pct = round(confidence * 100)
    color = COLORS["leaf"] if confidence >= 0.6 else COLORS["amber"]
    st.markdown(
        f"""
        <div>
            <strong>Disease Confidence — {pct}%</strong>
            <div class="agri-confidence-track">
                <div class="agri-confidence-fill" style="width:{pct}%; background-color:{color};"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if note:
        st.markdown(f'<div class="agri-mock-note">{note}</div>', unsafe_allow_html=True)


def insight_card(icon: str, title: str, lines: list[str], accent: str) -> None:
    items = "".join(f"<li>{line}</li>" for line in lines)
    st.markdown(
        f"""
        <div class="agri-insight" style="--accent:{accent};">
            <h4>{icon} {title}</h4>
            <ul>{items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mock_note(text: str) -> None:
    st.markdown(f'<div class="agri-mock-note">{text}</div>', unsafe_allow_html=True)


def section_title(text: str) -> None:
    st.markdown(f'<h3 class="agri-section-title">{text}</h3>', unsafe_allow_html=True)
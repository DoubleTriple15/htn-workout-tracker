"""
Unified Responsive Design System & Minimal-Morphism Theme for HTN.
Includes dynamic multi-theme engine, floating bottom-right INSTRUCTIONS button,
and Lifter Guide modal dialog.
"""

import json
import os
import streamlit as st

# =============================================================================
# THEME COLOR PALETTES & TOKENS
# =============================================================================
# Exact color palettes matching user specifications:
# 1. Original (Current Electric Lime)
# 2. Lush forest (#2E6F40, #CFFFDC, #68BA7F, #253D2C)
# 3. Chili spice (#CD1C18, #FFA896, #9B1313, #38000A)
# 4. Chocolate truffle (#713600, #C05800, #FDFBD4, #38240D)
# 5. Ink wash (#4A4A4A, #CBCBCB, #FFFFE3, #6D8196)
# 6. Hydrangea (#FF8DA1, #FFC2BA, #FF9CE9, #AD56C4)

THEMES = {
    "Original": {
        "name": "Original",
        "label": "Original",
        "subtitle": "Electric Lime on dark obsidian glass",
        "swatches": ["#b9ff2e", "#76c910", "#1a2414", "#0a0a0a"],
        "accent": "#b9ff2e",
        "accent_secondary": "#76c910",
        "accent_dim": "rgba(185, 255, 46, 0.12)",
        "accent_glow": "rgba(185, 255, 46, 0.32)",
        "bg": "#0a0a0a",
        "card": "#121412",
        "card_border": "#202420",
        "glass_card": "rgba(18, 20, 18, 0.72)",
        "glass_elevated": "rgba(24, 28, 24, 0.82)",
        "glass_border": "rgba(255, 255, 255, 0.08)",
        "glass_border_hover": "rgba(185, 255, 46, 0.40)",
        "morph_concave": "linear-gradient(145deg, rgba(22, 26, 22, 0.85), rgba(12, 14, 12, 0.85))",
        "btn_text": "#0a0a0a",
        "chart_line": "#b9ff2e",
        "chart_fill": "rgba(185, 255, 46, 0.08)",
    },
    "Lush forest": {
        "name": "Lush forest",
        "label": "Lush forest",
        "subtitle": "Emerald foliage, mint highlights, deep spruce glass",
        "swatches": ["#2E6F40", "#CFFFDC", "#68BA7F", "#253D2C"],
        "accent": "#58e688",
        "accent_secondary": "#2E6F40",
        "accent_dim": "rgba(88, 230, 136, 0.14)",
        "accent_glow": "rgba(88, 230, 136, 0.34)",
        "bg": "#08100a",
        "card": "#0f1c13",
        "card_border": "#1d3323",
        "glass_card": "rgba(15, 28, 19, 0.74)",
        "glass_elevated": "rgba(22, 38, 27, 0.84)",
        "glass_border": "rgba(207, 255, 220, 0.08)",
        "glass_border_hover": "rgba(88, 230, 136, 0.40)",
        "morph_concave": "linear-gradient(145deg, rgba(18, 34, 23, 0.85), rgba(10, 20, 13, 0.85))",
        "btn_text": "#051408",
        "chart_line": "#58e688",
        "chart_fill": "rgba(88, 230, 136, 0.08)",
    },
    "Chili spice": {
        "name": "Chili spice",
        "label": "Chili spice",
        "subtitle": "Crimson flame, coral glow, volcanic midnight glass",
        "swatches": ["#CD1C18", "#FFA896", "#9B1313", "#38000A"],
        "accent": "#ff3834",
        "accent_secondary": "#9B1313",
        "accent_dim": "rgba(255, 56, 52, 0.14)",
        "accent_glow": "rgba(255, 56, 52, 0.38)",
        "bg": "#0e0306",
        "card": "#19070a",
        "card_border": "#380c13",
        "glass_card": "rgba(25, 7, 10, 0.75)",
        "glass_elevated": "rgba(35, 11, 15, 0.84)",
        "glass_border": "rgba(255, 168, 150, 0.08)",
        "glass_border_hover": "rgba(255, 56, 52, 0.42)",
        "morph_concave": "linear-gradient(145deg, rgba(32, 10, 14, 0.85), rgba(16, 4, 7, 0.85))",
        "btn_text": "#ffffff",
        "chart_line": "#ff3834",
        "chart_fill": "rgba(255, 56, 52, 0.08)",
    },
    "Chocolate truffle": {
        "name": "Chocolate truffle",
        "label": "Chocolate truffle",
        "subtitle": "Roasted caramel, vanilla cream, espresso glass",
        "swatches": ["#713600", "#C05800", "#FDFBD4", "#38240D"],
        "accent": "#f57c00",
        "accent_secondary": "#713600",
        "accent_dim": "rgba(245, 124, 0, 0.14)",
        "accent_glow": "rgba(245, 124, 0, 0.36)",
        "bg": "#0c0804",
        "card": "#181008",
        "card_border": "#362211",
        "glass_card": "rgba(24, 16, 8, 0.75)",
        "glass_elevated": "rgba(34, 23, 12, 0.84)",
        "glass_border": "rgba(253, 251, 212, 0.08)",
        "glass_border_hover": "rgba(245, 124, 0, 0.42)",
        "morph_concave": "linear-gradient(145deg, rgba(30, 20, 10, 0.85), rgba(15, 10, 5, 0.85))",
        "btn_text": "#0c0804",
        "chart_line": "#f57c00",
        "chart_fill": "rgba(245, 124, 0, 0.08)",
    },
    "Ink wash": {
        "name": "Ink wash",
        "label": "Ink wash",
        "subtitle": "Slate indigo, platinum ivory, monochromatic glass",
        "swatches": ["#4A4A4A", "#CBCBCB", "#FFFFE3", "#6D8196"],
        "accent": "#7db3de",
        "accent_secondary": "#6D8196",
        "accent_dim": "rgba(125, 179, 222, 0.14)",
        "accent_glow": "rgba(125, 179, 222, 0.36)",
        "bg": "#0a0d10",
        "card": "#13181f",
        "card_border": "#232e3b",
        "glass_card": "rgba(19, 24, 31, 0.75)",
        "glass_elevated": "rgba(26, 33, 43, 0.84)",
        "glass_border": "rgba(255, 255, 227, 0.08)",
        "glass_border_hover": "rgba(125, 179, 222, 0.42)",
        "morph_concave": "linear-gradient(145deg, rgba(24, 31, 41, 0.85), rgba(13, 17, 23, 0.85))",
        "btn_text": "#0a0d10",
        "chart_line": "#7db3de",
        "chart_fill": "rgba(125, 179, 222, 0.08)",
    },
    "Hydrangea": {
        "name": "Hydrangea",
        "label": "Hydrangea",
        "subtitle": "Neon magenta petals, orchid violet, amethyst glass",
        "swatches": ["#FF8DA1", "#FFC2BA", "#FF9CE9", "#AD56C4"],
        "accent": "#ff73a9",
        "accent_secondary": "#AD56C4",
        "accent_dim": "rgba(255, 115, 169, 0.14)",
        "accent_glow": "rgba(255, 115, 169, 0.38)",
        "bg": "#0f0514",
        "card": "#1a0b22",
        "card_border": "#38144b",
        "glass_card": "rgba(26, 11, 34, 0.75)",
        "glass_elevated": "rgba(36, 16, 48, 0.84)",
        "glass_border": "rgba(255, 141, 161, 0.08)",
        "glass_border_hover": "rgba(255, 115, 169, 0.44)",
        "morph_concave": "linear-gradient(145deg, rgba(34, 14, 46, 0.85), rgba(17, 7, 23, 0.85))",
        "btn_text": "#0f0514",
        "chart_line": "#ff73a9",
        "chart_fill": "rgba(255, 115, 169, 0.08)",
    },
}


def clean_css(css: str) -> str:
    """Removes leading and trailing whitespace from each line to prevent markdown code block formatting."""
    return "\n".join(line.strip() for line in (css or "").split("\n") if line.strip())


def clean_html(html: str) -> str:
    """Strip leading spaces to ensure CommonMark HTML block compliance."""
    return "\n".join(line.lstrip() for line in (html or "").split("\n"))


def get_active_theme_name() -> str:
    """Retrieves the active theme name from Streamlit session state, database, or persisted global setting."""
    try:
        pref = st.session_state.get("theme_pref")
        if pref and pref in THEMES:
            return pref
    except Exception:
        pass

    try:
        user = st.session_state.get("user")
        if isinstance(user, dict) and user.get("theme_pref") in THEMES:
            t = user["theme_pref"]
            try:
                st.session_state.theme_pref = t
            except Exception:
                pass
            return t
    except Exception:
        pass

    # Check auth_user_id in session state if available
    try:
        uid = st.session_state.get("auth_user_id")
        if uid:
            from db.database import get_theme_pref
            t = get_theme_pref(int(uid))
            if t in THEMES:
                try:
                    st.session_state.theme_pref = t
                except Exception:
                    pass
                return t
    except Exception:
        pass

    # Check global persistent setting in SQLite
    try:
        from db.database import get_global_setting
        global_t = get_global_setting("last_active_theme")
        if global_t in THEMES:
            try:
                st.session_state.theme_pref = global_t
            except Exception:
                pass
            return global_t
    except Exception:
        pass

    # Fallback to local session file if user_id is cached on disk
    try:
        from auth import SESSION_FILE
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                cached_uid = data.get("user_id")
                if cached_uid:
                    from db.database import get_theme_pref
                    t = get_theme_pref(int(cached_uid))
                    if t in THEMES:
                        try:
                            st.session_state.theme_pref = t
                        except Exception:
                            pass
                        return t
    except Exception:
        pass

    return "Original"


def get_theme_tokens(theme_name: str | None = None) -> dict:
    """Returns the color tokens dictionary for the given or currently active theme."""
    name = theme_name or get_active_theme_name()
    return THEMES.get(name, THEMES["Original"])


def get_theme_css(theme_name: str | None = None) -> str:
    """Generates the dynamic CSS variable definitions and signature neon glow styles (raw CSS rules, no style tags)."""
    t = get_theme_tokens(theme_name)
    raw = f"""
:root {{
    --bg: {t['bg']} !important;
    --card: {t['card']} !important;
    --card-border: {t['card_border']} !important;
    --accent: {t['accent']} !important;
    --accent-secondary: {t['accent_secondary']} !important;
    --accent-dim: {t['accent_dim']} !important;
    --accent-glow: {t['accent_glow']} !important;
    --text: #f5f5f5 !important;
    --text-dim: #8f938f !important;
    --text-dimmer: #5f635f !important;

    --glass-card: {t['glass_card']} !important;
    --glass-elevated: {t['glass_elevated']} !important;
    --glass-border: {t['glass_border']} !important;
    --glass-border-hover: {t['glass_border_hover']} !important;
    --glass-highlight: inset 0 1px 1px 0 rgba(255, 255, 255, 0.10) !important;
    --glass-shadow: 0 14px 36px 0 rgba(0, 0, 0, 0.55) !important;
    --glass-inset: inset 0 2px 4px 0 rgba(0, 0, 0, 0.5) !important;
    --morph-concave: {t['morph_concave']} !important;
    --btn-text: {t['btn_text']} !important;
}}

/* Global Glow & Minimal-Morphism Components */
.htn-badge {{
    background: var(--accent-dim) !important;
    color: var(--accent) !important;
    border: 1px solid var(--accent) !important;
    box-shadow: inset 0 0 12px var(--accent-glow), 0 0 8px var(--accent-glow) !important;
}}

.stButton > button[kind="primary"] {{
    background: var(--accent) !important;
    color: var(--btn-text) !important;
    border: 1px solid var(--accent) !important;
    box-shadow: 0 6px 24px var(--accent-glow), inset 0 1px 1px rgba(255, 255, 255, 0.5) !important;
}}

.stButton > button:hover {{
    border-color: var(--glass-border-hover) !important;
    box-shadow: 0 8px 26px -2px rgba(0, 0, 0, 0.55), 0 0 16px var(--accent-glow), var(--glass-highlight) !important;
}}

.htn-card:hover {{
    border-color: var(--glass-border-hover) !important;
    box-shadow: 0 18px 40px 0 rgba(0, 0, 0, 0.65), 0 0 16px var(--accent-glow), var(--glass-highlight) !important;
}}

.st-key-chatbot_fab button {{
    border: 1.5px solid var(--accent) !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.7), 0 0 16px var(--accent-glow) !important;
    color: var(--accent) !important;
}}

.st-key-chatbot_fab button:hover {{
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.8), 0 0 24px var(--accent-glow) !important;
    border-color: var(--accent) !important;
}}

.hm-week-dot.active {{
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    box-shadow: 0 0 10px var(--accent-glow) !important;
}}

.st-key-bottom_nav button:hover {{
    border-color: transparent !important;
    background: transparent !important;
    transform: none !important;
}}

/* ── Minimal-Morphic BaseWeb Select & MultiSelect Engine ── */
div[data-testid="stSelectbox"], div[data-testid="stMultiSelect"] {{
    width: 100% !important;
    margin-bottom: 8px !important;
}}

div[data-testid="stWidgetLabel"] label,
div[data-testid="stWidgetLabel"] p {{
    font-size: 12px !important;
    font-weight: 700 !important;
    color: var(--text-dim) !important;
    letter-spacing: 0.3px !important;
    text-transform: uppercase !important;
    margin-bottom: 6px !important;
}}

/* Selectbox Trigger Control Box */
div[data-baseweb="select"] > div {{
    background: var(--glass-card) !important;
    background-image: var(--morph-concave) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 14px !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35), var(--glass-highlight) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    min-height: 44px !important;
    padding: 2px 10px !important;
    cursor: pointer !important;
    transition: all 0.22s var(--ease-out) !important;
}}

/* Hover state */
div[data-baseweb="select"]:hover > div {{
    border-color: var(--glass-border-hover) !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.45), 0 0 16px var(--accent-glow), var(--glass-highlight) !important;
    transform: translateY(-1px) !important;
}}

/* Active / Focused / Opened state */
div[data-baseweb="select"]:focus-within > div,
div[data-baseweb="select"] > div:focus-within {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 1px var(--accent), 0 0 20px var(--accent-glow) !important;
    background: var(--glass-elevated) !important;
}}

/* Text & Selected Value Inside Trigger Box */
div[data-baseweb="select"] div[aria-selected="true"],
div[data-baseweb="select"] [data-testid="stSelectbox"] div,
div[data-baseweb="select"] span {{
    color: var(--text) !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
}}

/* Input inside Select (searchable selectbox) */
div[data-baseweb="select"] input {{
    color: var(--text) !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
}}

/* Dropdown Chevron & Clear Icon */
div[data-baseweb="select"] svg {{
    color: var(--accent) !important;
    fill: var(--accent) !important;
    transition: transform 0.2s ease, color 0.2s ease !important;
}}

div[data-baseweb="select"]:hover svg {{
    filter: drop-shadow(0 0 6px var(--accent-glow));
}}

/* Popover Dropdown Menu (Floating list) */
div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
div[data-baseweb="menu"],
ul[role="listbox"] {{
    background: var(--glass-elevated) !important;
    background-color: var(--card) !important;
    border: 1px solid var(--glass-border-hover) !important;
    border-radius: 14px !important;
    box-shadow: 0 20px 48px rgba(0, 0, 0, 0.85), 0 0 24px var(--accent-glow) !important;
    backdrop-filter: blur(28px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
    padding: 6px !important;
    margin-top: 4px !important;
    overflow: hidden !important;
}}

/* Listbox Options */
li[role="option"],
li[data-baseweb="menu-item"],
div[role="option"] {{
    background: transparent !important;
    border: 1px solid transparent !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
    padding: 9px 14px !important;
    margin: 2px 0 !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
}}

/* Hover & Active Option */
li[role="option"]:hover,
li[role="option"][aria-selected="true"],
li[role="option"]:focus,
li[data-highlighted="true"] {{
    background: var(--accent-dim) !important;
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    box-shadow: 0 0 14px var(--accent-glow) !important;
    transform: translateX(2px) !important;
}}

li[role="option"] svg {{
    color: var(--accent) !important;
    fill: var(--accent) !important;
}}

ul[role="listbox"]::-webkit-scrollbar {{
    width: 6px !important;
}}
ul[role="listbox"]::-webkit-scrollbar-track {{
    background: transparent !important;
}}
ul[role="listbox"]::-webkit-scrollbar-thumb {{
    background: var(--glass-border-hover) !important;
    border-radius: 999px !important;
}}
ul[role="listbox"]::-webkit-scrollbar-thumb:hover {{
    background: var(--accent) !important;
}}

/* MultiSelect Tag Chips (Pills) */
div[data-baseweb="tag"] {{
    background: var(--accent-dim) !important;
    border: 1px solid var(--accent) !important;
    border-radius: 8px !important;
    color: var(--accent) !important;
    box-shadow: 0 0 10px var(--accent-glow) !important;
    padding: 4px 8px !important;
    margin: 2px 4px 2px 0 !important;
    transition: all 0.2s ease !important;
}}

div[data-baseweb="tag"] span {{
    color: var(--accent) !important;
    font-weight: 700 !important;
    font-size: 12px !important;
}}

div[data-baseweb="tag"] svg {{
    color: var(--accent) !important;
    fill: var(--accent) !important;
}}

div[data-baseweb="tag"]:hover {{
    box-shadow: 0 0 16px var(--accent-glow) !important;
    border-color: #ffffff !important;
}}

/* ── Minimal-Morphic Inputs (Text & Number) ── */
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div {{
    background: var(--glass-card) !important;
    background-image: var(--morph-concave) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 12px !important;
    color: var(--text) !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35), var(--glass-highlight) !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}}

div[data-baseweb="input"]:hover > div,
div[data-baseweb="textarea"]:hover > div {{
    border-color: var(--glass-border-hover) !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.45), 0 0 12px var(--accent-glow) !important;
}}

div[data-baseweb="input"]:focus-within > div,
div[data-baseweb="textarea"]:focus-within > div {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 1px var(--accent), 0 0 18px var(--accent-glow) !important;
}}

div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea {{
    color: var(--text) !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
}}

/* Number input step buttons */
button[data-testid="stNumberInputStepDown"],
button[data-testid="stNumberInputStepUp"] {{
    background: transparent !important;
    color: var(--text-dim) !important;
    border: none !important;
    transition: color 0.15s ease !important;
}}

button[data-testid="stNumberInputStepDown"]:hover,
button[data-testid="stNumberInputStepUp"]:hover {{
    color: var(--accent) !important;
}}

button[data-testid="stNumberInputStepDown"] svg,
button[data-testid="stNumberInputStepUp"] svg {{
    fill: currentColor !important;
}}

/* ── Radio Buttons ── */
div[data-testid="stRadio"] div[role="radiogroup"] label {{
    color: var(--text) !important;
    font-size: 13px !important;
    font-weight: 600 !important;
}}

div[data-baseweb="radio"] div:first-child {{
    border-color: var(--glass-border-hover) !important;
    background: transparent !important;
}}

div[data-baseweb="radio"] input:checked + div {{
    border-color: var(--accent) !important;
    background-color: var(--accent) !important;
    box-shadow: 0 0 12px var(--accent-glow) !important;
}}

/* ── Tabs ── */
button[data-baseweb="tab"] {{
    color: var(--text-dim) !important;
    font-weight: 700 !important;
    font-size: 13.5px !important;
    transition: all 0.2s ease !important;
}}

button[data-baseweb="tab"]:hover {{
    color: var(--text) !important;
}}

button[data-baseweb="tab"][aria-selected="true"] {{
    color: var(--accent) !important;
    text-shadow: 0 0 12px var(--accent-glow) !important;
}}

div[data-baseweb="tab-highlight"] {{
    background-color: var(--accent) !important;
    box-shadow: 0 0 14px var(--accent-glow) !important;
}}

/* ── Minimal-Morphism Accordion Cards (stExpander) ── */
div[data-testid="stExpander"] {{
    background: var(--glass-card) !important;
    background-image: var(--morph-concave) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 16px !important;
    margin-bottom: 12px !important;
    overflow: hidden !important;
    box-shadow: var(--glass-shadow), var(--glass-highlight) !important;
    backdrop-filter: blur(20px) saturate(160%) !important;
    -webkit-backdrop-filter: blur(20px) saturate(160%) !important;
    transition: all 0.22s var(--ease-out) !important;
}}

div[data-testid="stExpander"]:hover {{
    border-color: var(--glass-border-hover) !important;
    box-shadow: 0 18px 40px rgba(0, 0, 0, 0.65), 0 0 16px var(--accent-glow), var(--glass-highlight) !important;
    transform: translateY(-1px) !important;
}}

div[data-testid="stExpander"] summary {{
    padding: 13px 18px !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    color: var(--text) !important;
    cursor: pointer !important;
    transition: color 0.18s ease !important;
}}

div[data-testid="stExpander"] summary:hover {{
    color: var(--accent) !important;
}}

div[data-testid="stExpander"] summary svg {{
    color: var(--accent) !important;
    fill: var(--accent) !important;
    transition: transform 0.2s ease !important;
}}

div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
    padding: 14px 18px 16px 18px !important;
    background: rgba(0, 0, 0, 0.25) !important;
    border-top: 1px solid var(--glass-border) !important;
}}

/* ── DataFrames & Tables ── */
div[data-testid="stDataFrame"] {{
    border-radius: 16px !important;
    overflow: hidden !important;
    border: 1px solid var(--glass-border) !important;
    background: var(--card) !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45), var(--glass-highlight) !important;
}}

div[data-testid="stDataFrame"]:hover {{
    border-color: var(--glass-border-hover) !important;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.55), 0 0 16px var(--accent-glow) !important;
}}
"""
    return clean_css(raw)


BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

:root {
    --bg: #0a0a0a;
    --card: #121412;
    --card-border: #202420;
    --accent: #b9ff2e;
    --accent-dim: rgba(185, 255, 46, 0.12);
    --accent-glow: rgba(185, 255, 46, 0.28);
    --text: #f5f5f5;
    --text-dim: #8f938f;
    --text-dimmer: #5f635f;

    --glass-card: rgba(18, 20, 18, 0.72);
    --glass-elevated: rgba(24, 28, 24, 0.82);
    --glass-border: rgba(255, 255, 255, 0.08);
    --glass-border-hover: rgba(185, 255, 46, 0.38);
    --glass-highlight: inset 0 1px 1px 0 rgba(255, 255, 255, 0.10);
    --glass-shadow: 0 14px 36px 0 rgba(0, 0, 0, 0.55);
    --glass-inset: inset 0 2px 4px 0 rgba(0, 0, 0, 0.5);
    --morph-concave: linear-gradient(145deg, rgba(22, 26, 22, 0.85), rgba(12, 14, 12, 0.85));

    --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
    --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
}

html, body, [class*="css"] { 
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    letter-spacing: -0.015em;
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
}

#MainMenu, header, footer, [data-testid="stHeader"] { 
    display: none !important; 
    visibility: hidden !important; 
    height: 0 !important; 
    min-height: 0 !important; 
    padding: 0 !important; 
    margin: 0 !important; 
}
[data-testid="stAppViewContainer"] { background: var(--bg) !important; }
[data-testid="stAppViewBlockContainer"] { padding: 0 !important; }
[data-testid="stSidebar"] { display: none !important; }
section[data-testid="stMain"],
section[data-testid="stMain"] > div { 
    padding-top: 0 !important; 
}

body, .stApp { 
    background-color: var(--bg) !important; 
    color: var(--text) !important; 
    touch-action: manipulation;
    -webkit-tap-highlight-color: transparent;
}

/* Fluid Viewport Engine */
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
section[data-testid="stMain"],
div[data-testid="stMain"],
.main,
.block-container {
    transform: none !important;
    filter: none !important;
    perspective: none !important;
    contain: none !important;
}

.block-container {
    width: 100% !important;
    max-width: 1240px !important;
    padding: 12px clamp(1rem, 2.5vw, 2.5rem) 88px clamp(1rem, 2.5vw, 2.5rem) !important;
    margin: 0 auto !important;
    box-sizing: border-box !important;
    animation: htnCrossFade 0.15s ease-out;
}

[data-testid="stVerticalBlock"] {
    gap: 10px !important;
}

@media (max-width: 1024px) {
    .block-container {
        max-width: 95% !important;
        padding: 10px 1.2rem 88px 1.2rem !important;
    }
}

@media (max-width: 640px) {
    .block-container {
        max-width: 100% !important;
        padding: 10px 12px 96px 12px !important;
    }
}

@keyframes htnCrossFade {
    0% { opacity: 0.85; }
    100% { opacity: 1; }
}

/* Minimal-Morphism Containers & Universal Card Self-Adjustment */
.htn-card,
.wk-card,
.wk-routine-card,
.wk-exercise-card,
.wk-exercise-box,
.wk-exercise-box-compact,
.htn-meso-container,
.htn-period-ex-card,
.hm-card,
.hm-pr-card,
.hm-target-card,
.pf-header-card,
.pf-stat-card,
.pf-edit-card,
.pf-settings-card,
.pf-metric,
div[class*="st-key-wk_set_card_"],
div[class*="st-key-hub_routine_"],
div[class*="st-key-manage_r_"],
div[class*="st-key-manage_sess_"],
div[class*="st-key-manage_ex_"] {
    height: auto !important;
    min-height: auto !important;
    max-height: none !important;
    overflow: visible !important;
    box-sizing: border-box !important;
    word-break: break-word !important;
    overflow-wrap: anywhere !important;
}

.htn-card {
    background: var(--glass-card);
    background-image: var(--morph-concave);
    border: 1px solid var(--glass-border);
    box-shadow: var(--glass-shadow), var(--glass-highlight);
    backdrop-filter: blur(20px) saturate(160%);
    -webkit-backdrop-filter: blur(20px) saturate(160%);
    border-radius: 16px;
    padding: clamp(14px, 2vw, 20px);
    margin-bottom: 16px;
    width: 100%;
    box-sizing: border-box;
    transition: transform 0.22s var(--ease-out), border-color 0.22s var(--ease-out), box-shadow 0.22s var(--ease-out);
}

.htn-card:hover {
    border-color: var(--glass-border-hover);
    box-shadow: 0 18px 40px 0 rgba(0, 0, 0, 0.65), 0 0 16px var(--accent-glow), var(--glass-highlight);
    transform: translateY(-2px);
}

.htn-section-head { 
    display: flex; 
    justify-content: space-between; 
    align-items: center; 
    margin: 4px 0 10px 0;
    width: 100%;
}

.htn-section-title { 
    font-size: clamp(18px, 2vw, 23px); 
    font-weight: 800; 
    letter-spacing: -0.035em;
    color: var(--text); 
}

.htn-badge {
    background: var(--accent-dim);
    color: var(--accent);
    border: 1px solid var(--accent);
    box-shadow: inset 0 0 12px var(--accent-glow), 0 0 8px var(--accent-glow);
    padding: 5px 13px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.03em;
    white-space: nowrap;
}

/* Tactile Buttons */
.stButton > button {
    all: unset;
    box-sizing: border-box;
    cursor: pointer;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    padding: clamp(9px, 1.2vw, 13px) clamp(14px, 2vw, 20px);
    font-size: clamp(12.5px, 1vw, 14px);
    font-weight: 700;
    color: var(--text);
    background: var(--glass-card);
    background-image: linear-gradient(145deg, rgba(28, 32, 28, 0.8), rgba(16, 18, 16, 0.8));
    border: 1px solid var(--glass-border);
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35), var(--glass-highlight);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    transition: transform 0.18s var(--ease-spring), background 0.18s var(--ease-out), border-color 0.18s var(--ease-out), box-shadow 0.18s var(--ease-out);
}

.stButton > button p { margin: 0; }

.stButton > button:hover {
    transform: translateY(-2px);
    background: rgba(34, 40, 34, 0.95);
    border-color: var(--glass-border-hover);
    box-shadow: 0 8px 26px -2px rgba(0, 0, 0, 0.55), 0 0 16px var(--accent-glow), var(--glass-highlight);
    color: #ffffff;
}

.stButton > button:active {
    transform: scale(0.96) translateY(1px) !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4), var(--glass-inset) !important;
}

.stButton > button[kind="primary"] {
    background: var(--accent) !important;
    color: #0a0a0a !important;
    border: 1px solid var(--accent) !important;
    box-shadow: 0 6px 24px var(--accent-glow), inset 0 1px 1px rgba(255, 255, 255, 0.5) !important;
}

/* Permanently Pinned Docked Bottom Navigation Bar */
div.st-key-bottom_nav,
div[class*="st-key-bottom_nav"] {
    position: fixed !important; 
    bottom: 0 !important; 
    left: 0 !important; 
    right: 0 !important; 
    top: auto !important;
    transform: none !important;
    width: 100vw !important;
    max-width: 100vw !important;
    box-sizing: border-box !important;
    background: rgba(14, 16, 22, 0.96) !important;
    border: none !important;
    border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
    box-shadow: 0 -8px 32px rgba(0, 0, 0, 0.75) !important;
    backdrop-filter: blur(28px) saturate(190%) !important;
    -webkit-backdrop-filter: blur(28px) saturate(190%) !important;
    border-radius: 20px 20px 0 0 !important;
    padding: 10px 16px max(24px, env(safe-area-inset-bottom, 24px)) 16px !important;
    z-index: 999999 !important;
    overflow: visible !important;
    animation: none !important;
    contain: layout style !important;
}

div.st-key-bottom_nav [data-testid="stHorizontalBlock"],
div[class*="st-key-bottom_nav"] [data-testid="stHorizontalBlock"],
div.st-key-bottom_nav div.stHorizontalBlock,
div[class*="st-key-bottom_nav"] div.stHorizontalBlock { 
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 4px !important; 
    align-items: center !important; 
    justify-content: space-around !important;
    width: 100% !important;
    max-width: 580px !important;
    margin: 0 auto !important;
}

div.st-key-bottom_nav [data-testid="stColumn"],
div[class*="st-key-bottom_nav"] [data-testid="stColumn"],
div.st-key-bottom_nav div.stColumn,
div[class*="st-key-bottom_nav"] div.stColumn,
div.st-key-bottom_nav [data-testid="column"],
div.st-key-bottom_nav div[data-testid*="Column" i],
div.st-key-bottom_nav div[data-testid*="column" i],
div.st-key-bottom_nav div[class*="stColumn"],
div[class*="st-key-bottom_nav"] [data-testid="stHorizontalBlock"] > div,
div[class*="st-key-bottom_nav"] .stHorizontalBlock > div {
    min-width: 0 !important;
    max-width: 25% !important;
    width: 25% !important;
    flex: 1 1 0% !important;
    box-sizing: border-box !important;
}

div.st-key-bottom_nav [data-testid="stElementContainer"],
div[class*="st-key-bottom_nav"] [data-testid="stElementContainer"],
div.st-key-bottom_nav div.element-container,
div[class*="st-key-bottom_nav"] div.element-container {
    width: 100% !important;
    min-width: 0 !important;
}

div.st-key-bottom_nav button,
div[class*="st-key-bottom_nav"] button {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    display: flex !important;
    flex-direction: column !important; 
    align-items: center !important;
    justify-content: center !important;
    gap: 3px !important; 
    font-size: 11px !important; 
    font-weight: 500 !important; 
    padding: 6px 2px 8px 2px !important;
    border-radius: 0 !important;
    width: 100% !important;
    min-width: 0 !important;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    position: relative !important;
    -webkit-tap-highlight-color: transparent !important;
}

div.st-key-bottom_nav button:active,
div.st-key-bottom_nav button:focus,
div.st-key-bottom_nav button:focus-visible,
div.st-key-bottom_nav button:focus:not(:active),
div[class*="st-key-bottom_nav"] button:active,
div[class*="st-key-bottom_nav"] button:focus,
div[class*="st-key-bottom_nav"] button:focus-visible,
div[class*="st-key-bottom_nav"] button:focus:not(:active),
div.st-key-bottom_nav button:active > div,
div.st-key-bottom_nav button:focus > div {
    background: transparent !important;
    background-color: transparent !important;
    border-color: transparent !important;
    outline: none !important;
    box-shadow: none !important;
    transform: none !important;
}

div.st-key-bottom_nav button p,
div[class*="st-key-bottom_nav"] button p { 
    font-size: 11px !important; 
    font-weight: 500 !important;
    margin: 0 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    line-height: 1.2 !important;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
}

div.st-key-bottom_nav button:hover,
div[class*="st-key-bottom_nav"] button:hover {
    background: transparent !important;
    background-color: transparent !important;
    border-color: transparent !important;
    box-shadow: none !important;
    transform: none !important;
}

@media (max-width: 768px) {
    div.st-key-bottom_nav,
    div[class*="st-key-bottom_nav"] {
        padding: 8px 10px max(24px, env(safe-area-inset-bottom, 24px)) 10px !important;
        border-radius: 20px 20px 0 0 !important;
        width: 100vw !important;
        max-width: 100vw !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        top: auto !important;
        transform: none !important;
    }
    div.st-key-bottom_nav [data-testid="stHorizontalBlock"],
    div[class*="st-key-bottom_nav"] [data-testid="stHorizontalBlock"],
    div.st-key-bottom_nav div.stHorizontalBlock,
    div[class*="st-key-bottom_nav"] div.stHorizontalBlock {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 2px !important;
        width: 100% !important;
        max-width: 100% !important;
    }
    div.st-key-bottom_nav [data-testid="stColumn"],
    div[class*="st-key-bottom_nav"] [data-testid="stColumn"],
    div.st-key-bottom_nav div.stColumn,
    div[class*="st-key-bottom_nav"] div.stColumn,
    div.st-key-bottom_nav [data-testid="column"],
    div.st-key-bottom_nav div[data-testid*="Column" i],
    div.st-key-bottom_nav div[data-testid*="column" i],
    div.st-key-bottom_nav div[class*="stColumn"],
    div[class*="st-key-bottom_nav"] [data-testid="stHorizontalBlock"] > div,
    div[class*="st-key-bottom_nav"] .stHorizontalBlock > div {
        width: 25% !important;
        max-width: 25% !important;
        flex: 1 1 0% !important;
        min-width: 0 !important;
    }
    div.st-key-bottom_nav button,
    div[class*="st-key-bottom_nav"] button {
        padding: 6px 1px 6px 1px !important;
        border-radius: 0 !important;
        gap: 2px !important;
    }
    div.st-key-bottom_nav button p,
    div[class*="st-key-bottom_nav"] button p {
        font-size: 10px !important;
        white-space: nowrap !important;
    }
}

"""


def inject_theme_css(extra_css: str = "", theme_name: str | None = None) -> None:
    """Safely injects theme tokens, base styles, mobile PWA meta tags, and extra page CSS."""
    combined = f"{get_theme_css(theme_name)}\n{BASE_CSS}\n{extra_css}"
    mobile_meta = (
        '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">'
        '<meta name="apple-mobile-web-app-capable" content="yes">'
        '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">'
        '<meta name="mobile-web-app-capable" content="yes">'
        '<meta name="theme-color" content="#0a0a0a">'
    )
    st.markdown(f"{mobile_meta}\n<style>\n{clean_css(combined)}\n</style>", unsafe_allow_html=True)


def icon(name, color=None, size=20, stroke_width=2):
    """Feather-style scalable inline SVG icons, inheriting active theme accent color."""
    if color is None or color == "#b9ff2e":
        color = get_theme_tokens()["accent"]

    icons = {
        "dumbbell": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round"><path d="M6.5 6.5 17.5 17.5"/><path d="M21 21l-3-3"/><path d="M3 3l3 3"/><path d="M17 3l4 4-3 3-4-4z"/><path d="M3 17l4 4 3-3-4-4z"/></svg>',
        "scale": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="3"/><circle cx="12" cy="12" r="1"/></svg>',
        "trend": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 17 9 11 13 15 21 6"/><polyline points="15 6 21 6 21 12"/></svg>',
        "clock": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="9" r="9"/><polyline points="12 7 12 12 16 14"/></svg>',
        "flame": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>',
        "bench-press": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round"><line x1="2" y1="8" x2="22" y2="8"/><circle cx="4" cy="8" r="2.2"/><circle cx="20" cy="8" r="2.2"/><rect x="7" y="14" width="10" height="3" rx="1"/><line x1="9" y1="17" x2="9" y2="20"/><line x1="15" y1="17" x2="15" y2="20"/></svg>',
        "user": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/></svg>',
        "palette": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round"><circle cx="13.5" cy="6.5" r=".5" fill="{color}"/><circle cx="17.5" cy="10.5" r=".5" fill="{color}"/><circle cx="8.5" cy="7.5" r=".5" fill="{color}"/><circle cx="6.5" cy="12.5" r=".5" fill="{color}"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.563-2.512 5.563-5.563C22 6.5 17.5 2 12 2z"/></svg>',
        "check": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
        "chevron-right": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>',
    }
    return icons.get(name, "")


def _resolve_target(preferred: str, fallback: str) -> str:
    return preferred if os.path.exists(preferred) else fallback


NAV_ITEMS = [
    ("nav_home", ":material/home:", "Home", "home", "Home.py"),
    ("nav_workout", ":material/fitness_center:", "Workout", "workout", "pages/workout.py"),
    ("nav_progression", ":material/trending_up:", "Progression", "progression", "pages/progression.py"),
    ("nav_profile", ":material/person:", "Profile", "profile", _resolve_target("pages/Profile.py", "pages/profile.py")),
]


def _nav_button_css(active):
    rules = []
    for key, _, _, tab_id, _ in NAV_ITEMS:
        is_active = tab_id == active
        if is_active:
            rules.append(f"""
.st-key-{key} button,
.st-key-{key} button [data-testid="stIconMaterial"],
.st-key-{key} button span,
.st-key-{key} button p {{
    color: var(--accent) !important;
    fill: var(--accent) !important;
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    text-shadow: 0 0 10px var(--accent-glow) !important;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
}}
.st-key-{key} button::after {{
    content: "" !important;
    position: absolute !important;
    bottom: 0px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: 28px !important;
    height: 3px !important;
    background: var(--accent) !important;
    border-radius: 999px 999px 0 0 !important;
    box-shadow: 0 -2px 10px var(--accent-glow) !important;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
}}
""")
        else:
            rules.append(f"""
.st-key-{key} button,
.st-key-{key} button [data-testid="stIconMaterial"],
.st-key-{key} button span,
.st-key-{key} button p {{
    color: rgba(255, 255, 255, 0.55) !important;
    fill: rgba(255, 255, 255, 0.55) !important;
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    text-shadow: none !important;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
}}
.st-key-{key} button:hover,
.st-key-{key} button:hover [data-testid="stIconMaterial"],
.st-key-{key} button:hover span,
.st-key-{key} button:hover p {{
    color: rgba(255, 255, 255, 0.85) !important;
    fill: rgba(255, 255, 255, 0.85) !important;
    text-shadow: 0 0 6px rgba(255, 255, 255, 0.2) !important;
}}
.st-key-{key} button::after {{
    content: "" !important;
    position: absolute !important;
    bottom: 0px !important;
    left: 50% !important;
    transform: translateX(-50%) scaleX(0.4) !important;
    opacity: 0 !important;
    width: 28px !important;
    height: 3px !important;
    background: var(--accent) !important;
    border-radius: 999px 999px 0 0 !important;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
}}
""")
    return clean_css("\n".join(rules))


def render_nav_bar(active):
    """Renders the fixed bottom navigation dock with dynamic theme styling and glow."""
    dock_override = """
div.st-key-bottom_nav [data-testid="stHorizontalBlock"],
div[class*="st-key-bottom_nav"] [data-testid="stHorizontalBlock"],
div.st-key-bottom_nav div.stHorizontalBlock,
div[class*="st-key-bottom_nav"] div.stHorizontalBlock {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 4px !important;
    width: 100% !important;
    max-width: 580px !important;
    margin: 0 auto !important;
}
div.st-key-bottom_nav [data-testid="stColumn"],
div[class*="st-key-bottom_nav"] [data-testid="stColumn"],
div.st-key-bottom_nav div.stColumn,
div[class*="st-key-bottom_nav"] div.stColumn,
div.st-key-bottom_nav [data-testid="column"],
div.st-key-bottom_nav div[data-testid*="Column" i],
div.st-key-bottom_nav div[data-testid*="column" i],
div.st-key-bottom_nav div[class*="stColumn"],
div[class*="st-key-bottom_nav"] [data-testid="stHorizontalBlock"] > div,
div[class*="st-key-bottom_nav"] .stHorizontalBlock > div {
    min-width: 0 !important;
    max-width: 25% !important;
    width: 25% !important;
    flex: 1 1 0% !important;
    box-sizing: border-box !important;
}
"""
    nav_rules = f"{get_theme_css()}\n{_nav_button_css(active)}\n{dock_override}"
    st.markdown(f"<style>\n{clean_css(nav_rules)}\n</style>", unsafe_allow_html=True)
    with st.container(key="bottom_nav"):
        cols = st.columns(4)
        for col, (key, icon_code, label, tab_id, target) in zip(cols, NAV_ITEMS):
            with col:
                if st.button(label, icon=icon_code, key=key, use_container_width=True):
                    if target and os.path.exists(target):
                        st.switch_page(target)
                    else:
                        st.toast(f"{label} tab is loading...")


# =============================================================================
# INSTRUCTIONS & BEGINNER GUIDE MODAL
# =============================================================================
def _render_instructions_ui():
    """Renders the comprehensive beginner guide and instructions inside the dialog."""
    st.markdown(clean_html("""
    <div style="
        background: var(--accent-dim);
        border: 1px solid var(--accent);
        box-shadow: 0 0 14px var(--accent-glow);
        border-radius: 14px;
        padding: 12px 16px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 12px;
    ">
        <div>
            <div style="font-size: 13px; font-weight: 800; color: var(--accent); text-transform: uppercase; letter-spacing: 0.5px;">
                IMPORTANT NOTE
            </div>
            <div style="font-size: 13px; color: #f5f5f5; font-weight: 600;">
                This is mainly focused for Intermediate to advanced lifters.
            </div>
        </div>
    </div>
    <div style="margin-bottom: 18px;">
        <h3 style="font-size: 20px; font-weight: 800; color: #f5f5f5; margin: 0 0 6px 0;">Beginner Guide</h3>
        <p style="font-size: 13px; color: #8f938f; line-height: 1.5; margin: 0;">
            HTN is designed primarily for intermediate and advanced lifters. If you are a beginner, focus on building a strong foundation before worrying about advanced techniques, high training volume, or complex programs.
        </p>
    </div>
    """), unsafe_allow_html=True)

    tab_train, tab_diet, tab_rec = st.tabs(["Training", "Nutrition", "Recovery"])

    with tab_train:
        st.markdown(clean_html("""
        <div style="padding: 10px 4px;">
            <p style="font-size: 13.5px; color: #f5f5f5; line-height: 1.5;">
                As a beginner, your main goal is to learn proper exercise technique and build consistency.<br>
                Start with basic movements that train all major muscle groups. Use manageable weights and prioritize controlled, full-range repetitions over lifting as heavy as possible.<br>
                You do not need to train to failure on every set. Leave a few good repetitions in reserve and gradually increase the weight or repetitions as you become stronger.
            </p>
            <div style="font-size: 13px; font-weight: 700; color: var(--accent); margin: 12px 0 6px;">Focus on:</div>
            <ul style="font-size: 13px; color: #d0d4d0; line-height: 1.6; margin: 0; padding-left: 20px;">
                <li>Learning proper form and technique.</li>
                <li>Training each major muscle group regularly.</li>
                <li>Starting with a manageable amount of training volume.</li>
                <li>Progressively increasing weights or repetitions over time.</li>
                <li>Consistency rather than constantly changing exercises or programs.</li>
            </ul>
            <p style="font-size: 12.5px; color: #8f938f; margin-top: 12px; font-style: italic;">
                Do not worry about advanced methods such as forced reps, drop sets, or highly complicated routines until you have developed a solid training foundation.
            </p>
        </div>
        """), unsafe_allow_html=True)

    with tab_diet:
        st.markdown(clean_html("""
        <div style="padding: 10px 4px;">
            <p style="font-size: 13.5px; color: #f5f5f5; line-height: 1.5;">
                Your diet should support growth, performance, and recovery.<br>
                Make sure you are eating enough overall food and getting sufficient protein every day. Build your meals around nutritious, minimally processed foods while still allowing some flexibility for foods you enjoy.
            </p>
            <div style="font-size: 13px; font-weight: 700; color: var(--accent); margin: 12px 0 6px;">Focus on:</div>
            <ul style="font-size: 13px; color: #d0d4d0; line-height: 1.6; margin: 0; padding-left: 20px;">
                <li>Getting enough protein from foods you can digest comfortably.</li>
                <li>Eating enough calories for your goal.</li>
                <li>Consuming a variety of fruits, vegetables, grains, and other nutrient-rich foods.</li>
                <li>Drinking enough water.</li>
                <li>Keeping your diet consistent rather than chasing a perfect meal plan.</li>
            </ul>
            <p style="font-size: 12.5px; color: #8f938f; margin-top: 12px; font-style: italic;">
                Beginners do not need complicated diets or supplements to make progress. Get your basic nutrition right first.
            </p>
        </div>
        """), unsafe_allow_html=True)

    with tab_rec:
        st.markdown(clean_html("""
        <div style="padding: 10px 4px;">
            <p style="font-size: 13.5px; color: #f5f5f5; line-height: 1.5;">
                Muscle and strength improvements happen not only during training, but also while your body recovers.<br>
                Give your body enough time to recover between hard training sessions. Poor recovery can negatively affect your performance and make progress harder.
            </p>
            <div style="font-size: 13px; font-weight: 700; color: var(--accent); margin: 12px 0 6px;">Focus on:</div>
            <ul style="font-size: 13px; color: #d0d4d0; line-height: 1.6; margin: 0; padding-left: 20px;">
                <li>Getting around 7–9 hours of sleep each night.</li>
                <li>Taking rest days when needed.</li>
                <li>Managing stress.</li>
                <li>Eating enough food and protein.</li>
                <li>Avoiding unnecessary increases in training volume.</li>
                <li>Paying attention to persistent pain, excessive fatigue, or declining performance.</li>
            </ul>
            <p style="font-size: 12.5px; color: #8f938f; margin-top: 12px; font-style: italic;">
                Remember: training hard is important, but recovering well is part of training too.
            </p>
        </div>
        """), unsafe_allow_html=True)

    st.markdown(clean_html("""
    <div style="
        background: var(--glass-card);
        border: 1px solid var(--glass-border);
        border-radius: 14px;
        padding: 12px 16px;
        margin-top: 16px;
    ">
        <div style="font-size: 13px; font-weight: 800; color: var(--accent); margin-bottom: 4px;">
            Beginner Mindset
        </div>
        <div style="font-size: 12.5px; color: #8f938f; line-height: 1.45;">
            Do not compare your progress to experienced lifters using HTN. Your first priority is to build good habits, proper technique, consistency, and basic strength.<br>
            Once you have developed a solid foundation, you can gradually move toward more advanced training approaches.
        </div>
    </div>
    """), unsafe_allow_html=True)


if hasattr(st, "dialog"):
    @st.dialog("HTN · Lifter Guide", width="large")
    def _open_instructions_dialog():
        _render_instructions_ui()
else:
    def _open_instructions_dialog():
        with st.expander("HTN · Lifter Guide", expanded=True):
            _render_instructions_ui()


def render_chatbot_fab():
    """
    Renders the fixed bottom-right 'INSTRUCTIONS' floating action button
    and opens the Beginner Guide modal dialog.
    """
    fab_css = """
.st-key-chatbot_fab {
    position: fixed !important;
    right: 24px !important;
    bottom: 84px !important;
    left: auto !important;
    top: auto !important;
    width: auto !important;
    height: auto !important;
    z-index: 9998 !important;
}
.st-key-chatbot_fab button {
    border-radius: 999px !important;
    background: rgba(14, 20, 26, 0.92) !important;
    border: 1.5px solid var(--accent) !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.6), 0 0 12px var(--accent-glow) !important;
    padding: 7px 16px !important;
    min-height: 36px !important;
    height: 36px !important;
    font-size: 11px !important;
    font-weight: 800 !important;
    letter-spacing: 0.6px !important;
    color: var(--accent) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 6px !important;
    transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.2s ease !important;
}
.st-key-chatbot_fab button:hover {
    transform: translateY(-2px) scale(1.03) !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.8), 0 0 20px var(--accent-glow) !important;
    background: var(--accent-dim) !important;
    border-color: var(--accent) !important;
    color: #ffffff !important;
}
.st-key-chatbot_fab button:active {
    transform: scale(0.96) !important;
}
@media (max-width: 768px) {
    .st-key-chatbot_fab {
        right: 16px !important;
        bottom: calc(max(24px, env(safe-area-inset-bottom, 24px)) + 52px) !important;
        z-index: 9998 !important;
    }
    .st-key-chatbot_fab button {
        padding: 5px 13px !important;
        font-size: 10.5px !important;
        letter-spacing: 0.5px !important;
        min-height: 30px !important;
        height: 30px !important;
        border-radius: 999px !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.7), 0 0 10px var(--accent-glow) !important;
    }
}
"""
    st.markdown(f"<style>\n{clean_css(fab_css)}\n</style>", unsafe_allow_html=True)

    with st.container(key="chatbot_fab"):
        if st.button("INSTRUCTIONS", icon=":material/article:", key="chatbot_fab_btn", help="Beginner Guide & Instructions"):
            _open_instructions_dialog()


# Semantic alias
render_instructions_fab = render_chatbot_fab

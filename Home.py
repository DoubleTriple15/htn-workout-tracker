from datetime import date, datetime, timedelta

import streamlit as st

from db.database import (
    get_home_summary,
    get_or_create_local_user,
    get_recent_prs,
    get_recent_sessions,
    get_sets_for_session,
    init_db,
)
from htn_theme import (
    clean_html,
    icon,
    inject_theme_css,
    render_chatbot_fab,
    render_nav_bar,
)
from utils.calculations import kg_to_lbs

st.set_page_config(
    page_title="HTN — High Tier Normie",
    page_icon="HTN",
    layout="wide",
    initial_sidebar_state="collapsed",
)
init_db()

user = get_or_create_local_user()
user_id = user["id"]
if "theme_pref" not in st.session_state or not st.session_state.theme_pref:
    st.session_state.theme_pref = user.get("theme_pref") or "Original"

# ── unit system ──────────────────────────────────────────────────────────────
_db_unit = user.get("unit_pref", "metric")
if _db_unit not in ("metric", "imperial"):
    _db_unit = "metric"
use_imperial = _db_unit == "imperial"

PAGE_CSS = """
#MainMenu, footer, header, [data-testid="stHeader"] { 
    display: none !important; 
    height: 0 !important; 
    min-height: 0 !important; 
    padding: 0 !important; 
    margin: 0 !important; 
}
section[data-testid="stMain"] { padding-top: 0 !important; }
section[data-testid="stMain"] > div { padding-top: 0 !important; }

.block-container,
div[data-testid="stMain"] .block-container,
section[data-testid="stMain"] .block-container {
    padding-top: 10px !important;
    padding-left: 20px !important;
    padding-right: 20px !important;
    padding-bottom: 88px !important;
    max-width: 1000px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    box-sizing: border-box !important;
}

/* Page container */
.st-key-pr_head,
.st-key-hist_head {
    width: 100%;
    max-width: 1000px;
    margin: 0 auto;
    box-sizing: border-box;
}

.hm-header { 
    display: flex; 
    justify-content: space-between; 
    align-items: center; 
    margin-bottom: 14px; 
    width: 100%;
}
.hm-eyebrow { 
    color: var(--accent); 
    font-size: 11px; 
    font-weight: 700; 
    letter-spacing: 1.8px; 
    text-transform: uppercase; 
    margin-bottom: 4px; 
}
.hm-title { 
    font-size: clamp(28px, 4.5vw, 38px); 
    font-weight: 800; 
    color: var(--text); 
    line-height: 1.15; 
    margin: 0; 
    letter-spacing: -0.6px; 
}
.hm-date { 
    color: var(--text-dim); 
    font-size: 13.5px; 
    font-weight: 500; 
    margin-top: 4px; 
}
.hm-avatar { 
    width: 52px; 
    height: 52px; 
    border-radius: 50%; 
    border: 1.5px solid var(--accent); 
    background: rgba(255, 255, 255, 0.03); 
    box-shadow: 0 0 16px var(--accent-glow);
    display: flex; 
    align-items: center; 
    justify-content: center; 
    flex-shrink: 0; 
}

/* Summary Cards (Desktop Grid) */
.hm-stats { 
    display: grid; 
    grid-template-columns: repeat(3, minmax(0, 1fr)); 
    gap: 12px; 
    margin-bottom: 16px; 
    width: 100%;
}
.hm-card { 
    background: var(--card); 
    border: 1px solid var(--card-border); 
    border-radius: 20px; 
    padding: 14px 16px; 
    display: flex; 
    flex-direction: column; 
    box-sizing: border-box;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35);
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.hm-card:hover {
    border-color: var(--glass-border-hover);
    transform: translateY(-1px);
}
.hm-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
}
.hm-card-header-left {
    display: flex;
    align-items: center;
    gap: 10px;
}
.hm-header-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--accent);
}
.hm-icon-box {
    width: 28px;
    height: 28px;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
}
.hm-card-title {
    font-size: 14.5px;
    font-weight: 600;
    color: var(--text);
    letter-spacing: -0.2px;
}
.hm-card-big-val {
    font-size: 34px;
    font-weight: 800;
    color: var(--text);
    line-height: 1;
    letter-spacing: -0.6px;
}
.hm-val-row {
    display: flex;
    align-items: baseline;
    gap: 6px;
    margin: 14px 0 6px 0;
}
.hm-val-unit {
    font-size: 15.5px;
    font-weight: 600;
    color: var(--text-dim);
}
.hm-card-sub {
    font-size: 13px;
    color: var(--text-dim);
    font-weight: 500;
}

/* Weekly workout tracker within Card 1 */
.hm-week-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 8px;
    width: 100%;
    margin: 14px 0 12px 0;
    text-align: center;
}
.hm-day-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
}
.hm-day-letter {
    font-size: 11.5px;
    font-weight: 700;
    color: var(--text-dim);
    line-height: 1;
}
.hm-day-dot {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: transparent;
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    box-sizing: border-box;
    transition: all 0.2s ease;
}
.hm-day-dot.active {
    background: var(--accent);
    border: none;
    box-shadow: 0 0 10px var(--accent-glow);
}
.hm-week-footer {
    font-size: 12px;
    color: var(--text-dim);
    font-weight: 500;
    margin-top: 2px;
}

/* Card 3: Daily Target / Calorie Goal */
.hm-target-card {
    display: flex;
    flex-direction: row !important;
    justify-content: space-between;
    align-items: center;
}
.hm-target-left {
    display: flex;
    flex-direction: column;
}
.hm-target-val-row {
    display: flex;
    align-items: center;
    gap: 10px;
}
.hm-target-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--accent);
}
.hm-target-val {
    font-size: 26px;
    font-weight: 800;
    color: var(--text);
    line-height: 1;
    letter-spacing: -0.5px;
}

/* Section Headings & Pill Buttons */
.st-key-pr_head,
.st-key-hist_head {
    margin-top: 30px !important;
    margin-bottom: 14px !important;
}
.st-key-pr_head [data-testid="stHorizontalBlock"],
.st-key-hist_head [data-testid="stHorizontalBlock"],
.st-key-pr_head div.stHorizontalBlock,
.st-key-hist_head div.stHorizontalBlock { 
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important; 
    justify-content: space-between !important;
    padding: 0 !important; 
    width: 100% !important;
}
.st-key-pr_head [data-testid="stColumn"]:first-child,
.st-key-hist_head [data-testid="stColumn"]:first-child,
.st-key-pr_head div.stColumn:first-child,
.st-key-hist_head div.stColumn:first-child,
.st-key-pr_head div[data-testid*="Column" i]:first-child,
.st-key-hist_head div[data-testid*="Column" i]:first-child {
    flex: 1 1 auto !important;
    width: auto !important;
    min-width: 0 !important;
}
.st-key-pr_head [data-testid="stColumn"]:last-child,
.st-key-hist_head [data-testid="stColumn"]:last-child,
.st-key-pr_head div.stColumn:last-child,
.st-key-hist_head div.stColumn:last-child,
.st-key-pr_head div[data-testid*="Column" i]:last-child,
.st-key-hist_head div[data-testid*="Column" i]:last-child {
    flex: 0 0 auto !important;
    width: auto !important;
    min-width: 0 !important;
}
.st-key-pr_head button, 
.st-key-hist_head button { 
    background: rgba(255, 255, 255, 0.02) !important; 
    border: 1px solid var(--accent) !important; 
    box-shadow: 0 0 10px var(--accent-glow) !important;
    color: var(--accent) !important; 
    font-size: 13px !important; 
    font-weight: 700 !important; 
    border-radius: 9999px !important;
    padding: 5px 14px !important;
    min-height: 30px !important;
    height: 30px !important;
    width: auto !important;
    white-space: nowrap !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.2s ease !important;
}
.st-key-pr_head button:hover, 
.st-key-hist_head button:hover { 
    background: var(--accent-dim) !important;
    box-shadow: 0 0 16px var(--accent-glow) !important;
    transform: translateY(-1px) !important;
}

/* Personal Record Cards (Desktop Grid) */
.hm-pr-row { 
    display: grid; 
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
    gap: 10px; 
    margin-bottom: 14px; 
    width: 100%;
}
.hm-pr-card { 
    background: var(--card); 
    border: 1px solid var(--card-border); 
    border-radius: 20px; 
    padding: 12px 16px; 
    display: flex; 
    align-items: center;
    justify-content: space-between;
    box-sizing: border-box;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35);
    margin-bottom: 12px;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.hm-pr-card:hover {
    border-color: var(--glass-border-hover);
    transform: translateY(-1px);
}
.hm-pr-left {
    display: flex;
    align-items: center;
    gap: 16px;
}
.hm-pr-icon { 
    width: 48px; 
    height: 48px; 
    border-radius: 50%; 
    background: rgba(255, 255, 255, 0.04); 
    border: 1px solid rgba(255, 255, 255, 0.08); 
    display: flex; 
    align-items: center; 
    justify-content: center; 
    flex-shrink: 0; 
    color: var(--accent);
}
.hm-pr-info {
    display: flex;
    flex-direction: column;
}
.hm-pr-name { 
    font-size: 16px; 
    font-weight: 700; 
    color: var(--text); 
    line-height: 1.2;
}
.hm-pr-sub { 
    font-size: 12.5px; 
    color: var(--text-dim); 
    margin: 3px 0 3px 0;
}
.hm-pr-val-row {
    display: flex;
    align-items: baseline;
    gap: 4px;
}
.hm-pr-value { 
    font-size: 19px; 
    font-weight: 800; 
    color: var(--text); 
    line-height: 1.1; 
}
.hm-pr-value-unit { 
    font-size: 13.5px; 
    color: var(--text-dim); 
    font-weight: 600; 
}
.hm-chevron {
    color: var(--text-dim);
    opacity: 0.65;
    flex-shrink: 0;
}

/* Workout History Accordion-Card */
.hm-history-wrap {
    width: 100%;
    margin-bottom: 24px;
}
div[data-testid="stExpander"], .hm-history-wrap [data-testid="stExpander"] {
    background: var(--card) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 18px !important;
    margin-bottom: 10px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35) !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
div[data-testid="stExpander"]:hover, .hm-history-wrap [data-testid="stExpander"]:hover {
    border-color: var(--glass-border-hover) !important;
    transform: translateY(-1px) !important;
}
div[data-testid="stExpander"] summary, .hm-history-wrap [data-testid="stExpander"] summary {
    padding: 14px 18px !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    color: var(--text) !important;
    cursor: pointer !important;
}
div[data-testid="stExpander"] summary:hover, .hm-history-wrap [data-testid="stExpander"] summary:hover {
    color: var(--accent) !important;
}
div[data-testid="stExpander"] summary svg, .hm-history-wrap [data-testid="stExpander"] summary svg {
    color: var(--accent) !important;
    fill: var(--accent) !important;
}
div[data-testid="stExpander"] [data-testid="stExpanderDetails"], .hm-history-wrap [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    padding: 14px 18px !important;
    background: rgba(0, 0, 0, 0.22) !important;
    border-top: 1px solid var(--card-border) !important;
}

/* View More Button */
.st-key-view_more_home_workouts button {
    background: var(--card) !important;
    border: 1px solid var(--card-border) !important;
    color: var(--text-dim) !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    border-radius: 9999px !important;
    padding: 8px 18px !important;
    margin: 8px 0 24px 0 !important;
    transition: all 0.2s ease !important;
}
.st-key-view_more_home_workouts button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    background: var(--accent-dim) !important;
    box-shadow: 0 0 14px var(--accent-glow) !important;
}

/* PR card click overlay — button sits invisibly over the card */
div[class*="st-key-pr_card_"] {
    position: relative !important;
    margin-bottom: 16px !important;
    cursor: pointer !important;
}
div[class*="st-key-pr_card_"] div[data-testid="stMarkdownContainer"],
div[class*="st-key-pr_card_"] div[data-testid="stMarkdownContainer"] > p {
    margin-bottom: 0 !important;
    padding-bottom: 0 !important;
}
div[class*="st-key-pr_card_"] .hm-pr-card {
    margin-bottom: 0 !important;
}
div[class*="st-key-pr_btn_"] {
    position: absolute !important;
    inset: 0 !important;
    width: 100% !important;
    height: 100% !important;
    z-index: 5 !important;
    display: block !important;
}
div[class*="st-key-pr_btn_"] div.stButton,
div[class*="st-key-pr_btn_"] div[data-testid="stButton"],
div[class*="st-key-pr_btn_"] button {
    position: absolute !important;
    inset: 0 !important;
    width: 100% !important;
    height: 100% !important;
    opacity: 0 !important;
    cursor: pointer !important;
    border: none !important;
    background: transparent !important;
    padding: 0 !important;
    margin: 0 !important;
    min-height: unset !important;
    border-radius: 20px !important;
}
div[class*="st-key-pr_card_"]:has(button:hover) .hm-pr-card,
div[class*="st-key-pr_card_"]:has(button:focus) .hm-pr-card {
    border-color: var(--accent) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(0,0,0,0.45), 0 0 14px var(--accent-glow) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   MOBILE-FIRST RESPONSIVE ENGINE (Screens <= 640px)
   ═══════════════════════════════════════════════════════════════════════════ */
@media (max-width: 640px) {
  .block-container,
  div[data-testid="stMain"] .block-container,
  section[data-testid="stMain"] .block-container {
    padding: 8px 12px 96px 12px !important;
    box-sizing: border-box !important;
  }
  .hm-header {
    margin-bottom: 12px !important;
    gap: 8px !important;
  }
  .hm-eyebrow {
    font-size: 10px !important;
    letter-spacing: 1.2px !important;
    margin-bottom: 2px !important;
  }
  .hm-title {
    font-size: 24px !important;
    line-height: 1.15 !important;
    margin: 0 0 2px 0 !important;
  }
  .hm-date {
    font-size: 12px !important;
  }
  .hm-avatar {
    width: 40px !important;
    height: 40px !important;
    min-width: 40px !important;
  }

  /* Summary Cards: Stacked 1-Column Layout */
  .hm-stats {
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
    margin-bottom: 14px !important;
    width: 100% !important;
  }
  .hm-card {
    padding: 14px 16px !important;
    border-radius: 18px !important;
    width: 100% !important;
    height: auto !important;
    min-height: auto !important;
    overflow: visible !important;
    box-sizing: border-box !important;
  }
  .hm-card-title {
    font-size: 13px !important;
  }
  .hm-card-big-val {
    font-size: 24px !important;
  }
  .hm-val-row {
    margin: 6px 0 2px 0 !important;
  }
  .hm-val-unit {
    font-size: 13px !important;
  }
  .hm-card-sub {
    font-size: 11.5px !important;
  }

  /* Week tracker within Workouts this week card */
  .hm-week-grid {
    gap: 4px !important;
    margin: 8px 0 6px 0 !important;
  }
  .hm-day-letter {
    font-size: 10px !important;
  }
  .hm-day-dot {
    width: 10px !important;
    height: 10px !important;
  }
  .hm-week-footer {
    font-size: 11px !important;
  }

  /* Target Card */
  .hm-target-val {
    font-size: 20px !important;
  }

  /* Section Headings */
  .st-key-pr_head,
  .st-key-hist_head {
    margin-top: 14px !important;
    margin-bottom: 8px !important;
  }
  .htn-section-title {
    font-size: 16px !important;
  }
  .st-key-pr_head button,
  .st-key-hist_head button {
    font-size: 11px !important;
    padding: 3px 10px !important;
    min-height: 26px !important;
    height: 26px !important;
  }

  /* Personal Records Cards */
  .hm-pr-row {
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
    margin-bottom: 14px !important;
    width: 100% !important;
  }
  .hm-pr-card {
    padding: 13px 16px !important;
    border-radius: 18px !important;
    width: 100% !important;
    height: auto !important;
    min-height: auto !important;
    flex-wrap: wrap !important;
    overflow: visible !important;
    box-sizing: border-box !important;
    margin-bottom: 12px !important;
  }
  .hm-pr-left {
    gap: 10px !important;
  }
  .hm-pr-icon {
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
  }
  .hm-pr-name {
    font-size: 14px !important;
  }
  .hm-pr-sub {
    font-size: 11px !important;
    margin: 2px 0 !important;
  }
  .hm-pr-value {
    font-size: 15px !important;
  }
  .hm-pr-value-unit {
    font-size: 11.5px !important;
  }

  /* Workout History */
  .hm-history-wrap {
    margin-bottom: 14px !important;
  }
  .hm-history-wrap [data-testid="stExpander"] summary {
    font-size: 12px !important;
    padding: 8px 12px !important;
  }
  .hm-history-wrap [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    padding: 8px 12px !important;
  }
}

@media (orientation: landscape) and (max-height: 550px) {
  .hm-header { margin-bottom: 10px !important; }
  .hm-card { padding: 12px 16px !important; }
}
"""
inject_theme_css(PAGE_CSS)
render_chatbot_fab()
render_nav_bar(active="home")

if "expanded_home_history" not in st.session_state:
    st.session_state.expanded_home_history = False

summary = get_home_summary(user_id)
prs = get_recent_prs(user_id, 3)
recent_sessions = get_recent_sessions(user_id, 50)

today = date.today()
week_start = today - timedelta(days=today.weekday())
week_days = [week_start + timedelta(days=i) for i in range(7)]
day_letters = ["M", "T", "W", "T", "F", "S", "S"]

workouts_by_day = {day.isoformat(): [] for day in week_days}
for session in recent_sessions:
    session_day = str(session.get("date") or "")[:10]
    if session_day in workouts_by_day:
        workouts_by_day[session_day].append(session.get("name") or "Workout")

week_tracker_html = ""
for day, letter in zip(week_days, day_letters):
    day_sessions = workouts_by_day[day.isoformat()]
    has_workout = bool(day_sessions)
    dot_class = " active" if has_workout else ""

    week_tracker_html += f'''
      <div class="hm-day-col">
        <div class="hm-day-letter">{letter}</div>
        <div class="hm-day-dot{dot_class}"></div>
      </div>
    '''

week_tracker_html = (
    '<div class="hm-week-grid">'
    + week_tracker_html
    + '</div>'
    + f'<div class="hm-week-footer">{summary.get("week_sessions", 0)} workout'
    + ('s' if summary.get("week_sessions", 0) != 1 else '')
    + ' this week</div>'
)

def fmt_date(value):
    if not value:
        return "No workouts yet"
    try:
        return datetime.fromisoformat(str(value)).strftime("%d %b %Y")
    except ValueError:
        return str(value)

def tracking_label(exercise_type: str) -> str:
    labels = {
        "weights_reps": "Weights + Reps",
        "reps": "Weights + Reps",
        "time": "Time",
        "bodyweight": "Bodyweight",
        "weighted_calisthenics": "Weighted Calisthenics",
    }
    return labels.get(exercise_type, exercise_type.replace("_", " ").title())

# ── Dynamic Bodyweight Evaluation ───────────────────────────────────────────
raw_weight = user.get("bodyweight_kg")
has_weight = raw_weight is not None and float(raw_weight) > 0
if has_weight:
    w_val = float(raw_weight)
    disp_weight = f"{round(kg_to_lbs(w_val), 1) if use_imperial else round(w_val, 1)}"
    disp_weight_unit = "lbs" if use_imperial else "kg"
    stat_sub_label = "Active Goal"
else:
    disp_weight = "—"
    disp_weight_unit = ""
    stat_sub_label = "Not set yet"

cal_goal = user.get("calorie_goal")

# ── Header & Profile Summary ──────────────────────────────────────────────────
st.markdown(clean_html(f"""
<div class="hm-header">
  <div>
    <div class="hm-eyebrow">Welcome back</div>
    <h1 class="hm-title">{user.get('username', 'Lifter')}</h1>
    <div class="hm-date">{date.today().strftime('%A, %d %B')}</div>
  </div>
  <div class="hm-avatar">{icon('dumbbell', size=20)}</div>
</div>
"""), unsafe_allow_html=True)

# ── Quick Stats Grid ─────────────────────────────────────────────────────────
st.markdown(clean_html(f"""
<div class="hm-stats">
  <div class="hm-card">
    <div class="hm-card-header">
      <div class="hm-card-header-left">
        <div class="hm-header-icon">{icon('dumbbell', size=17)}</div>
        <span class="hm-card-title">Workouts this week</span>
      </div>
      {icon('chevron-right', color='var(--text-dim)', size=14)}
    </div>
    <div class="hm-card-big-val" style="margin: 10px 0 2px 0;">{summary.get('week_sessions', 0)}</div>
    {week_tracker_html}
  </div>
  <div class="hm-card">
    <div class="hm-card-header">
      <div class="hm-card-header-left">
        <div class="hm-header-icon hm-icon-box">{icon('scale', size=15)}</div>
        <span class="hm-card-title">Bodyweight</span>
      </div>
      {icon('chevron-right', color='var(--text-dim)', size=14)}
    </div>
    <div class="hm-val-row">
      <span class="hm-card-big-val">{disp_weight}</span>
      <span class="hm-val-unit">{disp_weight_unit}</span>
    </div>
    <div class="hm-card-sub">{stat_sub_label}</div>
  </div>
  <div class="hm-card hm-target-card">
    <div class="hm-target-left">
      <div class="hm-target-val-row">
        <div class="hm-target-icon">{icon('flame', size=19)}</div>
        <span class="hm-target-val">{f"{cal_goal:,}" if cal_goal else "—"}</span>
        <span class="hm-val-unit">kcal</span>
      </div>
      <div class="hm-card-sub" style="margin-left: 27px;">Daily Target</div>
    </div>
  </div>
</div>
"""), unsafe_allow_html=True)

# ── Recent PRs ───────────────────────────────────────────────────────────────
with st.container(key="pr_head"):
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown('<div class="htn-section-title">Recent Personal Records</div>', unsafe_allow_html=True)
    with c2:
        if st.button("View all ›", key="pr_view_all"):
            st.switch_page("pages/progression.py")

if not prs:
    st.markdown('<div style="padding:10px 0 20px;color:var(--text-dim);font-size:13px;">Complete a workout to start building your PR history.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="hm-pr-row">', unsafe_allow_html=True)
    for p in prs:
        ex_type = (p.get("exercise_type") or "reps").lower()
        best_weight = float(p.get("best_weight") or 0.0)
        best_1rm = float(p.get("best_1rm") or 0.0)
        best_reps = int(p.get("best_reps") or 0)
        best_duration = int(p.get("best_duration") or 0)

        if ex_type == "time":
            if best_duration >= 60:
                m = best_duration // 60
                s = best_duration % 60
                val_str = f"{m}:{s:02d}" if s else f"{m}"
                unit_str = " min"
            else:
                val_str = f"{best_duration}"
                unit_str = " s"
            sub = "Best Time"

        elif ex_type == "bodyweight" or (best_1rm == 0 and best_weight == 0 and best_reps > 0):
            val_str = f"{best_reps}"
            unit_str = " reps"
            sub = "Max Reps"

        elif ex_type == "weighted_calisthenics":
            if best_weight > 0:
                disp_w = kg_to_lbs(best_weight) if use_imperial else best_weight
                val_str = f"+{disp_w:.1f}"
                unit_str = " lbs" if use_imperial else " kg"
                sub = "Max Added Weight"
            else:
                val_str = f"{best_reps}"
                unit_str = " reps"
                sub = "Max Reps"

        else:
            if best_1rm > 0:
                disp_1rm = kg_to_lbs(best_1rm) if use_imperial else best_1rm
                val_str = f"{disp_1rm:.1f}"
                unit_str = " lbs" if use_imperial else " kg"
                sub = "Estimated 1RM"
            elif best_reps > 0:
                val_str = f"{best_reps}"
                unit_str = " reps"
                sub = "Max Reps"
            else:
                val_str = "0.0"
                unit_str = " lbs" if use_imperial else " kg"
                sub = "Estimated 1RM"

        safe_key = p['name'].replace(' ', '_').replace('-', '_').lower()
        card_html = clean_html(f"""
        <div class="hm-pr-card">
          <div class="hm-pr-left">
            <div class="hm-pr-icon">{icon('dumbbell', size=18)}</div>
            <div class="hm-pr-info">
              <div class="hm-pr-name">{p['name']}</div>
              <div class="hm-pr-sub">{sub}</div>
              <div class="hm-pr-val-row">
                <span class="hm-pr-value">{val_str}</span>
                <span class="hm-pr-value-unit">{unit_str}</span>
              </div>
            </div>
          </div>
          {icon('chevron-right', color='var(--accent)', size=14)}
        </div>""")

        with st.container(key=f"pr_card_{safe_key}"):
            st.markdown(card_html, unsafe_allow_html=True)
            if st.button("View progression →", key=f"pr_btn_{safe_key}", use_container_width=True):
                st.session_state.prog_jump_exercise = p['name']
                st.switch_page("pages/progression.py")

    st.markdown('</div>', unsafe_allow_html=True)

# ── Workout History (Button-styled Accordion Cards) ──────────────────────────
with st.container(key="hist_head"):
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown('<div class="htn-section-title">Workout History</div>', unsafe_allow_html=True)
    with c2:
        if st.button("View all ›", key="history_view_all"):
            st.switch_page("pages/workout.py")

if not recent_sessions:
    st.markdown('<div style="padding:10px 0 60px;color:var(--text-dim);font-size:13px;">No completed workouts yet.</div>', unsafe_allow_html=True)
else:
    HOME_HISTORY_PREVIEW_LIMIT = 3
    is_expanded = st.session_state.expanded_home_history
    visible_sessions = recent_sessions if is_expanded else recent_sessions[:HOME_HISTORY_PREVIEW_LIMIT]

    with st.container():
        st.markdown('<div class="hm-history-wrap">', unsafe_allow_html=True)
        for h in visible_sessions:
            s_id = h["id"]
            mins = f"{int(h['duration'])//60}m" if h.get("duration") is not None else "—"
            name = h["name"]
            session_date = fmt_date(h["date"])
            vol = h["volume"]
            ex_count = h["exercises"]
            session_notes = (h.get("notes") or "").strip()

            header_title = f"{name}   ·   {session_date}   ({mins}  |  {vol:,.0f} kg  |  {ex_count} exercises)"

            with st.expander(header_title, expanded=False):
                # Workout Notes Banner
                if session_notes:
                    st.markdown(
                        f'<div style="background:var(--accent-dim); border:1px solid var(--accent); box-shadow:0 0 10px var(--accent-glow); border-radius:10px; padding:9px 13px; margin:4px 0 12px; font-size:12.5px; color:#e0e0e0;">'
                        f'<span style="color:var(--accent); font-weight:800; text-transform:uppercase; font-size:10.5px; letter-spacing:0.8px; display:block; margin-bottom:2px;">Notes</span>'
                        f'{session_notes}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                sets = get_sets_for_session(s_id)
                if not sets:
                    st.caption("No individual sets recorded for this session.")
                else:
                    # Group sets by exercise name
                    grouped = {}
                    for row in sets:
                        ex_name = row["exercise_name"]
                        grouped.setdefault(ex_name, []).append(row)

                    for ex_name, s_list in grouped.items():
                        ex_type = s_list[0].get("exercise_type", "weights_reps")
                        st.markdown(
                            f'<div style="font-size:12.5px;font-weight:800;color:#f5f5f5;margin:5px 0 3px;">'
                            f'{ex_name} <span style="font-size:10.5px;font-weight:600;color:var(--text-dim);margin-left:6px;">· {tracking_label(ex_type)}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        for row in s_list:
                            s_num = row["set_number"]
                            s_cat = row.get("set_type", "working")
                            
                            if s_cat == "warmup":
                                cat_badge = '<span style="font-size:9.5px;font-weight:700;color:var(--accent);background:var(--accent-dim);border:1px solid var(--accent);box-shadow:0 0 6px var(--accent-glow);padding:1px 7px;border-radius:6px;margin:0 6px;">Warm-up</span>'
                            elif s_cat == "dropset":
                                cat_badge = '<span style="font-size:9.5px;font-weight:700;color:#ff9f43;background:rgba(255,159,67,0.12);border:1px solid rgba(255,159,67,0.3);padding:1px 7px;border-radius:6px;margin:0 6px;">Drop Set</span>'
                            else:
                                cat_badge = '<span style="font-size:9.5px;font-weight:700;color:#8f938f;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);padding:1px 7px;border-radius:6px;margin:0 6px;">Working</span>'

                            if ex_type == "time":
                                stat = f"{row.get('duration_seconds') or 0}s"
                            elif ex_type == "bodyweight":
                                stat = f"{row.get('reps') or 0} reps"
                            elif ex_type == "weighted_calisthenics":
                                w = float(row.get('weight') or 0.0)
                                stat = f"+{w:g}kg × {row.get('reps') or 0} reps"
                            else:
                                w = float(row.get('weight') or 0.0)
                                stat = f"{w:g}kg × {row.get('reps') or 0} reps"

                            rpe_text = f' <span style="color:#8f938f;font-size:10.5px;margin-left:6px;">@ RPE {row["rpe"]}</span>' if row.get("rpe") else ""

                            st.markdown(
                                f'<div style="display:flex;align-items:center;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:9px;padding:5px 10px;margin-bottom:3px;font-size:11.5px;color:#e0e0e0;">'
                                f'<span style="font-weight:700;min-width:40px;color:#8f938f;">Set {s_num}</span>'
                                f'{cat_badge}'
                                f'<span style="font-weight:700;color:#ffffff;margin-left:auto;">{stat}</span>'
                                f'{rpe_text}'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
        st.markdown('</div>', unsafe_allow_html=True)

    # View More / View Less Toggle Button
    if len(recent_sessions) > HOME_HISTORY_PREVIEW_LIMIT:
        if not is_expanded:
            remaining = len(recent_sessions) - HOME_HISTORY_PREVIEW_LIMIT
            if st.button(f"View more workouts ({remaining} more) ↓", key="view_more_home_workouts", use_container_width=True):
                st.session_state.expanded_home_history = True
                st.rerun()
        else:
            if st.button("View less workouts ↑", key="view_more_home_workouts", use_container_width=True):
                st.session_state.expanded_home_history = False
                st.rerun()

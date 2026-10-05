from contextlib import nullcontext
from datetime import date, datetime
import time

import streamlit as st
import streamlit.components.v1 as components

from db.database import (
    add_builtin_periodization_exercise,
    add_exercise_to_routine,
    advance_periodization_cycle_with_overload,
    calculate_progressive_overload_suggestion,
    change_session_exercise,
    create_exercise,
    create_periodization_program,
    create_routine,
    delete_builtin_periodization_exercise,
    delete_exercise,
    delete_periodization_program,
    delete_routine,
    delete_session,
    delete_session_exercise,
    delete_set,
    duplicate_periodization_day_as_routine,
    duplicate_periodization_program,
    duplicate_routine,
    finish_session,
    get_all_exercises,
    get_connection,
    get_all_periodization_programs,
    get_builtin_periodization_program,
    get_exercise_personal_bests,
    get_or_create_local_user,
    get_or_create_periodization_day,
    get_periodization_day_info,
    get_periodization_program_metadata,
    get_previous_performance,
    get_routine_exercises,
    get_routines,
    get_sessions,
    get_sets_for_session,
    init_db,
    log_set,
    start_session,
    update_builtin_periodization_day,
    update_builtin_periodization_exercise,
    update_periodization_program_settings,
    update_routine,
    update_session,
    update_set,
)
from htn_theme import (
    clean_html,
    get_theme_tokens,
    inject_theme_css,
    render_chatbot_fab,
    render_nav_bar,
)

st.set_page_config(
    page_title="Workout — HTN",
    page_icon="HTN",
    layout="wide",
    initial_sidebar_state="collapsed",
)
init_db()
user = get_or_create_local_user()
user_id = user["id"]
if "theme_pref" not in st.session_state or not st.session_state.theme_pref:
    st.session_state.theme_pref = user.get("theme_pref") or "Original"

MUSCLE_GROUPS = [
    "Chest",
    "Back",
    "Shoulders",
    "Biceps",
    "Triceps",
    "Legs",
    "Quads",
    "Hamstrings",
    "Glutes",
    "Calves",
    "Core",
    "Cardio",
    "Full Body",
    "Other",
]

SET_CATEGORIES = ["Working Set", "Warm-up Set", "Drop Set"]

PAGE_CSS = """
#MainMenu, footer, header { visibility:hidden; }
[data-testid="stSidebarNav"] { display:none; }
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

/* Fluid container adapting to horizontal & vertical screens */
.st-key-wk_shell {
    width: 100%;
    max-width: 1000px;
    margin: 0 auto;
    padding: 0 !important;
    box-sizing: border-box;
}

.wk-title {
    font-size: clamp(28px, 4.5vw, 36px); 
    font-weight: 800; 
    color: var(--text);
    line-height: 1.1; 
    margin: 0 0 2px; 
    letter-spacing: -0.5px;
}
.wk-subtitle { color: var(--text-dim); font-size: 13.5px; margin: 0 0 14px; }

.wk-actions-row { 
    display: grid; 
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
    gap: 10px; 
    margin-bottom: 16px; 
}
.st-key-start_empty button,
.st-key-new_routine button,
.st-key-btn_open_periodisation button {
    width: 100% !important; 
    min-height: 72px !important;
    border-radius: 16px !important; 
    padding: 12px 10px !important;
    box-sizing: border-box !important; 
    font-family: inherit !important;
    font-size: 14px !important; 
    font-weight: 800 !important; 
    line-height: 1.2 !important; 
    white-space: pre-line !important;
}
.st-key-start_empty button {
    background: var(--accent) !important;
    color: var(--btn-text) !important;
    border: 1px solid var(--accent) !important;
    box-shadow: 0 8px 24px var(--accent-glow), inset 0 1px 1px rgba(255, 255, 255, 0.4) !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
.st-key-new_routine button,
.st-key-btn_open_periodisation button {
    background: var(--glass-card) !important;
    background-image: var(--morph-concave) !important;
    color: var(--text) !important;
    border: 1px solid var(--glass-border) !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.08) !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
.st-key-start_empty button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 12px 32px var(--accent-glow), inset 0 1px 1px rgba(255, 255, 255, 0.5) !important;
    opacity: 0.96 !important;
}
.st-key-new_routine button:hover,
.st-key-btn_open_periodisation button:hover {
    transform: translateY(-2px) !important;
    border-color: var(--glass-border-hover) !important;
    color: var(--accent) !important;
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.5), 0 0 18px var(--accent-glow) !important;
}

.wk-section-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: 0 0 12px; }
.wk-section-title { font-size: clamp(18px, 3vw, 22px); font-weight: 800; color: var(--text); letter-spacing: -.2px; }
.st-key-manage button {
    background: var(--accent-dim) !important;
    border: 1.5px solid var(--accent) !important;
    box-shadow: 0 0 12px var(--accent-glow), inset 0 0 6px var(--accent-glow) !important;
    color: var(--accent) !important;
    font-size: 13px !important;
    font-weight: 800 !important;
    border-radius: 9999px !important;
    padding: 6px 16px !important;
    min-height: 34px !important;
    height: 34px !important;
    width: auto !important;
    white-space: nowrap !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
.st-key-manage button:hover {
    background: var(--accent) !important;
    color: #0a0a0a !important;
    box-shadow: 0 0 20px var(--accent-glow) !important;
    transform: translateY(-1.5px) !important;
}


.st-key-routine_back button,
.st-key-manage_back button,
.st-key-manage_back_top button,
.st-key-active_back button,
.st-key-periodization_back button {
    background: transparent !important; 
    border: none !important; 
    color: var(--accent) !important;
    font-size: 14px !important; 
    font-weight: 700 !important; 
    padding: 3px 0 !important;
    width: auto !important; 
    box-shadow: none !important;
}

.wk-card {
    background: var(--card); 
    border: 1px solid var(--card-border); 
    border-radius: 18px;
    padding: 16px 18px; 
    margin: 0 0 16px; 
    box-sizing: border-box;
}
.wk-muted { color: var(--text-dim); font-size: 13px; line-height: 1.5; }
.wk-small { color: var(--text-dim); font-size: 12px; line-height: 1.35; }

.wk-routine-card {
    display: flex; 
    flex-direction: column;
    gap: 6px;
    background: var(--card); 
    border: 1px solid var(--card-border); 
    border-radius: 18px;
    padding: 16px 18px; 
    margin-bottom: 16px; 
    box-sizing: border-box;
}
.wk-routine-name { font-size: 16px; font-weight: 800; color: var(--text); overflow-wrap: anywhere; }
.wk-routine-count { font-size: 12px; color: var(--text-dim); }
.wk-routine-muscles { font-size: 12px; color: var(--text-dim); line-height: 1.35; overflow-wrap: anywhere; }

div[class*="st-key-hub_routine_"] {
    margin-bottom: 16px !important;
}

.st-key-routine_start button {
    min-height: 44px !important; 
    width: 100% !important; 
    border-radius: 12px !important;
    border: 2px solid var(--accent) !important; 
    background: transparent !important; 
    color: var(--accent) !important; 
    font-size: 13px !important; 
    font-weight: 700 !important; 
    padding: 8px 11px !important;
}
.st-key-routine_start button:hover { background: var(--accent) !important; color: #0a0a0a !important; }

.wk-exercise-card {
    background: var(--card); 
    border: 1px solid var(--card-border); 
    border-radius: 16px;
    padding: 16px 18px; 
    margin-bottom: 16px;
}
.wk-exercise-title { font-size: 15px; font-weight: 700; color: var(--text); }
.wk-exercise-meta { margin-top: 4px; font-size: 12px; color: var(--text-dim); }

.wk-active-head { display: flex; align-items: center; justify-content: space-between; gap: 14px; margin-bottom: 14px; }
.wk-active-title { font-size: clamp(22px, 4vw, 28px); font-weight: 800; color: var(--text); }

/* Collapsible Exercise Header Button */
div[class*="st-key-toggle_ex_"] button {
    background: var(--card) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 16px !important;
    padding: 14px 18px !important;
    color: var(--text) !important;
    font-size: 15px !important;
    font-weight: 800 !important;
    letter-spacing: -0.2px !important;
    text-align: left !important;
    display: flex !important;
    justify-content: flex-start !important;
    align-items: center !important;
    margin-bottom: 8px !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3) !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
div[class*="st-key-toggle_ex_"] button:hover {
    border-color: var(--glass-border-hover) !important;
    color: var(--accent) !important;
    background: var(--glass-elevated) !important;
    box-shadow: 0 0 14px var(--accent-glow) !important;
}

.wk-exercise-box {
    background: var(--card); 
    border: 1px solid var(--card-border); 
    border-radius: 18px;
    padding: 16px; 
    margin: 0 0 16px;
}
.wk-exercise-box-head { margin-bottom: 12px; }

/* Clean Alignment Field Titles */
.wk-field-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-dim);
    margin-bottom: 8px;
    height: 20px;
    display: flex;
    align-items: center;
}

div[class*="st-key-set_complete_btn_"] button { 
    background: var(--accent) !important; 
    color: var(--btn-text) !important; 
    border: 1px solid var(--accent) !important; 
    border-radius: 12px !important; 
    font-weight: 800 !important; 
    min-height: 44px !important;
    margin-top: 8px;
    box-shadow: 0 4px 16px var(--accent-glow) !important;
}

.st-key-toggle_workout_timer button {
    height: 38px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    line-height: 38px !important;
    padding: 0 14px !important;
    font-size: 12.5px !important;
    font-weight: 800 !important;
    border-radius: 12px !important;
    box-sizing: border-box !important;
    margin: 0 !important;
}

.st-key-cancel_workout button {
    height: 38px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    line-height: 38px !important;
    background: transparent !important;
    color: #ff6b6b !important;
    border: 1px solid #ff6b6b !important;
    border-radius: 12px !important;
    font-weight: 800 !important;
    font-size: 12.5px !important;
    box-sizing: border-box !important;
}
.st-key-save_workout button {
    height: 38px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    line-height: 38px !important;
    background: var(--accent) !important;
    color: var(--btn-text) !important;
    border: 1px solid var(--accent) !important;
    border-radius: 12px !important;
    font-weight: 800 !important;
    font-size: 12.5px !important;
    box-shadow: 0 4px 16px var(--accent-glow) !important;
    box-sizing: border-box !important;
}

.st-key-rest_skip button { 
    background: var(--glass-card) !important; 
    color: var(--accent) !important; 
    border: 1px solid var(--glass-border) !important; 
    border-radius: 12px !important; 
    font-weight: 700 !important; 
    font-size: 13px !important;
    margin-top: 6px !important;
    margin-bottom: 14px !important;
    min-height: 40px !important;
}
.st-key-rest_skip button:hover {
    background: var(--accent-dim) !important;
    border-color: var(--accent) !important;
    box-shadow: 0 0 14px var(--accent-glow) !important;
}

.wk-fade-mask {
    margin-top: -42px;
    height: 48px;
    background: linear-gradient(180deg, rgba(10, 10, 10, 0) 0%, rgba(10, 10, 10, 0.8) 50%, #0a0a0a 100%);
    backdrop-filter: blur(2px);
    -webkit-backdrop-filter: blur(2px);
    position: relative;
    z-index: 2;
    pointer-events: none;
    margin-bottom: 6px;
    border-radius: 0 0 16px 16px;
}

.st-key-view_more_routines button,
.st-key-view_more_exercises button {
    background: var(--glass-card) !important;
    border: 1px solid var(--glass-border) !important;
    color: var(--text-dim) !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    padding: 8px 14px !important;
    margin-bottom: 16px !important;
    transition: all 0.2s ease !important;
}

.st-key-view_more_routines button:hover,
.st-key-view_more_exercises button:hover {
    border-color: var(--glass-border-hover) !important;
    color: var(--accent) !important;
    background: var(--accent-dim) !important;
    box-shadow: 0 0 14px var(--accent-glow) !important;
}

/* Periodization Mesocycle Hub */
.htn-meso-container {
    background: var(--glass-card);
    background-image: var(--morph-concave);
    border: 1px solid var(--glass-border);
    border-radius: 20px;
    padding: 22px 20px;
    margin: 16px 0 24px;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.htn-meso-container:hover {
    border-color: var(--glass-border-hover);
    box-shadow: 0 20px 48px rgba(0, 0, 0, 0.6), 0 0 20px var(--accent-glow), inset 0 1px 1px rgba(255, 255, 255, 0.12);
}

.htn-meso-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 16px;
    padding-bottom: 14px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.htn-meso-badge {
    background: var(--accent-dim);
    color: var(--accent);
    border: 1px solid var(--accent);
    box-shadow: 0 0 10px var(--accent-glow);
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

.htn-meso-pill {
    background: var(--accent-dim);
    border: 1px solid var(--accent);
    color: var(--accent);
    box-shadow: 0 0 8px var(--accent-glow);
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.3px;
    text-transform: uppercase;
}

.htn-stepper {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 8px;
    margin-bottom: 16px;
}
@media (max-width: 640px) {
    .htn-stepper {
        grid-template-columns: repeat(auto-fit, minmax(75px, 1fr));
    }
}

.htn-step-item {
    padding: 8px 6px;
    border-radius: 12px;
    background: rgba(18, 20, 18, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.06);
    text-align: center;
    transition: all 0.25s ease;
}
.htn-step-item.active {
    background: var(--accent-dim);
    border-color: var(--accent);
    box-shadow: 0 0 14px var(--accent-glow);
}
.htn-step-week {
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.5px;
    color: var(--text-dim);
    text-transform: uppercase;
}
.htn-step-item.active .htn-step-week {
    color: var(--accent);
}
.htn-step-name {
    font-size: 12px;
    font-weight: 700;
    color: var(--text);
    margin-top: 2px;
}

.htn-period-ex-card {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(18, 22, 18, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 14px;
    padding: 12px 16px;
    margin-bottom: 8px;
    box-sizing: border-box;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.htn-period-ex-card:hover {
    border-color: var(--glass-border-hover);
    transform: translateY(-1.5px);
    background: var(--glass-elevated);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4), 0 0 12px var(--accent-glow);
}

.htn-role-badge-primary {
    background: var(--accent-dim);
    color: var(--accent);
    border: 1px solid var(--accent);
    box-shadow: 0 0 8px var(--accent-glow);
    border-radius: 6px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.3px;
    text-transform: uppercase;
    display: inline-block;
    margin-bottom: 3px;
}
.htn-role-badge-aux {
    background: rgba(56, 189, 248, 0.14);
    color: #7dd3fc;
    border: 1px solid rgba(56, 189, 248, 0.35);
    border-radius: 6px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.3px;
    text-transform: uppercase;
    display: inline-block;
    margin-bottom: 3px;
}
.htn-role-badge-support {
    background: rgba(245, 158, 11, 0.14);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.35);
    border-radius: 6px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.3px;
    text-transform: uppercase;
    display: inline-block;
    margin-bottom: 3px;
}
.htn-target-badge {
    background: var(--accent-dim);
    color: var(--accent);
    border: 1px solid var(--accent);
    box-shadow: 0 0 8px var(--accent-glow);
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: -0.2px;
    text-align: right;
    white-space: nowrap;
}

div[class*="st-key-start_periodized_btn_"] button {
    background: var(--accent) !important;
    color: var(--btn-text) !important;
    border: 1px solid var(--accent) !important;
    border-radius: 14px !important;
    font-size: 15px !important;
    font-weight: 800 !important;
    min-height: 48px !important;
    box-shadow: 0 8px 24px var(--accent-glow), inset 0 1px 1px rgba(255, 255, 255, 0.4) !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
div[class*="st-key-start_periodized_btn_"] button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 12px 30px var(--accent-glow), inset 0 1px 1px rgba(255, 255, 255, 0.5) !important;
    opacity: 0.98 !important;
}

.st-key-btn_confirm_delete_cycle button {
    background: #e53e3e !important;
    border: 1px solid #ff4d4d !important;
    color: #ffffff !important;
    box-shadow: 0 0 16px rgba(229, 62, 62, 0.45) !important;
    font-weight: 800 !important;
}
.st-key-btn_confirm_delete_cycle button:hover {
    background: #c53030 !important;
    border-color: #ff6b6b !important;
    box-shadow: 0 0 24px rgba(229, 62, 62, 0.65) !important;
}
.st-key-btn_settings_remove_cycle button {
    border-color: rgba(255, 77, 77, 0.45) !important;
    color: #ff6b6b !important;
    background: rgba(255, 77, 77, 0.06) !important;
}
.st-key-btn_settings_remove_cycle button:hover {
    border-color: #ff4d4d !important;
    color: #ffffff !important;
    background: rgba(229, 62, 62, 0.8) !important;
    box-shadow: 0 0 16px rgba(229, 62, 62, 0.4) !important;
}

@media (max-width: 640px) {
    .block-container,
    div[data-testid="stMain"] .block-container,
    section[data-testid="stMain"] .block-container {
        padding: 8px 12px 140px 12px !important;
        box-sizing: border-box !important;
    }
    .st-key-wk_shell {
        padding: 0 !important;
    }
    .wk-title {
        font-size: 24px !important;
        line-height: 1.15 !important;
        margin: 0 0 2px !important;
    }
    .wk-subtitle {
        font-size: 12px !important;
        margin: 0 0 10px !important;
    }
    .wk-actions-row {
        grid-template-columns: 1fr !important;
        gap: 6px !important;
        margin-bottom: 12px !important;
    }
    .st-key-start_empty button,
    .st-key-new_routine button,
    .st-key-btn_open_periodisation button {
        min-height: 50px !important;
        font-size: 13px !important;
        line-height: 1.3 !important;
        border-radius: 12px !important;
        padding: 10px 8px !important;
    }
    .wk-section-row {
        margin: 0 0 8px !important;
    }
    .wk-section-title {
        font-size: 16px !important;
    }
    .wk-card,
    .wk-routine-card,
    .wk-exercise-card,
    .wk-exercise-box {
        padding: 14px 16px !important;
        border-radius: 16px !important;
        margin-bottom: 16px !important;
    }
    .wk-routine-name {
        font-size: 15px !important;
    }
    .wk-routine-count,
    .wk-routine-muscles {
        font-size: 11.5px !important;
    }
    .st-key-routine_start button {
        min-height: 38px !important;
        font-size: 12.5px !important;
        border-radius: 10px !important;
        padding: 6px 10px !important;
    }
    .wk-active-head {
        margin-bottom: 12px !important;
        gap: 10px !important;
    }
    .wk-active-title {
        font-size: 20px !important;
    }
    div[class*="st-key-toggle_ex_"] button {
        padding: 10px 14px !important;
        font-size: 13.5px !important;
        border-radius: 14px !important;
    }
    div[class*="st-key-set_complete_btn_"] button {
        min-height: 38px !important;
        font-size: 12.5px !important;
        border-radius: 10px !important;
    }
    div[class*="st-key-wt_"] input,
    div[class*="st-key-reps_"] input,
    div[class*="st-key-rpe_"] input,
    div[class*="st-key-sec_"] input {
        height: 36px !important;
        font-size: 12.5px !important;
    }
    .htn-meso-container {
        padding: 14px 16px !important;
        border-radius: 18px !important;
        margin: 12px 0 20px !important;
    }
    .htn-stepper {
        grid-template-columns: repeat(5, 1fr) !important;
        gap: 4px !important;
    }
    .htn-step-item {
        padding: 6px 3px !important;
        border-radius: 10px !important;
    }
    .htn-step-week {
        font-size: 9px !important;
    }
    .htn-step-name {
        font-size: 10.5px !important;
    }



    /* Keep manage & routine action columns in clean horizontal rows on mobile */
    div[class*="st-key-manage_r_"] [data-testid="stHorizontalBlock"],
    div[class*="st-key-manage_r_"] div.stHorizontalBlock,
    div[class*="st-key-manage_sess_"] [data-testid="stHorizontalBlock"],
    div[class*="st-key-manage_sess_"] div.stHorizontalBlock,
    div[class*="st-key-hub_routine_"] [data-testid="stHorizontalBlock"],
    div[class*="st-key-hub_routine_"] div.stHorizontalBlock {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 10px !important;
        width: 100% !important;
    }
    
    /* Fix overlap between routine card and its buttons */
    div[class*="st-key-hub_routine_"] div[data-testid="stMarkdownContainer"] {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    div[class*="st-key-manage_r_"] [data-testid="stColumn"],
    div[class*="st-key-manage_r_"] div.stColumn,
    div[class*="st-key-manage_sess_"] [data-testid="stColumn"],
    div[class*="st-key-manage_sess_"] div.stColumn,
    div[class*="st-key-hub_routine_"] [data-testid="stColumn"],
    div[class*="st-key-hub_routine_"] div.stColumn {
        min-width: 0 !important;
        flex: 1 1 0 !important;
    }

    div[class*="st-key-manage_ex_"] [data-testid="stHorizontalBlock"],
    div[class*="st-key-manage_ex_"] div.stHorizontalBlock {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 8px !important;
        align-items: center !important;
        width: 100% !important;
    }
    div[class*="st-key-manage_ex_"] [data-testid="stColumn"]:first-child,
    div[class*="st-key-manage_ex_"] div.stColumn:first-child {
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }
    div[class*="st-key-manage_ex_"] [data-testid="stColumn"]:last-child,
    div[class*="st-key-manage_ex_"] div.stColumn:last-child {
        flex: 0 0 72px !important;
        min-width: 72px !important;
    }

    /* Active Workout Top Bar */
    div[class*="st-key-wk_active_bar"] [data-testid="stHorizontalBlock"],
    div[class*="st-key-wk_active_bar"] div.stHorizontalBlock {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 6px !important;
        width: 100% !important;
    }
    div[class*="st-key-wk_active_bar"] [data-testid="stColumn"],
    div[class*="st-key-wk_active_bar"] div.stColumn {
        min-width: 0 !important;
        flex: 1 1 auto !important;
    }

    /* Hub Actions Row — Mature 2-column grid */
    div[class*="st-key-wk_hub_actions"] [data-testid="stHorizontalBlock"],
    div[class*="st-key-wk_hub_actions"] div.stHorizontalBlock {
        display: grid !important;
        grid-template-columns: 1fr 1fr !important;
        gap: 10px !important;
        width: 100% !important;
    }
    div[class*="st-key-wk_hub_actions"] [data-testid="stColumn"],
    div[class*="st-key-wk_hub_actions"] div.stColumn {
        min-width: 0 !important;
        width: 100% !important;
    }
    /* Make the first button (Start Empty Workout) span full width */
    div[class*="st-key-wk_hub_actions"] [data-testid="stColumn"]:nth-child(1),
    div[class*="st-key-wk_hub_actions"] div.stColumn:nth-child(1) {
        grid-column: 1 / -1 !important;
    }

    /* Routines Header */
    div[class*="st-key-wk_routines_head"] [data-testid="stHorizontalBlock"],
    div[class*="st-key-wk_routines_head"] div.stHorizontalBlock {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: space-between !important;
        width: 100% !important;
    }
    div[class*="st-key-wk_routines_head"] [data-testid="stColumn"]:first-child,
    div[class*="st-key-wk_routines_head"] div.stColumn:first-child {
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }
    div[class*="st-key-wk_routines_head"] [data-testid="stColumn"]:last-child,
    div[class*="st-key-wk_routines_head"] div.stColumn:last-child {
        flex: 0 0 auto !important;
        min-width: 85px !important;
        display: flex !important;
        justify-content: flex-end !important;
    }
    div[class*="st-key-wk_routines_head"] button {
        font-size: 12px !important;
        padding: 5px 14px !important;
        min-height: 32px !important;
        height: 32px !important;
    }

    /* Active Workout Set Cards: Responsive Mobile Layout */
    div[class*="st-key-wk_set_card_"] {
        padding: 10px 12px !important;
        margin-bottom: 10px !important;
        border-radius: 14px !important;
    }
    div[class*="st-key-wk_set_card_"] [data-testid="stHorizontalBlock"],
    div[class*="st-key-wk_set_card_"] div.stHorizontalBlock {
        gap: 5px !important;
        align-items: flex-start !important;
    }
    div[class*="st-key-wk_set_card_"] [data-testid="stHorizontalBlock"]:first-of-type,
    div[class*="st-key-wk_set_card_"] div.stHorizontalBlock:first-of-type {
        align-items: center !important;
    }
    /* Active Workout Buttons & Inputs: Standardized 38px / 12px */
    div[class*="st-key-wk_set_card_"] div[data-baseweb="input"],
    div[class*="st-key-wk_set_card_"] div[data-baseweb="input"] input,
    div[class*="st-key-log_set_"] button,
    div[class*="st-key-cat_btn_"] button,
    .st-key-toggle_workout_timer button,
    div[class*="st-key-wk_ex_toolbar_"] button,
    div[class*="st-key-wk_ex_toolbar_"] div[data-baseweb="select"],
    div[class*="st-key-wk_finish_bar"] button {
        height: 38px !important;
        min-height: 38px !important;
        max-height: 38px !important;
        line-height: 38px !important;
        font-size: 12px !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
        box-sizing: border-box !important;
    }
    div[class*="st-key-cat_btn_"] button {
        padding: 0 12px !important;
        width: auto !important;
    }
    div[class*="st-key-log_set_"] button {
        padding: 0 4px !important;
        margin: 0 !important;
    }
    .wk-set-meta-pill {
        font-size: 10.5px !important;
        gap: 6px !important;
        min-height: 38px !important;
        height: 38px !important;
        line-height: 38px !important;
    }
    .wk-input-col-label {
        font-size: 9.5px !important;
        height: 16px !important;
        line-height: 16px !important;
        margin-bottom: 4px !important;
    }

    /* Historical Set Rows: MUST NEVER STACK ON MOBILE */
    div[class*="st-key-form_hist_set_"] [data-testid="stHorizontalBlock"],
    div[class*="st-key-form_hist_set_"] div.stHorizontalBlock {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 4px !important;
        align-items: center !important;
        width: 100% !important;
    }
    div[class*="st-key-form_hist_set_"] [data-testid="stColumn"],
    div[class*="st-key-form_hist_set_"] div.stColumn {
        width: auto !important;
        min-width: 0 !important;
    }

    /* Cycle Bar: Keep in clean row */
    div[class*="st-key-wk_cycle_bar"] [data-testid="stHorizontalBlock"],
    div[class*="st-key-wk_cycle_bar"] div.stHorizontalBlock {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 4px !important;
        width: 100% !important;
    }
    div[class*="st-key-wk_cycle_bar"] [data-testid="stColumn"],
    div[class*="st-key-wk_cycle_bar"] div.stColumn {
        min-width: 0 !important;
        flex: 1 1 0 !important;
    }

    /* Exercise Toolbar Under Sets */
    div[class*="st-key-wk_ex_toolbar_"] [data-testid="stHorizontalBlock"],
    div[class*="st-key-wk_ex_toolbar_"] div.stHorizontalBlock {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 4px !important;
        align-items: center !important;
        width: 100% !important;
    }
    div[class*="st-key-wk_ex_toolbar_"] [data-testid="stColumn"],
    div[class*="st-key-wk_ex_toolbar_"] div.stColumn {
        min-width: 0 !important;
        flex: 1 1 0 !important;
        display: flex !important;
        align-items: center !important;
    }


    /* Finish & Discard Bar */
    div[class*="st-key-wk_finish_bar"] [data-testid="stHorizontalBlock"],
    div[class*="st-key-wk_finish_bar"] div.stHorizontalBlock {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 8px !important;
        width: 100% !important;
    }
    div[class*="st-key-wk_finish_bar"] [data-testid="stColumn"],
    div[class*="st-key-wk_finish_bar"] div.stColumn {
        min-width: 0 !important;
        flex: 1 1 50% !important;
    }
}

.wk-exercise-box-compact {
    background: rgba(14, 18, 14, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 10px 14px;
    margin: 6px 0 10px;
}
.wk-table-th {
    font-size: 10px;
    font-weight: 800;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding-bottom: 3px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    margin-bottom: 4px;
}
.wk-pr-badge {
    background: var(--accent-dim);
    color: var(--accent);
    border: 1px solid var(--accent);
    box-shadow: 0 0 8px var(--accent-glow);
    border-radius: 6px;
    padding: 2px 7px;
    font-size: 10.5px;
    font-weight: 800;
}
.wk-target-pill {
    background: rgba(56, 189, 248, 0.1);
    color: #7dd3fc;
    border: 1px solid rgba(56, 189, 248, 0.28);
    border-radius: 6px;
    padding: 2px 7px;
    font-size: 10.5px;
    font-weight: 800;
}
div[class*="st-key-log_set_"] button {
    min-height: 38px !important;
    padding: 2px 6px !important;
    font-size: 12px !important;
    font-weight: 800 !important;
}
div[class*="st-key-wt_"] input, div[class*="st-key-reps_"] input, div[class*="st-key-rpe_"] input, div[class*="st-key-sec_"] input {
    height: 38px !important;
    font-size: 13px !important;
    font-weight: 700 !important;
}
.htn-overload-card {
    background: linear-gradient(135deg, var(--accent-dim), var(--glass-card));
    border: 1px solid var(--accent);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25), 0 0 12px var(--accent-glow);
    border-radius: 14px;
    padding: 14px 18px;
    margin: 14px 0 16px;
}
.htn-overload-badge {
    background: var(--accent-dim);
    color: var(--accent);
    border: 1px solid var(--accent);
    box-shadow: 0 0 8px var(--accent-glow);
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 10.5px;
    font-weight: 900;
    letter-spacing: 0.6px;
    text-transform: uppercase;
}

/* Manage Routines & Workouts Compact Containers */
.st-key-manage_back_top button {
    background: transparent !important;
    border: none !important;
    color: var(--accent) !important;
    font-size: 13.5px !important;
    font-weight: 700 !important;
    padding: 2px 0 !important;
    width: auto !important;
    box-shadow: none !important;
    text-align: right !important;
    margin-left: auto !important;
}

div[class*="st-key-manage_r_"],
div[class*="st-key-manage_sess_"] {
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 14px;
    padding: 11px 14px;
    margin-bottom: 9px;
    box-sizing: border-box;
}

.wk-manage-item-title {
    font-size: 14.5px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 6px;
    overflow-wrap: anywhere;
}

div[class*="st-key-manage_r_"] [data-testid="stHorizontalBlock"],
div[class*="st-key-manage_r_"] div.stHorizontalBlock,
div[class*="st-key-manage_sess_"] [data-testid="stHorizontalBlock"],
div[class*="st-key-manage_sess_"] div.stHorizontalBlock {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 6px !important;
    width: 100% !important;
}

div[class*="st-key-manage_r_"] [data-testid="stColumn"],
div[class*="st-key-manage_r_"] div.stColumn,
div[class*="st-key-manage_sess_"] [data-testid="stColumn"],
div[class*="st-key-manage_sess_"] div.stColumn {
    min-width: 0 !important;
    flex: 1 1 0 !important;
}

div[class*="st-key-manage_r_"] button,
div[class*="st-key-manage_sess_"] button {
    min-height: 32px !important;
    font-size: 11.5px !important;
    font-weight: 700 !important;
    padding: 4px 8px !important;
    border-radius: 8px !important;
}

div[class*="st-key-del_r_"] button {
    border-color: rgba(255, 77, 77, 0.4) !important;
    color: #ff6b6b !important;
    background: rgba(255, 77, 77, 0.06) !important;
}
div[class*="st-key-del_r_"] button:hover {
    border-color: #ff4d4d !important;
    color: #ffffff !important;
    background: rgba(229, 62, 62, 0.8) !important;
}

div[class*="st-key-manage_ex_"] {
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 9px 12px;
    margin-bottom: 6px;
    box-sizing: border-box;
}

div[class*="st-key-manage_ex_"] [data-testid="stHorizontalBlock"],
div[class*="st-key-manage_ex_"] div.stHorizontalBlock {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 8px !important;
    align-items: center !important;
    width: 100% !important;
}

div[class*="st-key-manage_ex_"] [data-testid="stColumn"]:first-child,
div[class*="st-key-manage_ex_"] div.stColumn:first-child {
    flex: 1 1 auto !important;
    min-width: 0 !important;
}

div[class*="st-key-manage_ex_"] [data-testid="stColumn"]:last-child,
div[class*="st-key-manage_ex_"] div.stColumn:last-child {
    flex: 0 0 72px !important;
    min-width: 72px !important;
}

.wk-manage-ex-info {
    font-size: 13.5px;
    font-weight: 700;
    color: var(--text);
    overflow-wrap: anywhere;
}

div[class*="st-key-del_e_"] button {
    min-height: 28px !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    padding: 3px 6px !important;
    border-radius: 8px !important;
    background: rgba(255, 77, 77, 0.08) !important;
    color: #ff6b6b !important;
    border: 1px solid rgba(255, 77, 77, 0.3) !important;
}

div[class*="st-key-del_e_"] button:hover {
    background: rgba(229, 62, 62, 0.8) !important;
    color: #fff !important;
}

/* Hub Routines Compact Layout */
div[class*="st-key-hub_routine_"] {
    margin-bottom: 16px;
}
div[class*="st-key-hub_routine_"] [data-testid="stHorizontalBlock"],
div[class*="st-key-hub_routine_"] div.stHorizontalBlock {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 8px !important;
    width: 100% !important;
}
div[class*="st-key-hub_routine_"] [data-testid="stColumn"],
div[class*="st-key-hub_routine_"] div.stColumn {
    min-width: 0 !important;
    flex: 1 1 0 !important;
}
div[class*="st-key-hub_routine_"] button {
    min-height: 38px !important;
    font-size: 12.5px !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
}

/* Active Workout Top Bar */
div[class*="st-key-wk_active_bar"] {
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 14px;
    padding: 8px 12px;
    margin-bottom: 12px;
    box-sizing: border-box;
}
/* Vertically center the main columns (Left text vs Right controls) and the timer/button columns */
div[class*="st-key-wk_active_bar"] [data-testid="stHorizontalBlock"],
div[class*="st-key-wk_active_bar"] div.stHorizontalBlock {
    align-items: center !important;
}
/* Remove margin from timer iframe */
div[class*="st-key-wk_active_bar"] iframe,
div[class*="st-key-wk_active_bar"] div[data-testid="stHtml"],
div[class*="st-key-wk_active_bar"] div[data-testid="stMarkdownContainer"] {
    margin-bottom: 0 !important;
    padding-bottom: 0 !important;
}

/* Hub Actions */
div[class*="st-key-wk_hub_actions"] {
    margin-bottom: 14px;
}

/* ── Self-Adjusting Active Set Cards ── */
div[class*="st-key-wk_set_card_"] {
    background: rgba(20, 24, 20, 0.55) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 14px !important;
    padding: 12px 14px !important;
    margin-bottom: 12px !important;
    height: auto !important;
    min-height: auto !important;
    overflow: visible !important;
    box-sizing: border-box !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
div[class*="st-key-wk_set_card_"]:hover {
    border-color: rgba(255, 255, 255, 0.16) !important;
    background: rgba(24, 28, 24, 0.7) !important;
}
div[class*="st-key-wk_set_card_"]:has(button[kind="secondary"]) {
    border-color: rgba(34, 197, 94, 0.35) !important;
    background: rgba(18, 30, 20, 0.65) !important;
}


/* Align set card horizontal rows */
div[class*="st-key-wk_set_card_"] [data-testid="stHorizontalBlock"],
div[class*="st-key-wk_set_card_"] div.stHorizontalBlock {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: flex-start !important;
    gap: 6px !important;
    width: 100% !important;
}
div[class*="st-key-wk_set_card_"] [data-testid="stHorizontalBlock"]:first-of-type,
div[class*="st-key-wk_set_card_"] div.stHorizontalBlock:first-of-type {
    align-items: center !important;
    justify-content: space-between !important;
    margin-bottom: 8px !important;
}
div[class*="st-key-wk_set_card_"] [data-testid="stColumn"],
div[class*="st-key-wk_set_card_"] div.stColumn {
    min-width: 0 !important;
    flex: 1 1 0 !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-start !important;
}
div[class*="st-key-wk_set_card_"] [data-testid="stHorizontalBlock"]:first-of-type [data-testid="stColumn"]:first-child,
div[class*="st-key-wk_set_card_"] div.stHorizontalBlock:first-of-type div.stColumn:first-child {
    flex: 0 0 auto !important;
}
div[class*="st-key-wk_set_card_"] [data-testid="stHorizontalBlock"]:first-of-type [data-testid="stColumn"]:last-child,
div[class*="st-key-wk_set_card_"] div.stHorizontalBlock:first-of-type div.stColumn:last-child {
    flex: 1 1 auto !important;
}

/* Category button in set header (identical 38px height & 12px radius) */
div[class*="st-key-cat_btn_"] button {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    color: var(--text) !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    border-radius: 12px !important;
    padding: 0 14px !important;
    min-height: 38px !important;
    height: 38px !important;
    max-height: 38px !important;
    line-height: 38px !important;
    width: auto !important;
    white-space: nowrap !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-sizing: border-box !important;
    transition: all 0.2s ease !important;
}
div[class*="st-key-cat_btn_"] button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    background: var(--accent-dim) !important;
}

/* Set meta benchmarks pill (Previous & Target) */
.wk-set-meta-pill {
    display: flex !important;
    align-items: center !important;
    justify-content: flex-end !important;
    gap: 10px !important;
    font-size: 11.5px !important;
    color: var(--text-dim) !important;
    flex-wrap: wrap !important;
    min-height: 38px !important;
    height: 38px !important;
    line-height: 38px !important;
}

/* Column input labels placed directly over each input */
.wk-input-col-label {
    font-size: 10px !important;
    font-weight: 800 !important;
    color: var(--text-dim) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    margin-bottom: 4px !important;
    text-align: center !important;
    height: 18px !important;
    line-height: 18px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* Inputs within set card */
div[class*="st-key-wk_set_card_"] div[data-testid="stNumberInput"],
div[class*="st-key-wk_set_card_"] div.stButton {
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
}
div[class*="st-key-wk_set_card_"] div[data-baseweb="input"] {
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    padding: 0 !important;
    height: 38px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    box-sizing: border-box !important;
}
div[class*="st-key-wk_set_card_"] div[data-baseweb="input"] input {
    height: 38px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    line-height: 38px !important;
    font-size: 13.5px !important;
    font-weight: 700 !important;
    text-align: center !important;
    padding: 0 4px !important;
    color: var(--text) !important;
    box-sizing: border-box !important;
}
div[class*="st-key-wk_set_card_"] div[data-baseweb="input"]:focus-within {
    border-color: var(--accent) !important;
    box-shadow: 0 0 10px var(--accent-glow) !important;
}

/* Hide bulky steppers */
div[class*="st-key-wk_set_card_"] button[data-testid="stNumberInputStepDown"],
div[class*="st-key-wk_set_card_"] button[data-testid="stNumberInputStepUp"] {
    display: none !important;
}

/* Log / Done action button (identical 38px height & 12px radius) */
div[class*="st-key-log_set_"] button {
    height: 38px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    line-height: 38px !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    border-radius: 12px !important;
    padding: 0 6px !important;
    margin: 0 !important;
    width: 100% !important;
    box-sizing: border-box !important;
    transition: all 0.2s ease !important;
}
div[class*="st-key-log_set_"] button[kind="secondary"] {
    background: rgba(34, 197, 94, 0.16) !important;
    border: 1px solid rgba(34, 197, 94, 0.45) !important;
    color: #4ade80 !important;
    box-shadow: 0 0 10px rgba(34, 197, 94, 0.2) !important;
}
div[class*="st-key-log_set_"] button[kind="secondary"]:hover {
    background: rgba(34, 197, 94, 0.28) !important;
    box-shadow: 0 0 14px rgba(34, 197, 94, 0.35) !important;
}
div[class*="st-key-log_set_"] button[kind="primary"] {
    background: var(--accent) !important;
    color: var(--btn-text) !important;
    border: 1px solid var(--accent) !important;
    box-shadow: 0 2px 12px var(--accent-glow) !important;
}

/* Historical Edit Set Form Components */
div[class*="st-key-form_hist_set_"] {
    background: rgba(20, 24, 20, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 6px 10px;
    margin-bottom: 6px;
    box-sizing: border-box;
}
div[class*="st-key-form_hist_set_"] div[data-baseweb="select"] {
    min-height: 28px !important;
    font-size: 11px !important;
    border-radius: 8px !important;
}
div[class*="st-key-form_hist_set_"] div[data-baseweb="input"] input {
    height: 34px !important;
    font-size: 12.5px !important;
    font-weight: 700 !important;
    text-align: center !important;
    padding: 2px 4px !important;
}
div[class*="st-key-form_hist_set_"] button {
    min-height: 34px !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    border-radius: 8px !important;
    padding: 4px 6px !important;
}

/* Cycle Bar Buttons */
div[class*="st-key-wk_cycle_bar"] {
    margin: 6px 0 10px;
}
div[class*="st-key-wk_cycle_bar"] button {
    height: 38px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    line-height: 38px !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    border-radius: 12px !important;
    padding: 0 10px !important;
    box-sizing: border-box !important;
}

/* Exercise Toolbar Under Sets */
div[class*="st-key-wk_ex_toolbar_"] {
    margin: 4px 0 10px;
}
div[class*="st-key-wk_ex_toolbar_"] button {
    height: 38px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    line-height: 38px !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    border-radius: 12px !important;
    padding: 0 10px !important;
    box-sizing: border-box !important;
}

/* Force selectbox to exactly 38px to match buttons */
div[class*="st-key-wk_ex_toolbar_"] [data-testid="stSelectbox"],
div[class*="st-key-wk_ex_toolbar_"] div[data-baseweb="select"],
div[class*="st-key-wk_ex_toolbar_"] div[data-baseweb="select"] > div {
    height: 38px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    margin: 0 !important;
    box-sizing: border-box !important;
}
div[class*="st-key-wk_ex_toolbar_"] div[data-baseweb="select"] > div {
    border-radius: 12px !important;
}
div[class*="st-key-wk_ex_toolbar_"] [data-testid="stHorizontalBlock"],
div[class*="st-key-wk_ex_toolbar_"] div.stHorizontalBlock {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 6px !important;
    align-items: center !important;
    width: 100% !important;
}
div[class*="st-key-wk_ex_toolbar_"] [data-testid="stColumn"],
div[class*="st-key-wk_ex_toolbar_"] div.stColumn {
    min-width: 0 !important;
    flex: 1 1 0 !important;
    display: flex !important;
    align-items: center !important;
}

/* Finish & Discard Bar */
div[class*="st-key-wk_finish_bar"] {
    margin-top: 8px;
}
div[class*="st-key-wk_finish_bar"] button {
    height: 38px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    line-height: 38px !important;
    font-size: 13px !important;
    font-weight: 800 !important;
    border-radius: 12px !important;
    box-sizing: border-box !important;
}

/* Never let chatbot FAB overlap active workout interface */
body:has(div[class*="st-key-wk_set_card_"]) .st-key-chatbot_fab,
div[class*="st-key-wk_set_card_"] ~ div .st-key-chatbot_fab,
.st-key-wk_shell:has(.st-key-toggle_workout_timer) ~ div .st-key-chatbot_fab {
    display: none !important;
}
"""
inject_theme_css(PAGE_CSS)
if st.session_state.get("workout_mode") != "active":
    render_chatbot_fab()
render_nav_bar(active="workout")

# -----------------------------------------------------------------------------
# Session state
# -----------------------------------------------------------------------------
_defaults = {
    "workout_mode": None,
    "active_session_id": None,
    "workout_timer_running": False,
    "workout_elapsed_seconds": 0,
    "workout_timer_start_time": None,
    "active_exercises": [],
    "set_counts": {},
    "active_set_entries": {},
    "open_exercises": set(),
    "create_exercise_open": False,
    "rest_timer_end": None,
    "rest_timer_exercise_id": None,
    "rest_timer_label": None,
    "editing_routine_id": None,
    "editing_session_id": None,
    "pending_delete_session_id": None,
    "expanded_section": None,
}
for _key, _value in _defaults.items():
    if _key not in st.session_state:
        st.session_state[_key] = _value.copy() if isinstance(_value, (dict, set)) else list(_value) if isinstance(_value, list) else _value


def get_set_entry(ex_id: int, set_num: int) -> dict:
    if "active_set_entries" not in st.session_state:
        st.session_state.active_set_entries = {}
    key = (ex_id, set_num)
    if key not in st.session_state.active_set_entries:
        st.session_state.active_set_entries[key] = {
            "weight": 0.0,
            "reps": 0,
            "rpe": 0.0,
            "time": 0,
            "category": "Working Set",
            "completed": False,
        }
    return st.session_state.active_set_entries[key]


def auto_fill_sets_callback(ex_id: int, count: int, sug: dict, ex_type: str, ex_name: str):
    for s in range(1, count + 1):
        se = get_set_entry(ex_id, s)
        if not se.get("completed"):
            se["weight"] = float(sug.get("weight", 0.0))
            se["reps"] = int(sug.get("reps", 0))
            se["rpe"] = float(sug.get("rpe", 0.0))
            st.session_state[f"wt_{ex_id}_{s}"] = se["weight"]
            st.session_state[f"reps_{ex_id}_{s}"] = se["reps"]
            st.session_state[f"rpe_{ex_id}_{s}"] = se["rpe"]
            if ex_type == "time":
                se["time"] = int(sug.get("duration", 45))
                st.session_state[f"sec_{ex_id}_{s}"] = se["time"]
    st.toast(f"Filled suggested targets for {ex_name}!")


def reset_rest_timer():
    st.session_state.rest_timer_end = None
    st.session_state.rest_timer_exercise_id = None
    st.session_state.rest_timer_label = None


def selected_rest_seconds(exercise_id):
    choice = st.session_state.get(f"rest_timer_choice_{exercise_id}", "60 sec")
    if choice == "Off":
        return 0
    if choice == "Custom":
        return max(0, int(st.session_state.get(f"rest_custom_seconds_{exercise_id}", 60)))
    return int(choice.split()[0])


def start_rest_timer(exercise_id, label):
    seconds = selected_rest_seconds(exercise_id)
    if seconds < 1:
        reset_rest_timer()
        return
    st.session_state.rest_timer_end = time.time() + seconds
    st.session_state.rest_timer_exercise_id = exercise_id
    st.session_state.rest_timer_label = label


def rest_timer_html():
    end = st.session_state.get("rest_timer_end")
    label = st.session_state.get("rest_timer_label") or "Rest"
    if not end:
        return

    remaining = max(0, int(end - time.time() + 0.999))
    safe_label = (
        label.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    tk = get_theme_tokens()

    components.html(
        f"""
        <div id="htn-rest-card" style="
            width:100%;
            box-sizing:border-box;
            border:1px solid {tk['accent']};
            background:{tk['accent_dim']};
            box-shadow:0 0 16px {tk['accent_glow']};
            border-radius:16px;
            padding:14px 16px;
            margin:0;
            text-align:center;
            font-family:Inter, sans-serif;
            transition: all 0.3s ease;
        ">
            <div id="htn-rest-sub" style="color:#9a9d98; font-size:11px; text-transform:uppercase; letter-spacing:.8px; font-weight:600;">
                Rest timer · {safe_label}
            </div>
            <div id="htn-rest-time" style="color:{tk['accent']}; font-size:32px; font-weight:800; margin-top:2px; line-height:1.1; text-shadow:0 0 14px {tk['accent_glow']};">
                {remaining}s
            </div>
        </div>

        <script>
        (() => {{
            const end = {end * 1000};
            const el = document.getElementById("htn-rest-time");
            const sub = document.getElementById("htn-rest-sub");
            const card = document.getElementById("htn-rest-card");
            let finished = false;
            if (!el) return;

            function playBeep() {{
                try {{
                    const ctx = new (window.AudioContext || window.webkitAudioContext)();
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    osc.type = "sine";
                    osc.frequency.setValueAtTime(880, ctx.currentTime);
                    gain.gain.setValueAtTime(0.12, ctx.currentTime);
                    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.6);
                    osc.start();
                    osc.stop(ctx.currentTime + 0.6);
                }} catch (e) {{}}
            }}

            const tick = () => {{
                const left = Math.max(0, Math.ceil((end - Date.now()) / 1000));
                if (left > 0) {{
                    el.textContent = left + "s";
                }} else if (!finished) {{
                    finished = true;
                    el.textContent = "DONE!";
                    el.style.color = "#ffffff";
                    if (sub) sub.textContent = "REST COMPLETE · READY FOR NEXT SET";
                    if (card) {{
                        card.style.background = "{tk['accent_dim']}";
                        card.style.borderColor = "#ffffff";
                    }}
                    playBeep();
                }}
            }};
            window.setInterval(tick, 200);
            tick();
        }})();
        </script>
        """,
        height=76,
        scrolling=False,
    )

    if st.button("Dismiss rest", key="rest_skip", use_container_width=True):
        reset_rest_timer()
        st.rerun()


def elapsed_timer_html(is_running: bool, base_seconds: int, start_ts: float | None):
    tk = get_theme_tokens()
    status_label = "elapsed" if is_running else ("paused" if base_seconds > 0 else "ready")
    status_color = tk["accent"] if is_running else "#8f938f"

    initial_sec = base_seconds
    if is_running and start_ts:
        initial_sec += max(0, int(time.time() - start_ts))

    init_m = initial_sec // 60
    init_s = initial_sec % 60

    components.html(
        f"""
        <style>
            html, body {{
                margin: 0;
                padding: 0;
                background: transparent;
                overflow: hidden;
                font-family: Inter, Arial, sans-serif;
            }}
            .timer-wrap {{
                width: 100%;
                height: 48px;
                display: flex;
                align-items: center;
                justify-content: flex-end;
                box-sizing: border-box;
            }}
            .timer-card {{
                text-align: right;
                line-height: 1;
            }}
            .timer-value {{
                color: {tk['accent']};
                font-size: clamp(22px, 3.5vw, 26px);
                font-weight: 800;
                letter-spacing: -0.5px;
                text-shadow: 0 0 12px {tk['accent_glow']};
            }}
            .timer-label {{
                margin-top: 4px;
                color: {status_color};
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
        </style>

        <div class="timer-wrap">
            <div class="timer-card">
                <div class="timer-value" id="htn-workout-elapsed">
                    {init_m}:{init_s:02d}
                </div>
                <div class="timer-label">{status_label}</div>
            </div>
        </div>

        <script>
        (() => {{
            const isRunning = {str(is_running).lower()};
            if (!isRunning) return;

            const base = {base_seconds};
            const started = {(start_ts or time.time()) * 1000};
            const el = document.getElementById("htn-workout-elapsed");
            if (!el) return;

            const tick = () => {{
                const extra = Math.max(0, Math.floor((Date.now() - started) / 1000));
                const total = base + extra;
                const mins = Math.floor(total / 60);
                const secs = String(total % 60).padStart(2, "0");
                el.textContent = mins + ":" + secs;
                window.setTimeout(tick, 250);
            }};

            tick();
        }})();
        </script>
        """,
        height=52,
        scrolling=False,
    )


def tracking_label(exercise_type: str) -> str:
    labels = {
        "weights_reps": "Weights + Reps",
        "reps": "Weights + Reps",
        "time": "Time",
        "bodyweight": "Bodyweight",
        "weighted_calisthenics": "Weighted Calisthenics",
    }
    return labels.get(exercise_type, exercise_type.replace("_", " ").title())


def _normalise_exercise_name(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def _format_pr_delta(val: float) -> str:
    return str(int(val)) if val == int(val) else f"{val:.1f}"


def check_set_prs(exercise, set_number: int, entry: dict):
    ex_id = exercise["id"]
    ex_type = exercise["exercise_type"]
    bests = get_exercise_personal_bests(user_id, ex_id)

    current = {}
    if ex_type == "time":
        val = entry.get("time", 0)
        if val > 0:
            current["duration"] = float(val)
    elif ex_type == "bodyweight":
        reps = entry.get("reps", 0)
        rpe = entry.get("rpe", 0.0)
        if reps > 0:
            current["reps"] = float(reps)
        if rpe > 0:
            current["rpe"] = float(rpe)
    else:
        reps = entry.get("reps", 0)
        rpe = entry.get("rpe", 0.0)
        weight = entry.get("weight", 0.0)
        if reps > 0:
            current["reps"] = float(reps)
        if rpe > 0:
            current["rpe"] = float(rpe)
        if weight > 0:
            current["weight"] = float(weight)

    previous_map = {
        "weight": bests.get("best_weight"),
        "reps": bests.get("best_reps"),
        "rpe": bests.get("best_rpe"),
        "duration": bests.get("best_duration"),
    }
    labels = {
        "weight": "weights",
        "reps": "reps",
        "rpe": "rpe",
        "duration": "time",
    }
    units = {
        "weight": " kg",
        "reps": " reps",
        "rpe": "",
        "duration": "s",
    }

    for metric, value in current.items():
        old = previous_map.get(metric)
        if old is not None:
            old_val = float(old)
            if value > old_val:
                diff = value - old_val
                pct = (diff / old_val * 100) if old_val > 0 else 0
                diff_str = f"+{_format_pr_delta(diff)}{units[metric]}"
                pct_str = f"+{pct:.1f}%"
                st.toast(
                    f"You just hit a PR in {labels[metric]} by {diff_str} ({pct_str})!"
                )
        elif value > 0:
            val_str = f"{_format_pr_delta(value)}{units[metric]}"
            st.toast(
                f"You just set a PR in {labels[metric]} of {val_str}!"
            )


def show_create_exercise():
    st.markdown('<div class="wk-section-title" style="margin:4px 0 12px;">Create exercise</div>', unsafe_allow_html=True)
    with st.form("create_exercise_form", clear_on_submit=True):
        name = st.text_input("Exercise name", placeholder="e.g. Bulgarian Split Squat")
        muscle = st.selectbox("Muscle group", MUSCLE_GROUPS)
        ex_type = st.selectbox("Tracking type", ["Weights + Reps", "Time", "Bodyweight", "Weighted Calisthenics"])
        equipment = st.text_input("Equipment", placeholder="Optional (e.g. Dumbbell, Barbell)")
        save = st.form_submit_button("Create exercise", use_container_width=True)
        if save:
            normalised_name = _normalise_exercise_name(name)
            existing_names = {_normalise_exercise_name(ex["name"]) for ex in get_all_exercises(user_id)}
            if normalised_name in existing_names:
                st.error("exercise already added")
                return

            type_value = {
                "Weights + Reps": "weights_reps",
                "Time": "time",
                "Bodyweight": "bodyweight",
                "Weighted Calisthenics": "weighted_calisthenics",
            }[ex_type]
            result = create_exercise(user_id, name, muscle, type_value, equipment)
            if result["success"]:
                st.session_state.create_exercise_open = False
                st.success("Exercise created.")
                st.rerun()
            st.error(result["error"])


def reset_workout_state():
    st.session_state.workout_mode = None
    st.session_state.active_session_id = None
    st.session_state.workout_timer_running = False
    st.session_state.workout_elapsed_seconds = 0
    st.session_state.workout_timer_start_time = None
    st.session_state.active_exercises = []
    st.session_state.set_counts = {}
    st.session_state.active_set_entries = {}
    st.session_state.open_exercises = set()
    st.session_state.active_workout_source = None
    st.session_state.active_exercise_prescriptions = {}
    reset_rest_timer()


def start_empty_workout():
    session_id = start_session(user_id, None)
    st.session_state.workout_mode = "active"
    st.session_state.active_session_id = session_id
    st.session_state.workout_timer_running = False
    st.session_state.workout_elapsed_seconds = 0
    st.session_state.workout_timer_start_time = None
    st.session_state.active_exercises = []
    st.session_state.set_counts = {}
    st.session_state.active_set_entries = {}
    st.session_state.open_exercises = set()
    st.session_state.active_workout_source = "empty"
    st.session_state.active_routine_name = "Freestyle Workout"
    st.session_state.active_exercise_prescriptions = {}
    reset_rest_timer()


def start_routine(routine_id):
    exercises = get_routine_exercises(routine_id)
    routine_name = "Routine"
    conn_r = get_connection()
    r_row = conn_r.execute("SELECT name FROM routines WHERE id=?", (routine_id,)).fetchone()
    if not r_row:
        r_row = conn_r.execute("SELECT name FROM builtin_routines WHERE id=?", (routine_id,)).fetchone()
    if r_row:
        routine_name = r_row["name"]
    conn_r.close()

    session_id = start_session(user_id, routine_id)
    st.session_state.workout_mode = "active"
    st.session_state.active_session_id = session_id
    st.session_state.workout_timer_running = False
    st.session_state.workout_elapsed_seconds = 0
    st.session_state.workout_timer_start_time = None
    st.session_state.active_exercises = exercises
    st.session_state.set_counts = {e["id"]: 3 for e in exercises}
    st.session_state.active_set_entries = {}
    st.session_state.open_exercises = {exercises[0]["id"]} if exercises else set()
    st.session_state.active_workout_source = "routine"
    st.session_state.active_routine_name = routine_name
    st.session_state.active_exercise_prescriptions = {}
    reset_rest_timer()


def finish_active_workout(notes: str):
    running = st.session_state.get("workout_timer_running", False)
    base_sec = st.session_state.get("workout_elapsed_seconds", 0)
    start_ts = st.session_state.get("workout_timer_start_time")
    duration = base_sec
    if running and start_ts:
        duration += max(0, int(time.time() - start_ts))

    session_id = st.session_state.active_session_id

    entries = st.session_state.get("active_set_entries", {})

    for ex in st.session_state.active_exercises:
        ex_id = ex["id"]
        count = st.session_state.set_counts.get(ex_id, 1)
        for i in range(1, count + 1):
            s_data = entries.get((ex_id, i))
            if not s_data:
                continue

            cat_display = s_data.get("category", "Working Set")
            set_type = "warmup" if cat_display == "Warm-up Set" else ("dropset" if cat_display == "Drop Set" else "working")

            if ex["exercise_type"] == "time":
                seconds = int(s_data.get("time") or 0)
                if seconds > 0:
                    log_set(
                        session_id,
                        ex_id,
                        i,
                        duration_seconds=seconds,
                        set_type=set_type,
                    )
            elif ex["exercise_type"] == "bodyweight":
                reps = int(s_data.get("reps") or 0)
                rpe_val = float(s_data.get("rpe") or 0.0)
                if reps > 0:
                    log_set(
                        session_id,
                        ex_id,
                        i,
                        reps=reps,
                        weight=None,
                        rpe=rpe_val if rpe_val > 0 else None,
                        set_type=set_type,
                    )
            else:
                reps = int(s_data.get("reps") or 0)
                weight_val = float(s_data.get("weight") or 0.0)
                rpe_val = float(s_data.get("rpe") or 0.0)
                if reps > 0 or weight_val > 0:
                    log_set(
                        session_id,
                        ex_id,
                        i,
                        reps=reps if reps > 0 else None,
                        weight=weight_val if weight_val > 0 else None,
                        rpe=rpe_val if rpe_val > 0 else None,
                        set_type=set_type,
                    )

    source_type = st.session_state.get("active_workout_source", "empty")
    if source_type == "periodization":
        w_num = st.session_state.get("active_periodization_week", 1)
        d_num = st.session_state.get("active_periodization_day", 1)
        prog_id = st.session_state.get("active_periodization_program_id", 1)
        p_kg = st.session_state.get("active_periodization_prog_kg", 2.5) or 2.5
        p_reps = st.session_state.get("active_periodization_prog_reps", 1) or 1
        c_name = st.session_state.get("active_periodization_cycle_name", "Training Cycle")
        st.session_state.post_workout_periodization_notice = {
            "week": w_num,
            "day": d_num,
            "program_id": prog_id,
            "cycle_name": c_name,
            "prog_kg": p_kg,
            "prog_reps": p_reps,
        }

    finish_session(session_id, duration, notes)
    reset_workout_state()
    st.rerun()


def active_workout_view():
    source_type = st.session_state.get("active_workout_source", "empty")
    if source_type == "periodization":
        w_num = st.session_state.get("active_periodization_week", 1)
        d_num = st.session_state.get("active_periodization_day", 1)
        ph_title = st.session_state.get("active_periodization_phase", "Training")
        c_name = st.session_state.get("active_periodization_cycle_name", "Periodization Mesocycle")
        p_kg = st.session_state.get("active_periodization_prog_kg", 2.5)
        ctx_title = f"{c_name} · W{w_num}D{d_num}"
        ctx_sub = f"{ph_title} · Overload: +{p_kg} kg"
    elif source_type == "routine":
        r_name = st.session_state.get("active_routine_name", "Custom Routine")
        ctx_title = r_name
        ctx_sub = "Scheduled Routine Training"
    else:
        ctx_title = "Freestyle"
        ctx_sub = "Active Training Session"

    # ── Compact Top Bar ──────────────────────────────────────────────────────
    with st.container(key="wk_active_bar"):
        c_head_left, c_head_ctrl = st.columns([1.5, 1.5], gap="small")
        with c_head_left:
            st.markdown(
                clean_html(f"""
                <div style="font-size:11px;font-weight:800;color:var(--accent);text-transform:uppercase;letter-spacing:0.8px;">
                    Active Workout
                </div>
                <div style="font-size:16px;font-weight:900;color:var(--text);letter-spacing:-0.3px;line-height:1.25;margin-top:2px;overflow-wrap:anywhere;">
                    {ctx_title}
                </div>
                <div style="font-size:11px;color:var(--text-dim);margin-top:2px;">{ctx_sub}</div>
                """),
                unsafe_allow_html=True,
            )

        is_running = st.session_state.get("workout_timer_running", False)
        base_seconds = st.session_state.get("workout_elapsed_seconds", 0)
        start_ts = st.session_state.get("workout_timer_start_time")

        with c_head_ctrl:
            c_timer, c_btn = st.columns([1.2, 1.0], gap="small")
            with c_timer:
                elapsed_timer_html(is_running, base_seconds, start_ts)
            with c_btn:
                if not is_running:
                    btn_label = "Resume" if base_seconds > 0 else "Start"
                    if st.button(btn_label, key="toggle_workout_timer", type="primary", use_container_width=True):
                        st.session_state.workout_timer_running = True
                        st.session_state.workout_timer_start_time = time.time()
                        st.rerun()
                else:
                    if st.button("Pause", key="toggle_workout_timer", use_container_width=True):
                        if start_ts:
                            st.session_state.workout_elapsed_seconds = base_seconds + max(0, int(time.time() - start_ts))
                        st.session_state.workout_timer_running = False
                        st.session_state.workout_timer_start_time = None
                        st.rerun()

    rest_timer_html()

    if not st.session_state.active_exercises:
        st.markdown('<div class="wk-card wk-muted">This workout is empty. Add an exercise below.</div>', unsafe_allow_html=True)

    rest_choices = ["Off", "15 sec", "30 sec", "45 sec", "60 sec", "90 sec", "120 sec", "Custom"]
    if "open_exercises" not in st.session_state:
        st.session_state.open_exercises = {st.session_state.active_exercises[0]["id"]} if st.session_state.active_exercises else set()

    prog_kg = st.session_state.get("active_periodization_prog_kg", 2.5) or 2.5
    prog_reps = st.session_state.get("active_periodization_prog_reps", 1) or 1

    # ── Collapsible Exercises with Compact Set Matrix ────────────────────────
    for ex in st.session_state.active_exercises:
        ex_type = ex["exercise_type"]
        ex_id = ex["id"]
        count = st.session_state.set_counts.get(ex_id, 1)
        completed_count = sum(1 for s in range(1, count + 1) if get_set_entry(ex_id, s).get("completed"))
        is_all_done = (completed_count == count and count > 0)
        status_tag = f"Done {completed_count}/{count}" if is_all_done else f"{completed_count}/{count} sets"

        # Prescription details
        presc = st.session_state.get("active_exercise_prescriptions", {}).get(ex_id, {})
        target_str = presc.get("target", "")
        role = presc.get("role", "")
        if role in ("focus", "primary"):
            role_badge = '<span class="htn-role-badge-primary">PRIMARY FOCUS</span>'
        elif role in ("support", "hypertrophy"):
            role_badge = '<span class="htn-role-badge-support">HYPERTROPHY SUPPORT</span>'
        elif role in ("auxiliary", "aux"):
            role_badge = '<span class="htn-role-badge-aux">COMPOUND AUXILIARY</span>'
        else:
            role_badge = ''

        # Personal Best
        bests = get_exercise_personal_bests(user_id, ex_id)
        if bests.get("best_weight"):
            best_str = f"{bests['best_weight']}kg"
            if bests.get("best_reps"):
                best_str += f" × {bests['best_reps']}"
        elif bests.get("best_reps"):
            best_str = f"{bests['best_reps']} reps"
        elif bests.get("best_duration"):
            best_str = f"{bests['best_duration']}s"
        else:
            best_str = "No PR yet"

        # Previous History
        previous = get_previous_performance(user_id, ex_id)
        if previous:
            if ex_type == "time":
                prev_text = ", ".join(f"{p['duration_seconds']}s" for p in previous[:3] if p.get("duration_seconds") is not None)
            elif ex_type == "bodyweight":
                prev_text = ", ".join(f"{p['reps']}r" for p in previous[:3] if p.get("reps") is not None)
            elif ex_type == "weighted_calisthenics":
                prev_text = ", ".join(f"+{p['weight']}kg × {p['reps']}" for p in previous[:3] if p.get("weight") is not None and p.get("reps") is not None)
            else:
                prev_text = ", ".join(f"{p['weight']}kg × {p['reps']}" for p in previous[:3] if p.get("weight") is not None and p.get("reps") is not None)
        else:
            prev_text = "First session"

        # Calculate Smart Progressive Overload Suggestion
        sug = calculate_progressive_overload_suggestion(
            user_id=user_id,
            exercise_id=ex_id,
            prescribed_target=target_str,
            exercise_type=ex_type,
            cycle_prog_kg=prog_kg,
            cycle_prog_reps=prog_reps,
        )

        is_open = ex_id in st.session_state.open_exercises
        arrow = "▾" if is_open else "▸"
        done_flag = "[DONE] " if is_all_done else ""
        btn_label = f"{arrow}  {done_flag}{ex['name']}  ·  {ex['muscle_group']}   [{status_tag}]"

        if st.button(btn_label, key=f"toggle_ex_{ex_id}", use_container_width=True):
            if is_open:
                st.session_state.open_exercises.discard(ex_id)
            else:
                st.session_state.open_exercises.add(ex_id)
            st.rerun()

        if is_open:
            sug_display = f"{sug['weight']}kg × {sug['reps']}r" if ex_type not in ("bodyweight", "time") else (f"{sug['reps']} reps" if ex_type == "bodyweight" else f"{sug.get('duration', 45)}s")
            target_badge_html = f'<span class="wk-target-pill">Target: {target_str}</span>' if target_str else ''

            st.markdown(
                clean_html(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;padding:2px 4px;margin:2px 0 10px 0;font-size:11px;color:var(--text-dim);">
                    <div style="display:flex;align-items:center;gap:6px;">
                        {role_badge}
                        <span class="wk-pr-badge">PR: {best_str}</span>
                    </div>
                    <div style="font-size:11px;color:var(--text-dim);">
                        <span style="color:var(--accent);font-weight:700;">Target:</span> <b style="color:var(--accent);">{sug_display}</b> <span style="font-size:10px;font-weight:400;color:var(--text-dim);">({sug['reason']})</span>
                    </div>
                </div>
                """),
                unsafe_allow_html=True,
            )

            # Self-Adjusting Set Cards (Line 1: Header/Bench, Line 2: Inputs/Status)
            cat_order = ["Working Set", "Warm-up Set", "Drop Set"]
            for s_idx in range(1, count + 1):
                entry = get_set_entry(ex_id, s_idx)
                is_done = entry.get("completed", False)

                p_set = previous[s_idx - 1] if previous and len(previous) >= s_idx else None
                if p_set:
                    if ex_type == "time":
                        p_set_str = f"{p_set.get('duration_seconds', 0)}s"
                    elif ex_type == "bodyweight":
                        p_set_str = f"{p_set.get('reps', 0)}r"
                    else:
                        p_set_str = f"{p_set.get('weight', 0)}k × {p_set.get('reps', 0)}"
                else:
                    p_set_str = "—"

                # Pre-fill untouched entries with suggestion defaults
                if not is_done:
                    if ex_type not in ("bodyweight", "time") and entry.get("weight", 0.0) == 0.0 and sug["weight"] > 0:
                        entry["weight"] = sug["weight"]
                    if ex_type != "time" and entry.get("reps", 0) == 0 and sug["reps"] > 0:
                        entry["reps"] = sug["reps"]
                    if entry.get("rpe", 0.0) == 0.0 and sug.get("rpe", 0.0) > 0:
                        entry["rpe"] = sug["rpe"]
                    if ex_type == "time" and entry.get("time", 0) == 0 and sug.get("duration", 0) > 0:
                        entry["time"] = sug["duration"]

                curr_cat = entry.get("category", "Working Set")
                cat_tag = "Warm-up" if curr_cat == "Warm-up Set" else ("Drop" if curr_cat == "Drop Set" else "Set")
                done_prefix = "✓ " if is_done else ""
                tag_label = f"{done_prefix}#{s_idx} · {cat_tag}"

                with st.container(key=f"wk_set_card_{ex_id}_{s_idx}"):
                    # Line 1: Header / Benchmark Line (Category pill + Previous/Target benchmarks)
                    c_badge, c_bench = st.columns([1.1, 1.9], gap="small")
                    with c_badge:
                        if st.button(tag_label, key=f"cat_btn_{ex_id}_{s_idx}", help=f"Type: {curr_cat}. Tap to change (Working / Warm-up / Drop)"):
                            next_idx = (cat_order.index(curr_cat) + 1) % len(cat_order) if curr_cat in cat_order else 0
                            entry["category"] = cat_order[next_idx]
                            st.rerun()
                    with c_bench:
                        if ex_type == "time":
                            tgt_label = f"{sug.get('duration', 45)}s"
                        elif ex_type == "bodyweight":
                            tgt_label = f"{sug['reps']}r"
                        else:
                            tgt_label = f"{sug['weight']}k × {sug['reps']}r"
                        st.markdown(
                            f'<div class="wk-set-meta-pill">'
                            f'<span>Prev: <b>{p_set_str}</b></span>'
                            f'<span>Target: <b style="color:var(--accent);">{tgt_label}</b></span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                    # Line 2: Self-Adjusting Column Inputs with Direct Top Labels
                    if ex_type == "time":
                        c_val, c_act = st.columns([2.0, 1.2], gap="small")
                        with c_val:
                            st.markdown('<div class="wk-input-col-label">SECONDS</div>', unsafe_allow_html=True)
                            val_t = st.number_input("Seconds", min_value=0, value=int(entry.get("time", sug.get("duration", 45))), step=5, key=f"sec_{ex_id}_{s_idx}", label_visibility="collapsed")
                            entry["time"] = int(val_t)
                        with c_act:
                            st.markdown('<div class="wk-input-col-label">LOG</div>', unsafe_allow_html=True)
                            btn_txt = "✓ Done" if is_done else "Log Set"
                            if st.button(btn_txt, key=f"log_set_{ex_id}_{s_idx}", type="secondary" if is_done else "primary", use_container_width=True, help="Completed set (tap to undo)" if is_done else "Log this set"):
                                if is_done:
                                    entry["completed"] = False
                                else:
                                    entry["completed"] = True
                                    check_set_prs(ex, s_idx, entry)
                                    start_rest_timer(ex_id, f"{ex['name']} · Set {s_idx}")
                                st.rerun()

                    elif ex_type == "bodyweight":
                        c_r, c_rpe, c_act = st.columns([1.3, 1.1, 1.2], gap="small")
                        with c_r:
                            st.markdown('<div class="wk-input-col-label">REPS</div>', unsafe_allow_html=True)
                            val_r = st.number_input("Reps", min_value=0, value=int(entry.get("reps", sug["reps"])), step=1, key=f"reps_{ex_id}_{s_idx}", label_visibility="collapsed")
                            entry["reps"] = int(val_r)
                        with c_rpe:
                            st.markdown('<div class="wk-input-col-label">RPE</div>', unsafe_allow_html=True)
                            val_rpe = st.number_input("RPE", min_value=0.0, max_value=10.0, value=float(entry.get("rpe", sug["rpe"])), step=0.5, key=f"rpe_{ex_id}_{s_idx}", label_visibility="collapsed")
                            entry["rpe"] = float(val_rpe)
                        with c_act:
                            st.markdown('<div class="wk-input-col-label">LOG</div>', unsafe_allow_html=True)
                            btn_txt = "✓ Done" if is_done else "Log Set"
                            if st.button(btn_txt, key=f"log_set_{ex_id}_{s_idx}", type="secondary" if is_done else "primary", use_container_width=True, help="Completed set (tap to undo)" if is_done else "Log this set"):
                                if is_done:
                                    entry["completed"] = False
                                else:
                                    entry["completed"] = True
                                    check_set_prs(ex, s_idx, entry)
                                    start_rest_timer(ex_id, f"{ex['name']} · Set {s_idx}")
                                st.rerun()

                    else:
                        w_col_label = "+KG" if ex_type == "weighted_calisthenics" else "KG"
                        c_w, c_r, c_rpe, c_act = st.columns([1.1, 1.1, 1.0, 1.2], gap="small")
                        with c_w:
                            st.markdown(f'<div class="wk-input-col-label">{w_col_label}</div>', unsafe_allow_html=True)
                            val_w = st.number_input("Weight", min_value=0.0, value=float(entry.get("weight", sug["weight"])), step=0.5, key=f"wt_{ex_id}_{s_idx}", label_visibility="collapsed")
                            entry["weight"] = float(val_w)
                        with c_r:
                            st.markdown('<div class="wk-input-col-label">REPS</div>', unsafe_allow_html=True)
                            val_r = st.number_input("Reps", min_value=0, value=int(entry.get("reps", sug["reps"])), step=1, key=f"reps_{ex_id}_{s_idx}", label_visibility="collapsed")
                            entry["reps"] = int(val_r)
                        with c_rpe:
                            st.markdown('<div class="wk-input-col-label">RPE</div>', unsafe_allow_html=True)
                            val_rpe = st.number_input("RPE", min_value=0.0, max_value=10.0, value=float(entry.get("rpe", sug["rpe"])), step=0.5, key=f"rpe_{ex_id}_{s_idx}", label_visibility="collapsed")
                            entry["rpe"] = float(val_rpe)
                        with c_act:
                            st.markdown('<div class="wk-input-col-label">LOG</div>', unsafe_allow_html=True)
                            btn_txt = "✓ Done" if is_done else "Log Set"
                            if st.button(btn_txt, key=f"log_set_{ex_id}_{s_idx}", type="secondary" if is_done else "primary", use_container_width=True, help="Completed set (tap to undo)" if is_done else "Log this set"):
                                if is_done:
                                    entry["completed"] = False
                                else:
                                    entry["completed"] = True
                                    check_set_prs(ex, s_idx, entry)
                                    start_rest_timer(ex_id, f"{ex['name']} · Set {s_idx}")
                                st.rerun()

            # Compact toolbar under exercise
            with st.container(key=f"wk_ex_toolbar_{ex_id}"):
                c_bt1, c_bt2, c_bt3, c_bt4 = st.columns([1.0, 1.0, 1.4, 1.6], gap="small")
                with c_bt1:
                    if st.button("＋ Set", key=f"add_set_btn_{ex_id}", use_container_width=True):
                        st.session_state.set_counts[ex_id] = count + 1
                        get_set_entry(ex_id, count + 1)
                        st.rerun()
                with c_bt2:
                    if count > 1 and st.button("− Del", key=f"del_set_btn_{ex_id}", use_container_width=True):
                        st.session_state.set_counts[ex_id] = count - 1
                        st.session_state.active_set_entries.pop((ex_id, count), None)
                        st.rerun()
                with c_bt3:
                    choice_key = f"rest_timer_choice_{ex_id}"
                    if st.session_state.get(choice_key) not in rest_choices:
                        st.session_state[choice_key] = "60 sec"
                    st.selectbox("Rest", rest_choices, index=rest_choices.index(st.session_state.get(choice_key, "60 sec")), key=choice_key, label_visibility="collapsed")
                with c_bt4:
                    st.button(
                        "Auto-Fill",
                        key=f"fill_sug_{ex_id}",
                        use_container_width=True,
                        help="Fill uncompleted sets with progressive overload recommendations",
                        on_click=auto_fill_sets_callback,
                        args=(ex_id, count, sug, ex_type, ex["name"]),
                    )

            st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

    # ── Extra Exercise Drawer ────────────────────────────────────────────────
    exercises = get_all_exercises(user_id)
    if exercises:
        existing_ids = {x["id"] for x in st.session_state.active_exercises}
        options = {f"{e['name']} · {tracking_label(e['exercise_type'])}": e for e in exercises if e["id"] not in existing_ids}
        if options:
            with st.expander("＋ Add another exercise to this session", expanded=False):
                selected = st.selectbox("Select exercise", ["—"] + list(options), label_visibility="collapsed")
                if st.button("Add to workout", key="btn_add_extra_ex", use_container_width=True) and selected != "—":
                    ex = options[selected]
                    st.session_state.active_exercises.append(ex)
                    st.session_state.set_counts[ex["id"]] = 3
                    st.session_state.open_exercises.add(ex["id"])
                    st.rerun()

    notes_key = f"workout_notes_{st.session_state.active_session_id}"
    workout_notes = st.text_area("Workout notes", key=notes_key, placeholder="Optional workout notes...", height=64)

    with st.container(key="wk_finish_bar"):
        c1, c2 = st.columns(2, gap="small")
        with c1:
            if st.button("Discard Workout", key="cancel_workout", use_container_width=True):
                delete_session(st.session_state.active_session_id, user_id)
                reset_workout_state()
                st.rerun()
        with c2:
            if st.button("Finish Workout", key="save_workout", type="primary", use_container_width=True):
                finish_active_workout(workout_notes)

    # ── Clean bottom clearance (ample space to scroll above fixed bottom nav) ──
    st.markdown('<div style="height: 140px; min-height: 140px; width: 100%;"></div>', unsafe_allow_html=True)


def routine_builder():
    st.markdown('<div class="wk-section-title" style="margin-bottom:12px;">New Routine</div>', unsafe_allow_html=True)
    exercises = get_all_exercises(user_id)
    if not exercises:
        st.markdown('<div class="wk-card wk-muted">Create at least one exercise first.</div>', unsafe_allow_html=True)
        if st.button("Create an exercise", key="builder_create_exercise", use_container_width=True):
            st.session_state.create_exercise_open = True
            st.session_state.workout_mode = None
            st.rerun()
        return

    with st.form("routine_form"):
        name = st.text_input("Routine name", placeholder="Push Day")
        labels = [f"{e['name']} · {e['muscle_group']}" for e in exercises]
        chosen = st.multiselect("Exercises", labels)
        save = st.form_submit_button("Save routine", use_container_width=True)
        if save:
            if not name.strip():
                st.error("Give the routine a name.")
            elif not chosen:
                st.error("Choose at least one exercise.")
            else:
                rid = create_routine(user_id, name)
                label_to_id = {f"{e['name']} · {e['muscle_group']}": e["id"] for e in exercises}
                for idx, label in enumerate(chosen):
                    add_exercise_to_routine(rid, label_to_id[label], idx)
                st.session_state.workout_mode = None
                st.success("Routine saved.")
                st.rerun()


def edit_routine_view(routine: dict):
    st.markdown('<div class="wk-section-title" style="margin:10px 0 12px;">Edit Routine</div>', unsafe_allow_html=True)
    exercises = get_all_exercises(user_id)
    current_routine_exs = get_routine_exercises(routine["id"])
    current_ids = {e["id"] for e in current_routine_exs}

    with st.form(f"edit_routine_form_{routine['id']}"):
        name = st.text_input("Routine name", value=routine.get("name", ""))
        labels = [f"{e['name']} · {e['muscle_group']}" for e in exercises]
        id_to_label = {e["id"]: f"{e['name']} · {e['muscle_group']}" for e in exercises}
        label_to_id = {f"{e['name']} · {e['muscle_group']}": e["id"] for e in exercises}

        default_chosen = [id_to_label[eid] for eid in current_ids if eid in id_to_label]
        chosen = st.multiselect("Exercises", labels, default=default_chosen)

        c1, c2 = st.columns(2, gap="small")
        with c1:
            save = st.form_submit_button("Save Routine", use_container_width=True)
        with c2:
            cancel = st.form_submit_button("Cancel", use_container_width=True)

        if cancel:
            st.session_state.editing_routine_id = None
            st.rerun()
        if save:
            selected_ids = [label_to_id[c] for c in chosen if c in label_to_id]
            res = update_routine(routine["id"], user_id, name, selected_ids)
            if res["success"]:
                st.session_state.editing_routine_id = None
                st.success("Routine updated.")
                st.rerun()
            st.error(res["error"])


def _session_date_value(value):
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)).date()
    except (TypeError, ValueError):
        return date.today()


def edit_previous_workout_view(session: dict):
    session_id = session["id"]
    c_ewhead1, c_ewhead2 = st.columns([3, 1], gap="small")
    with c_ewhead1:
        st.markdown('<div class="wk-section-title" style="margin:6px 0 8px;">Edit Workout</div>', unsafe_allow_html=True)
    with c_ewhead2:
        if st.button("← Done", key=f"done_edit_session_top_{session_id}", use_container_width=True):
            st.session_state.editing_session_id = None
            st.rerun()
    
    # ── Workout Meta Details (Date, Duration, Notes) ──────────────────────────
    with st.form(f"edit_session_form_{session_id}"):
        c_d1, c_d2 = st.columns(2, gap="small")
        with c_d1:
            session_date = st.date_input("Workout date", value=_session_date_value(session.get("date")))
        with c_d2:
            duration = st.number_input("Duration (seconds)", min_value=0, value=int(session.get("duration") or 0), step=60)
        notes = st.text_area("Notes", value=session.get("notes") or "", height=50)
        save_meta = st.form_submit_button("Save Workout Info", use_container_width=True)
        if save_meta:
            result = update_session(session_id, user_id, session_date.isoformat(), duration, notes)
            if result["success"]:
                st.success("Workout details updated.")
                st.rerun()
            st.error(result["error"])

    all_exercises = get_all_exercises(user_id)
    all_ex_map = {e["id"]: e for e in all_exercises}
    sets = get_sets_for_session(session_id)

    st.markdown('<div class="wk-section-title" style="font-size:17px; margin:22px 0 10px;">Exercises & Sets</div>', unsafe_allow_html=True)

    grouped_sets = {}
    for s in sets:
        grouped_sets.setdefault(s["exercise_id"], []).append(s)

    if not grouped_sets:
        st.markdown('<div class="wk-card wk-muted" style="margin-bottom:12px;">This workout currently has 0 exercises logged. Add an exercise below.</div>', unsafe_allow_html=True)

    # ── Render Each Exercise Group Inside Previous Workout ────────────────────
    for idx, (ex_id, ex_sets) in enumerate(grouped_sets.items()):
        ex_info = all_ex_map.get(ex_id, {
            "id": ex_id,
            "name": ex_sets[0]["exercise_name"],
            "exercise_type": ex_sets[0].get("exercise_type", "weights_reps"),
            "muscle_group": "",
        })
        ex_type = ex_info.get("exercise_type", "weights_reps")

        with st.expander(f"{ex_info['name']} ({len(ex_sets)} sets)", expanded=(idx == 0)):
            c_swap_sel, c_swap_btn, c_del_ex = st.columns([3, 1, 1], gap="small")
            with c_swap_sel:
                swap_options = {f"{e['name']} ({e['muscle_group']})": e["id"] for e in all_exercises if e["id"] != ex_id}
                chosen_swap = st.selectbox(
                    "Swap exercise to",
                    ["—"] + list(swap_options.keys()),
                    key=f"swap_ex_{session_id}_{ex_id}",
                    label_visibility="collapsed",
                )
            with c_swap_btn:
                if st.button("Swap", key=f"btn_swap_{session_id}_{ex_id}", use_container_width=True):
                    if chosen_swap != "—":
                        new_id = swap_options[chosen_swap]
                        change_session_exercise(session_id, ex_id, new_id, user_id)
                        st.success(f"Swapped to {all_ex_map[new_id]['name']}.")
                        st.rerun()
            with c_del_ex:
                if st.button("Remove", key=f"btn_del_ex_{session_id}_{ex_id}", use_container_width=True):
                    delete_session_exercise(session_id, ex_id, user_id)
                    st.success(f"Removed {ex_info['name']} and its sets.")
                    st.rerun()

            st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)

            # ── Individual Sets in this Exercise (Compact 2-line cards) ────────
            for set_row in ex_sets:
                set_id = set_row["id"]
                s_num = set_row["set_number"]
                cur_type = set_row.get("set_type", "working")
                type_display = "Warm-up Set" if cur_type == "warmup" else ("Drop Set" if cur_type == "dropset" else "Working Set")

                with st.form(f"form_hist_set_{set_id}"):
                    c_h1, c_h2 = st.columns([1, 2], gap="small")
                    with c_h1:
                        st.markdown(f'<div class="wk-set-tag" style="margin-top:4px;">Set #{s_num}</div>', unsafe_allow_html=True)
                    with c_h2:
                        chosen_cat = st.selectbox(
                            "Category",
                            SET_CATEGORIES,
                            index=SET_CATEGORIES.index(type_display),
                            key=f"hist_cat_{set_id}",
                            label_visibility="collapsed",
                        )

                    if ex_type == "time":
                        c_t, c_act = st.columns([2, 1], gap="small")
                        with c_t:
                            duration_seconds = st.number_input(
                                "Seconds",
                                min_value=0,
                                value=int(set_row.get("duration_seconds") or 0),
                                step=5,
                                key=f"hist_duration_{set_id}",
                                label_visibility="collapsed",
                            )
                        with c_act:
                            save_set = st.form_submit_button("Save", use_container_width=True)
                        reps = weight = rpe = None
                    elif ex_type == "bodyweight":
                        c1, c2, c_act = st.columns([1.2, 1.0, 1.2], gap="small")
                        with c1:
                            reps = st.number_input("Reps", min_value=0, value=int(set_row.get("reps") or 0), step=1, key=f"hist_reps_{set_id}", label_visibility="collapsed")
                        with c2:
                            rpe = st.number_input("RPE", min_value=0.0, max_value=10.0, value=float(set_row.get("rpe") or 0), step=0.5, key=f"hist_rpe_{set_id}", label_visibility="collapsed")
                        with c_act:
                            save_set = st.form_submit_button("Save", use_container_width=True)
                        weight = duration_seconds = None
                    else:
                        c1, c2, c3, c_act = st.columns([1.1, 1.0, 0.9, 1.1], gap="small")
                        with c1:
                            weight = st.number_input("kg", min_value=0.0, value=float(set_row.get("weight") or 0), step=0.5, key=f"hist_weight_{set_id}", label_visibility="collapsed")
                        with c2:
                            reps = st.number_input("reps", min_value=0, value=int(set_row.get("reps") or 0), step=1, key=f"hist_reps_{set_id}", label_visibility="collapsed")
                        with c3:
                            rpe = st.number_input("RPE", min_value=0.0, max_value=10.0, value=float(set_row.get("rpe") or 0), step=0.5, key=f"hist_rpe_{set_id}", label_visibility="collapsed")
                        with c_act:
                            save_set = st.form_submit_button("Save", use_container_width=True)
                        duration_seconds = None

                    if save_set:
                        mapped_type = "warmup" if chosen_cat == "Warm-up Set" else ("dropset" if chosen_cat == "Drop Set" else "working")
                        result = update_set(
                            set_id,
                            user_id,
                            reps=reps,
                            weight=weight,
                            rpe=rpe,
                            duration_seconds=duration_seconds,
                            set_type=mapped_type,
                        )
                        if result["success"]:
                            st.success(f"Set #{s_num} updated.")
                            st.rerun()
                        st.error(result["error"])

                c_del_col, _ = st.columns([1.2, 2.8], gap="small")
                with c_del_col:
                    if st.button(f"Delete #{s_num}", key=f"remove_hist_set_{set_id}", use_container_width=True):
                        result = delete_set(set_id, user_id)
                        if result["success"]:
                            st.rerun()
                        st.error(result["error"])

            if st.button(f"＋ Add Set to {ex_info['name']}", key=f"add_set_to_{session_id}_{ex_id}", use_container_width=True):
                next_set_num = len(ex_sets) + 1
                log_set(
                    session_id,
                    ex_id,
                    next_set_num,
                    reps=10 if ex_type != "time" else None,
                    weight=0.0 if ex_type in ("weights_reps", "weighted_calisthenics") else None,
                    duration_seconds=60 if ex_type == "time" else None,
                    set_type="working",
                )
                st.rerun()

    # ── Add New Exercise to Workout ──────────────────────────────────────────
    st.markdown('<div class="wk-section-title" style="font-size:15px; margin:20px 0 8px;">Add Exercise to this Workout</div>', unsafe_allow_html=True)
    add_col1, add_col2 = st.columns([3, 1], gap="small")
    with add_col1:
        add_options = {f"{e['name']} · {e['muscle_group']}": e for e in all_exercises}
        chosen_add = st.selectbox("Choose exercise to add", ["—"] + list(add_options.keys()), key=f"add_ex_sel_{session_id}")
    with add_col2:
        if st.button("＋ Add", key=f"btn_add_ex_to_session_{session_id}", use_container_width=True):
            if chosen_add != "—":
                new_ex = add_options[chosen_add]
                log_set(
                    session_id,
                    new_ex["id"],
                    1,
                    reps=10 if new_ex["exercise_type"] != "time" else None,
                    weight=0.0 if new_ex["exercise_type"] in ("weights_reps", "weighted_calisthenics") else None,
                    duration_seconds=60 if new_ex["exercise_type"] == "time" else None,
                    set_type="working",
                )
                st.success(f"Added {new_ex['name']} to workout.")
                st.rerun()

    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
    if st.button("Done editing workout", key=f"done_edit_session_{session_id}", type="primary", use_container_width=True):
        st.session_state.editing_session_id = None
        st.rerun()


def manage_view():
    c_mhead1, c_mhead2 = st.columns([3, 1], gap="small")
    with c_mhead1:
        st.markdown('<div class="wk-section-title" style="margin-bottom:0;">Manage</div>', unsafe_allow_html=True)
    with c_mhead2:
        st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
        if st.button("← Back", key="manage_back_top", use_container_width=True):
            st.session_state.workout_mode = None
            st.session_state.editing_routine_id = None
            st.session_state.editing_session_id = None
            st.rerun()

    routines = get_routines(user_id)
    exercises = get_all_exercises(user_id)
    sessions = get_sessions(user_id)

    tab_labels = ["Routines", "Workouts", "Exercises"]
    default_tab = "Routines"
    if st.session_state.get("editing_session_id") is not None:
        default_tab = "Workouts"
    elif st.session_state.get("editing_routine_id") is not None:
        default_tab = "Routines"

    tab_routines, tab_workouts, tab_exercises = st.tabs(tab_labels, default=default_tab)

    with tab_routines:
        editing_routine_id = st.session_state.get("editing_routine_id")
        if editing_routine_id is not None:
            selected_routine = next((r for r in routines if r["id"] == editing_routine_id), None)
            if selected_routine:
                edit_routine_view(selected_routine)
            else:
                st.session_state.editing_routine_id = None
                st.rerun()
        else:
            st.markdown('<div class="wk-small" style="margin:10px 0 8px;">My routines</div>', unsafe_allow_html=True)
            if not routines:
                st.caption("No routines created yet.")
            for r in routines:
                with st.container(key=f"manage_r_{r['id']}"):
                    st.markdown(f'<div class="wk-manage-item-title"><b>{r["name"]}</b></div>', unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3, gap="small")
                    with c1:
                        if st.button("Edit", key=f"edit_r_{r['id']}", use_container_width=True):
                            st.session_state.editing_routine_id = r["id"]
                            st.rerun()
                    with c2:
                        if st.button("Duplicate", key=f"dup_r_{r['id']}", use_container_width=True):
                            duplicate_routine(r["id"], user_id)
                            st.rerun()
                    with c3:
                        if st.button("Delete", key=f"del_r_{r['id']}", use_container_width=True):
                            delete_routine(r["id"], user_id)
                            if st.session_state.get("editing_routine_id") == r["id"]:
                                st.session_state.editing_routine_id = None
                            st.rerun()

    with tab_workouts:
        editing_session_id = st.session_state.get("editing_session_id")
        if editing_session_id is not None:
            selected_session = next((s for s in sessions if s["id"] == editing_session_id), None)
            if selected_session:
                edit_previous_workout_view(selected_session)
            else:
                st.session_state.editing_session_id = None
                st.rerun()
        else:
            st.markdown('<div class="wk-small" style="margin:10px 0 8px;">Previous workouts</div>', unsafe_allow_html=True)
            if not sessions:
                st.caption("No completed workouts yet.")
            else:
                SESSIONS_PREVIEW_LIMIT = 5
                is_sessions_expanded = st.session_state.get("expanded_section") == "sessions"
                visible_sessions = sessions if is_sessions_expanded else sessions[:SESSIONS_PREVIEW_LIMIT]

                for session in visible_sessions:
                    session_id = session["id"]
                    name = session.get("routine_name") or "Empty Workout"
                    session_date = str(session.get("date") or "")
                    duration = int(session.get("duration") or 0)
                    sets = get_sets_for_session(session_id)
                    exercise_count = len({row["exercise_id"] for row in sets}) if sets else 0
                    with st.container(key=f"manage_sess_{session_id}"):
                        st.markdown(
                            f'<div class="wk-manage-item-title"><b>{name}</b></div><div class="wk-small" style="margin-bottom:6px;">{session_date} · {duration // 60}m · {exercise_count} exercise{"s" if exercise_count != 1 else ""}</div>',
                            unsafe_allow_html=True,
                        )
                        c1, c2 = st.columns(2, gap="small")
                        with c1:
                            if st.button("Edit", key=f"edit_session_{session_id}", use_container_width=True):
                                st.session_state.editing_session_id = session_id
                                st.session_state.pending_delete_session_id = None
                                st.rerun()
                        with c2:
                            if st.session_state.get("pending_delete_session_id") == session_id:
                                if st.button("Confirm delete", key=f"confirm_delete_session_{session_id}", use_container_width=True):
                                    result = delete_session(session_id, user_id)
                                    if result:
                                        st.session_state.pending_delete_session_id = None
                                        if st.session_state.get("editing_session_id") == session_id:
                                            st.session_state.editing_session_id = None
                                        st.rerun()
                                    st.error("Could not delete workout.")
                            elif st.button("Remove", key=f"remove_session_{session_id}", use_container_width=True):
                                st.session_state.pending_delete_session_id = session_id
                                st.rerun()

                        if st.session_state.get("pending_delete_session_id") == session_id:
                            st.warning("Delete this workout and all of its logged sets?")
                            if st.button("Cancel", key=f"cancel_delete_session_{session_id}", use_container_width=True):
                                st.session_state.pending_delete_session_id = None
                                st.rerun()

                if len(sessions) > SESSIONS_PREVIEW_LIMIT:
                    if not is_sessions_expanded:
                        st.markdown('<div class="wk-fade-mask"></div>', unsafe_allow_html=True)
                        remaining = len(sessions) - SESSIONS_PREVIEW_LIMIT
                        if st.button(f"View more workouts ({remaining} more) ↓", key="view_more_sessions", use_container_width=True):
                            st.session_state.expanded_section = "sessions"
                            st.rerun()
                    else:
                        if st.button("View less workouts ↑", key="view_more_sessions", use_container_width=True):
                            st.session_state.expanded_section = None
                            st.rerun()

    with tab_exercises:
        st.markdown('<div class="wk-small" style="margin:10px 0 8px;">Exercise library</div>', unsafe_allow_html=True)
        if not exercises:
            st.caption("No exercises found.")
        for e in exercises:
            is_builtin = e.get("user_id") is None
            badge = ' <span class="htn-badge" style="font-size:10px;padding:2px 8px;margin-left:6px;">Built-in</span>' if is_builtin else ''
            with st.container(key=f"manage_ex_{e['id']}"):
                c1, c2 = st.columns([4, 1.2], gap="small")
                with c1:
                    st.markdown(
                        f'<div class="wk-manage-ex-info"><b>{e["name"]}</b>{badge}<div class="wk-small">{e["muscle_group"]} · {tracking_label(e["exercise_type"])}</div></div>',
                        unsafe_allow_html=True,
                    )
                with c2:
                    if st.button("Remove", key=f"del_e_{e['id']}", use_container_width=True):
                        result = delete_exercise(e["id"], user_id)
                        if not result["success"]:
                            st.warning(result["error"])
                        else:
                            st.rerun()


# -----------------------------------------------------------------------------
# 5-Week Periodization Mesocycle Module
# -----------------------------------------------------------------------------
PERIODIZATION_MESOCYCLE = {
    1: {
        "phase": "Hypertrophy",
        "badge": "2x8-10 · RPE 9-10",
        "objective": "High-volume hypertrophy foundation & structural adaptation",
        "days": {
            1: [
                {"name": "Pull-ups", "target": "2x8-10 (RPE 9-10)", "muscle": "Back", "type": "bodyweight", "equip": "Pull-up Bar", "sets": 2, "role": "focus"},
                {"name": "Lat Pullover", "target": "2x8-10", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"},
                {"name": "Dumbbell Bicep Curl", "target": "2x8-10", "muscle": "Biceps", "type": "weights_reps", "equip": "Dumbbell", "sets": 2, "role": "support"},
                {"name": "Rear Delt Fly", "target": "2x8-10", "muscle": "Shoulders", "type": "weights_reps", "equip": "Dumbbell", "sets": 2, "role": "support"},
                {"name": "Bench Press (Bottom Half)", "target": "2x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"},
                {"name": "Leg Extension", "target": "2x10-15", "muscle": "Quads", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "auxiliary"},
            ],
            2: [
                {"name": "Bench Press", "target": "2x8-10 (RPE 9-10)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"},
                {"name": "Machine Chest Press", "target": "2x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "support"},
                {"name": "Overhead Extension", "target": "2x8-10", "muscle": "Triceps", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"},
                {"name": "Zercher Squats (Bottom Half)", "target": "2x8-10", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"},
                {"name": "Leg Curl", "target": "2x10-15", "muscle": "Hamstrings", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "auxiliary"},
            ],
            3: [
                {"name": "Zercher Squats", "target": "2x8-10 (RPE 9-10)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"},
                {"name": "Leg Extension", "target": "2x8-10", "muscle": "Quads", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "support"},
                {"name": "Leg Curl", "target": "2x8-10", "muscle": "Hamstrings", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "support"},
                {"name": "Pull-ups (Top Half)", "target": "2x8-10", "muscle": "Back", "type": "bodyweight", "equip": "Pull-up Bar", "sets": 2, "role": "auxiliary"},
                {"name": "Lat Pullover", "target": "2x10-15", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "auxiliary"},
            ],
            4: [
                {"name": "Pull-ups", "target": "2x8-10 (RPE 9-10)", "muscle": "Back", "type": "bodyweight", "equip": "Pull-up Bar", "sets": 2, "role": "focus"},
                {"name": "Machine Chest Press", "target": "2x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "auxiliary"},
                {"name": "Rear Delt Fly", "target": "2x10-15", "muscle": "Shoulders", "type": "weights_reps", "equip": "Dumbbell", "sets": 2, "role": "support"},
                {"name": "Lat Pullover", "target": "2x8-10", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"},
                {"name": "Dumbbell Bicep Curl", "target": "2x8-10", "muscle": "Biceps", "type": "weights_reps", "equip": "Dumbbell", "sets": 2, "role": "support"},
            ],
            5: [
                {"name": "Bench Press", "target": "2x8-10 (RPE 9-10)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"},
                {"name": "Zercher Squats (Bottom Half)", "target": "2x8-10", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"},
                {"name": "Dumbbell Bicep Curl", "target": "2x10-15", "muscle": "Biceps", "type": "weights_reps", "equip": "Dumbbell", "sets": 2, "role": "auxiliary"},
                {"name": "Machine Chest Press", "target": "2x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "support"},
                {"name": "Overhead Extension", "target": "2x8-10", "muscle": "Triceps", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"},
            ],
        },
    },
    2: {
        "phase": "Singles",
        "badge": "4x1 (RPE 8-9) · Paused 2x5 (RPE 8)",
        "objective": "Maximal neural recruitment with paused technical mastery",
        "days": {
            1: [
                {"name": "Pull-ups", "target": "4x1 (RPE 8-9)", "muscle": "Back", "type": "bodyweight", "equip": "Pull-up Bar", "sets": 4, "role": "focus"},
                {"name": "Lat Pullover", "target": "1x8-10", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"},
                {"name": "Dumbbell Bicep Curl", "target": "1x8-10", "muscle": "Biceps", "type": "weights_reps", "equip": "Dumbbell", "sets": 1, "role": "support"},
                {"name": "Rear Delt Fly", "target": "1x8-10", "muscle": "Shoulders", "type": "weights_reps", "equip": "Dumbbell", "sets": 1, "role": "support"},
                {"name": "Paused Bench Press", "target": "2x5 (RPE 8)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"},
                {"name": "Leg Extension", "target": "1x10-15", "muscle": "Quads", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "auxiliary"},
            ],
            2: [
                {"name": "Bench Press", "target": "4x1 (RPE 8-9)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 4, "role": "focus"},
                {"name": "Machine Chest Press", "target": "1x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"},
                {"name": "Overhead Extension", "target": "1x8-10", "muscle": "Triceps", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"},
                {"name": "Paused Zercher Squats", "target": "2x5 (RPE 8)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"},
                {"name": "Leg Curl", "target": "1x10-15", "muscle": "Hamstrings", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "auxiliary"},
            ],
            3: [
                {"name": "Zercher Squats", "target": "4x1 (RPE 8-9)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 4, "role": "focus"},
                {"name": "Leg Extension", "target": "1x8-10", "muscle": "Quads", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"},
                {"name": "Leg Curl", "target": "1x8-10", "muscle": "Hamstrings", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"},
                {"name": "Paused Pull-ups (Top Half)", "target": "2x5 (RPE 8)", "muscle": "Back", "type": "bodyweight", "equip": "Pull-up Bar", "sets": 2, "role": "auxiliary"},
                {"name": "Lat Pullover", "target": "1x10-15", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "auxiliary"},
            ],
            4: [
                {"name": "Pull-ups", "target": "4x1 (RPE 8-9)", "muscle": "Back", "type": "bodyweight", "equip": "Pull-up Bar", "sets": 4, "role": "focus"},
                {"name": "Machine Chest Press", "target": "2x8-10 (RPE 8)", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "auxiliary"},
                {"name": "Rear Delt Fly", "target": "1x10-15", "muscle": "Shoulders", "type": "weights_reps", "equip": "Dumbbell", "sets": 1, "role": "support"},
                {"name": "Lat Pullover", "target": "1x8-10", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"},
                {"name": "Dumbbell Bicep Curl", "target": "1x8-10", "muscle": "Biceps", "type": "weights_reps", "equip": "Dumbbell", "sets": 1, "role": "support"},
            ],
            5: [
                {"name": "Bench Press", "target": "4x1 (RPE 8-9)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 4, "role": "focus"},
                {"name": "Paused Zercher Squats", "target": "2x5 (RPE 8)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"},
                {"name": "Dumbbell Bicep Curl", "target": "1x10-15", "muscle": "Biceps", "type": "weights_reps", "equip": "Dumbbell", "sets": 1, "role": "auxiliary"},
                {"name": "Machine Chest Press", "target": "1x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"},
                {"name": "Overhead Extension", "target": "1x8-10", "muscle": "Triceps", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"},
            ],
        },
    },
    3: {
        "phase": "Conditioning",
        "badge": "2x5 [Slow Eccentrics] · RPE 8",
        "objective": "Eccentric control & mechanical tension under strict tempo",
        "days": {
            1: [
                {"name": "Pull-ups", "target": "2x5 [Slow Eccentrics] (RPE 8)", "muscle": "Back", "type": "bodyweight", "equip": "Pull-up Bar", "sets": 2, "role": "focus"},
                {"name": "Paused Bench Press", "target": "2x5 (RPE 8)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"},
                {"name": "Leg Extension", "target": "2x10-15", "muscle": "Quads", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "auxiliary"},
                {"name": "Lat Pullover", "target": "2x8-10", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"},
                {"name": "Dumbbell Bicep Curl", "target": "2x8-10", "muscle": "Biceps", "type": "weights_reps", "equip": "Dumbbell", "sets": 2, "role": "support"},
                {"name": "Rear Delt Fly", "target": "2x8-10", "muscle": "Shoulders", "type": "weights_reps", "equip": "Dumbbell", "sets": 2, "role": "support"},
            ],
            2: [
                {"name": "Bench Press", "target": "2x5 [Slow Eccentrics] (RPE 8)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"},
                {"name": "Paused Zercher Squats", "target": "2x5 (RPE 8)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"},
                {"name": "Leg Curl", "target": "2x10-15", "muscle": "Hamstrings", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "auxiliary"},
                {"name": "Machine Chest Press", "target": "2x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "support"},
                {"name": "Overhead Extension", "target": "2x8-10", "muscle": "Triceps", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"},
            ],
            3: [
                {"name": "Zercher Squats", "target": "2x5 [Slow Eccentrics] (RPE 8)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"},
                {"name": "Paused Pull-ups (Top Half)", "target": "2x5 (RPE 8)", "muscle": "Back", "type": "bodyweight", "equip": "Pull-up Bar", "sets": 2, "role": "auxiliary"},
                {"name": "Lat Pullover", "target": "2x10-15", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "auxiliary"},
                {"name": "Leg Extension", "target": "2x8-10", "muscle": "Quads", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "support"},
                {"name": "Leg Curl", "target": "2x8-10", "muscle": "Hamstrings", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "support"},
            ],
            4: [
                {"name": "Pull-ups", "target": "2x5 [Slow Eccentrics] (RPE 8)", "muscle": "Back", "type": "bodyweight", "equip": "Pull-up Bar", "sets": 2, "role": "focus"},
                {"name": "Machine Chest Press", "target": "2x8-10 (RPE 8)", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "auxiliary"},
                {"name": "Rear Delt Fly", "target": "2x10-15", "muscle": "Shoulders", "type": "weights_reps", "equip": "Dumbbell", "sets": 2, "role": "support"},
                {"name": "Lat Pullover", "target": "2x8-10", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"},
                {"name": "Dumbbell Bicep Curl", "target": "2x8-10", "muscle": "Biceps", "type": "weights_reps", "equip": "Dumbbell", "sets": 2, "role": "support"},
            ],
            5: [
                {"name": "Bench Press", "target": "2x5 [Slow Eccentrics] (RPE 8)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"},
                {"name": "Paused Zercher Squats", "target": "2x5 (RPE 8)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"},
                {"name": "Dumbbell Bicep Curl", "target": "2x10-15", "muscle": "Biceps", "type": "weights_reps", "equip": "Dumbbell", "sets": 2, "role": "auxiliary"},
                {"name": "Machine Chest Press", "target": "2x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "support"},
                {"name": "Overhead Extension", "target": "2x8-10", "muscle": "Triceps", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"},
            ],
        },
    },
    4: {
        "phase": "Strength",
        "badge": "2x3 (RPE 9-10) · Paused 2x3 (RPE 8)",
        "objective": "Heavy intensity work pushing near-maximal neuromuscular limits",
        "days": {
            1: [
                {"name": "Pull-ups", "target": "2x3 (RPE 9-10)", "muscle": "Back", "type": "bodyweight", "equip": "Pull-up Bar", "sets": 2, "role": "focus"},
                {"name": "Paused Bench Press", "target": "2x3 (RPE 8)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"},
                {"name": "Leg Extension", "target": "1x10-15", "muscle": "Quads", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "auxiliary"},
                {"name": "Lat Pullover", "target": "1x8-10", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"},
                {"name": "Dumbbell Bicep Curl", "target": "1x8-10", "muscle": "Biceps", "type": "weights_reps", "equip": "Dumbbell", "sets": 1, "role": "support"},
                {"name": "Rear Delt Fly", "target": "1x8-10", "muscle": "Shoulders", "type": "weights_reps", "equip": "Dumbbell", "sets": 1, "role": "support"},
            ],
            2: [
                {"name": "Bench Press", "target": "2x3 (RPE 9-10)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"},
                {"name": "Paused Zercher Squats", "target": "2x3 (RPE 8)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"},
                {"name": "Leg Curl", "target": "1x10-15", "muscle": "Hamstrings", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "auxiliary"},
                {"name": "Machine Chest Press", "target": "1x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"},
                {"name": "Overhead Extension", "target": "1x8-10", "muscle": "Triceps", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"},
            ],
            3: [
                {"name": "Zercher Squats", "target": "2x3 (RPE 9-10)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"},
                {"name": "Paused Pull-ups (Top Half)", "target": "2x3 (RPE 8)", "muscle": "Back", "type": "bodyweight", "equip": "Pull-up Bar", "sets": 2, "role": "auxiliary"},
                {"name": "Lat Pullover", "target": "1x10-15", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "auxiliary"},
                {"name": "Leg Extension", "target": "1x8-10", "muscle": "Quads", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"},
                {"name": "Leg Curl", "target": "1x8-10", "muscle": "Hamstrings", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"},
            ],
            4: [
                {"name": "Pull-ups", "target": "2x3 (RPE 9-10)", "muscle": "Back", "type": "bodyweight", "equip": "Pull-up Bar", "sets": 2, "role": "focus"},
                {"name": "Machine Chest Press", "target": "1-2x8-10 (RPE 8)", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "auxiliary"},
                {"name": "Rear Delt Fly", "target": "1x10-15", "muscle": "Shoulders", "type": "weights_reps", "equip": "Dumbbell", "sets": 1, "role": "support"},
                {"name": "Lat Pullover", "target": "1x8-10", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"},
                {"name": "Dumbbell Bicep Curl", "target": "1x8-10", "muscle": "Biceps", "type": "weights_reps", "equip": "Dumbbell", "sets": 1, "role": "support"},
            ],
            5: [
                {"name": "Bench Press", "target": "2x3 (RPE 9-10)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"},
                {"name": "Paused Zercher Squats", "target": "2x3 (RPE 8)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"},
                {"name": "Dumbbell Bicep Curl", "target": "1x10-15", "muscle": "Biceps", "type": "weights_reps", "equip": "Dumbbell", "sets": 1, "role": "auxiliary"},
                {"name": "Machine Chest Press", "target": "1x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"},
                {"name": "Overhead Extension", "target": "1x8-10", "muscle": "Triceps", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"},
            ],
        },
    },
    5: {
        "phase": "Deload",
        "badge": "2x6 (RPE 7) · Active Recovery",
        "objective": "Active CNS dissipation, joint recovery & technique priming",
        "days": {
            1: [
                {"name": "Pull-ups", "target": "2x6 (RPE 7)", "muscle": "Back", "type": "bodyweight", "equip": "Pull-up Bar", "sets": 2, "role": "focus"},
                {"name": "Bench Press", "target": "2x6 (RPE 7)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"},
                {"name": "Leg Extension", "target": "1x10-15", "muscle": "Quads", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "auxiliary"},
                {"name": "Lat Pullover", "target": "1x10-15", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"},
                {"name": "Dumbbell Bicep Curl", "target": "1x10-15", "muscle": "Biceps", "type": "weights_reps", "equip": "Dumbbell", "sets": 1, "role": "support"},
                {"name": "Rear Delt Fly", "target": "1x10-15", "muscle": "Shoulders", "type": "weights_reps", "equip": "Dumbbell", "sets": 1, "role": "support"},
            ],
            2: [
                {"name": "Bench Press", "target": "2x6 (RPE 7)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"},
                {"name": "Zercher Squats", "target": "2x6 (RPE 7)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"},
                {"name": "Leg Curl", "target": "1x10-15", "muscle": "Hamstrings", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "auxiliary"},
                {"name": "Machine Chest Press", "target": "1x10-15", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"},
                {"name": "Overhead Extension", "target": "1x10-15", "muscle": "Triceps", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"},
            ],
            3: [
                {"name": "Zercher Squats", "target": "2x6 (RPE 7)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"},
                {"name": "Pull-ups", "target": "2x6 (RPE 7)", "muscle": "Back", "type": "bodyweight", "equip": "Pull-up Bar", "sets": 2, "role": "auxiliary"},
                {"name": "Lat Pullover", "target": "1x10-15", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "auxiliary"},
                {"name": "Leg Extension", "target": "1x10-15", "muscle": "Quads", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"},
                {"name": "Leg Curl", "target": "1x10-15", "muscle": "Hamstrings", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"},
            ],
            4: [
                {"name": "Pull-ups", "target": "2x6 (RPE 7)", "muscle": "Back", "type": "bodyweight", "equip": "Pull-up Bar", "sets": 2, "role": "focus"},
                {"name": "Machine Chest Press", "target": "2x10 (RPE 7)", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "auxiliary"},
                {"name": "Rear Delt Fly", "target": "1x10-15", "muscle": "Shoulders", "type": "weights_reps", "equip": "Dumbbell", "sets": 1, "role": "support"},
                {"name": "Lat Pullover", "target": "1x10-15", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"},
                {"name": "Dumbbell Bicep Curl", "target": "1x10-15", "muscle": "Biceps", "type": "weights_reps", "equip": "Dumbbell", "sets": 1, "role": "support"},
            ],
            5: [
                {"name": "Bench Press", "target": "2x6 (RPE 7)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"},
                {"name": "Zercher Squats", "target": "2x6 (RPE 7)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"},
                {"name": "Dumbbell Bicep Curl", "target": "1x10-15", "muscle": "Biceps", "type": "weights_reps", "equip": "Dumbbell", "sets": 1, "role": "auxiliary"},
                {"name": "Machine Chest Press", "target": "1x10-15", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"},
                {"name": "Overhead Extension", "target": "1x10-15", "muscle": "Triceps", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"},
            ],
        },
    },
}


def _get_or_create_periodization_exercise(uid: int, name: str, muscle: str, ex_type: str, equip: str = "") -> dict:
    all_ex = get_all_exercises(uid)
    clean_n = name.strip()
    for e in all_ex:
        if e["name"].strip().lower() == clean_n.lower():
            return e
    res = create_exercise(uid, clean_n, muscle, ex_type, equip)
    if res.get("success") and res.get("exercise_id"):
        for e in get_all_exercises(uid):
            if e["id"] == res["exercise_id"]:
                return e
    return all_ex[0] if all_ex else {"id": 1, "name": clean_n, "muscle_group": muscle, "exercise_type": ex_type}


def start_periodized_session(week_num: int, day_num: int, program_id: Optional[int] = None):
    prog_map = get_builtin_periodization_program(program_id)
    if not prog_map or week_num not in prog_map or day_num not in prog_map[week_num].get("days", {}):
        prog_map = PERIODIZATION_MESOCYCLE

    day_data = prog_map[week_num]["days"][day_num]
    phase_title = prog_map[week_num]["phase"]

    loaded_exercises = []
    set_counts = {}
    ex_prescriptions = {}
    for item in day_data:
        ex = _get_or_create_periodization_exercise(
            user_id, item["name"], item["muscle"], item["type"], item.get("equip", "")
        )
        if ex:
            loaded_exercises.append(ex)
            set_counts[ex["id"]] = item.get("sets", 2)
            ex_prescriptions[ex["id"]] = item

    prog_meta = get_periodization_program_metadata(program_id) or {}
    prog_name = prog_meta.get("name", "Mesocycle")
    prog_kg = prog_meta.get("weight_progression_kg", 2.5) or 2.5
    prog_reps = prog_meta.get("reps_progression", 1) or 1

    session_id = start_session(user_id, None)
    st.session_state.workout_mode = "active"
    st.session_state.active_session_id = session_id
    st.session_state.workout_timer_running = False
    st.session_state.workout_elapsed_seconds = 0
    st.session_state.workout_timer_start_time = None
    st.session_state.active_exercises = loaded_exercises
    st.session_state.set_counts = set_counts
    st.session_state.active_set_entries = {}
    st.session_state.open_exercises = {loaded_exercises[0]["id"]} if loaded_exercises else set()
    st.session_state.active_workout_source = "periodization"
    st.session_state.active_periodization_program_id = program_id
    st.session_state.active_periodization_week = week_num
    st.session_state.active_periodization_day = day_num
    st.session_state.active_periodization_phase = phase_title
    st.session_state.active_periodization_cycle_name = prog_name
    st.session_state.active_periodization_prog_kg = float(prog_kg)
    st.session_state.active_periodization_prog_reps = int(prog_reps)
    st.session_state.active_exercise_prescriptions = ex_prescriptions
    reset_rest_timer()
    st.rerun()


def _render_periodization_master_grid_html(prog_map: dict = None) -> str:
    if not prog_map:
        prog_map = get_builtin_periodization_program(1)
    if not prog_map:
        prog_map = PERIODIZATION_MESOCYCLE

    weeks_keys = sorted([w for w in prog_map.keys() if isinstance(w, int)])
    if not weeks_keys:
        return "<div style='padding:12px;color:#8f938f;'>No periodization weeks configured.</div>"

    max_days = 0
    for w in weeks_keys:
        d_cnt = len(prog_map[w].get("days", {}))
        if d_cnt > max_days:
            max_days = d_cnt
    max_days = max(1, max_days)

    day_headers = "".join([f'<th style="padding:11px 12px;font-weight:800;color:#f5f5f5;border-right:1px solid rgba(255,255,255,0.08);">Day {d}</th>' for d in range(1, max_days + 1)])

    table_rows = []
    for w in weeks_keys:
        w_data = prog_map.get(w, {})
        phase_title = w_data.get("phase", f"Week {w}")
        badge_val = w_data.get("badge", "")
        row_bg = "rgba(18,20,18,0.75)" if w % 2 == 1 else "rgba(14,16,14,0.75)"
        cells = [
            f'<td style="padding:10px 12px;white-space:nowrap;border-right:1px solid rgba(255,255,255,0.08);">'
            f'<div style="font-weight:800;color:var(--accent);font-size:12px;">Week {w}</div>'
            f'<div style="font-size:11px;color:#f5f5f5;font-weight:700;">{phase_title}</div>'
            f'<div style="font-size:10px;color:#8f938f;margin-top:2px;">{badge_val}</div>'
            f'</td>'
        ]
        days_dict = w_data.get("days", {})
        for d in range(1, max_days + 1):
            items = days_dict.get(d, [])
            cell_items = []
            for it in items:
                role = it.get("role", "auxiliary")
                color = "var(--accent)" if role == "focus" else ("#fbbf24" if role == "support" else "#7dd3fc")
                role_label = " [Focus]" if role == "focus" else (" [Support]" if role == "support" else "")
                cell_items.append(
                    f'<div style="margin-bottom:4px;line-height:1.25;">'
                    f'<span style="color:{color};font-weight:700;">{it["name"]}</span>'
                    f'<span style="color:#8f938f;font-size:10px;"> ({it["target"]}){role_label}</span>'
                    f'</div>'
                )
            border_r = "border-right:1px solid rgba(255,255,255,0.08);" if d < max_days else ""
            cells.append(
                f'<td style="padding:9px 11px;{border_r}min-width:145px;">'
                f'{"".join(cell_items) if cell_items else "<span style=\'color:#666;font-size:11px;\'>Rest</span>"}'
                f'</td>'
            )
        table_rows.append(
            f'<tr style="background:{row_bg};border-bottom:1px solid rgba(255,255,255,0.06);vertical-align:top;">'
            f'{"".join(cells)}'
            f'</tr>'
        )

    html = (
        '<div style="overflow-x:auto;margin:12px 0 8px;border-radius:14px;border:1px solid rgba(255,255,255,0.08);background:rgba(12,14,12,0.92);box-shadow:0 8px 24px rgba(0,0,0,0.5);">'
        '<table style="width:100%;border-collapse:collapse;font-size:11.5px;color:#f5f5f5;text-align:left;font-family:Inter,sans-serif;">'
        '<thead>'
        '<tr style="background:var(--accent-dim);border-bottom:1px solid var(--accent-glow);">'
        f'<th style="padding:11px 12px;font-weight:800;color:var(--accent);white-space:nowrap;border-right:1px solid rgba(255,255,255,0.08);">Phase / Week</th>'
        f'{day_headers}'
        '</tr>'
        '</thead>'
        '<tbody>'
        f'{"".join(table_rows)}'
        '</tbody>'
        '</table>'
        '</div>'
    )
    return html


def render_periodization_section(uid: int, in_expander: bool = False):
    st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)

    post_notice = st.session_state.get("post_workout_periodization_notice")
    if post_notice:
        st.markdown(
            clean_html(f"""
            <div style="background:linear-gradient(135deg, var(--accent-dim), var(--card));border:1px solid var(--accent-glow);border-radius:12px;padding:12px 16px;margin:8px 0 12px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <div>
                    <div style="font-size:13.5px;font-weight:800;color:var(--text);">
                        Session Logged: Week {post_notice['week']} Day {post_notice['day']}
                    </div>
                    <div style="font-size:12px;color:var(--text-dim);margin-top:2px;">
                        Progressive Overload Target for next cycle wave: Increase compound lifts by <b>+{post_notice['prog_kg']} kg</b> and accessories by <b>+{post_notice['prog_reps']} reps</b>.
                    </div>
                </div>
                <div class="htn-overload-badge">Overload Target Active</div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("Dismiss Notice", key="btn_dismiss_period_notice"):
            st.session_state.post_workout_periodization_notice = None
            st.rerun()

    all_programs = get_all_periodization_programs()
    if not all_programs:
        init_db()
        all_programs = get_all_periodization_programs()

    prog_id_options = [p["id"] for p in all_programs]
    prog_names_map = {p["id"]: p["name"] for p in all_programs}

    if "selected_periodization_program_id" not in st.session_state or st.session_state.selected_periodization_program_id not in prog_names_map:
        st.session_state.selected_periodization_program_id = prog_id_options[0] if prog_id_options else 1
    if "active_periodization_cycle_selector" in st.session_state and st.session_state.active_periodization_cycle_selector not in prog_names_map:
        del st.session_state["active_periodization_cycle_selector"]

    cur_prog_id = st.session_state.selected_periodization_program_id
    prog_meta = get_periodization_program_metadata(cur_prog_id) or {"name": "Periodization Mesocycle", "description": ""}

    if in_expander:
        ctx_manager = st.expander(f"PERIODIZATION MESOCYCLE — {prog_meta['name'].upper()}", expanded=True)
    else:
        ctx_manager = nullcontext()

    with ctx_manager:
        st.markdown(
            clean_html(f"""
            <div class="htn-meso-container">
                <div class="htn-meso-header">
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div style="width:42px;height:42px;border-radius:12px;background:var(--accent-dim);border:1px solid var(--accent);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:900;color:var(--accent);box-shadow:0 0 16px var(--accent-glow);letter-spacing:0.5px;">
                            MESO
                        </div>
                        <div>
                            <div style="font-size:17px;font-weight:800;color:var(--text);letter-spacing:-0.3px;">
                                {prog_meta['name']}
                            </div>
                            <div style="font-size:12px;color:var(--text-dim);margin-top:2px;">
                                {prog_meta.get('description') or 'Multi-week progressive overload mesocycle with periodized intensity and volume.'}
                            </div>
                        </div>
                    </div>
                    <div class="htn-meso-badge">Macro Structure</div>
                </div>
            """),
            unsafe_allow_html=True,
        )

        # ── Cycle Switcher, Creator & Settings Bar ──────────────────────────
        chosen_prog_id = st.selectbox(
            "Active Training Cycle",
            options=prog_id_options,
            format_func=lambda pid: prog_names_map.get(pid, f"Cycle #{pid}"),
            index=prog_id_options.index(cur_prog_id) if cur_prog_id in prog_id_options else 0,
            key="active_periodization_cycle_selector",
            label_visibility="collapsed",
        )
        if chosen_prog_id != cur_prog_id:
            st.session_state.selected_periodization_program_id = chosen_prog_id
            st.session_state.periodization_sel_week = 1
            st.session_state.periodization_sel_day = 1
            st.session_state.delete_cycle_confirm_open = False
            st.rerun()

        with st.container(key="wk_cycle_bar"):
            c_new, c_dup, c_del, c_cfg = st.columns(4, gap="small")
            with c_new:
                if st.button("＋ New", key="btn_open_create_cycle", use_container_width=True):
                    st.session_state.create_cycle_modal_open = not st.session_state.get("create_cycle_modal_open", False)
                    st.session_state.cycle_settings_modal_open = False
                    st.session_state.delete_cycle_confirm_open = False
                    st.rerun()
            with c_dup:
                if st.button("Duplicate", key="btn_dup_active_cycle", use_container_width=True, help="Clone this entire periodization cycle"):
                    dup_res = duplicate_periodization_program(chosen_prog_id)
                    if dup_res.get("success"):
                        st.session_state.selected_periodization_program_id = dup_res["program_id"]
                        st.session_state.periodization_sel_week = 1
                        st.session_state.periodization_sel_day = 1
                        st.session_state.delete_cycle_confirm_open = False
                        st.toast(f"Cloned cycle '{dup_res['name']}'!")
                        st.rerun()
            with c_del:
                can_delete_prog = len(prog_id_options) > 1
                if st.button(
                    "Remove",
                    key="btn_open_delete_cycle",
                    use_container_width=True,
                    help="Remove this periodization cycle" if can_delete_prog else "Cannot remove the only remaining cycle",
                    disabled=not can_delete_prog,
                ):
                    st.session_state.delete_cycle_confirm_open = not st.session_state.get("delete_cycle_confirm_open", False)
                    st.session_state.create_cycle_modal_open = False
                    st.session_state.cycle_settings_modal_open = False
                    st.rerun()
            with c_cfg:
                if st.button("Settings", key="btn_open_cycle_settings", use_container_width=True, help="Configure progressive overload rate and cycle details"):
                    st.session_state.cycle_settings_modal_open = not st.session_state.get("cycle_settings_modal_open", False)
                    st.session_state.create_cycle_modal_open = False
                    st.session_state.delete_cycle_confirm_open = False
                    st.rerun()

        # ── Delete Cycle Confirmation Card ─────────────────────────────────
        if st.session_state.get("delete_cycle_confirm_open"):
            with st.container():
                st.markdown(
                    clean_html(f"""
                    <div style="background:rgba(255, 77, 77, 0.08);border:1px solid rgba(255, 77, 77, 0.35);border-radius:14px;padding:14px 16px;margin:8px 0 14px;">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div style="font-size:14px;font-weight:800;color:#ff6b6b;">Delete Periodization Cycle</div>
                            <span style="font-size:11px;font-weight:700;padding:2px 8px;border-radius:6px;background:rgba(255,77,77,0.15);color:#ff6b6b;border:1px solid rgba(255,77,77,0.3);">{prog_meta['name']}</span>
                        </div>
                        <div style="font-size:12px;color:var(--text-dim);margin-top:6px;line-height:1.4;">
                            Are you sure you want to remove <b>'{prog_meta['name']}'</b>? All scheduled weeks, days, targets, and exercise prescriptions in this cycle will be permanently deleted. This action cannot be undone.
                        </div>
                    </div>
                    """),
                    unsafe_allow_html=True,
                )
                col_d_confirm, col_d_cancel = st.columns(2)
                with col_d_confirm:
                    if st.button("Confirm Delete Cycle", key="btn_confirm_delete_cycle", use_container_width=True):
                        del_res = delete_periodization_program(cur_prog_id)
                        if del_res.get("success"):
                            st.session_state.delete_cycle_confirm_open = False
                            remaining = get_all_periodization_programs()
                            if remaining:
                                st.session_state.selected_periodization_program_id = remaining[0]["id"]
                            st.session_state.periodization_sel_week = 1
                            st.session_state.periodization_sel_day = 1
                            cycle_name = del_res.get("name") or prog_meta["name"]
                            st.toast(f"Cycle '{cycle_name}' deleted.")
                            st.rerun()
                        else:
                            st.error(del_res.get("error", "Failed to delete cycle."))
                with col_d_cancel:
                    if st.button("Cancel", key="btn_cancel_delete_cycle", use_container_width=True):
                        st.session_state.delete_cycle_confirm_open = False
                        st.rerun()

        # ── Cycle Settings Form (Expandable) ─────────────────────────────────
        if st.session_state.get("cycle_settings_modal_open"):
            with st.container():
                st.markdown(
                    clean_html(f"""
                    <div style="background:var(--glass-elevated);border:1px solid var(--glass-border-hover);border-radius:14px;padding:14px 16px;margin:8px 0 14px;">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div style="font-size:14px;font-weight:800;color:var(--text);">Cycle Progressive Overload Settings</div>
                            <span class="htn-meso-badge">{prog_meta['name']}</span>
                        </div>
                        <div style="font-size:12px;color:var(--text-dim);margin-top:2px;">
                            Configure how much weight and reps this cycle should increment each wave to enforce progressive overload.
                        </div>
                    </div>
                    """),
                    unsafe_allow_html=True,
                )
                with st.form("edit_cycle_progression_settings_form"):
                    col_cs1, col_cs2 = st.columns(2)
                    with col_cs1:
                        cur_w_prog = float(prog_meta.get("weight_progression_kg") if prog_meta.get("weight_progression_kg") is not None else 2.5)
                        edit_prog_kg = st.number_input("Weight Progression per Cycle (+kg)", min_value=0.25, max_value=50.0, value=cur_w_prog, step=0.5, help="Weight added to exercise suggestions when progressing to the next cycle wave")
                    with col_cs2:
                        cur_r_prog = int(prog_meta.get("reps_progression") if prog_meta.get("reps_progression") is not None else 1)
                        edit_prog_reps = st.number_input("Reps Progression per Cycle (+reps)", min_value=1, max_value=10, value=cur_r_prog, step=1, help="Reps added to bodyweight and accessory exercise suggestions")

                    edit_c_name = st.text_input("Cycle Name", value=prog_meta["name"])
                    edit_c_desc = st.text_input("Description (Optional)", value=prog_meta.get("description") or "")

                    c_cs_save, c_cs_cancel = st.columns(2)
                    with c_cs_save:
                        if st.form_submit_button("Save Settings", type="primary", use_container_width=True):
                            up_res = update_periodization_program_settings(
                                cur_prog_id,
                                weight_progression_kg=float(edit_prog_kg),
                                reps_progression=int(edit_prog_reps),
                                name=edit_c_name.strip(),
                                description=edit_c_desc.strip(),
                            )
                            if up_res.get("success"):
                                st.session_state.cycle_settings_modal_open = False
                                st.toast("Cycle progression settings updated.")
                                st.rerun()
                            else:
                                st.error(up_res.get("error", "Failed to update settings."))
                    with c_cs_cancel:
                        if st.form_submit_button("Close", use_container_width=True):
                            st.session_state.cycle_settings_modal_open = False
                            st.rerun()

                if len(prog_id_options) > 1:
                    st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)
                    if st.button("Delete This Cycle", key="btn_settings_remove_cycle", use_container_width=True, help="Open confirmation to delete this cycle"):
                        st.session_state.delete_cycle_confirm_open = True
                        st.session_state.cycle_settings_modal_open = False
                        st.rerun()

        # ── Create Cycle Form (Expandable) ───────────────────────────────────
        if st.session_state.get("create_cycle_modal_open"):
            with st.container():
                st.markdown(
                    clean_html("""
                    <div style="background:var(--glass-elevated);border:1px solid var(--glass-border-hover);border-radius:14px;padding:14px 16px;margin:8px 0 14px;">
                        <div style="font-size:14px;font-weight:800;color:var(--text);margin-bottom:4px;">Create New Periodization Cycle</div>
                        <div style="font-size:12px;color:var(--text-dim);">Design a custom training mesocycle with configurable progressive overload rates.</div>
                    </div>
                    """),
                    unsafe_allow_html=True,
                )
                with st.form("create_periodization_cycle_form"):
                    new_cycle_name = st.text_input("Cycle Name", placeholder="e.g. 5-Week Hypertrophy & Power Wave")
                    new_cycle_desc = st.text_input("Description (Optional)", placeholder="e.g. Phase progression for strength and hypertrophy")
                    template_choice = st.radio(
                        "Starting Structure",
                        options=["Clone from Current Cycle (Recommended)", "Create Blank Cycle"],
                        index=0,
                        horizontal=True,
                    )
                    col_cf1, col_cf2 = st.columns(2)
                    with col_cf1:
                        weeks_cnt = st.number_input("Number of Weeks", min_value=1, max_value=16, value=5, step=1)
                    with col_cf2:
                        days_cnt = st.number_input("Days per Week", min_value=1, max_value=7, value=5, step=1)

                    col_po1, col_po2 = st.columns(2)
                    with col_po1:
                        cycle_prog_kg = st.number_input("Weight Progression per Cycle (+kg)", min_value=0.25, max_value=50.0, value=2.5, step=0.5, help="Weight added to recommended exercises upon cycle completion")
                    with col_po2:
                        cycle_prog_reps = st.number_input("Reps Progression per Cycle (+reps)", min_value=1, max_value=10, value=1, step=1, help="Reps added to accessory/bodyweight prescriptions upon cycle completion")

                    c_sub1, c_sub2 = st.columns(2)
                    with c_sub1:
                        submit_create = st.form_submit_button("Create Cycle", type="primary", use_container_width=True)
                    with c_sub2:
                        cancel_create = st.form_submit_button("Cancel", use_container_width=True)

                    if submit_create:
                        if not new_cycle_name.strip():
                            st.error("Please enter a name for the cycle.")
                        else:
                            template_id = cur_prog_id if "Clone" in template_choice else None
                            res = create_periodization_program(
                                name=new_cycle_name.strip(),
                                description=new_cycle_desc.strip(),
                                weeks_count=int(weeks_cnt),
                                days_per_week=int(days_cnt),
                                template_program_id=template_id,
                                weight_progression_kg=float(cycle_prog_kg),
                                reps_progression=int(cycle_prog_reps),
                            )
                            if res.get("success"):
                                st.session_state.selected_periodization_program_id = res["program_id"]
                                st.session_state.create_cycle_modal_open = False
                                st.session_state.periodization_sel_week = 1
                                st.session_state.periodization_sel_day = 1
                                st.toast(f"Periodization cycle '{res['name']}' created!")
                                st.rerun()
                            else:
                                st.error(res.get("error", "Failed to create cycle."))
                    elif cancel_create:
                        st.session_state.create_cycle_modal_open = False
                        st.rerun()

        prog_map = get_builtin_periodization_program(cur_prog_id)
        if not prog_map:
            prog_map = PERIODIZATION_MESOCYCLE

        weeks_list = sorted([w for w in prog_map.keys() if isinstance(w, int)])
        if not weeks_list:
            weeks_list = [1]

        cur_week = st.session_state.get("periodization_sel_week", 1)
        if cur_week not in weeks_list:
            cur_week = weeks_list[0]
            st.session_state.periodization_sel_week = cur_week

        # ── Multi-Phase Interactive Visual Stepper ───────────────────────────
        step_items = []
        for w in weeks_list:
            w_data = prog_map.get(w, {})
            phase_name = w_data.get("phase", f"Week {w}")
            is_active = (w == cur_week)
            active_cls = " active" if is_active else ""
            step_items.append(
                f'<div class="htn-step-item{active_cls}">'
                f'<div class="htn-step-week">Week {w}</div>'
                f'<div class="htn-step-name">{phase_name}</div>'
                f'</div>'
            )
        stepper_html = f'<div class="htn-stepper">{"".join(step_items)}</div>'
        st.markdown(clean_html(stepper_html), unsafe_allow_html=True)

        # ── Week & Day Selectors ─────────────────────────────────────────────
        col_w, col_d = st.columns(2, gap="small")
        with col_w:
            week_opts = {
                w: f"Week {w} — {prog_map.get(w, {}).get('phase', f'Week {w}')} ({prog_map.get(w, {}).get('badge', '')})"
                for w in weeks_list
            }
            selected_week = st.selectbox(
                "Training Phase / Week",
                options=weeks_list,
                format_func=lambda w: week_opts.get(w, f"Week {w}"),
                index=weeks_list.index(cur_week) if cur_week in weeks_list else 0,
                key="periodization_sel_week",
            )

        week_data = prog_map.get(selected_week, {})
        days_dict = week_data.get("days", {})
        days_list = sorted(days_dict.keys()) if days_dict else [1]

        cur_day = st.session_state.get("periodization_sel_day", 1)
        if cur_day not in days_list:
            cur_day = days_list[0]
            st.session_state.periodization_sel_day = cur_day

        with col_d:
            selected_day = st.selectbox(
                "Training Day",
                options=days_list,
                format_func=lambda d: f"Day {d} ({len(days_dict.get(d, []))} exercises)",
                index=days_list.index(cur_day) if cur_day in days_list else 0,
                key="periodization_sel_day",
            )

        day_items = days_dict.get(selected_day, [])
        day_id = get_or_create_periodization_day(cur_prog_id, selected_week, selected_day)
        day_info = get_periodization_day_info(cur_prog_id, selected_week, selected_day)

        phase_name = day_info.get("phase_name") or week_data.get("phase", f"Week {selected_week}")
        badge_text = day_info.get("phase_badge") or week_data.get("badge", "")
        objective_text = day_info.get("objective") or week_data.get("objective", "")

        # ── Day Overview Header ──────────────────────────────────────────────
        overview_html = (
            f'<div style="background:var(--accent-dim);border:1px solid var(--glass-border-hover);border-radius:14px;padding:12px 16px;margin:12px 0 14px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">'
            f'<div>'
            f'<div style="font-size:14px;font-weight:800;color:var(--text);letter-spacing:-0.2px;">'
            f'Week {selected_week} · Day {selected_day} — {phase_name} Phase'
            f'</div>'
            f'<div style="font-size:11.5px;color:var(--text-dim);margin-top:2px;">'
            f'{objective_text}'
            f'</div>'
            f'</div>'
            f'<div class="htn-meso-pill">'
            f'{badge_text}'
            f'</div>'
            f'</div>'
        )
        st.markdown(clean_html(overview_html), unsafe_allow_html=True)

        # ── Edit Phase & Day Metadata Expander ───────────────────────────────
        with st.expander("Edit Phase & Day Focus", expanded=False):
            with st.form(f"edit_phase_day_form_{cur_prog_id}_{selected_week}_{selected_day}"):
                c_p1, c_p2 = st.columns([2, 1])
                with c_p1:
                    new_phase_title = st.text_input("Phase Title", value=phase_name)
                with c_p2:
                    new_badge_title = st.text_input("Protocol / Target Badge", value=badge_text, placeholder="e.g. 2x8-10 (RPE 9-10)")
                new_obj_desc = st.text_area("Training Objective", value=objective_text, placeholder="e.g. Maximize volume threshold and mechanical tension")
                if st.form_submit_button("Update Phase & Day Details", type="primary", use_container_width=True):
                    up_res = update_builtin_periodization_day(day_id, new_phase_title, new_badge_title, new_obj_desc)
                    if up_res.get("success"):
                        st.toast("Day details updated.")
                        st.rerun()
                    else:
                        st.error(up_res.get("error", "Failed to update day details."))

        # ── Exercise Breakdown Cards ─────────────────────────────────────────
        if not day_items:
            st.markdown(
                clean_html(f"""
                <div style="background:rgba(255,255,255,0.02);border:1px dashed var(--glass-border-hover);border-radius:12px;padding:16px 18px;margin:8px 0 14px;text-align:center;">
                    <div style="font-size:14px;font-weight:800;color:var(--text);">No exercises prescribed for Week {selected_week} Day {selected_day} yet</div>
                    <div style="font-size:12px;color:var(--text-dim);margin-top:4px;">Add your Primary Focus compound lifts, Hypertrophy Support accessories, or Compound Auxiliaries using the form below.</div>
                </div>
                """),
                unsafe_allow_html=True,
            )
        else:
            for item in day_items:
                ex_row_id = item["id"]
                role = item.get("role", "auxiliary")
                if role in ("focus", "primary"):
                    role_badge = '<span class="htn-role-badge-primary">PRIMARY FOCUS</span>'
                elif role in ("support", "hypertrophy"):
                    role_badge = '<span class="htn-role-badge-support">HYPERTROPHY SUPPORT</span>'
                else:
                    role_badge = '<span class="htn-role-badge-aux">COMPOUND AUXILIARY</span>'

                equip_tag = f" · {item.get('equip')}" if item.get("equip") else ""
                sets_count = item.get("sets", 2)
                sets_label = f"{sets_count} {'Sets' if sets_count != 1 else 'Set'}"

                card_html = (
                    f'<div class="htn-period-ex-card">'
                    f'<div>'
                    f'<div>{role_badge}</div>'
                    f'<div style="font-size:15px;font-weight:800;color:var(--text);line-height:1.2;">{item["name"]}</div>'
                    f'<div style="font-size:11px;color:var(--text-dim);margin-top:2px;">{item["muscle"]}{equip_tag} · {tracking_label(item["type"])}</div>'
                    f'</div>'
                    f'<div style="text-align:right;">'
                    f'<div class="htn-target-badge">{item["target"]}</div>'
                    f'<div style="font-size:11px;color:var(--text-dim);margin-top:3px;font-weight:600;">{sets_label}</div>'
                    f'</div>'
                    f'</div>'
                )
                st.markdown(clean_html(card_html), unsafe_allow_html=True)

                with st.expander(f"Edit / Delete · {item['name']}", expanded=False):
                    with st.form(f"edit_ex_form_{ex_row_id}"):
                        c_er1, c_er2 = st.columns([2, 1])
                        with c_er1:
                            e_name = st.text_input("Exercise Name", value=item["name"])
                        with c_er2:
                            current_role_idx = 0 if role in ("focus", "primary") else (1 if role in ("support", "hypertrophy") else 2)
                            e_role_choice = st.selectbox(
                                "Role",
                                options=["Primary Focus", "Hypertrophy Support", "Compound Auxiliary"],
                                index=current_role_idx,
                            )
                        c_et1, c_et2 = st.columns([2, 1])
                        with c_et1:
                            e_target = st.text_input("Target Prescription", value=item["target"])
                        with c_et2:
                            e_sets = st.number_input("Sets", min_value=1, max_value=10, value=int(sets_count), step=1)
                        c_em1, c_em2, c_em3 = st.columns([1.5, 1.5, 1.5])
                        with c_em1:
                            muscle_options = [
                                "Chest", "Back", "Shoulders", "Biceps", "Triceps", "Legs",
                                "Quads", "Hamstrings", "Glutes", "Calves", "Core", "Cardio", "Full Body", "Other"
                            ]
                            m_idx = muscle_options.index(item["muscle"]) if item["muscle"] in muscle_options else 0
                            e_muscle = st.selectbox("Muscle", options=muscle_options, index=m_idx)
                        with c_em2:
                            e_equip = st.text_input("Equipment", value=item.get("equip") or "")
                        with c_em3:
                            tracking_keys = ["weights_reps", "bodyweight", "weighted_calisthenics", "time"]
                            t_labels = ["Weights + Reps", "Bodyweight", "Weighted Calisthenics", "Time"]
                            curr_type_idx = tracking_keys.index(item["type"]) if item["type"] in tracking_keys else 0
                            e_type_choice = st.selectbox("Tracking Type", options=t_labels, index=curr_type_idx)

                        if st.form_submit_button("Update Exercise", type="primary", use_container_width=True):
                            t_map = {"Weights + Reps": "weights_reps", "Bodyweight": "bodyweight", "Weighted Calisthenics": "weighted_calisthenics", "Time": "time"}
                            upd_res = update_builtin_periodization_exercise(
                                ex_row_id,
                                name=e_name,
                                muscle=e_muscle,
                                ex_type=t_map.get(e_type_choice, "weights_reps"),
                                equip=e_equip,
                                target=e_target,
                                sets=int(e_sets),
                                role=e_role_choice,
                            )
                            if upd_res.get("success"):
                                st.toast(f"Updated '{e_name}'.")
                                st.rerun()
                            else:
                                st.error(upd_res.get("error", "Failed to update exercise."))

                    if st.button("Delete Exercise", key=f"btn_del_item_{ex_row_id}", use_container_width=True):
                        delete_builtin_periodization_exercise(ex_row_id)
                        st.toast(f"Removed '{item['name']}' from this day.")
                        st.rerun()

        # ── Add Exercise Form (Always available, auto-expanded if 0 exercises) ─
        with st.expander("＋ Add Exercise (Primary Focus / Hypertrophy Support / Compound Auxiliary)", expanded=(len(day_items) == 0)):
            st.markdown(
                clean_html("""
                <div style="font-size:12px;color:var(--text-dim);margin-bottom:10px;line-height:1.45;">
                    <b style="color:var(--accent);">Primary Focus:</b> Heavy core compound lift (Pull-ups, Bench Press, Squats).<br/>
                    <b style="color:#fbbf24;">Hypertrophy Support:</b> High-activation accessory/isolation work (Lat Pullover, Bicep Curl, Leg Extension).<br/>
                    <b style="color:#7dd3fc;">Compound Auxiliary:</b> Paused lifts or secondary compound variations (Paused Bench, Paused Squats).
                </div>
                """),
                unsafe_allow_html=True,
            )
            all_lib_exs = get_all_exercises(uid)
            all_lib_names = sorted(list({e["name"] for e in all_lib_exs}))

            c_src1, c_src2 = st.columns([2, 2])
            with c_src1:
                add_role_choice = st.radio(
                    "Role Prescription",
                    options=["Primary Focus", "Hypertrophy Support", "Compound Auxiliary"],
                    index=0 if len(day_items) == 0 else 1,
                    horizontal=True,
                    key=f"add_role_{cur_prog_id}_{selected_week}_{selected_day}",
                )
            with c_src2:
                add_source_mode = st.radio(
                    "Source",
                    options=["Choose from Exercise Library", "Enter Custom Exercise Name"],
                    horizontal=True,
                    key=f"add_src_{cur_prog_id}_{selected_week}_{selected_day}",
                )

            with st.form(f"add_period_ex_form_{cur_prog_id}_{selected_week}_{selected_day}"):
                c_ex_name, c_ex_tgt = st.columns([2.5, 2])
                with c_ex_name:
                    if add_source_mode == "Choose from Exercise Library" and all_lib_names:
                        selected_lib_name = st.selectbox("Select Exercise", options=all_lib_names)
                        final_add_name = selected_lib_name
                        lib_obj = next((e for e in all_lib_exs if e["name"] == selected_lib_name), None)
                        default_muscle = lib_obj["muscle_group"] if lib_obj else "Chest"
                        default_equip = lib_obj.get("equipment") or ""
                        default_type = lib_obj["exercise_type"] if lib_obj else "weights_reps"
                    else:
                        final_add_name = st.text_input("Exercise Name", placeholder="e.g. Incline Dumbbell Press")
                        default_muscle = "Chest"
                        default_equip = ""
                        default_type = "weights_reps"

                with c_ex_tgt:
                    add_target_input = st.text_input(
                        "Target Prescription",
                        value=badge_text if (badge_text and badge_text != "Custom Target" and add_role_choice == "Primary Focus") else "",
                        placeholder="e.g. 2x8-10 (RPE 9-10), 4x1 (RPE 8-9), 2x5 [Slow Eccentrics]",
                    )

                c_a1, c_a2, c_a3, c_a4 = st.columns([1, 1.5, 1.5, 1.5])
                with c_a1:
                    add_sets_input = st.number_input("Sets", min_value=1, max_value=10, value=2, step=1)
                with c_a2:
                    muscle_list = [
                        "Chest", "Back", "Shoulders", "Biceps", "Triceps", "Legs",
                        "Quads", "Hamstrings", "Glutes", "Calves", "Core", "Cardio", "Full Body", "Other"
                    ]
                    m_def_idx = muscle_list.index(default_muscle) if default_muscle in muscle_list else 0
                    add_muscle_input = st.selectbox("Muscle Group", options=muscle_list, index=m_def_idx)
                with c_a3:
                    add_equip_input = st.text_input("Equipment", value=default_equip, placeholder="e.g. Barbell, Cable, Machine")
                with c_a4:
                    tracking_opts = ["Weights + Reps", "Bodyweight", "Weighted Calisthenics", "Time"]
                    t_keys = ["weights_reps", "bodyweight", "weighted_calisthenics", "time"]
                    t_def_idx = t_keys.index(default_type) if default_type in t_keys else 0
                    add_type_choice = st.selectbox("Tracking Type", options=tracking_opts, index=t_def_idx)

                if st.form_submit_button(f"＋ Add to Week {selected_week} Day {selected_day}", type="primary", use_container_width=True):
                    if not (final_add_name or "").strip():
                        st.error("Please enter or select an exercise name.")
                    else:
                        t_map = {"Weights + Reps": "weights_reps", "Bodyweight": "bodyweight", "Weighted Calisthenics": "weighted_calisthenics", "Time": "time"}
                        target_final = (add_target_input or "").strip() or "2x8-10"
                        res_add = add_builtin_periodization_exercise(
                            day_id=day_id,
                            name=final_add_name.strip(),
                            muscle=add_muscle_input,
                            ex_type=t_map.get(add_type_choice, "weights_reps"),
                            equip=add_equip_input.strip(),
                            target=target_final,
                            sets=int(add_sets_input),
                            role=add_role_choice,
                        )
                        if res_add.get("success"):
                            st.toast(f"Added '{final_add_name}' as {add_role_choice} to Week {selected_week} Day {selected_day}!")
                            st.rerun()
                        else:
                            st.error(res_add.get("error", "Failed to add exercise."))

        st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
        col_act1, col_act2 = st.columns([3, 2], gap="small")
        with col_act1:
            if st.button(
                f"Start Week {selected_week} Day {selected_day} Workout ({len(day_items)} Exercises)",
                key=f"start_periodized_btn_{cur_prog_id}_{selected_week}_{selected_day}",
                use_container_width=True,
                type="primary",
                disabled=(len(day_items) == 0),
            ):
                start_periodized_session(selected_week, selected_day, program_id=cur_prog_id)
        with col_act2:
            if st.button(
                "Save as My Routine",
                key=f"save_as_routine_btn_{cur_prog_id}_{selected_week}_{selected_day}",
                use_container_width=True,
                disabled=(len(day_items) == 0),
            ):
                new_rid = duplicate_periodization_day_as_routine(uid, selected_week, selected_day, program_id=cur_prog_id)
                if new_rid.get("success"):
                    st.toast(f"Saved Week {selected_week} Day {selected_day} to My Routines!")
                    st.rerun()
                else:
                    st.error(new_rid.get("error", "Failed to duplicate routine."))

        # ── Mesocycle Progressive Overload Hub ───────────────────────────────
        is_final_week = (selected_week == weeks_list[-1])
        prog_kg = float(prog_meta.get("weight_progression_kg") if prog_meta.get("weight_progression_kg") is not None else 2.5)
        prog_reps = int(prog_meta.get("reps_progression") if prog_meta.get("reps_progression") is not None else 1)
        import re
        wave_m = re.search(r'Wave\s*([0-9]+)', prog_meta['name'], re.IGNORECASE)
        curr_wave_num = int(wave_m.group(1)) if wave_m else 1
        next_wave_num = curr_wave_num + 1

        if is_final_week:
            status_desc = f"You have reached the final week (Week {selected_week} of {weeks_list[-1]}). Complete this phase and advance to Wave {next_wave_num} with auto-calibrated progressive overload (+{prog_kg} kg on compound lifts, +{prog_reps} reps on accessories)."
            badge_title = "WAVE COMPLETION READY"
        else:
            status_desc = f"Week {selected_week} of {weeks_list[-1]} in progress. Overload increments (+{prog_kg} kg / +{prog_reps} reps) are actively suggested during each workout session. Advance to Wave {next_wave_num} when this cycle is finished."
            badge_title = f"WAVE {curr_wave_num} ACTIVE"

        st.markdown(
            clean_html(f"""
            <div class="htn-overload-card">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:10px;">
                    <div>
                        <div style="display:flex;align-items:center;gap:8px;">
                            <span class="htn-overload-badge">{badge_title}</span>
                            <span style="font-size:11px;color:var(--text-dim);font-weight:700;">Progressive Overload Engine</span>
                        </div>
                        <div style="font-size:15px;font-weight:800;color:var(--text);margin-top:6px;">
                            +{prog_kg} kg Compound Lifts &bull; +{prog_reps} Reps Accessories per Wave
                        </div>
                        <div style="font-size:12px;color:var(--text-dim);margin-top:3px;line-height:1.45;">
                            {status_desc}
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:10px;font-weight:800;color:var(--accent);letter-spacing:0.5px;">NEXT TARGET WAVE</div>
                        <div style="font-size:15px;font-weight:800;color:var(--text);margin-top:2px;">Wave {next_wave_num}</div>
                    </div>
                </div>
            </div>
            """),
            unsafe_allow_html=True,
        )

        c_adv1, c_adv2 = st.columns([3, 2], gap="small")
        with c_adv1:
            if st.button(
                f"Advance to Wave {next_wave_num} (+{prog_kg} kg Overload)",
                key=f"btn_advance_wave_{cur_prog_id}",
                type="primary" if is_final_week else "secondary",
                use_container_width=True,
                help=f"Clone this mesocycle into Wave {next_wave_num} with +{prog_kg} kg progression",
            ):
                adv_res = advance_periodization_cycle_with_overload(cur_prog_id)
                if adv_res.get("success"):
                    st.session_state.selected_periodization_program_id = adv_res["program_id"]
                    st.session_state.periodization_sel_week = 1
                    st.session_state.periodization_sel_day = 1
                    st.toast(f"Advanced to {adv_res['name']} with +{adv_res['overload_kg']} kg overload applied!")
                    st.rerun()
                else:
                    st.error(adv_res.get("error", "Failed to advance cycle wave."))
        with c_adv2:
            if st.button(
                "Configure Overload (+kg / +reps)",
                key=f"btn_cfg_overload_{cur_prog_id}",
                use_container_width=True,
            ):
                st.session_state.cycle_settings_modal_open = True
                st.rerun()

        with st.expander(f"View {prog_meta['name']} Master Matrix", expanded=False):
            st.markdown(clean_html(_render_periodization_master_grid_html(prog_map)), unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


with st.container(key="wk_shell"):
    if st.session_state.workout_mode == "active":
        active_workout_view()
        if st.button("← Back", key="active_back"):
            delete_session(st.session_state.active_session_id, user_id)
            reset_workout_state()
            st.rerun()

    elif st.session_state.workout_mode == "routine":
        c_rhead1, c_rhead2 = st.columns([3, 1], gap="small")
        with c_rhead1:
            st.markdown('<div class="wk-title">Workout</div>', unsafe_allow_html=True)
            st.markdown('<div class="wk-subtitle">Build. Train. Become High Tier.</div>', unsafe_allow_html=True)
        with c_rhead2:
            st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)
            if st.button("← Back", key="routine_back_top", use_container_width=True):
                st.session_state.workout_mode = None
                st.rerun()
        routine_builder()
        if st.button("← Back", key="routine_back"):
            st.session_state.workout_mode = None
            st.rerun()

    elif st.session_state.workout_mode == "manage":
        manage_view()
        if st.button("← Back to Workout", key="manage_back"):
            st.session_state.workout_mode = None
            st.session_state.editing_routine_id = None
            st.session_state.editing_session_id = None
            st.rerun()

    elif st.session_state.workout_mode == "periodization":
        c_phead1, c_phead2 = st.columns([3, 1], gap="small")
        with c_phead1:
            st.markdown('<div class="wk-title">Periodisation</div>', unsafe_allow_html=True)
            st.markdown('<div class="wk-subtitle">Multi-Week Progressive Overload Mesocycle</div>', unsafe_allow_html=True)
        with c_phead2:
            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
            if st.button("← Back to Workout", key="periodization_back_top", use_container_width=True):
                st.session_state.workout_mode = None
                st.rerun()

        render_periodization_section(user_id, in_expander=False)

        st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
        if st.button("← Back to Workout", key="periodization_back_bottom"):
            st.session_state.workout_mode = None
            st.rerun()

    else:
        st.markdown('<div class="wk-title">Workout</div>', unsafe_allow_html=True)
        st.markdown('<div class="wk-subtitle">Build. Train. Become High Tier.</div>', unsafe_allow_html=True)

        post_notice = st.session_state.get("post_workout_periodization_notice")
        if post_notice:
            st.markdown(
                clean_html(f"""
                <div style="background:linear-gradient(135deg, var(--accent-dim), var(--card));border:1px solid var(--accent-glow);border-radius:12px;padding:12px 16px;margin:8px 0 12px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                    <div>
                        <div style="font-size:13.5px;font-weight:800;color:var(--text);">
                            Session Logged: Week {post_notice['week']} Day {post_notice['day']}
                        </div>
                        <div style="font-size:12px;color:var(--text-dim);margin-top:2px;">
                            Progressive Overload Target for next cycle wave: Increase compound lifts by <b>+{post_notice['prog_kg']} kg</b> and accessories by <b>+{post_notice['prog_reps']} reps</b>.
                        </div>
                    </div>
                    <div class="htn-overload-badge">Overload Target Active</div>
                </div>
                """),
                unsafe_allow_html=True,
            )
            col_not1, col_not2 = st.columns([2, 1], gap="small")
            with col_not1:
                if st.button("Open Periodisation", key="btn_open_period_from_notice", type="primary", use_container_width=True):
                    st.session_state.workout_mode = "periodization"
                    st.rerun()
            with col_not2:
                if st.button("Dismiss", key="btn_dismiss_main_period_notice", use_container_width=True):
                    st.session_state.post_workout_periodization_notice = None
                    st.rerun()

        with st.container(key="wk_hub_actions"):
            c1, c2, c3 = st.columns(3, gap="medium")
            with c1:
                if st.button("＋ Start Empty Workout", key="start_empty", use_container_width=True):
                    start_empty_workout()
                    st.rerun()
            with c2:
                if st.button("＋ New Routine", key="new_routine", use_container_width=True):
                    st.session_state.workout_mode = "routine"
                    st.rerun()
            with c3:
                if st.button("＋ Periodisation", key="btn_open_periodisation", use_container_width=True):
                    st.session_state.workout_mode = "periodization"
                    st.rerun()

        with st.container(key="wk_routines_head"):
            c1, c2 = st.columns([2.2, 1.2], gap="small")
            with c1:
                st.markdown('<div class="wk-section-title">My Routines</div>', unsafe_allow_html=True)
            with c2:
                if st.button("Manage ›", key="manage"):
                    st.session_state.workout_mode = "manage"
                    st.rerun()

        # ------------------- My Routines Section -------------------
        routines = get_routines(user_id)
        if not routines:
            st.markdown('<div class="wk-card wk-muted">No routines yet. Create one from your own exercises.</div>', unsafe_allow_html=True)
        else:
            ROUTINES_PREVIEW_LIMIT = 2
            is_routines_expanded = st.session_state.get("expanded_section") == "routines"
            visible_routines = routines if is_routines_expanded else routines[:ROUTINES_PREVIEW_LIMIT]

            for r in visible_routines:
                exercises = get_routine_exercises(r["id"])
                muscles = " • ".join(dict.fromkeys(e["muscle_group"] for e in exercises))
                with st.container(key=f"hub_routine_{r['id']}"):
                    st.markdown(
                        clean_html(f"""<div class="wk-routine-card" style="margin-bottom:10px;">
                            <div class="wk-routine-name">{r["name"]}</div>
                            <div class="wk-routine-count">{len(exercises)} exercise{"s" if len(exercises) != 1 else ""}</div>
                            <div class="wk-routine-muscles">{muscles or "No exercises yet"}</div>
                        </div>"""),
                        unsafe_allow_html=True,
                    )
                    c1, c2 = st.columns([1.4, 1], gap="small")
                    with c1:
                        if st.button("Start Routine", key=f"routine_start_{r['id']}", type="primary", use_container_width=True):
                            start_routine(r["id"])
                            st.rerun()
                    with c2:
                        if st.button("Duplicate", key=f"routine_dup_{r['id']}", use_container_width=True):
                            duplicate_routine(r["id"], user_id)
                            st.rerun()

            if len(routines) > ROUTINES_PREVIEW_LIMIT:
                if not is_routines_expanded:
                    st.markdown('<div class="wk-fade-mask"></div>', unsafe_allow_html=True)
                    remaining_routines = len(routines) - ROUTINES_PREVIEW_LIMIT
                    if st.button(f"View more routines ({remaining_routines} more) ↓", key="view_more_routines", use_container_width=True):
                        st.session_state.expanded_section = "routines"
                        st.rerun()
                else:
                    if st.button("View less routines ↑", key="view_more_routines", use_container_width=True):
                        st.session_state.expanded_section = None
                        st.rerun()

        # ------------------- Exercise Library Section -------------------
        st.markdown('<div class="wk-section-title" style="margin:20px 0 12px;">Exercise Library</div>', unsafe_allow_html=True)
        exercises = get_all_exercises(user_id)
        if not exercises:
            st.markdown('<div class="wk-card wk-muted">No exercises yet. Create your first exercise below.</div>', unsafe_allow_html=True)
        else:
            EXERCISES_PREVIEW_LIMIT = 4
            is_exercises_expanded = st.session_state.get("expanded_section") == "exercises"
            visible_exercises = exercises if is_exercises_expanded else exercises[:EXERCISES_PREVIEW_LIMIT]

            for e in visible_exercises:
                badge = ' <span class="htn-badge" style="font-size:10px;padding:2px 8px;margin-left:6px;">Built-in</span>' if e.get("user_id") is None else ''
                st.markdown(
                    f'<div class="wk-exercise-card"><div class="wk-exercise-title">{e["name"]}{badge}</div><div class="wk-exercise-meta">{e["muscle_group"]} · {tracking_label(e["exercise_type"])}</div></div>',
                    unsafe_allow_html=True,
                )

            if len(exercises) > EXERCISES_PREVIEW_LIMIT:
                if not is_exercises_expanded:
                    st.markdown('<div class="wk-fade-mask"></div>', unsafe_allow_html=True)
                    remaining_exercises = len(exercises) - EXERCISES_PREVIEW_LIMIT
                    if st.button(f"View more exercises ({remaining_exercises} more) ↓", key="view_more_exercises", use_container_width=True):
                        st.session_state.expanded_section = "exercises"
                        st.rerun()
                else:
                    if st.button("View less exercises ↑", key="view_more_exercises", use_container_width=True):
                        st.session_state.expanded_section = None
                        st.rerun()

        if st.button("+ Create exercise", key="open_create_exercise", use_container_width=True):
            st.session_state.create_exercise_open = not st.session_state.create_exercise_open
            st.rerun()

        if st.session_state.create_exercise_open:
            show_create_exercise()
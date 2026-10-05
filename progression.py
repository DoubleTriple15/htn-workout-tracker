from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from db.database import (
    get_all_exercises,
    get_estimated_1rm,
    get_exercise_personal_bests,
    get_muscle_group_distribution,
    get_or_create_local_user,
    get_progression,
    init_db,
)
from htn_theme import (
    clean_html,
    get_theme_tokens,
    inject_theme_css,
    render_chatbot_fab,
    render_nav_bar,
)
from utils.calculations import kg_to_lbs

st.set_page_config(
    page_title="Progression — HTN",
    page_icon="HTN",
    layout="wide",
    initial_sidebar_state="collapsed",
)
init_db()
user = get_or_create_local_user()
uid = user["id"]
if "theme_pref" not in st.session_state or not st.session_state.theme_pref:
    st.session_state.theme_pref = user.get("theme_pref") or "Original"

use_imperial = user.get("unit_pref") == "imperial"
weight_unit = "lbs" if use_imperial else "kg"


def tracking_label(exercise_type: str) -> str:
    labels = {
        "weights_reps": "Weights + Reps",
        "reps": "Weights + Reps",
        "time": "Time",
        "bodyweight": "Bodyweight",
        "weighted_calisthenics": "Weighted Calisthenics",
    }
    return labels.get(exercise_type, exercise_type.replace("_", " ").title())


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

/* Responsive main shell */
.pg-shell {
    width: 100%;
    max-width: 1000px;
    margin: 0 auto;
    box-sizing: border-box;
    padding: 0 !important;
}

.pg-header {
    margin-bottom: 12px;
}

.pg-title {
    font-size: clamp(24px, 4vw, 32px);
    font-weight: 800;
    color: var(--text);
    line-height: 1.15;
    margin: 0 0 2px 0;
    letter-spacing: -0.5px;
}

.pg-subtitle {
    font-size: 13px;
    color: var(--text-dim);
}

/* Rounded card wrapper for the progression chart */
[data-testid="stPlotlyChart"] {
    border-radius: 16px !important;
    overflow: hidden !important;
    border: 1px solid var(--card-border) !important;
    background: var(--card) !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45), var(--glass-highlight) !important;
    padding: 6px 4px 4px 4px;
    box-sizing: border-box;
}

[data-testid="stPlotlyChart"] > div {
    border-radius: 13px !important;
    overflow: hidden !important;
}

@media (max-width: 640px) {
    .block-container,
    div[data-testid="stMain"] .block-container,
    section[data-testid="stMain"] .block-container {
        padding: 8px 12px 96px 12px !important;
        box-sizing: border-box !important;
    }
    .pg-shell {
        padding: 0 !important;
    }
    .pg-header {
        margin-bottom: 12px !important;
    }
    .pg-title {
        font-size: 24px !important;
        line-height: 1.15 !important;
    }
}
"""

inject_theme_css(PAGE_CSS)
render_chatbot_fab()
render_nav_bar(active="progression")

with st.container():
    st.markdown(clean_html("""
    <div class="pg-shell">
        <div class="pg-header">
            <h1 class="pg-title">Progression</h1>
            <div class="pg-subtitle">Track your lifts. Stay consistent.</div>
        </div>
    """), unsafe_allow_html=True)

    exercises = get_all_exercises(uid)
    if not exercises:
        st.info("Complete a workout with your exercises to unlock progression charts.")
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    labels = [f"{e['name']} · {e['muscle_group']}" for e in exercises]

    # Pre-select exercise if navigated from a Home PR card
    jump_name = st.session_state.pop("prog_jump_exercise", None)
    default_idx = 0
    if jump_name:
        for i, e in enumerate(exercises):
            if e["name"].lower() == jump_name.lower():
                default_idx = i
                break

    selected_label = st.selectbox("Exercise", labels, index=default_idx)
    selected = exercises[labels.index(selected_label)]
    ex_id = selected["id"]
    ex_type = (selected.get("exercise_type") or "weights_reps").lower()

    progression = get_progression(uid, ex_id)
    session_count = len(progression)
    pbs = get_exercise_personal_bests(uid, ex_id)
    one_rm = get_estimated_1rm(uid, ex_id)

    best_weight = float(pbs.get("best_weight") or 0.0)
    best_reps = int(pbs.get("best_reps") or 0)
    best_duration = int(pbs.get("best_duration") or 0)

    # ── Dynamic Stat Metric based on Exercise Type ────────────────────────────────
    if ex_type == "time":
        metric_label = "Best Time"
        if best_duration >= 60:
            m, s = divmod(best_duration, 60)
            metric_val = f"{m}:{s:02d} min" if s else f"{m} min"
        elif best_duration > 0:
            metric_val = f"{best_duration}s"
        else:
            metric_val = "—"

    elif ex_type == "bodyweight":
        metric_label = "Max Reps"
        metric_val = f"{best_reps} reps" if best_reps > 0 else "—"

    elif ex_type == "weighted_calisthenics":
        if best_weight > 0:
            disp_w = kg_to_lbs(best_weight) if use_imperial else best_weight
            metric_label = "Max Added Weight"
            metric_val = f"+{disp_w:.1f} {weight_unit}"
        else:
            metric_label = "Max Reps"
            metric_val = f"{best_reps} reps" if best_reps > 0 else "—"

    else:
        metric_label = "Estimated 1RM"
        if one_rm > 0:
            disp_1rm = kg_to_lbs(one_rm) if use_imperial else one_rm
            metric_val = f"{disp_1rm:.1f} {weight_unit}"
        elif best_reps > 0:
            metric_label = "Max Reps"
            metric_val = f"{best_reps} reps"
        else:
            metric_val = "—"

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(metric_label, metric_val)
    with c2:
        st.metric("Sessions", session_count)
    with c3:
        st.metric("Tracking", tracking_label(ex_type))

    def format_point_date(val):
        try:
            return datetime.fromisoformat(str(val)[:10]).strftime("%d %b")
        except Exception:
            return str(val)

    # ── Dynamic Progression Chart ────────────────────────────────────────────────
    chart_x = []
    chart_y = []
    y_axis_title = ""

    if ex_type == "time":
        chart_data = [r for r in progression if (r.get("max_duration") or 0) > 0]
        if chart_data:
            chart_x = [format_point_date(r["date"]) for r in chart_data]
            chart_y = [r["max_duration"] for r in chart_data]
            y_axis_title = "Seconds"

    elif ex_type == "bodyweight":
        chart_data = [r for r in progression if (r.get("max_reps") or 0) > 0]
        if chart_data:
            chart_x = [format_point_date(r["date"]) for r in chart_data]
            chart_y = [r["max_reps"] for r in chart_data]
            y_axis_title = "Reps"

    elif ex_type == "weighted_calisthenics":
        has_weights = any((r.get("max_weight") or 0) > 0 for r in progression)
        if has_weights:
            chart_data = [r for r in progression if (r.get("max_weight") or 0) > 0]
            chart_x = [format_point_date(r["date"]) for r in chart_data]
            chart_y = [
                round(kg_to_lbs(r["max_weight"]), 1) if use_imperial else round(r["max_weight"], 1)
                for r in chart_data
            ]
            y_axis_title = f"+Weight ({weight_unit})"
        else:
            chart_data = [r for r in progression if (r.get("max_reps") or 0) > 0]
            chart_x = [format_point_date(r["date"]) for r in chart_data]
            chart_y = [r["max_reps"] for r in chart_data]
            y_axis_title = "Reps"

    else:
        has_weights = any((r.get("best_1rm") or r.get("max_weight") or 0) > 0 for r in progression)
        if has_weights:
            chart_data = [r for r in progression if (r.get("best_1rm") or r.get("max_weight") or 0) > 0]
            chart_x = [format_point_date(r["date"]) for r in chart_data]
            raw_vals = [r.get("best_1rm") or r.get("max_weight") or 0 for r in chart_data]
            chart_y = [
                round(kg_to_lbs(w), 1) if use_imperial else round(w, 1)
                for w in raw_vals
            ]
            y_axis_title = f"1RM ({weight_unit})"
        else:
            chart_data = [r for r in progression if (r.get("max_reps") or 0) > 0]
            chart_x = [format_point_date(r["date"]) for r in chart_data]
            chart_y = [r["max_reps"] for r in chart_data]
            y_axis_title = "Reps"

    if chart_x and chart_y:
        st.markdown(
            clean_html("""
            <div style="font-size:11px; font-weight:700; color:var(--accent); text-transform:uppercase; letter-spacing:1.5px; margin-top:14px; margin-bottom:4px;">
                Performance Curve
            </div>
            """),
            unsafe_allow_html=True,
        )

        tokens = get_theme_tokens()
        chart_line_col = tokens["chart_line"]
        chart_fill_col = tokens["chart_fill"]

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=chart_x,
                y=chart_y,
                mode="lines+markers",
                fill="tozeroy",
                fillcolor=chart_fill_col,
                line=dict(
                    color=chart_line_col,
                    width=3.5,
                    shape="spline",
                    smoothing=1.3,
                ),
                marker=dict(
                    size=8,
                    color=chart_line_col,
                    symbol="circle",
                    line=dict(color=tokens["card"], width=2.5),
                ),
                hovertemplate=f"<b>%{{y}} {y_axis_title}</b><br><span style='font-size:11px; color:#8e928a;'>%{{x}}</span><extra></extra>",
            )
        )

        fig.update_layout(
            height=245,
            margin=dict(l=14, r=14, t=16, b=14),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor=tokens["card"],
                bordercolor=chart_line_col,
                font=dict(color="#f5f5f5", size=12),
            ),
            xaxis=dict(
                type="category",
                showgrid=False,
                zeroline=False,
                tickfont=dict(color="#8e928a", size=11),
                linecolor="rgba(255, 255, 255, 0.08)",
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(255, 255, 255, 0.05)",
                zeroline=False,
                tickfont=dict(color="#8e928a", size=11),
            ),
        )

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown(
            '<div style="color:var(--text-dim);font-size:13px;padding:12px 0;">Log at least one session with recorded sets to render the progression chart.</div>',
            unsafe_allow_html=True,
        )

    # ── Muscles Breakdown ────────────────────────────────────────────────────────
    muscles = get_muscle_group_distribution(uid)
    if muscles:
        st.markdown(
            '<div class="htn-section-head" style="margin-top:20px;">'
            '<div class="htn-section-title">Muscles Worked</div>'
            '<div class="htn-badge">Set Distribution</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        total_all_sets = sum(m.get("total_sets", 0) for m in muscles) or 1

        muscle_items_html = []
        for m in muscles:
            m_name = m.get("muscle_group", "Other")
            m_sets = m.get("total_sets", 0)
            pct = round((m_sets / total_all_sets) * 100, 1)
            bar_width = max(3.0, min(100.0, pct))

            muscle_items_html.append(f"""
            <div style="margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                    <div style="display:flex;align-items:center;gap:8px;">
                        <span style="font-size:13.5px;font-weight:700;color:var(--text);">{m_name}</span>
                        <span style="font-size:11px;font-weight:600;color:var(--text-dim);">{m_sets} {'sets' if m_sets != 1 else 'set'}</span>
                    </div>
                    <span style="font-size:12px;font-weight:800;color:var(--accent);letter-spacing:0.3px;">{pct}%</span>
                </div>
                <div style="height:7px;background:rgba(255,255,255,0.06);border-radius:999px;overflow:hidden;position:relative;">
                    <div style="height:100%;width:{bar_width}%;background:linear-gradient(90deg, var(--accent-secondary), var(--accent));border-radius:999px;box-shadow:0 0 10px var(--accent-glow);transition:width 0.4s ease;"></div>
                </div>
            </div>
            """)

        card_content = "".join(muscle_items_html)
        st.markdown(
            clean_html(f"""
            <div class="htn-card" style="padding:14px 16px 8px 16px;">
                {card_content}
            </div>
            """),
            unsafe_allow_html=True,
        )
        with st.expander("Detailed Muscle Group Table", expanded=False):
            st.dataframe(pd.DataFrame(muscles), hide_index=True, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

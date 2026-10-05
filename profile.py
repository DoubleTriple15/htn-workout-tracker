import base64
from datetime import date, timedelta
import io
import math

from PIL import Image, ImageOps
import streamlit as st

from auth import log_out
from db.database import (
    delete_account,
    get_muscle_group_distribution,
    get_or_create_local_user,
    init_db,
    update_profile,
    update_theme_pref,
    update_unit_pref,
)
from htn_theme import (
    THEMES,
    clean_html,
    get_active_theme_name,
    get_theme_tokens,
    icon,
    inject_theme_css,
    render_chatbot_fab,
    render_nav_bar,
)
from utils.calculations import ACTIVITY_FACTORS, bmi, bmi_category, calorie_goal, ffmi, ffmi_category

st.set_page_config(
    page_title="Profile — HTN",
    page_icon="HTN",
    layout="wide",
    initial_sidebar_state="collapsed",
)
init_db()
user = get_or_create_local_user()
user_id = user["id"]

if "theme_pref" not in st.session_state or not st.session_state.theme_pref:
    st.session_state.theme_pref = user.get("theme_pref") or "Original"

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
.pf-container {
    width: 100%;
    max-width: 1000px;
    margin: 0 auto;
    box-sizing: border-box;
    padding: 0 !important;
}

/* ── Aligned Profile Header ── */
.pf-header-card {
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 18px;
    padding: 14px 18px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    box-sizing: border-box;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
}
.pf-header-left {
    display: flex;
    align-items: center;
    gap: 14px;
    min-width: 0;
    flex: 1;
}
.pf-avatar-box {
    width: 70px;
    height: 70px;
    min-width: 70px;
    border-radius: 50%;
    border: 2px solid var(--accent);
    background: linear-gradient(160deg, #1e2a14, #111);
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    flex-shrink: 0;
    box-shadow: 0 0 16px var(--accent-glow);
}
.pf-avatar-box img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 50%;
}
.pf-header-info { 
    display: flex;
    flex-direction: column;
    min-width: 0;
}
.pf-name { 
    font-size: clamp(20px, 3.5vw, 25px); 
    font-weight: 800; 
    color: var(--text); 
    line-height: 1.15;
    margin-bottom: 2px; 
}
.pf-handle { 
    font-size: 12.5px; 
    font-weight: 600; 
    color: var(--text-dim); 
    margin-bottom: 4px; 
}
.pf-bio {
    font-size: 12.5px;
    color: #d6d9d6;
    line-height: 1.4;
    margin-top: 2px;
    word-break: break-word;
}
.pf-bio-empty {
    font-size: 12px;
    color: var(--text-dim);
    font-style: italic;
}

.st-key-edit_profile_toggle button {
    background: var(--accent-dim) !important;
    border: 1px solid var(--accent) !important;
    color: var(--accent) !important;
    box-shadow: 0 0 12px var(--accent-glow) !important;
    font-weight: 700 !important;
    font-size: 12.5px !important;
    border-radius: 12px !important;
    padding: 6px 16px !important;
    min-height: 35px !important;
    white-space: nowrap !important;
}
.st-key-edit_profile_toggle button:hover {
    background: var(--accent) !important;
    color: #0a0a0a !important;
}

/* Edit Card Container */
.pf-edit-card {
    background: var(--card);
    border: 1px solid var(--accent-glow);
    border-radius: 16px;
    padding: 16px 18px;
    margin-bottom: 18px;
    box-sizing: border-box;
}

/* ── Replace default 200MB text with 10MB in file uploader ── */
div[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] small,
div[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] > *:not(button):not([data-testid*="Button"]) {
    font-size: 0 !important;
    line-height: 0 !important;
}
div[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] small::after,
div[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] > *:not(button):not([data-testid*="Button"])::after {
    content: "10MB per file • PNG, JPG, WEBP" !important;
    font-size: 13px !important;
    line-height: 1.4 !important;
    color: var(--text-dim) !important;
}

/* Auto-fitting stats and metric rows */
.pf-stats-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 150px), 1fr));
    gap: 10px;
    margin-bottom: 16px;
    width: 100%;
}
.pf-stat-card {
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 16px;
    padding: 11px 13px;
    display: flex;
    flex-direction: column;
}
.pf-stat-icon { margin-bottom: 5px; }
.pf-stat-value { font-size: clamp(19px, 3.2vw, 22px); font-weight: 800; color: var(--accent); line-height: 1; margin-bottom: 2px; }
.pf-stat-unit { font-size: 11px; color: var(--text-dim); }
.pf-stat-label { font-size: 11px; color: var(--text-dim); line-height: 1.3; }

.pf-section-title { font-size: clamp(17px, 2.8vw, 20px); font-weight: 800; color: var(--text); margin: 18px 0 10px; }

.pf-metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 150px), 1fr));
    gap: 10px;
    margin-bottom: 10px;
    width: 100%;
}
.pf-metric {
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 16px;
    padding: 12px 14px;
}
.pf-metric-number { font-size: clamp(19px, 3.2vw, 22px); font-weight: 800; color: var(--accent); line-height: 1; }
.pf-metric-label { font-size: 11px; color: var(--text-dim); margin-top: 4px; }

/* Buttons & Actions */
.st-key-save_profile button {
    background: var(--accent) !important;
    color: #0a0a0a !important;
    border-radius: 12px !important;
    font-weight: 800 !important;
}
.st-key-delete_account button {
    background: transparent !important;
    color: #ff4b4b !important;
    border: 1px solid #ff4b4b !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
}
.st-key-logout_account button {
    background: transparent !important;
    color: var(--accent) !important;
    border: 1px solid var(--accent) !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
}

/* Minimal-Morphism Card for Radial Chart */
.pf-radial-container {
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 18px;
    padding: 18px 14px 20px 14px;
    margin: 6px 0 16px 0;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 100%;
    box-shadow: 0 14px 36px rgba(0, 0, 0, 0.45);
}

.pf-radial-svg-box {
    width: 100%;
    max-width: 440px;
    margin: 0 auto;
    display: flex;
    justify-content: center;
}

@media (max-width: 640px) {
    .block-container,
    div[data-testid="stMain"] .block-container,
    section[data-testid="stMain"] .block-container { 
        padding: 8px 12px 96px 12px !important; 
        box-sizing: border-box !important;
    }
    .pf-container { padding: 0 !important; }
    .pf-header-card { flex-direction: column; align-items: flex-start; padding: 12px 14px; gap: 10px; margin-bottom: 14px !important; }
    .pf-avatar-box { width: 50px; height: 50px; min-width: 50px; }
    .pf-name { font-size: 20px !important; }
    .st-key-edit_profile_toggle button { width: 100% !important; }
    .pf-stat-card { padding: 10px 12px; }
    .pf-radial-container { padding: 12px 10px; }
}
"""
inject_theme_css(PAGE_CSS)
render_chatbot_fab()
render_nav_bar(active="profile")

if "edit_identity_open" not in st.session_state:
    st.session_state.edit_identity_open = False
if "edit_profile_open" not in st.session_state:
    st.session_state.edit_profile_open = False

display_name = user.get("display_name") or "High Tier Normie"
handle = (user.get("handle") or user.get("username") or "htn_lifter").lstrip("@")
bio_text = user.get("bio") or ""
avatar_b64 = user.get("avatar_b64")

with st.container():
    # ── Aligned Profile Header ───────────────────────────────────────────────
    av_html = f'<img src="{avatar_b64}" />' if avatar_b64 else icon("user", color="#8f938f", size=32)
    bio_html = f'<div class="pf-bio">{bio_text}</div>' if bio_text else '<div class="pf-bio-empty">No bio added yet. Click edit to add your bio and avatar.</div>'

    st.markdown(
        clean_html(f"""
        <div class="pf-container">
            <div class="pf-header-card">
                <div class="pf-header-left">
                    <div class="pf-avatar-box">{av_html}</div>
                    <div class="pf-header-info">
                        <div class="pf-name">{display_name}</div>
                        <div class="pf-handle">@{handle}</div>
                        {bio_html}
                    </div>
                </div>
            </div>
        """),
        unsafe_allow_html=True,
    )

    if st.button("Edit Profile & Bio", key="edit_profile_toggle"):
        st.session_state.edit_identity_open = not st.session_state.edit_identity_open
        st.rerun()

    # ── Edit Identity, Bio, & Profile Picture Section ────────────────────────
    if st.session_state.edit_identity_open:
        st.markdown('<div class="pf-edit-card">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:17px;font-weight:800;color:var(--text);margin-bottom:14px;">Edit Profile & Avatar</div>', unsafe_allow_html=True)

        c_id1, c_id2 = st.columns(2, gap="small")
        with c_id1:
            new_display_name = st.text_input("Display name", value=display_name, key="edit_inp_display_name")
        with c_id2:
            new_handle = st.text_input("Handle", value=f"@{handle}", key="edit_inp_handle")

        new_bio = st.text_area(
            "Bio",
            value=bio_text,
            placeholder="Tell the HTN community about your lifting journey, PRs, or goals...",
            max_chars=250,
            key="edit_inp_bio",
        )

        st.markdown('<div style="font-size:14px;font-weight:700;color:var(--text);margin:16px 0 6px;">Profile Picture (Max 10MB)</div>', unsafe_allow_html=True)
        uploaded_avatar = st.file_uploader(
            "Upload new photo",
            type=["png", "jpg", "jpeg", "webp"],
            key="avatar_upload_input",
            help="File size must be 10MB or less.",
        )

        if uploaded_avatar is not None:
            if uploaded_avatar.size > 10 * 1024 * 1024:
                st.error("Uploaded image exceeds the 10MB limit. Please upload an image under 10MB.")
            else:
                st.image(uploaded_avatar, width=110, caption="New Selected Photo")

        remove_avatar_cb = False
        if avatar_b64:
            remove_avatar_cb = st.checkbox("Remove current profile picture", key="remove_avatar_cb")

        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        c_save1, c_save2 = st.columns(2, gap="small")
        with c_save1:
            if st.button("Save All Changes", type="primary", use_container_width=True, key="btn_save_all_profile"):
                clean_h = new_handle.strip().lstrip("@")
                if not clean_h:
                    st.error("Handle cannot be empty.")
                else:
                    avatar_to_persist = None
                    if remove_avatar_cb:
                        avatar_to_persist = "REMOVE"
                    elif uploaded_avatar is not None:
                        if uploaded_avatar.size <= 10 * 1024 * 1024:
                            try:
                                img = Image.open(uploaded_avatar).convert("RGB")
                                img = ImageOps.fit(img, (360, 360), Image.Resampling.LANCZOS)
                                buf = io.BytesIO()
                                img.save(buf, format="JPEG", quality=88)
                                avatar_to_persist = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
                            except Exception as err:
                                st.error(f"Could not process image: {err}")

                    update_profile(
                        user_id,
                        username=user.get("username") or clean_h,
                        display_name=new_display_name.strip() or "High Tier Normie",
                        handle=clean_h,
                        bio=new_bio,
                        avatar_b64=avatar_to_persist,
                        height_cm=float(user.get("height_cm") or 0.0),
                        bodyweight_kg=float(user.get("bodyweight_kg") or 0.0),
                        body_fat_pct=float(user.get("body_fat_pct")) if user.get("body_fat_pct") is not None else None,
                        age=int(user.get("age")) if user.get("age") is not None else None,
                        sex=user.get("sex"),
                        activity_level=user.get("activity_level"),
                        calorie_goal=user.get("calorie_goal"),
                    )
                    st.session_state.edit_identity_open = False
                    st.success("Profile saved.")
                    st.rerun()

        with c_save2:
            if st.button("Cancel", use_container_width=True, key="btn_cancel_edit_profile"):
                st.session_state.edit_identity_open = False
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # ── Unit settings ────────────────────────────────────────────────────────
    weight_unit = st.session_state.get("weight_unit", "kg")
    height_unit = st.session_state.get("height_unit", "cm")

    if "weight_unit_initialized" not in st.session_state:
        saved_unit = user.get("unit_pref") or "metric"
        if saved_unit == "imperial":
            st.session_state.weight_unit = "lbs"
            st.session_state.height_unit = "in"
        else:
            st.session_state.weight_unit = "kg"
            st.session_state.height_unit = "cm"
        st.session_state.weight_unit_initialized = True

    weight_unit = st.session_state.weight_unit
    height_unit = st.session_state.height_unit

    def kg_to_lbs(value):
        return float(value) * 2.2046226218

    def lbs_to_kg(value):
        return float(value) / 2.2046226218

    def cm_to_in(value):
        return float(value) / 2.54

    def in_to_cm(value):
        return float(value) * 2.54

    raw_bw = user.get("bodyweight_kg")
    has_bw = raw_bw is not None and float(raw_bw) > 0
    raw_ht = user.get("height_cm")
    has_ht = raw_ht is not None and float(raw_ht) > 0

    bodyweight_kg = float(raw_bw) if has_bw else 0.0
    height_cm = float(raw_ht) if has_ht else 0.0
    bodyfat = user.get("body_fat_pct")

    bodyweight = kg_to_lbs(bodyweight_kg) if weight_unit == "lbs" else bodyweight_kg
    height = cm_to_in(height_cm) if height_unit == "in" else height_cm
    bmi_value = bmi(bodyweight_kg, height_cm) if bodyweight_kg > 0 and height_cm > 0 else None
    ffmi_value = ffmi(bodyweight_kg, height_cm, float(bodyfat)) if bodyweight_kg > 0 and height_cm > 0 and bodyfat is not None else None

    disp_pf_bw = f"{bodyweight:.1f}" if has_bw else "—"
    disp_pf_bw_label = f"Bodyweight ({weight_unit})" if has_bw else "Bodyweight (Not set)"
    disp_pf_ht = f"{height:.1f}" if has_ht else "—"
    disp_pf_ht_label = f"Height ({height_unit})" if has_ht else "Height (Not set)"

    def bodyfat_status(percent, sex):
        if percent is None:
            return "Body-fat percentage not set"
        pct = float(percent)
        if sex == "Female":
            if pct <= 16: return "Shredded"
            if pct <= 20: return "Peeled"
            if pct <= 24: return "Lean"
            if pct <= 29: return "Fit"
            if pct <= 35: return "Carries some fat"
            return "Higher body fat"
        if pct <= 8: return "Shredded"
        if pct <= 10: return "Peeled"
        if pct <= 14: return "Lean"
        if pct <= 18: return "Fit"
        if pct <= 24: return "Carries some fat"
        return "Higher body fat"

    # ── Stats Overview ─────────────────────────────────────────────────────────
    st.markdown(clean_html(f"""
    <div class="pf-stats-row">
      <div class="pf-stat-card">
        <div class="pf-stat-icon">{icon('scale', size=18)}</div>
        <div class="pf-stat-value">{disp_pf_bw}</div>
        <div class="pf-stat-label">{disp_pf_bw_label}</div>
      </div>
      <div class="pf-stat-card">
        <div class="pf-stat-icon">{icon('trend', size=18)}</div>
        <div class="pf-stat-value">{disp_pf_ht}</div>
        <div class="pf-stat-label">{disp_pf_ht_label}</div>
      </div>
      <div class="pf-stat-card">
        <div class="pf-stat-icon">{icon('dumbbell', size=18)}</div>
        <div class="pf-stat-value">{f"{bmi_value:.1f}" if bmi_value is not None else "—"}</div>
        <div class="pf-stat-label">BMI ({bmi_category(bmi_value) if bmi_value else '—'})</div>
      </div>
    </div>
    """), unsafe_allow_html=True)

    # ── Body Metrics ──────────────────────────────────────────────────────────
    st.markdown('<div class="pf-section-title">Body Metrics</div>', unsafe_allow_html=True)
    st.markdown(clean_html(f"""
    <div class="pf-metric-grid">
      <div class="pf-metric">
        <div class="pf-metric-number">{f'{bmi_value:.1f}' if bmi_value else '—'}</div>
        <div class="pf-metric-label">BMI</div>
      </div>
      <div class="pf-metric">
        <div class="pf-metric-number">{f'{ffmi_value:.1f}' if ffmi_value else '—'}</div>
        <div class="pf-metric-label">FFMI</div>
      </div>
      <div class="pf-metric">
        <div class="pf-metric-number">{f'{user.get("calorie_goal"):,}' if user.get("calorie_goal") else '—'}</div>
        <div class="pf-metric-label">Target kcal/day</div>
      </div>
    </div>
    """), unsafe_allow_html=True)

    if ffmi_value:
        st.caption(f"FFMI: {ffmi_category(ffmi_value)}")
    else:
        st.caption("FFMI: Enter body-fat percentage to calculate.")

    if bodyfat is not None:
        st.caption(f"Body fat: {float(bodyfat):.1f}% · {bodyfat_status(bodyfat, user.get('sex'))}")
    else:
        st.caption("Body fat: Not set · Add an approximate value to unlock FFMI.")

    if st.button("Edit body stats & calculators", key="edit_profile_btn", use_container_width=True):
        st.session_state.edit_profile_open = not st.session_state.edit_profile_open
        st.rerun()

    if st.session_state.edit_profile_open:
        with st.form("profile_form"):
            username = st.text_input("Username / handle", value=(user.get("handle") or user.get("username") or "htn_lifter").lstrip("@"))
            c1, c2 = st.columns(2)
            with c1:
                weight_label = "Bodyweight (lbs)" if weight_unit == "lbs" else "Bodyweight (kg)"
                height_label = "Height (in)" if height_unit == "in" else "Height (cm)"
                p_weight = st.number_input(
                    weight_label,
                    min_value=44.0 if weight_unit == "lbs" else 20.0,
                    max_value=660.0 if weight_unit == "lbs" else 300.0,
                    value=bodyweight or (154.3 if weight_unit == "lbs" else 70.0),
                    step=0.1,
                )
                p_height = st.number_input(
                    height_label,
                    min_value=39.4 if height_unit == "in" else 100.0,
                    max_value=98.4 if height_unit == "in" else 250.0,
                    value=height or (66.9 if height_unit == "in" else 170.0),
                    step=0.1 if height_unit == "in" else 0.5,
                )
                p_bodyfat = st.number_input("Body fat (%)", min_value=1.0, max_value=60.0, value=float(bodyfat or 20.0), step=0.5)
            with c2:
                p_age = st.number_input("Age", min_value=13, max_value=100, value=int(user.get("age") or 25), step=1)
                p_sex = st.selectbox("Sex", ["Male", "Female"], index=0 if user.get("sex") != "Female" else 1)
                p_activity = st.selectbox("Activity", list(ACTIVITY_FACTORS.keys()), index=list(ACTIVITY_FACTORS.keys()).index(user.get("activity_level")) if user.get("activity_level") in ACTIVITY_FACTORS else 2)
            p_goal = st.selectbox("Calorie goal", ["Gain muscle", "Maintain", "Lose weight"])
            save = st.form_submit_button("Save Body Stats", key="save_profile", use_container_width=True)
            if save:
                save_weight_kg = lbs_to_kg(p_weight) if weight_unit == "lbs" else p_weight
                save_height_cm = in_to_cm(p_height) if height_unit == "in" else p_height
                calories = calorie_goal(save_weight_kg, save_height_cm, p_age, p_sex, p_activity, p_goal)
                update_profile(
                    user_id,
                    username=username,
                    display_name=display_name,
                    handle=username,
                    height_cm=save_height_cm,
                    bodyweight_kg=save_weight_kg,
                    body_fat_pct=p_bodyfat,
                    age=p_age,
                    sex=p_sex,
                    activity_level=p_activity,
                    calorie_goal=calories,
                )
                st.session_state.edit_profile_open = False
                st.success("Body stats saved.")
                st.rerun()

    # ── Circular Muscle Group Distribution Graph ──────────────────────────────
    st.markdown('<div class="pf-section-title">Muscle Volume Distribution</div>', unsafe_allow_html=True)

    time_options = {
        "Day (Today)": date.today().isoformat(),
        "Week (Last 7 Days)": (date.today() - timedelta(days=7)).isoformat(),
        "Month (Last 30 Days)": (date.today() - timedelta(days=30)).isoformat(),
        "Year (Last 365 Days)": (date.today() - timedelta(days=365)).isoformat(),
        "All Time": None,
    }

    c_time1, c_time2 = st.columns([2, 1], gap="small")
    with c_time1:
        st.markdown('<div style="font-size:13px; color:var(--text-dim); margin-top:8px;">Radial breakdown of sets performed across muscle groups.</div>', unsafe_allow_html=True)
    with c_time2:
        chosen_time_label = st.selectbox("Timeframe", list(time_options.keys()), index=2, key="muscle_tf_select")

    tf_start_date = time_options[chosen_time_label]
    muscles_data = get_muscle_group_distribution(user_id, start_date=tf_start_date)

    muscle_counts = {m["muscle_group"].title(): m["total_sets"] for m in muscles_data}
    total_volume_sets = sum(muscle_counts.values())

    standard_groups = [
        "Chest", "Shoulders", "Biceps", "Triceps", "Back",
        "Core", "Quads", "Hamstrings", "Glutes", "Calves", "Cardio"
    ]
    for m in muscle_counts:
        if m not in standard_groups:
            standard_groups.append(m)

    max_sets = max(muscle_counts.values()) if muscle_counts else 1

    # ── Radial Barplot SVG Generator (Clean Dynamic Theme Alignment) ─────────────────
    active_tokens = get_theme_tokens()
    t_accent = active_tokens["accent"]
    t_accent_sec = active_tokens["accent_secondary"]
    t_accent_glow = active_tokens["accent_glow"]
    t_accent_dim = active_tokens["accent_dim"]

    cx, cy = 280, 280
    r_inner = 98
    max_bar_h = 75
    n_items = len(standard_groups)

    svg_parts = []
    svg_parts.append(f"""
      <defs>
        <linearGradient id="htnBarGrad" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stop-color="{t_accent_sec}"/>
          <stop offset="100%" stop-color="{t_accent}"/>
        </linearGradient>
        <filter id="htnNeonGlow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="3.5" result="blur"/>
          <feComposite in="SourceGraphic" in2="blur" operator="over"/>
        </filter>
      </defs>
    """)

    svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r_inner}" fill="none" stroke="{t_accent_dim}" stroke-width="1.8" />')
    svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r_inner + max_bar_h * 0.5:.1f}" fill="none" stroke="rgba(255, 255, 255, 0.05)" stroke-dasharray="3,4" stroke-width="1" />')
    svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r_inner + max_bar_h:.1f}" fill="none" stroke="rgba(255, 255, 255, 0.05)" stroke-dasharray="3,4" stroke-width="1" />')

    for idx, grp in enumerate(standard_groups):
        sets_val = muscle_counts.get(grp, 0)
        ang_deg = idx * (360.0 / n_items)
        phi_rad = math.radians(ang_deg - 90)

        if sets_val > 0:
            bar_h = 16.0 + (sets_val / max_sets) * max_bar_h
            bar_fill = "url(#htnBarGrad)"
            bar_filter = 'filter="url(#htnNeonGlow)"'
            label_color = t_accent
            label_weight = "800"
            bar_stroke = t_accent
        else:
            bar_h = 8.0
            bar_fill = "#161b15"
            bar_filter = ""
            label_color = "#636d62"
            label_weight = "600"
            bar_stroke = "rgba(255, 255, 255, 0.06)"

        r_outer = r_inner + bar_h
        bar_w = 17.0

        svg_parts.append(
            f'<rect x="-{bar_w/2:.2f}" y="-{r_outer:.2f}" width="{bar_w:.2f}" height="{bar_h:.2f}" rx="3.5" ry="3.5" '
            f'transform="translate({cx}, {cy}) rotate({ang_deg:.2f})" '
            f'fill="{bar_fill}" stroke="{bar_stroke}" stroke-width="0.8" {bar_filter} />'
        )

        r_label = r_outer + 14.0
        lx = cx + r_label * math.cos(phi_rad)
        ly = cy + r_label * math.sin(phi_rad)
        label_text = f"{grp} ({sets_val})" if sets_val > 0 else f"{grp}"

        if ang_deg <= 180.0:
            rot_text = ang_deg - 90.0
            anchor = "start"
        else:
            rot_text = ang_deg + 90.0
            anchor = "end"

        svg_parts.append(
            f'<text x="{lx:.2f}" y="{ly:.2f}" text-anchor="{anchor}" '
            f'transform="rotate({rot_text:.2f}, {lx:.2f}, {ly:.2f})" '
            f'fill="{label_color}" font-size="11.5" font-weight="{label_weight}" '
            f'font-family="Inter, sans-serif" alignment-baseline="middle">{label_text}</text>'
        )

    svg_parts.append(
        f'<text x="{cx}" y="{cy - 10}" text-anchor="middle" fill="#f5f5f5" font-size="36" font-weight="900" font-family="Inter, sans-serif">{total_volume_sets}</text>'
        f'<text x="{cx}" y="{cy + 14}" text-anchor="middle" fill="{t_accent}" font-size="11" font-weight="800" font-family="Inter, sans-serif" letter-spacing="2">TOTAL SETS</text>'
        f'<text x="{cx}" y="{cy + 32}" text-anchor="middle" fill="#8f938f" font-size="10" font-weight="600" font-family="Inter, sans-serif">{chosen_time_label.split()[0].upper()}</text>'
    )

    svg_content = "".join(svg_parts)
    st.markdown(
        f'<div class="pf-radial-container"><div class="pf-radial-svg-box"><svg viewBox="0 0 560 560" width="100%" height="auto" style="overflow:visible; display:block;">{svg_content}</svg></div></div>',
        unsafe_allow_html=True,
    )

    # ── Unit Preferences ──────────────────────────────────────────────────────
    st.markdown('<div class="pf-section-title">Training Preferences</div>', unsafe_allow_html=True)
    with st.container(key="unit_setting"):
        u1, u2 = st.columns(2)
        with u1:
            selected_weight_unit = st.selectbox("Weight Unit", ["kg", "lbs"], index=0 if weight_unit == "kg" else 1, key="profile_weight_unit")
        with u2:
            selected_height_unit = st.selectbox("Height Unit", ["cm", "in"], index=0 if height_unit == "cm" else 1, key="profile_height_unit")

        if selected_weight_unit != weight_unit:
            st.session_state.weight_unit = selected_weight_unit
            unit_map = {"kg": "metric", "lbs": "imperial"}
            update_unit_pref(user_id, unit_map[selected_weight_unit])
            st.rerun()

        if selected_height_unit != height_unit:
            st.session_state.height_unit = selected_height_unit
            st.rerun()

    # ── Color Theme & Aesthetic ───────────────────────────────────────────────
    st.markdown('<div class="pf-section-title">Color Theme & Aesthetic</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:13px; color:var(--text-dim); margin-bottom:14px; line-height:1.45;">'
        'Switch palettes on the fly. All themes preserve our signature neon glow halo, minimal-morphism dark glass cards, and high-contrast typography.'
        '</div>',
        unsafe_allow_html=True,
    )

    current_theme = get_active_theme_name()
    theme_items = list(THEMES.items())

    t_cols = st.columns(2, gap="medium")
    for idx, (t_key, t_info) in enumerate(theme_items):
        target_col = t_cols[idx % 2]
        with target_col:
            is_active = (t_key == current_theme)
            card_border = "var(--accent)" if is_active else "var(--card-border)"
            glow_box = f"box-shadow: 0 0 18px {t_info['accent_glow']};" if is_active else "box-shadow: 0 4px 14px rgba(0,0,0,0.35);"
            badge_html = f'<span class="htn-badge" style="background:{t_info["accent_dim"]}; color:{t_info["accent"]}; border-color:{t_info["accent"]}; font-size:10px; padding:3px 9px;">ACTIVE</span>' if is_active else ""

            swatches_html = "".join(
                f'<span style="display:inline-block; width:19px; height:19px; border-radius:50%; background:{hex_c}; border:1.5px solid rgba(255,255,255,0.18); box-shadow:0 2px 6px rgba(0,0,0,0.5);"></span>'
                for hex_c in t_info["swatches"]
            )

            st.markdown(
                clean_html(f"""
                <div style="background:{t_info['card']}; border:1.5px solid {card_border}; border-radius:16px; padding:12px 15px; margin-bottom:10px; {glow_box}">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <span style="font-size:14.5px; font-weight:800; color:#f5f5f5; letter-spacing:-0.2px;">{t_info['label']}</span>
                        {badge_html}
                    </div>
                    <div style="font-size:11px; color:#8f938f; margin-bottom:10px; line-height:1.35;">
                        {t_info['subtitle']}
                    </div>
                    <div style="display:flex; align-items:center; gap:7px; margin-bottom:10px;">
                        {swatches_html}
                    </div>
                </div>
                """),
                unsafe_allow_html=True,
            )

            btn_label = f"Active ({t_key})" if is_active else f"Apply {t_key}"
            btn_key = f"apply_theme_{t_key.lower().replace(' ', '_')}"
            if st.button(btn_label, key=btn_key, disabled=is_active, use_container_width=True, type="primary" if is_active else "secondary"):
                update_theme_pref(user_id, t_key)
                st.session_state.theme_pref = t_key
                if "user" in st.session_state and isinstance(st.session_state.user, dict):
                    st.session_state.user["theme_pref"] = t_key
                st.rerun()

    # ── Data & Account ────────────────────────────────────────────────────────
    st.markdown('<div class="pf-section-title">Data & Account</div>', unsafe_allow_html=True)

    # Backup Database
    import os
    db_path = os.path.join(os.path.dirname(__file__), "..", "db", "htn.db")
    if os.path.exists(db_path):
        with open(db_path, "rb") as f:
            st.download_button("Backup Database (htn.db)", f, file_name="htn_backup.db", mime="application/octet-stream", use_container_width=True)
    
    # Restore Database
    uploaded_db = st.file_uploader("Restore Database", type=["db"], help="Upload an htn.db backup file to overwrite your current data.")
    if uploaded_db is not None:
        if st.button("Confirm Restore", type="primary", use_container_width=True):
            with open(db_path, "wb") as f:
                f.write(uploaded_db.getbuffer())
            st.success("Database restored successfully! Please log in again.")
            st.session_state.clear()
            st.rerun()

    if st.button("Log out", key="logout_account", use_container_width=True):
        log_out()

    if "delete_confirm" not in st.session_state:
        st.session_state.delete_confirm = False
    if st.button("Delete Account", key="delete_account", use_container_width=True):
        st.session_state.delete_confirm = not st.session_state.delete_confirm
    if st.session_state.delete_confirm:
        st.warning("This permanently removes your HTN profile, routines, exercises, and workout logs.")
        if st.button("Yes, permanently delete everything", key="delete_account_confirm", use_container_width=True):
            delete_account(user_id)
            st.session_state.clear()
            st.success("Account deleted.")
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


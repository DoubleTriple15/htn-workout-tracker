import streamlit as st
from auth import (
    authenticate_user,
    log_in,
    register_auth_user,
    restore_login,
    validate_password,
    validate_username,
)
from db.database import (
    add_builtin_periodization_exercise,
    create_builtin_exercise,
    create_builtin_routine,
    create_periodization_program,
    delete_account,
    delete_builtin_exercise,
    delete_builtin_periodization_exercise,
    delete_builtin_routine,
    delete_periodization_program,
    duplicate_periodization_program,
    duplicate_routine,
    get_all_periodization_programs,
    get_all_registered_users,
    get_builtin_exercises,
    get_builtin_periodization_program,
    get_builtin_routine_exercises,
    get_builtin_routines,
    get_connection,
    init_db,
    reset_builtin_periodization_to_default,
    update_builtin_exercise,
    update_builtin_periodization_day,
    update_builtin_periodization_exercise,
    update_builtin_routine,
)
from htn_theme import clean_html, get_active_theme_name, icon, inject_theme_css

st.set_page_config(
    page_title="HTN — Login",
    page_icon="HTN",
    layout="wide",
    initial_sidebar_state="collapsed",
)
init_db()
if "theme_pref" not in st.session_state or not st.session_state.theme_pref:
    st.session_state.theme_pref = get_active_theme_name()

# If session already valid, redirect immediately to Home
if restore_login():
    st.switch_page("Home.py")

PAGE_CSS = """
#MainMenu,header,footer{visibility:hidden}
.block-container{max-width:100%!important;padding:0!important}
.st-key-auth_card{
    width:min(420px,calc(100vw - 32px));
    max-width:420px!important;
    margin:0 auto!important;
    padding:26px 28px 24px!important;
    box-sizing:border-box;
    background:var(--card);
    border:1px solid var(--card-border);
    border-radius:22px;
    box-shadow:0 18px 55px rgba(0,0,0,.35)
}
.st-key-admin_card{
    width:min(640px,calc(100vw - 32px));
    max-width:640px!important;
    margin:0 auto!important;
    padding:26px 28px 24px!important;
    box-sizing:border-box;
    background:var(--card);
    border:1px solid var(--accent);
    border-radius:22px;
    box-shadow:0 18px 55px rgba(0,0,0,.5), 0 0 16px var(--accent-glow);
}
.auth-brand{display:flex;align-items:center;gap:11px;margin-bottom:4px}
.auth-icon{
    width:42px;
    height:42px;
    display:flex;
    align-items:center;
    justify-content:center;
    border:1px solid var(--accent);
    border-radius:13px;
    background:#151a12
}
.auth-title{color:var(--text);font-size:26px;font-weight:800}
.auth-subtitle{color:var(--text-dim);font-size:12px;margin-bottom:20px}
.auth-form-title{color:var(--text);font-size:20px;font-weight:800;margin:0 0 3px}
.auth-form-subtitle{color:var(--text-dim);font-size:12px;margin-bottom:14px}
.auth-help{color:var(--text-dim);font-size:10px;line-height:1.35;margin:-2px 0 5px}
.st-key-auth_card [data-testid="stTextInput"],
.st-key-auth_card [data-testid="stTextInputRootElement"],
.st-key-admin_card [data-testid="stTextInput"],
.st-key-auth_card input,
.st-key-admin_card input{width:100%!important;box-sizing:border-box!important}
.st-key-auth_submit button{
    background:var(--accent)!important;
    color:#0a0a0a!important;
    border-radius:11px!important;
    min-height:42px!important;
    font-weight:800!important
}
.st-key-auth_toggle button,
.st-key-admin_toggle button{
    background:transparent!important;
    border:0!important;
    color:var(--accent)!important;
    font-weight:700!important;
    min-height:34px!important
}
.st-key-admin_toggle button{
    color:var(--text-dim)!important;
    font-size:11.5px!important
}
.st-key-admin_toggle button:hover{
    color:var(--accent)!important
}

/* Admin Card Rows */
.admin-item-row {
    background: rgba(22, 26, 22, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 12px 14px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.admin-item-info {
    display: flex;
    flex-direction: column;
}
.admin-item-name {
    font-weight: 800;
    font-size: 14px;
    color: #f5f5f5;
}
.admin-item-meta {
    font-size: 11px;
    color: var(--text-dim);
    margin-top: 2px;
}
div[class*="st-key-del_admin_btn_"] button {
    background: rgba(255, 75, 75, 0.12) !important;
    border: 1px solid #ff4b4b !important;
    color: #ff4b4b !important;
    font-size: 11px !important;
    font-weight: 800 !important;
    border-radius: 10px !important;
    padding: 5px 12px !important;
    min-height: 32px !important;
}
div[class*="st-key-del_admin_btn_"] button:hover {
    background: #ff4b4b !important;
    color: #ffffff !important;
}

@media(max-width:420px){
    .st-key-auth_card, .st-key-admin_card{width:calc(100vw - 20px);padding:22px 20px 20px!important}
}
"""
inject_theme_css(PAGE_CSS)

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

# -----------------------------------------------------------------------------
# ADMIN PORTAL
# -----------------------------------------------------------------------------
if st.session_state.auth_mode == "admin":
    with st.container(key="admin_card"):
        st.markdown(
            f'<div class="auth-brand"><div class="auth-icon">{icon("dumbbell", size=23)}</div><div class="auth-title">HTN Admin</div></div><div class="auth-subtitle">Administrative Management Portal</div>',
            unsafe_allow_html=True,
        )

        if not st.session_state.admin_authenticated:
            st.markdown('<div class="auth-form-title">Enter Admin Password</div><div class="auth-form-subtitle">Restricted to HTN administrators.</div>', unsafe_allow_html=True)
            admin_pwd = st.text_input("Password", type="password", key="admin_pwd_field", placeholder="Enter admin password")
            
            if st.button("Unlock Admin Panel", key="auth_submit", use_container_width=True):
                if admin_pwd == "enter password":
                    st.session_state.admin_authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect admin password.")

            if st.button("← Back to Login", key="auth_toggle", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.session_state.admin_authenticated = False
                st.rerun()
        else:
            admin_tab_users, admin_tab_ex, admin_tab_routines, admin_tab_periodization = st.tabs([
                "Registered Users",
                "Built-in Exercises",
                "Built-in Routines",
                "Built-in Periodization",
            ])

            # ── Tab 1: Registered Users ──────────────────────────────────────
            with admin_tab_users:
                st.markdown('<div style="font-size:15px;font-weight:800;color:var(--text);margin:10px 0 4px;">Registered Lifters</div>', unsafe_allow_html=True)
                users = get_all_registered_users()
                if not users:
                    st.info("No registered users found.")
                else:
                    for u in users:
                        uid = u["id"]
                        uname = u["username"]
                        dname = u.get("display_name") or uname
                        sessions = u.get("session_count", 0)

                        c_user, c_del = st.columns([3, 1], gap="small")
                        with c_user:
                            st.markdown(
                                clean_html(f"""
                                <div class="admin-item-row">
                                    <div class="admin-item-info">
                                        <div class="admin-item-name">{dname} (@{uname})</div>
                                        <div class="admin-item-meta">User ID: {uid} · {sessions} workout session(s)</div>
                                    </div>
                                </div>
                                """),
                                unsafe_allow_html=True,
                            )
                        with c_del:
                            st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)
                            with st.container(key=f"del_admin_btn_user_{uid}"):
                                if st.button("Remove", key=f"btn_remove_user_{uid}", use_container_width=True):
                                    delete_account(uid)
                                    st.success(f"User '{uname}' removed.")
                                    st.rerun()

            # ── Tab 2: Built-in Exercises ────────────────────────────────────
            with admin_tab_ex:
                st.markdown('<div style="font-size:15px;font-weight:800;color:var(--text);margin:10px 0 4px;">Add New Built-in Exercise</div>', unsafe_allow_html=True)
                with st.form("admin_create_exercise_form", clear_on_submit=True):
                    ex_name = st.text_input("Exercise name", placeholder="e.g. Incline Cable Fly")
                    c_m1, c_m2 = st.columns(2)
                    with c_m1:
                        ex_muscle = st.selectbox("Muscle group", [
                            "Chest", "Back", "Shoulders", "Biceps", "Triceps", "Legs",
                            "Quads", "Hamstrings", "Glutes", "Calves", "Core", "Cardio", "Full Body", "Other"
                        ])
                    with c_m2:
                        ex_type_label = st.selectbox("Tracking Type", [
                            "Weights + Reps", "Time", "Bodyweight", "Weighted Calisthenics"
                        ])
                    ex_equip = st.text_input("Equipment", placeholder="e.g. Cable, Barbell, Dumbbell")
                    if st.form_submit_button("Add Built-in Exercise", use_container_width=True):
                        type_map = {
                            "Weights + Reps": "weights_reps",
                            "Time": "time",
                            "Bodyweight": "bodyweight",
                            "Weighted Calisthenics": "weighted_calisthenics",
                        }
                        res = create_builtin_exercise(ex_name, ex_muscle, type_map[ex_type_label], ex_equip)
                        if res["success"]:
                            st.success(f"Built-in exercise '{ex_name}' added.")
                            st.rerun()
                        else:
                            st.error(res["error"])

                st.markdown('<div style="font-size:15px;font-weight:800;color:var(--text);margin:16px 0 6px;">Manage Built-in Exercises</div>', unsafe_allow_html=True)
                b_exercises = get_builtin_exercises()
                if not b_exercises:
                    st.info("No built-in exercises found.")
                else:
                    for be in b_exercises:
                        eid = be["id"]
                        with st.expander(f"{be['name']} ({be['muscle_group']} · {be['exercise_type']})", expanded=False):
                            with st.form(f"edit_b_ex_{eid}"):
                                up_name = st.text_input("Name", value=be["name"])
                                up_muscle = st.selectbox("Muscle", [
                                    "Chest", "Back", "Shoulders", "Biceps", "Triceps", "Legs",
                                    "Quads", "Hamstrings", "Glutes", "Calves", "Core", "Cardio", "Full Body", "Other"
                                ], index=[
                                    "Chest", "Back", "Shoulders", "Biceps", "Triceps", "Legs",
                                    "Quads", "Hamstrings", "Glutes", "Calves", "Core", "Cardio", "Full Body", "Other"
                                ].index(be["muscle_group"]) if be["muscle_group"] in [
                                    "Chest", "Back", "Shoulders", "Biceps", "Triceps", "Legs",
                                    "Quads", "Hamstrings", "Glutes", "Calves", "Core", "Cardio", "Full Body", "Other"
                                ] else 0)
                                up_type = st.selectbox("Tracking Type", ["weights_reps", "time", "bodyweight", "weighted_calisthenics"], index=["weights_reps", "time", "bodyweight", "weighted_calisthenics"].index(be["exercise_type"]) if be["exercise_type"] in ["weights_reps", "time", "bodyweight", "weighted_calisthenics"] else 0)
                                up_equip = st.text_input("Equipment", value=be.get("equipment") or "")
                                c_save, c_del = st.columns(2)
                                with c_save:
                                    if st.form_submit_button("Save Changes", use_container_width=True):
                                        res = update_builtin_exercise(eid, up_name, up_muscle, up_type, up_equip)
                                        if res["success"]:
                                            st.success("Exercise updated.")
                                            st.rerun()
                                        else:
                                            st.error(res["error"])
                            with st.container(key=f"del_admin_btn_ex_{eid}"):
                                if st.button("Delete Exercise", key=f"btn_remove_b_ex_{eid}", use_container_width=True):
                                    delete_builtin_exercise(eid)
                                    st.success(f"Built-in exercise '{be['name']}' removed.")
                                    st.rerun()

            # ── Tab 3: Built-in Starter Routines ────────────────────────────
            with admin_tab_routines:
                st.markdown('<div style="font-size:15px;font-weight:800;color:var(--text);margin:10px 0 4px;">Create Built-in Routine</div>', unsafe_allow_html=True)
                all_b_exs = get_builtin_exercises()
                ex_options = {f"{e['name']} ({e['muscle_group']})": e["id"] for e in all_b_exs}

                with st.form("admin_create_routine_form", clear_on_submit=True):
                    r_name = st.text_input("Routine Name", placeholder="e.g. Upper Body Hypertrophy")
                    selected_exs = st.multiselect("Select Exercises", list(ex_options.keys()))
                    if st.form_submit_button("Add Built-in Routine", use_container_width=True):
                        e_ids = [ex_options[s] for s in selected_exs]
                        res = create_builtin_routine(r_name, e_ids)
                        if res["success"]:
                            st.success(f"Built-in routine '{r_name}' added.")
                            st.rerun()
                        else:
                            st.error(res["error"])

                st.markdown('<div style="font-size:15px;font-weight:800;color:var(--text);margin:16px 0 6px;">Manage Built-in Routines</div>', unsafe_allow_html=True)
                b_routines = get_builtin_routines()
                if not b_routines:
                    st.info("No built-in routines found.")
                else:
                    for br in b_routines:
                        rid = br["id"]
                        ex_list = get_builtin_routine_exercises(rid)
                        ex_summary = ", ".join(e["name"] for e in ex_list) or "No exercises"

                        with st.expander(f"{br['name']} ({len(ex_list)} exercises)", expanded=False):
                            with st.form(f"edit_b_routine_{rid}"):
                                up_r_name = st.text_input("Routine Name", value=br["name"])
                                default_sel = [f"{e['name']} ({e['muscle_group']})" for e in ex_list if f"{e['name']} ({e['muscle_group']})" in ex_options]
                                up_sel_exs = st.multiselect("Exercises", list(ex_options.keys()), default=default_sel)
                                if st.form_submit_button("Save Routine Changes", use_container_width=True):
                                    new_ids = [ex_options[s] for s in up_sel_exs]
                                    res = update_builtin_routine(rid, up_r_name, new_ids)
                                    if res["success"]:
                                        st.success("Routine updated.")
                                        st.rerun()
                                    else:
                                        st.error(res["error"])

                            c_dup, c_del = st.columns(2)
                            with c_dup:
                                if st.button("Duplicate Routine", key=f"btn_dup_b_routine_{rid}", use_container_width=True):
                                    res = duplicate_routine(rid, 1) # Clones as template
                                    if res["success"]:
                                        st.success(f"Routine duplicated as '{res['name']}'.")
                                        st.rerun()
                                    else:
                                        st.error(res["error"])
                            with c_del:
                                with st.container(key=f"del_admin_btn_routine_{rid}"):
                                    if st.button("Delete Routine", key=f"btn_remove_b_routine_{rid}", use_container_width=True):
                                        delete_builtin_routine(rid)
                                        st.success(f"Built-in routine '{br['name']}' removed.")
                                        st.rerun()

            # ── Tab 4: Built-in Periodization Mesocycle ──────────────────────
            with admin_tab_periodization:
                st.markdown('<div style="font-size:15px;font-weight:800;color:var(--text);margin:10px 0 4px;">Periodization Program Management</div>', unsafe_allow_html=True)
                st.caption("Admin control: Manage multi-week periodization cycles, phases, days, exercises, targets, and roles.")

                all_progs = get_all_periodization_programs()
                prog_options = {p["id"]: p["name"] for p in all_progs}

                if "adm_sel_prog_id" in st.session_state and st.session_state.adm_sel_prog_id not in prog_options:
                    del st.session_state["adm_sel_prog_id"]

                c_p_sel, c_p_new, c_p_dup, c_p_del = st.columns([2.6, 1.1, 1.1, 1.1], gap="small")
                with c_p_sel:
                    adm_sel_prog_id = st.selectbox(
                        "Select Periodization Cycle to Manage",
                        options=list(prog_options.keys()),
                        format_func=lambda pid: prog_options[pid],
                        key="adm_sel_prog_id",
                    )
                with c_p_new:
                    if st.button("＋ New Cycle", key="adm_btn_new_cycle", use_container_width=True):
                        st.session_state.adm_show_new_cycle = not st.session_state.get("adm_show_new_cycle", False)
                        st.session_state.adm_confirm_del_cycle = False
                        st.rerun()
                with c_p_dup:
                    if st.button("Duplicate Cycle", key="adm_btn_dup_cycle", use_container_width=True):
                        res = duplicate_periodization_program(adm_sel_prog_id)
                        if res["success"]:
                            st.session_state.adm_confirm_del_cycle = False
                            st.success(f"Duplicated cycle '{res['name']}'.")
                            st.rerun()
                        else:
                            st.error(res.get("error", "Failed to duplicate cycle."))
                with c_p_del:
                    adm_can_del = len(all_progs) > 1
                    if st.button(
                        "Delete Cycle",
                        key="adm_btn_del_cycle",
                        use_container_width=True,
                        disabled=not adm_can_del,
                        help="Delete this cycle" if adm_can_del else "Cannot delete the only remaining cycle",
                    ):
                        st.session_state.adm_confirm_del_cycle = not st.session_state.get("adm_confirm_del_cycle", False)
                        st.session_state.adm_show_new_cycle = False
                        st.rerun()

                if st.session_state.get("adm_confirm_del_cycle"):
                    st.markdown(
                        clean_html(f"""
                        <div style="background:rgba(255, 77, 77, 0.08);border:1px solid rgba(255, 77, 77, 0.35);border-radius:12px;padding:12px 16px;margin:8px 0 12px;">
                            <div style="display:flex;justify-content:space-between;align-items:center;">
                                <div style="font-size:14px;font-weight:800;color:#ff6b6b;">Confirm Cycle Deletion</div>
                                <span style="font-size:11px;font-weight:700;padding:2px 8px;border-radius:6px;background:rgba(255,77,77,0.15);color:#ff6b6b;border:1px solid rgba(255,77,77,0.3);">{prog_options.get(adm_sel_prog_id, 'Cycle')}</span>
                            </div>
                            <div style="font-size:12px;color:var(--text-dim);margin-top:4px;">
                                Are you sure you want to permanently delete <b>'{prog_options.get(adm_sel_prog_id, '')}'</b> and all associated days and exercises? This action cannot be undone.
                            </div>
                        </div>
                        """),
                        unsafe_allow_html=True,
                    )
                    c_ad_del_yes, c_ad_del_no = st.columns(2)
                    with c_ad_del_yes:
                        if st.button("Permanently Delete Cycle", key="adm_btn_confirm_delete_cycle", type="primary", use_container_width=True):
                            del_res = delete_periodization_program(adm_sel_prog_id)
                            if del_res.get("success"):
                                st.session_state.adm_confirm_del_cycle = False
                                if "adm_sel_prog_id" in st.session_state:
                                    del st.session_state["adm_sel_prog_id"]
                                c_name = del_res.get("name") or prog_options.get(adm_sel_prog_id)
                                st.success(f"Periodization cycle '{c_name}' deleted.")
                                st.rerun()
                            else:
                                st.error(del_res.get("error", "Failed to delete cycle."))
                    with c_ad_del_no:
                        if st.button("Cancel", key="adm_btn_cancel_delete_cycle", use_container_width=True):
                            st.session_state.adm_confirm_del_cycle = False
                            st.rerun()

                if st.session_state.get("adm_show_new_cycle"):
                    with st.form("adm_create_cycle_form"):
                        st.markdown('<div style="font-size:14px;font-weight:800;color:var(--text);">Create New Periodization Cycle</div>', unsafe_allow_html=True)
                        adm_c_name = st.text_input("Cycle Name", placeholder="e.g. 5-Week Strength Wave")
                        adm_c_desc = st.text_input("Description", placeholder="e.g. Primary powerbuilding progression")
                        adm_t_choice = st.radio("Template", ["Clone from Selected Cycle", "Blank Cycle"], index=0, horizontal=True)
                        c_w_cnt, c_d_cnt = st.columns(2)
                        with c_w_cnt:
                            adm_weeks = st.number_input("Weeks Count", min_value=1, max_value=16, value=5, step=1)
                        with c_d_cnt:
                            adm_days = st.number_input("Days per Week", min_value=1, max_value=7, value=5, step=1)
                        c_ac1, c_ac2 = st.columns(2)
                        with c_ac1:
                            if st.form_submit_button("Create Cycle", type="primary", use_container_width=True):
                                if not adm_c_name.strip():
                                    st.error("Cycle name is required.")
                                else:
                                    t_id = adm_sel_prog_id if "Clone" in adm_t_choice else None
                                    res = create_periodization_program(adm_c_name.strip(), adm_c_desc.strip(), int(adm_weeks), int(adm_days), t_id)
                                    if res["success"]:
                                        st.session_state.adm_show_new_cycle = False
                                        st.success(f"Created cycle '{res['name']}'.")
                                        st.rerun()
                                    else:
                                        st.error(res.get("error", "Failed to create cycle."))
                        with c_ac2:
                            if st.form_submit_button("Cancel", use_container_width=True):
                                st.session_state.adm_show_new_cycle = False
                                st.rerun()

                prog_data = get_builtin_periodization_program(adm_sel_prog_id)
                weeks_list = sorted([w for w in prog_data.keys() if isinstance(w, int)])
                if not weeks_list:
                    weeks_list = [1]

                c_pw, c_pd = st.columns(2)
                with c_pw:
                    admin_p_week = st.selectbox("Select Week", options=weeks_list, format_func=lambda w: f"Week {w} ({prog_data.get(w, {}).get('phase', f'Week {w}')})", key="adm_p_week")

                current_w = prog_data.get(admin_p_week, {})
                days_dict = current_w.get("days", {})
                days_list = sorted(days_dict.keys()) if days_dict else [1]

                with c_pd:
                    admin_p_day = st.selectbox("Select Day", options=days_list, format_func=lambda d: f"Day {d}", key="adm_p_day")

                current_d_exs = days_dict.get(admin_p_day, [])

                # Find day_id from DB
                conn_tmp = get_connection()
                d_row = conn_tmp.execute("SELECT id FROM builtin_periodization_days WHERE program_id=? AND week_number=? AND day_number=?", (adm_sel_prog_id, admin_p_week, admin_p_day)).fetchone()
                conn_tmp.close()
                day_id = d_row["id"] if d_row else 1

                # Edit Day Overview (Phase, Badge, Objective)
                with st.expander("Edit Phase & Day Metadata", expanded=False):
                    with st.form("admin_edit_phase_meta_form"):
                        up_phase = st.text_input("Phase Name", value=current_w.get("phase", f"Week {admin_p_week}"))
                        up_badge = st.text_input("Protocol Badge", value=current_w.get("badge", ""))
                        up_obj = st.text_area("Phase Objective", value=current_w.get("objective", ""))
                        if st.form_submit_button("Update Phase Metadata", use_container_width=True):
                            res = update_builtin_periodization_day(day_id, up_phase, up_badge, up_obj)
                            if res["success"]:
                                st.success("Phase metadata updated.")
                                st.rerun()
                            else:
                                st.error(res["error"])

                st.markdown(f'<div style="font-size:14px;font-weight:800;color:var(--text);margin:14px 0 6px;">Exercises in Week {admin_p_week} Day {admin_p_day} ({len(current_d_exs)} scheduled)</div>', unsafe_allow_html=True)

                for item in current_d_exs:
                    ex_row_id = item["id"]
                    role_display = "Focus Lift #1" if item["role"] == "focus" else ("Hypertrophy Support" if item["role"] == "support" else "Compound Auxiliary")
                    with st.expander(f"{item['name']} · {item['target']} [{role_display}]", expanded=False):
                        with st.form(f"adm_edit_p_ex_{ex_row_id}"):
                            e_name = st.text_input("Exercise Name", value=item["name"])
                            e_target = st.text_input("Target (e.g. 2x8-10, 4x1)", value=item["target"])
                            e_sets = st.number_input("Sets", min_value=1, max_value=10, value=int(item["sets"]))
                            e_role = st.selectbox("Role", ["focus", "auxiliary", "support"], index=["focus", "auxiliary", "support"].index(item["role"]) if item["role"] in ["focus", "auxiliary", "support"] else 1)
                            e_muscle = st.selectbox("Muscle Group", [
                                "Chest", "Back", "Shoulders", "Biceps", "Triceps", "Legs",
                                "Quads", "Hamstrings", "Glutes", "Calves", "Core", "Cardio", "Full Body", "Other"
                            ], index=[
                                "Chest", "Back", "Shoulders", "Biceps", "Triceps", "Legs",
                                "Quads", "Hamstrings", "Glutes", "Calves", "Core", "Cardio", "Full Body", "Other"
                            ].index(item["muscle"]) if item["muscle"] in [
                                "Chest", "Back", "Shoulders", "Biceps", "Triceps", "Legs",
                                "Quads", "Hamstrings", "Glutes", "Calves", "Core", "Cardio", "Full Body", "Other"
                            ] else 0)
                            e_equip = st.text_input("Equipment", value=item.get("equip") or "")
                            e_type = st.selectbox("Tracking Type", ["weights_reps", "bodyweight", "weighted_calisthenics", "time"], index=["weights_reps", "bodyweight", "weighted_calisthenics", "time"].index(item["type"]) if item["type"] in ["weights_reps", "bodyweight", "weighted_calisthenics", "time"] else 0)

                            if st.form_submit_button("Save Exercise Changes", use_container_width=True):
                                res = update_builtin_periodization_exercise(ex_row_id, e_name, e_muscle, e_type, e_equip, e_target, e_sets, e_role)
                                if res["success"]:
                                    st.success(f"Updated '{e_name}'.")
                                    st.rerun()
                                else:
                                    st.error(res["error"])

                        if st.button("Delete this Exercise", key=f"btn_del_p_ex_{ex_row_id}", use_container_width=True):
                            delete_builtin_periodization_exercise(ex_row_id)
                            st.success(f"Removed '{item['name']}'.")
                            st.rerun()

                # Add new exercise to this day
                st.markdown('<div style="font-size:14px;font-weight:800;color:var(--text);margin:16px 0 6px;">Add Exercise to this Day</div>', unsafe_allow_html=True)
                with st.form("admin_add_p_ex_form", clear_on_submit=True):
                    add_name = st.text_input("Exercise Name", placeholder="e.g. Dumbbell Hammer Curl")
                    add_target = st.text_input("Target Prescription", placeholder="e.g. 2x8-10 (RPE 9-10)")
                    add_sets = st.number_input("Sets", min_value=1, max_value=10, value=2)
                    add_role = st.selectbox("Role", ["support", "auxiliary", "focus"])
                    add_muscle = st.selectbox("Muscle Group", [
                        "Chest", "Back", "Shoulders", "Biceps", "Triceps", "Legs",
                        "Quads", "Hamstrings", "Glutes", "Calves", "Core", "Cardio", "Full Body", "Other"
                    ])
                    add_equip = st.text_input("Equipment", placeholder="e.g. Dumbbell, Cable")
                    add_type = st.selectbox("Tracking Type", ["weights_reps", "bodyweight", "weighted_calisthenics", "time"])
                    if st.form_submit_button("Add Exercise to Day", use_container_width=True):
                        res = add_builtin_periodization_exercise(day_id, add_name, add_muscle, add_type, add_equip, add_target, add_sets, add_role)
                        if res["success"]:
                            st.success(f"Added '{add_name}' to Week {admin_p_week} Day {admin_p_day}.")
                            st.rerun()
                        else:
                            st.error(res["error"])

                st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
                if len(all_progs) > 1:
                    if st.button(f"Delete Cycle '{prog_options.get(adm_sel_prog_id, '')}'", key=f"adm_del_cycle_{adm_sel_prog_id}", use_container_width=True):
                        st.session_state.adm_confirm_del_cycle = True
                        st.rerun()

                if adm_sel_prog_id == 1:
                    if st.button("Reset Built-in Periodization Program to Official Default", key="reset_periodization_btn", use_container_width=True):
                        reset_builtin_periodization_to_default()
                        st.success("Periodization program successfully reset to official 5-week default.")
                        st.rerun()
            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
            if st.button("Exit Admin Panel", key="auth_exit_admin", use_container_width=True):
                st.session_state.admin_authenticated = False
                st.session_state.auth_mode = "login"
                st.rerun()

# -----------------------------------------------------------------------------
# LOGIN & REGISTRATION
# -----------------------------------------------------------------------------
else:
    with st.container(key="auth_card"):
        st.markdown(
            f'<div class="auth-brand"><div class="auth-icon">{icon("dumbbell", size=23)}</div><div class="auth-title">HTN</div></div><div class="auth-subtitle">High Tier Normie · Train. Track. Improve.</div>',
            unsafe_allow_html=True,
        )
        if st.session_state.auth_mode == "login":
            st.markdown('<div class="auth-form-title">Welcome back</div><div class="auth-form-subtitle">Log in to continue to HTN.</div>', unsafe_allow_html=True)
            username = st.text_input("Username", key="login_username", placeholder="Your username")
            password = st.text_input("Password", type="password", key="login_password", placeholder="Your password")
            if st.button("Log in", key="auth_submit", use_container_width=True):
                if not username.strip() or not password:
                    st.error("Enter your username and password.")
                else:
                    result = authenticate_user(username, password)
                    if result["success"]:
                        log_in(result["user"])
                        st.switch_page("Home.py")
                    else:
                        st.error(result["error"])
            st.caption("Don't have an account?")
            if st.button("Create an account", key="auth_toggle", use_container_width=True):
                st.session_state.auth_mode = "register"
                st.rerun()

            # Admin Portal Entry
            if st.button("Admin Portal", key="admin_toggle", use_container_width=True):
                st.session_state.auth_mode = "admin"
                st.rerun()

        else:
            st.markdown('<div class="auth-form-title">Create your HTN account</div><div class="auth-form-subtitle">Only a username and password are needed.</div>', unsafe_allow_html=True)
            username = st.text_input("Username", key="register_username", placeholder="Choose a username")
            st.markdown('<div class="auth-help">Letters and special characters only. No numbers or spaces.</div>', unsafe_allow_html=True)
            password = st.text_input("Password", type="password", key="register_password", placeholder="At least 6 characters")
            confirm = st.text_input("Confirm password", type="password", key="register_confirm", placeholder="Repeat your password")
            if st.button("Register", key="auth_submit", use_container_width=True):
                err = validate_username(username)
                if err:
                    st.error(err)
                else:
                    err = validate_password(password)
                    if err:
                        st.error(err)
                    elif password != confirm:
                        st.error("Passwords do not match.")
                    else:
                        result = register_auth_user(username, password)
                        if result["success"]:
                            st.success("Account created. You can now log in.")
                            st.session_state.auth_mode = "login"
                            st.rerun()
                        else:
                            st.error(result["error"])
            if st.button("Back to login", key="auth_toggle", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()

import streamlit as st
import pandas as pd
import datetime
from datetime import datetime, time, timedelta
import io

# Set page config
st.set_page_config(
    page_title="Shah Cement - Production & Downtime Tracking System",
    page_icon="🏭",
    layout="wide"
)

# Custom Styling for Branding & Dashboard UI
st.markdown("""
<style>
    .brand-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
        padding: 24px 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .brand-title {
        font-size: 32px;
        font-weight: 800;
        letter-spacing: 1.5px;
        margin: 0;
        color: #FFFFFF;
        text-transform: uppercase;
    }
    .brand-subtitle {
        font-size: 15px;
        font-weight: 500;
        color: #93C5FD;
        margin-top: 6px;
    }
    .developer-tag {
        font-size: 13px;
        color: #CBD5E1;
        margin-top: 8px;
        font-weight: 500;
        font-style: italic;
    }
    .card-metric {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .card-title {
        color: #64748B;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    .card-value {
        color: #1E293B;
        font-size: 24px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session States
if 'users' not in st.session_state:
    st.session_state.users = {
        'viewer': {'password': 'view123', 'role': 'Viewer', 'name': 'General Viewer'},
        'operator': {'password': 'op123', 'role': 'Operator', 'name': 'Machine Operator'},
        'admin': {'password': 'admin123', 'role': 'Admin', 'name': 'Plant Manager'},
        'creator': {'password': 'creator123', 'role': 'Creator', 'name': 'System Developer'}
    }

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'username' not in st.session_state:
    st.session_state.username = None

# Helper Functions


def auto_purge_old_data(df, retention_days=1095):  # 3 Years Retention
    if df.empty:
        return df
    temp_df = df.copy()
    temp_df['temp_date'] = pd.to_datetime(
        temp_df['Production Date'], errors='coerce')
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    filtered_df = temp_df[temp_df['temp_date'] >=
                          cutoff_date].drop(columns=['temp_date'])
    return filtered_df


if 'downtime_data' not in st.session_state:
    initial_data = pd.DataFrame([
        {
            "ID": 1,
            "Production Date": "2026-09-16",
            "Start Time": "2026-09-16 08:30 AM",
            "End Time": "2026-09-16 09:45 AM",
            "Duration (Mins)": 75,
            "Shift": "A Shift",
            "Equipment": "BM1 Polycom M1",
            "Breakdown Category": "Mechanical",
            "Reason / Description": "Hydraulic Pressure Loss",
            "Entry Person (Operator/Engr)": "Engr. Shaed",
            "Logged By": "operator",
            "Status": "Closed"
        }
    ])
    st.session_state.downtime_data = auto_purge_old_data(initial_data)


def get_production_day_and_shift(dt_obj):
    hour = dt_obj.hour
    if hour < 6:
        prod_date = dt_obj.date() - timedelta(days=1)
    else:
        prod_date = dt_obj.date()

    if 6 <= hour < 14:
        shift = "A Shift"
    elif 14 <= hour < 22:
        shift = "B Shift"
    else:
        shift = "C Shift"

    return prod_date.strftime("%Y-%m-%d"), shift

# HEADER BANNER


def render_header():
    st.markdown("""
        <div class="brand-header">
            <div class="brand-title">SHAH CEMENT INDUSTRIES LIMITED</div>
            <div class="brand-subtitle">Production & Downtime Tracking System (DTA App)</div>
            <div class="developer-tag">⚡ Developed by SCIL ELECTRICAL</div>
        </div>
    """, unsafe_allow_html=True)


# LOGIN SCREEN
if not st.session_state.authenticated:
    render_header()
    col1, _ = st.columns([1, 1])
    with col1:
        st.subheader("🔒 Secure System Login")
        with st.form("login_form"):
            input_username = st.text_input("Username")
            input_password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                user_info = st.session_state.users.get(input_username.lower())
                if user_info and user_info['password'] == input_password:
                    st.session_state.authenticated = True
                    st.session_state.user_role = user_info['role']
                    st.session_state.username = input_username.lower()
                    st.rerun()
                else:
                    st.error("Invalid Username or Password!")
    st.stop()

# MAIN INTERFACE
render_header()

# SIDEBAR
st.sidebar.title(
    f"👤 {st.session_state.users[st.session_state.username]['name']}")
st.sidebar.caption(f"Role: **{st.session_state.user_role}**")

if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.rerun()

menu = ["📝 Downtime Entry", "📊 Dashboard & Analytics",
        "📜 Breakdown History", "📑 Shift-wise Report", "📥 Excel Export"]
choice = st.sidebar.radio("Go to Section", menu)

EQUIPMENT_LIST = [
    "BM1", "BM1 Polycom M1", "BM1 Polycom M2",
    "BM2", "BM3", "BM4", "BM4 Roller Press M1", "BM4 Roller Press M2",
    "VRM", "Packer 1", "Packer 2", "Packer 3", "Packer 4", "Packer 5",
    "Packer 6", "Packer 7", "Packer 8", "Packer 9",
    "E-Crane 1", "E-Crane 2", "E-Crane 3", "E-Crane 4", "E-Crane 5", "E-Crane 6", "E-Crane 7",
    "X-Crane", "Z-Crane"
]

# DOWNTIME ENTRY FORM
if choice == "📝 Downtime Entry":
    st.subheader("📝 New Downtime Event Logging")
    st.caption(
        "ℹ️ *Note: System automatically retains downtime logs for 3 years.*")

    with st.form("downtime_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            equipment = st.selectbox(
                "Select Equipment / Machine", EQUIPMENT_LIST)
            start_date = st.date_input("Start Date", datetime.now().date())
            start_time_val = st.time_input("Start Time", datetime.now().time())
            category = st.selectbox("Breakdown Category", [
                                    "Mechanical", "Electrical", "Process", "Instrumentation", "Operational", "Power Outage"])
            entry_person = st.text_input(
                "Operator / Shift Engineer Name", placeholder="e.g. Engr. Shaed / Operator Kabir")

        with col2:
            status = st.selectbox("Status", ["Closed", "Ongoing"])
            if status == "Closed":
                end_date = st.date_input("End Date", datetime.now().date())
                end_time_val = st.time_input("End Time", datetime.now().time())

            reason = st.text_area("Reason / Description of Failure")

        submit_btn = st.form_submit_button("Submit Downtime Log")

        if submit_btn:
            if not entry_person.strip():
                st.error("Please enter the Operator or Shift Engineer's name!")
            else:
                start_dt = datetime.combine(start_date, start_time_val)
                prod_date, auto_shift = get_production_day_and_shift(start_dt)

                duration_mins = 0
                end_str = "ONGOING"
                if status == "Closed":
                    end_dt = datetime.combine(end_date, end_time_val)
                    duration_mins = int(
                        (end_dt - start_dt).total_seconds() / 60)
                    end_str = end_dt.strftime("%Y-%m-%d %I:%M %p")

                new_entry = {
                    "ID": len(st.session_state.downtime_data) + 1,
                    "Production Date": prod_date,
                    "Start Time": start_dt.strftime("%Y-%m-%d %I:%M %p"),
                    "End Time": end_str,
                    "Duration (Mins)": duration_mins,
                    "Shift": auto_shift,
                    "Equipment": equipment,
                    "Breakdown Category": category,
                    "Reason / Description": reason,
                    "Entry Person (Operator/Engr)": entry_person,
                    "Logged By": st.session_state.username,
                    "Status": status
                }

                # Append new record and apply auto-purge rule
                st.session_state.downtime_data = pd.concat(
                    [st.session_state.downtime_data, pd.DataFrame([new_entry])], ignore_index=True)
                st.session_state.downtime_data = auto_purge_old_data(
                    st.session_state.downtime_data)

                st.success(f"✅ Logged successfully by **{entry_person}**!")

# FOOTER
st.markdown("""
    <div style="text-align: center; padding: 20px; color: #64748B; font-size: 13px; border-top: 1px solid #E2E8F0; margin-top: 40px;">
        © Shah Cement Industries Limited | ⚡ Developed by SCIL ELECTRICAL
    </div>
""", unsafe_allow_html=True)

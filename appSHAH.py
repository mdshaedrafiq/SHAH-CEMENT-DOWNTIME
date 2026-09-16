import streamlit as st
import pandas as pd
import sqlite3
import datetime
from datetime import datetime, timedelta
import io

# Page Config
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

# --- DATABASE SETUP (SQLite) ---
def get_db_connection():
    conn = sqlite3.connect('scil_downtime.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS downtime_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prod_date TEXT,
            start_time TEXT,
            end_time TEXT,
            duration INTEGER,
            shift TEXT,
            equipment TEXT,
            category TEXT,
            reason TEXT,
            entry_person TEXT,
            logged_by TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 3-Year Retention Logic
def load_and_purge_data():
    conn = get_db_connection()
    df = pd.read_sql("SELECT * FROM downtime_logs", conn)
    
    if not df.empty:
        df['temp_date'] = pd.to_datetime(df['prod_date'], errors='coerce')
        cutoff_date = datetime.now() - timedelta(days=1095) # 3 Years
        
        old_ids = df[df['temp_date'] < cutoff_date]['id'].tolist()
        if old_ids:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM downtime_logs WHERE id IN ({','.join(map(str, old_ids))})")
            conn.commit()
            df = df[df['temp_date'] >= cutoff_date]
            
        df = df.drop(columns=['temp_date'])
    conn.close()
    return df

# --- SHIFT & PRODUCTION DAY CALCULATION ---
def get_production_day_and_shift(dt_obj):
    hour = dt_obj.hour
    
    # Production Day: 6 AM to 6 AM
    if hour < 6:
        prod_date = dt_obj.date() - timedelta(days=1)
    else:
        prod_date = dt_obj.date()
        
    # Shift Logic: A (6-14), B (14-22), C (22-6)
    if 6 <= hour < 14:
        shift = "A Shift"
    elif 14 <= hour < 22:
        shift = "B Shift"
    else:
        shift = "C Shift"
        
    return prod_date.strftime("%Y-%m-%d"), shift

# Header Render
def render_header():
    st.markdown("""
        <div class="brand-header">
            <div class="brand-title">SHAH CEMENT INDUSTRIES LIMITED</div>
            <div class="brand-subtitle">Production & Downtime Tracking System (DTA App)</div>
            <div class="developer-tag">⚡ Developed by SCIL ELECTRICAL</div>
        </div>
    """, unsafe_allow_html=True)

# --- USER SESSION & AUTHENTICATION STATES ---
if 'users' not in st.session_state:
    st.session_state.users = {
        'viewer': {'password': 'view123', 'role': 'Viewer', 'name': 'General Viewer'},
        'operator/engineer': {'password': 'op123', 'role': 'Operator', 'name': 'Machine Operator/Shift engineer'},
        'admin': {'password': 'admin123', 'role': 'Admin', 'name': 'Plant Manager'},
        'creator': {'password': 'creator123', 'role': 'Creator', 'name': 'System Developer'}
    }

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'username' not in st.session_state:
    st.session_state.username = None

# LOGIN SCREEN
if not st.session_state.authenticated:
    render_header()
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("🔒 Secure System Login")
        with st.form("login_form"):
            input_username = st.text_input("Username / User ID")
            input_password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                user_info = st.session_state.users.get(input_username.lower())
                if user_info and user_info['password'] == input_password:
                    st.session_state.authenticated = True
                    st.session_state.user_role = user_info['role']
                    st.session_state.username = input_username.lower()
                    st.success(f"Logged in as {user_info['name']}")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password!")
                    

    st.stop()

# MAIN INTERFACE (Logged In)
render_header()

# SIDEBAR (Profile & Logout)
st.sidebar.title(f"👤 {st.session_state.users[st.session_state.username]['name']}")
st.sidebar.caption(f"Role: **{st.session_state.user_role}**")

if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.username = None
    st.rerun()

st.sidebar.markdown("---")

# Role-based Navigation Menu
if st.session_state.user_role == 'Viewer':
    menu = ["📊 Dashboard & Analytics", "📜 Breakdown History", "📑 Shift-wise Report"]
elif st.session_state.user_role == 'Operator':
    menu = ["📝 Downtime Entry", "📜 Breakdown History"]
elif st.session_state.user_role == 'Admin':
    menu = ["📝 Downtime Entry", "📊 Dashboard & Analytics", "📜 Breakdown History", "📑 Shift-wise Report", "📥 Excel Export"]
else: # Creator / Developer
    menu = ["📝 Downtime Entry", "📊 Dashboard & Analytics", "📜 Breakdown History", "📑 Shift-wise Report", "📥 Excel Export", "⚙️ User Management / Admin"]

choice = st.sidebar.radio("Go to Section", menu)

EQUIPMENT_LIST = [
    "BM1", "BM1 Polycom M1", "BM1 Polycom M2",
    "BM2", "BM3", "BM4", "BM4 Roller Press M1", "BM4 Roller Press M2",
    "VRM M1", "VRM M2",
    "Packer 1", "Packer 2", "Packer 3", "Packer 4", "Packer 5",
    "Packer 6", "Packer 7", "Packer 8", "Packer 9",
    "E-Crane 1", "E-Crane 2", "E-Crane 3", "E-Crane 4", "E-Crane 5", "E-Crane 6", "E-Crane 7",
    "X-Crane", "Z-Crane"
]

# --- 1. DOWNTIME ENTRY FORM ---
if choice == "📝 Downtime Entry":
    st.subheader("📝 New Downtime Event Logging")
    st.caption("ℹ️ *Production Day: 6 AM to 6 AM | Shift A (6 AM-2 PM), Shift B (2 PM-10 PM), Shift C (10 PM-6 AM)*")
    
    with st.form("downtime_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            equipment = st.selectbox("Select Equipment / Machine", EQUIPMENT_LIST)
            start_date = st.date_input("Start Date", datetime.now().date())
            start_time_val = st.time_input("Start Time (12-hour AM/PM)", datetime.now().time())
            category = st.selectbox("Breakdown Category", ["Mechanical", "Electrical", "Process", "Instrumentation", "Operational", "Power Outage"])
            entry_person = st.text_input("Operator / Shift Engineer Name", placeholder="e.g. Engr. Shaed / Operator Kabir")
            
        with col2:
            status = st.selectbox("Status", ["Closed", "Ongoing"])
            if status == "Closed":
                end_date = st.date_input("End Date", datetime.now().date())
                end_time_val = st.time_input("End Time (12-hour AM/PM)", datetime.now().time())
            
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
                    duration_mins = int((end_dt - start_dt).total_seconds() / 60)
                    end_str = end_dt.strftime("%Y-%m-%d %I:%M %p")
                
                # Insert into SQLite DB
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO downtime_logs (prod_date, start_time, end_time, duration, shift, equipment, category, reason, entry_person, logged_by, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (prod_date, start_dt.strftime("%Y-%m-%d %I:%M %p"), end_str, duration_mins, auto_shift, equipment, category, reason, entry_person, st.session_state.username, status))
                
                conn.commit()
                conn.close()
                
                st.success(f"✅ Logged successfully! Production Day: **{prod_date}**, Shift: **{auto_shift}**, Operator: **{entry_person}**")

# --- 2. DASHBOARD & ANALYTICS ---
elif choice == "📊 Dashboard & Analytics":
    st.subheader("📊 Downtime Summary & KPI Overview")
    df = load_and_purge_data()
    
    if df.empty:
        st.info("No downtime data recorded yet.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        total_downtime = df["duration"].sum()
        total_events = len(df)
        top_eq = df.groupby("equipment")["duration"].sum().idxmax() if not df.empty else "N/A"
        ongoing_events = len(df[df["status"] == "Ongoing"])
        
        with col1:
            st.markdown(f'<div class="card-metric"><div class="card-title">Total Downtime</div><div class="card-value">{total_downtime} Mins<br><span style="font-size:14px;color:#3B82F6;">({round(total_downtime/60, 1)} Hrs)</span></div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="card-metric"><div class="card-title">Total Breakdown Events</div><div class="card-value">{total_events}</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="card-metric"><div class="card-title">Highest Downtime Machine</div><div class="card-value" style="font-size:18px;">{top_eq}</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="card-metric"><div class="card-title">Ongoing Breakdowns</div><div class="card-value" style="color:#EF4444;">{ongoing_events}</div></div>', unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### ⚙️ Equipment-wise Downtime (Minutes)")
            eq_summary = df.groupby("equipment")["duration"].sum().reset_index().sort_values(by="duration", ascending=False)
            st.bar_chart(eq_summary.set_index("equipment"))
            
        with c2:
            st.markdown("#### 🕒 Shift-wise Breakdown Distribution")
            shift_summary = df.groupby("shift")["duration"].sum().reset_index()
            st.bar_chart(shift_summary.set_index("shift"))

# --- 3. BREAKDOWN HISTORY ---
elif choice == "📜 Breakdown History":
    st.subheader("📜 Maintenance Log & Breakdown History")
    df = load_and_purge_data()
    st.dataframe(df, use_container_width=True)

# --- 4. SHIFT-WISE REPORT ---
elif choice == "📑 Shift-wise Report":
    st.subheader("📑 Shift-Wise Downtime Matrix")
    df = load_and_purge_data()
    if not df.empty:
        pivot_table = pd.pivot_table(
            df,
            values="duration",
            index=["prod_date", "shift"],
            columns=["equipment"],
            aggfunc="sum",
            fill_value=0
        )
        st.dataframe(pivot_table, use_container_width=True)
    else:
        st.info("No data available to generate reports.")

# --- 5. EXCEL EXPORT ---
elif choice == "📥 Excel Export":
    st.subheader("📥 Export Downtime Data to Excel")
    df = load_and_purge_data()
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Downtime Log History', index=False)
            
    buffer.seek(0)
    st.download_button(
        label="Download Report (.xlsx)",
        data=buffer,
        file_name=f"SCIL_Downtime_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- 6. USER MANAGEMENT ---
elif choice == "⚙️ User Management / Admin":
    st.subheader("⚙️ User & Access Control")
    
    user_list = []
    for uname, udata in st.session_state.users.items():
        user_list.append({"Username": uname, "Full Name": udata["name"], "Role": udata["role"]})
    st.table(pd.DataFrame(user_list))

# Footer
st.markdown("""
    <div style="text-align: center; padding: 20px; color: #64748B; font-size: 13px; border-top: 1px solid #E2E8F0; margin-top: 40px;">
        © Shah Cement Industries Limited | ⚡ Developed by SCIL ELECTRICAL
    </div>
""", unsafe_allow_html=True)

import streamlit as st
import pandas as pd
import sqlite3
import datetime
from datetime import datetime, timedelta

# Page Config
st.set_page_config(
    page_title="Shah Cement - Production & Downtime Tracking System",
    page_icon="🏭",
    layout="wide"
)

# Custom Branding CSS
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
</style>
""", unsafe_allow_html=True)

# Database Setup
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

# Auto Purge Data (>3 Years)
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

# Production Day & Shift Calculation
def get_production_day_and_shift(dt_obj):
    hour = dt_obj.hour
    
    # Production Day: 6 AM to 6 AM
    if hour < 6:
        prod_date = dt_obj.date() - timedelta(days=1)
    else:
        prod_date = dt_obj.date()
        
    # Shift Logic: A (6 AM-2 PM), B (2 PM-10 PM), C (10 PM-6 AM)
    if 6 <= hour < 14:
        shift = "A Shift"
    elif 14 <= hour < 22:
        shift = "B Shift"
    else:
        shift = "C Shift"
        
    return prod_date.strftime("%Y-%m-%d"), shift

# Header Render
st.markdown("""
    <div class="brand-header">
        <div class="brand-title">SHAH CEMENT INDUSTRIES LIMITED</div>
        <div class="brand-subtitle">Production & Downtime Tracking System (DTA App)</div>
        <div class="developer-tag">⚡ Developed by SCIL ELECTRICAL</div>
    </div>
""", unsafe_allow_html=True)

EQUIPMENT_LIST = [
    "BM1", "BM1 Polycom M1", "BM1 Polycom M2",
    "BM2", "BM3", "BM4", "BM4 Roller Press M1", "BM4 Roller Press M2",
    "VRM M1", "VRM M2",
    "Packer 1", "Packer 2", "Packer 3", "Packer 4", "Packer 5",
    "Packer 6", "Packer 7", "Packer 8", "Packer 9",
    "E-Crane 1", "E-Crane 2", "E-Crane 3", "E-Crane 4", "E-Crane 5", "E-Crane 6", "E-Crane 7",
    "X-Crane", "Z-Crane"
]

menu = ["📝 Downtime Entry", "📜 Breakdown History"]
choice = st.sidebar.radio("Go to Section", menu)

if choice == "📝 Downtime Entry":
    st.subheader("📝 New Downtime Event Logging")
    st.caption("ℹ️ *Production Day: 6:00 AM to 6:00 AM | Time format: 12-Hour AM/PM*")
    
    with st.form("downtime_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            equipment = st.selectbox("Select Equipment / Machine", EQUIPMENT_LIST)
            start_date = st.date_input("Start Date", datetime.now().date())
            
            # 12-Hour AM/PM Time Input
            start_time_val = st.time_input("Start Time (hh:mm AM/PM)", datetime.now().time())
            
            category = st.selectbox("Breakdown Category", ["Mechanical", "Electrical", "Process", "Instrumentation", "Operational", "Power Outage"])
            entry_person = st.text_input("Operator / Shift Engineer Name", placeholder="e.g. Engr. Shaed / Operator Kabir")
            
        with col2:
            status = st.selectbox("Status", ["Closed", "Ongoing"])
            
            if status == "Closed":
                end_date = st.date_input("End Date", datetime.now().date())
                # 12-Hour AM/PM Time Input
                end_time_val = st.time_input("End Time (hh:mm AM/PM)", datetime.now().time())
            
            reason = st.text_area("Reason / Description of Failure")
            
        submit_btn = st.form_submit_button("Submit Downtime Log")
        
        if submit_btn:
            if not entry_person.strip():
                st.error("Please enter the Operator or Shift Engineer's name!")
            else:
                start_dt = datetime.combine(start_date, start_time_val)
                prod_date, auto_shift = get_production_day_and_shift(start_dt)
                
                # Format start time in 12-hour AM/PM format
                formatted_start = start_dt.strftime("%Y-%m-%d %I:%M %p")
                
                duration_mins = 0
                formatted_end = "ONGOING"
                if status == "Closed":
                    end_dt = datetime.combine(end_date, end_time_val)
                    duration_mins = int((end_dt - start_dt).total_seconds() / 60)
                    formatted_end = end_dt.strftime("%Y-%m-%d %I:%M %p")
                
                # Database Insert
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO downtime_logs (prod_date, start_time, end_time, duration, shift, equipment, category, reason, entry_person, logged_by, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (prod_date, formatted_start, formatted_end, duration_mins, auto_shift, equipment, category, reason, entry_person, "Operator", status))
                
                conn.commit()
                conn.close()
                
                st.success(f"✅ Downtime Logged! Start: **{formatted_start}** | End: **{formatted_end}** | Duration: **{duration_mins} Mins**")

elif choice == "📜 Breakdown History":
    st.subheader("📜 Maintenance Log & Breakdown History")
    df = load_and_purge_data()
    st.dataframe(df, use_container_width=True)

# Footer
st.markdown("""
    <div style="text-align: center; padding: 20px; color: #64748B; font-size: 13px; border-top: 1px solid #E2E8F0; margin-top: 40px;">
        © Shah Cement Industries Limited | ⚡ Developed by SCIL ELECTRICAL
    </div>
""", unsafe_allow_html=True)

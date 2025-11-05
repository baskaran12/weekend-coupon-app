import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
import json 

# -----------------------------
# Google Sheet setup
# -----------------------------
SHEET_NAME = "coupon_records"

# Connect to Google Sheets
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
#raw=st.secrets["GOOGLE_CREDS"]
# if isinstance(raw, str):
#     raw = raw.strip().replace('\n', '\\n')
creds_dict = json.loads(st.secrets["GOOGLE_CREDS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# -----------------------------
# Load existing data
# -----------------------------
data = sheet.get_all_records()
df = pd.DataFrame(data)

if df.empty:
    df = pd.DataFrame(columns=["Date", "Employee Name", "Coupon Bought", "Issued By", "Locked"])

# -----------------------------
# Determine current weekend date
# -----------------------------
today = datetime.today().date()

if today.weekday() in [5, 6]:
    # If today is Saturday (5) or Sunday (6)
    current_weekend = today
    editable = True
else:
    # Not a weekend → show most recent past Saturday
    days_since_saturday = (today.weekday() - 5) % 7
    #current_weekend = today - timedelta(days=days_since_saturday)
    last_saturday = today - timedelta(days=days_since_saturday)
    last_sunday = last_saturday + timedelta(days=1)
    editable = True

current_date_str = current_weekend.strftime("%Y-%m-%d")if  today.weekday() in [5, 6] else last_saturday.strftime("%Y-%m-%d")+ " / " + last_sunday.strftime("%Y-%m-%d")

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("🍱 週末クーポン管理")
if today.weekday() in [5, 6]:
    st.markdown(f"### **{current_weekend.strftime('%A, %B %d, %Y')}**")
else:
    st.markdown(f"### **前回の週末: {last_saturday.strftime('%A, %B %d, %Y')} & {last_sunday.strftime('%A, %B %d, %Y')}**")

# -----------------------------
# Show recent weekend data (read-only)
# -----------------------------
if not df.empty:
    if  today.weekday() in [5, 6]:
        df_filtered = df[df["Date"]==current_date_str]
    else:
        df_filtered = df[(df["Date"]==last_saturday.strftime("%Y-%m-%d")) | (df["Date"]==last_sunday.strftime("%Y-%m-%d"))] 
    if not df_filtered.empty:
        st.subheader("📋 Weekend Records")
        st.dataframe(df_filtered[['Date','Employee Name','Coupon Bought','Issued By']].rename(columns={'Date': '日付','Employee Name':'従業員名','Coupon Bought':'購入したクーポン','Issued By':'発行者'}), use_container_width=True)
    else:
        st.info("この週末のデータはまだありません。")
else:
    st.info("まだ記録がありません.")

# -----------------------------
# Add new record section (only for weekends)
# -----------------------------
if editable:
    st.markdown("---")
    st.subheader("➕ 新しい記録を追加")

    employee_name = st.text_input("従業員名")
    coupon_bought = st.selectbox("購入したクーポン", ["はい", "いいえ"])
    issued_by = st.text_input("発行者")

    if st.button("💾 保存"):
        if not employee_name or not issued_by:
            st.warning("保存する前にすべての項目を入力してください.")
        else:
            new_row = [current_date_str, employee_name, coupon_bought, issued_by, "TRUE"]
            sheet.append_row(new_row)
            st.success("✅ 保存してロックしました！ ")
            st.rerun()
else:
    st.info("🗓️ 週末ではありません — 最新の週末の記録を表示中（読み取り専用）。 ")


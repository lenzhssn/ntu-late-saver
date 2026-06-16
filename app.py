import json
import os
import time
import datetime
import streamlit as st

# --- 核心設定 ---
NTU_PERIODS = {
    "第 0 節": {"start": (7, 10), "end": (8, 0)},
    "第 1 節": {"start": (8, 10), "end": (9, 0)},
    "第 2 節": {"start": (9, 10), "end": (10, 0)},
    "第 3 節": {"start": (10, 20), "end": (11, 10)},
    "第 4 節": {"start": (11, 20), "end": (12, 10)},
    "第 5 節": {"start": (12, 20), "end": (13, 10)},
    "第 6 節": {"start": (13, 20), "end": (14, 10)},
    "第 7 節": {"start": (14, 20), "end": (15, 10)},
    "第 8 節": {"start": (15, 30), "end": (16, 20)},
    "第 9 節": {"start": (16, 30), "end": (17, 20)},
    "第 10 節": {"start": (17, 30), "end": (18, 20)},
    "第 A 節": {"start": (18, 25), "end": (19, 15)},
    "第 B 節": {"start": (19, 20), "end": (20, 10)},
    "第 C 節": {"start": (20, 15), "end": (21, 5)},
    "第 D 節": {"start": (21, 10), "end": (22, 0)},
}

def get_user_file(username):
    return f"{username}_ntu_data.json"

def load_data(username):
    filename = get_user_file(username)
    default_locations = [
        "公館捷運站", "科技大樓捷運站", "新生教學館", "綜合體育館", 
        "博雅教學館", "共同教學館", "台大管院1管", "台大管院2管", 
        "綜合教學館", "舊體育館", "戶外泳池"
    ]
    if not os.path.exists(filename):
        return {"history": [], "locations": default_locations, "schedule": {}}
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "locations" not in data: data["locations"] = default_locations
    if "schedule" not in data: data["schedule"] = {}
    return data

def save_data(data, username):
    with open(get_user_file(username), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_current_ntu_period_info():
    now = datetime.datetime.now()
    weekday_idx = now.weekday()
    days = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    
    # 假日判定
    if weekday_idx == 6: return "星期日", "無課程安排"
    
    current_time_val = now.hour * 60 + now.minute
    # 強制休息時段判定 (07:10之前 或 22:00之後)
    if current_time_val < 430 or current_time_val >= 1320:
        return days[weekday_idx], "休息時間"
    
    current_period = "休息時間"
    for period, t_range in NTU_PERIODS.items():
        start_val = t_range["start"][0] * 60 + t_range["start"][1]
        if start_val <= current_time_val < (start_val + 50):
            current_period = period
            break
    return days[weekday_idx], current_period

# --- UI 初始化 ---
st.set_page_config(page_title="NTU Late Saver", layout="centered")
st.title("NTU Late Saver")
user_name = st.text_input("請輸入您的個人識別碼 (學號/暱稱) 以載入數據")

if user_name:
    data = load_data(user_name)
    cur_day, cur_period = get_current_ntu_period_info()
    classroom_options = [loc for loc in data["locations"] if loc not in ["公館捷運站", "科技大樓捷運站"]]
    
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 紀錄通勤", "🔍 情境查詢", "⏱️ 智慧防遲到", "⚙️ 課表設定"])
    
    st.sidebar.markdown("### 選擇 天氣/通勤方式")
    trans_mode = st.sidebar.radio("通勤方式", ["走路", "腳踏車"])
    weather_condition = st.sidebar.radio("當前天氣", ["晴天", "雨天"])

    with tab1:
        s1 = st.selectbox("出發地", data["locations"] + ["其他"], key="s1")
        s1_o = st.text_input("新起點名稱", key="s1_o") if s1 == "其他" else ""
        d1 = st.selectbox("目的地", data["locations"] + ["其他"], key="d1")
        d1_o = st.text_input("新終點名稱", key="d1_o") if d1 == "其他" else ""
        if "is_timing" not in st.session_state: st.session_state.is_timing = False
        if not st.session_state.is_timing:
            if st.button("⏱️ 開始計時"):
                st.session_state.is_timing = True
                st.session_state.start_time = time.time()
                st.rerun()
        else:
            if st.button("🛑 停止計時並儲存"):
                duration = round((time.time() - st.session_state.start_time) / 60, 1)
                st.session_state.is_timing = False
                start, dest = (s1 if s1 != "其他" else s1_o), (d1 if d1 != "其他" else d1_o)
                if start and dest:
                    data["history"].append({"start": start, "dest": dest, "trans": trans_mode, "weather": weather_condition, "time": duration})
                    save_data(data, user_name)
                    st.success(f"儲存成功：{duration} 分鐘")
                    st.rerun()

    with tab2:
        s2 = st.selectbox("出發地", data["locations"] + ["其他"], key="s2")
        s2_o = st.text_input("新起點名稱", key="s2_o") if s2 == "其他" else ""
        d2 = st.selectbox("目的地", data["locations"] + ["其他"], key="d2")
        d2_o = st.text_input("新終點名稱",

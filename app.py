import json
import os
import time
import datetime
import streamlit as st

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
    if weekday_idx == 6: return "星期日", "無課程安排"
    
    current_time_val = now.hour * 60 + now.minute
    # 深夜休息時段判定 (07:10之前 或 22:00之後)
    if current_time_val < 430 or current_time_val >= 1320:
        days = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        return days[weekday_idx], "非上課時段"
    
    days = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    current_period = "未知時段"
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
        d2_o = st.text_input("新終點名稱", key="d2_o") if d2 == "其他" else ""
        if st.button("📊 查詢歷史數據"):
            start, dest = (s2 if s2 != "其他" else s2_o), (d2 if d2 != "其他" else d2_o)
            records = [h for h in data["history"] if h["start"] == start and h["dest"] == dest and h["trans"] == trans_mode and h["weather"] == weather_condition]
            if not records: st.error("查無紀錄")
            else: st.info(f"平均通勤時間：{round(sum(r['time'] for r in records)/len(records), 1)} 分鐘")

    with tab3:
        st.write(f"系統狀態：{cur_day} / {cur_period}")
        s3 = st.selectbox("出發地", data["locations"] + ["其他"], key="s3")
        s3_o = st.text_input("新起點名稱", key="s3_o") if s3 == "其他" else ""
        q_day = st.selectbox("查詢星期", ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六"])
        q_period = st.selectbox("查詢節次", list(NTU_PERIODS.keys()))
        if st.button("⏰ 計算出發時限"):
            start, key = (s3 if s3 != "其他" else s3_o), f"{q_day}_{q_period}"
            info = data["schedule"].get(key)
            if not info: st.warning("請先至課表設定綁定教室")
            else:
                d3 = info["location"]
                records = [h for h in data["history"] if h["start"] == start and h["dest"] == d3 and h["trans"] == trans_mode and h["weather"] == weather_condition]
                if not records: st.error("缺少該路段的通勤數據")
                else:
                    avg = sum(r['time'] for r in records)/len(records)
                    start_min = NTU_PERIODS[q_period]["start"][0]*60 + NTU_PERIODS[q_period]["start"][1]
                    latest = int(start_min - avg)
                    st.metric("🚨 最晚出發防線", f"{latest//60:02d}:{latest%60:02d}")

    with tab4:
        c_day = st.selectbox("上課星期", ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六"])
        c_period = st.selectbox("上課節次", list(NTU_PERIODS.keys()))
        c_loc = st.selectbox("教室位置", classroom_options)
        if st.button("💾 儲存課表綁定"):
            data["schedule"][f"{c_day}_{c_period}"] = {"has_class": True, "location": c_loc}
            save_data(data, user_name)
            st.success("設定已更新")
else:
    st.info("請輸入識別碼以開始使用。")

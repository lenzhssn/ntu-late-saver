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

def get_user_file(username): return f"{username}_ntu_data.json"

def load_data(username):
    filename = get_user_file(username)
    default_locations = ["公館捷運站", "科技大樓捷運站", "新生教學館", "綜合體育館", "博雅教學館", "共同教學館", "台大管院1管", "台大管院2管", "綜合教學館", "舊體育館", "戶外泳池"]
    if not os.path.exists(filename): return {"history": [], "locations": default_locations, "schedule": {}}
    with open(filename, "r", encoding="utf-8") as f: data = json.load(f)
    if "locations" not in data: data["locations"] = default_locations
    if "schedule" not in data: data["schedule"] = {}
    return data

def save_data(data, username):
    with open(get_user_file(username), "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

def get_current_ntu_period_info():
    tz = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(tz)
    weekday_idx = now.weekday()
    days = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    if weekday_idx == 6: return "星期日", "無課程安排"
    current_time_val = now.hour * 60 + now.minute
    if current_time_val < 430 or current_time_val >= 1320: return days[weekday_idx], "休息時間"
    for period, t_range in NTU_PERIODS.items():
        s = t_range["start"][0] * 60 + t_range["start"][1]
        if s <= current_time_val < (s + 50): return days[weekday_idx], period
    return days[weekday_idx], "休息時間"

def get_unlocked_titles(history):
    unlocked = set()
    if len(history) >= 1: unlocked.add("通勤新手")
    # 早鳥成就：第2節前(第0/1節)準時或早到
    if len([h for h in history if h.get("period") in ["第 0 節", "第 1 節"] and h.get("status") == "早到"]) >= 3: unlocked.add("早鳥專屬")
    if len(history) >= 30: unlocked.add("通勤馬拉松")
    # 隱藏：死線戰士 (早到 1 分鐘以內)
    if any(h.get("status") == "早到" and h.get("diff", 0) <= 1 for h in history): unlocked.add("死線戰士")
    # 隱藏：舟山路泳將 (雨天早到)
    if any(h.get("weather") == "雨天" and h.get("status") == "早到" for h in history): unlocked.add("舟山路泳將")
    return unlocked

st.set_page_config(page_title="NTU Late Saver", layout="centered")
st.title("NTU Late Saver")
user_name = st.text_input("請輸入您的個人ID以載入數據")

if user_name:
    data = load_data(user_name)
    cur_day, cur_period = get_current_ntu_period_info()
    classroom_list = [loc for loc in data["locations"] if loc not in ["公館捷運站", "科技大樓捷運站"]]
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["記錄通勤", "情境查詢", "智慧防遲到", "課表設定", "成就中心"])
    
    trans_mode = st.sidebar.radio("通勤方式", ["走路", "腳踏車"])
    weather_condition = st.sidebar.radio("當前天氣", ["晴天", "雨天"])

    with tab1:
        s1 = st.selectbox("出發地", data["locations"] + ["其他"], key="s1")
        s1_o = st.text_input("出發地：", key="s1_o") if s1 == "其他" else ""
        d1 = st.selectbox("目的地", data["locations"] + ["其他"], key="d1")
        d1_o = st.text_input("目的地：", key="d1_o") if d1 == "其他" else ""
        
        if "is_timing" not in st.session_state: st.session_state.is_timing = False
        if not st.session_state.is_timing:
            if st.button("開始計時"):
                st.session_state.is_timing = True
                st.session_state.start_time = time.time()
                st.rerun()
        else:
            if st.button("停止計時並記錄狀態"):
                duration = round((time.time() - st.session_state.start_time) / 60, 1)
                st.session_state.is_timing = False
                st.session_state.last_duration = duration
                st.rerun()
        
        if "last_duration" in st.session_state:
            st.write(f"本次通勤耗時: {st.session_state.last_duration} 分鐘")
            # 這裡增加使用者輸入狀況的 UI
            arrival_status = st.radio("本次狀態", ["早到", "遲到"])
            diff = st.number_input("與目標時間差 (分鐘)", min_value=0, value=0, help="請輸入您距離上課時間提前或遲到的分鐘數")
            
            if st.button("確認提交紀錄"):
                data["history"].append({
                    "start": (s1 if s1 != "其他" else s1_o), "dest": (d1 if d1 != "其他" else d1_o),
                    "trans": trans_mode, "weather": weather_condition, "time": st.session_state.last_duration,
                    "status": arrival_status, "diff": diff, "period": cur_period
                })
                save_data(data, user_name)
                st.success("記錄成功！")
                del st.session_state.last_duration
                st.rerun()

    with tab2:
        s2 = st.selectbox("出發地", data["locations"] + ["其他"], key="s2")
        s2_o = st.text_input("出發地：", key="s2_o") if s2 == "其他" else ""
        d2 = st.selectbox("目的地", data["locations"] + ["其他"], key="d2")
        d2_o = st.text_input("目的地：", key="d2_o") if d2 == "其他" else ""
        if st.button("查詢並清洗數據"):
            recs = [h for h in data["history"] if h["start"] == (s2 if s2 != "其他" else s2_o) and h["dest"] == (d2 if d2 != "其他" else d2_o) and h["trans"] == trans_mode and h["weather"] == weather_condition]
            if not recs: st.error("查無紀錄")
            else:
                avg = sum([r["time"] for r in recs]) / len(recs)
                st.info(f"建議平均通勤時間：{round(avg, 1)} 分鐘")

    with tab3:
        st.write(f"系統狀態：{cur_day} / {cur_period}")
        s3 = st.selectbox("出發地", data["locations"] + ["其他"], key="s3")
        q_day = st.selectbox("查詢星期", ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六"])
        q_period = st.selectbox("查詢節次", list(NTU_PERIODS.keys()))
        if st.button("計算出發時間"):
            info = data["schedule"].get(f"{q_day}_{q_period}")
            if not info: st.warning("請先設定課表")
            else:
                recs = [h for h in data["history"] if h["start"] == s3 and h["dest"] == info["location"]]
                if not recs: st.error("無路段數據")
                else:
                    avg = sum([r['time'] for r in recs]) / len(recs)
                    latest = int((NTU_PERIODS[q_period]["start"][0]*60 + NTU_PERIODS[q_period]["start"][1]) - avg)
                    st.metric("最晚出發時間", f"{latest//60:02d}:{latest%60:02d}")

    with tab4:
        c_day = st.selectbox("上課星期", ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六"])
        c_period = st.selectbox("上課節次", list(NTU_PERIODS.keys()))
        c_loc = st.selectbox("教室位置", classroom_list + ["其他"])
        c_loc_o = st.text_input("輸入教室") if c_loc == "其他" else ""
        if st.button("儲存課表"):
            data["schedule"][f"{c_day}_{c_period}"] = {"location": c_loc if c_loc != "其他" else c_loc_o}
            save_data(data, user_name)
            st.success("更新成功")

    with tab5:
        st.subheader("🏆 成就與稱號")
        ACHIEVEMENTS = {"通勤新手": "累積 1 次紀錄", "早鳥專屬": "第 2 節前完成 3 次早到", "通勤馬拉松": "累積 30 次通勤", "死線戰士": "？？？", "舟山路泳將": "？？？"}
        unlocked = get_unlocked_titles(data["history"])
        cols = st.columns(2)
        for i, (t, c) in enumerate(ACHIEVEMENTS.items()):
            with cols[i % 2]:
                if t in unlocked: st.success(f"✅ {t}")
                else: st.warning(f"🔒 {t}\n條件：{c}")
else: st.info("請輸入ID開始使用")

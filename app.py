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
    default_locs = ["公館捷運站", "科技大樓捷運站", "新生教學館", "綜合體育館", "博雅教學館", "共同教學館", "台大管院1管", "台大管院2管", "綜合教學館", "舊體育館", "戶外泳池"]
    if not os.path.exists(filename): return {"history": [], "locations": default_locs, "schedule": {}}
    with open(filename, "r", encoding="utf-8") as f: data = json.load(f)
    if "locations" not in data: data["locations"] = default_locs
    if "schedule" not in data: data["schedule"] = {}
    return data

def save_data(data, username):
    with open(get_user_file(username), "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

def get_current_period():
    tz = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(tz)
    weekday_idx = now.weekday()
    days = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    if weekday_idx == 6: return days[weekday_idx], "休息時間"
    val = now.hour * 60 + now.minute
    for p, t in NTU_PERIODS.items():
        s = t["start"][0] * 60 + t["start"][1]
        if s <= val < (s + 50): return days[weekday_idx], p
    return days[weekday_idx], "休息時間"

def get_unlocked_titles(history):
    unlocked = set()
    if len(history) >= 1: unlocked.add("通勤新手")
    if len([h for h in history if h.get("period") in ["第 0 節", "第 1 節"] and h.get("status") == "早到"]) >= 3: unlocked.add("早鳥專屬")
    if len(history) >= 30: unlocked.add("通勤馬拉松")
    if any(h.get("status") == "早到" and h.get("diff", 0) <= 1 for h in history): unlocked.add("死線戰士")
    if any(h.get("weather") == "雨天" and h.get("status") == "早到" for h in history): unlocked.add("舟山路泳將")
    return unlocked

st.set_page_config(page_title="NTU Late Saver", layout="centered")
st.title("NTU Late Saver")
user_name = st.text_input("請輸入您的個人ID")

if user_name:
    data = load_data(user_name)
    cur_day, cur_period = get_current_period()
    locs = data["locations"]
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["記錄通勤", "情境查詢", "智慧防遲到", "課表設定", "成就中心"])
    
    mode = st.sidebar.radio("通勤方式", ["走路", "腳踏車"])
    weather = st.sidebar.radio("天氣", ["晴天", "雨天"])

    with tab1:
        s1 = st.selectbox("出發地", locs + ["其他"], key="s1")
        s1_o = st.text_input("出發地：", key="s1_o") if s1 == "其他" else ""
        d1 = st.selectbox("目的地", locs + ["其他"], key="d1")
        d1_o = st.text_input("目的地：", key="d1_o") if d1 == "其他" else ""
        
        if "is_timing" not in st.session_state: st.session_state.is_timing = False
        if not st.session_state.is_timing:
            if st.button("開始計時"):
                st.session_state.is_timing = True
                st.session_state.start_time = time.time()
                st.rerun()
        else:
            if st.button("停止計時"):
                st.session_state.last_dur = round((time.time() - st.session_state.start_time) / 60, 1)
                st.session_state.is_timing = False
                st.rerun()
        
        if "last_dur" in st.session_state:
            st.subheader(f"本次耗時：{st.session_state.last_dur} 分鐘")
            status = st.radio("本次狀態", ["早到", "遲到"])
            diff = st.number_input("與目標時間差 (分)", min_value=0, value=0)
            if st.button("確認提交"):
                data["history"].append({"start": (s1 if s1 != "其他" else s1_o), "dest": (d1 if d1 != "其他" else d1_o), "trans": mode, "weather": weather, "time": st.session_state.last_dur, "status": status, "diff": diff, "period": cur_period})
                save_data(data, user_name)
                st.success("記錄已儲存！")
                del st.session_state.last_dur
                st.rerun()

    with tab2:
        s2 = st.selectbox("出發地", locs + ["其他"], key="s2")
        d2 = st.selectbox("目的地", locs + ["其他"], key="d2")
        if st.button("查詢並清洗數據"):
            recs = [h for h in data["history"] if h["start"] == (s2 if s2!="其他" else st.text_input("起點", key="s2o")) and h["dest"] == (d2 if d2!="其他" else st.text_input("終點", key="d2o")) and h["trans"] == mode and h["weather"] == weather]
            if not recs: st.error("查無紀錄")
            else:
                avg = sum([r["time"] for r in recs]) / len(recs)
                st.info(f"平均通勤時間：{round(avg, 1)} 分鐘")

    with tab3:
        s3 = st.selectbox("出發地", locs + ["其他"], key="s3")
        q_day = st.selectbox("星期", ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六"])
        q_period = st.selectbox("節次", list(NTU_PERIODS.keys()))
        if st.button("計算出發時間"):
            info = data["schedule"].get(f"{q_day}_{q_period}")
            if not info: st.warning("請先設定課表")
            else:
                recs = [h for h in data["history"] if h["start"] == (s3 if s3!="其他" else st.text_input("起點", key="s3o")) and h["dest"] == info["location"]]
                if not recs: st.error("無路段數據")
                else:
                    avg = sum([r['time'] for r in recs]) / len(recs)
                    latest = int((NTU_PERIODS[q_period]["start"][0]*60 + NTU_PERIODS[q_period]["start"][1]) - avg)
                    st.metric("最晚出發時間", f"{latest//60:02d}:{latest%60:02d}")

    with tab4:
        c_day = st.selectbox("上課星期", ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六"])
        c_period = st.selectbox("上課節次", list(NTU_PERIODS.keys()))
        c_loc = st.selectbox("教室", [l for l in locs if l not in ["公館捷運站", "科技大樓捷運站"]] + ["其他"])
        if st.button("儲存課表"):
            data["schedule"][f"{c_day}_{c_period}"] = {"location": c_loc if c_loc != "其他" else st.text_input("輸入教室", key="loco")}
            save_data(data, user_name)
            st.success("課表已更新")

    with tab5:
        st.subheader("🏆 成就收藏櫃")
        ACHIEVEMENTS = {"通勤新手": "累積 1 次", "早鳥專屬": "第 2 節前 3 次早到", "通勤馬拉松": "累積 30 次", "死線戰士": "？？？", "舟山路泳將": "？？？"}
        STYLE_MAP = {"通勤新手": ("green", "🔰"), "早鳥專屬": ("blue", "🐦"), "通勤馬拉松": ("orange", "🏃"), "死線戰士": ("violet", "⚔️"), "舟山路泳將": ("blue", "🏊")}
        
        unlocked = get_unlocked_titles(data["history"])
        if "last_cnt" not in st.session_state: st.session_state.last_cnt = len(unlocked)
        if len(unlocked) > st.session_state.last_cnt:
            st.balloons()
            st.session_state.last_cnt = len(unlocked)
            
        cols = st.columns(2)
        for i, (t, c) in enumerate(ACHIEVEMENTS.items()):
            with cols[i % 2]:
                if t in unlocked:
                    col, icon = STYLE_MAP.get(t, ("green", "✅"))
                    st.markdown(f"**{icon} :{col}[{t}]**")
                else:
                    st.markdown(f"🔒 :gray[{t}]")
                    with st.expander("查看條件"): st.caption(c)
else: st.info("請輸入ID開始")

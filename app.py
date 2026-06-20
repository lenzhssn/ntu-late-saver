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
    if len([h for h in history if h.get("status") == "早到" and h.get("diff", 0) >= 1]) >= 3: 
        unlocked.add("時間管理大師")
    if len(history) >= 30: unlocked.add("全勤獎")
    if len([h for h in history if h.get("period") in ["第 0 節", "第 1 節"] and h.get("status") == "早到"]) >= 3: 
        unlocked.add("早起的鳥兒")
    if any(h.get("weather") == "雨天" and h.get("status") == "早到" for h in history): 
        unlocked.add("舟山河泳將")
    if len([h for h in history if h.get("status") == "遲到"]) >= 5: 
        unlocked.add("請問你現在那邊是幾點")
    return unlocked

st.set_page_config(page_title="NTU Late Saver", layout="centered")
st.title("NTU Late Saver")
user_name = st.text_input("請輸入您的個人ID")

if user_name:
    data = load_data(user_name)
    cur_day, cur_period = get_current_period()
    locs = data["locations"]
    
    st.sidebar.info(f"當前時間：{cur_day} {cur_period}")
    
    if cur_period != "休息時間":
        key = f"{cur_day}_{cur_period}"
        if key in data["schedule"]:
            start_h, start_m = NTU_PERIODS[cur_period]["start"]
            start_min = start_h * 60 + start_m
            now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
            now_min = now.hour * 60 + now.minute
            diff = start_min - now_min
            if 0 < diff <= 15:
                st.warning(f"⚠️ {cur_period} starts in {diff} minutes! Move now!")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["記錄通勤", "情境查詢", "智慧防遲到", "課表設定", "成就中心"])
    mode = st.sidebar.radio("通勤方式", ["走路", "腳踏車"])
    weather = st.sidebar.radio("天氣", ["晴天", "雨天"])

    with tab1:
        s1 = st.selectbox("出發地", locs + ["其他"], key="s1")
        d1 = st.selectbox("目的地", locs + ["其他"], key="d1")
        
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
            st.divider()
            st.subheader(f"本次耗時：{st.session_state.last_dur} 分鐘")
            status = st.radio("本次狀態", ["早到", "遲到"])
            diff = st.number_input("與目標時間差 (分)", min_value=1, value=1)
            
            matched_class = None
            key = f"{cur_day}_{cur_period}"
            if key in data["schedule"]:
                matched_class = data["schedule"][key]["location"]

            if st.button("確認提交紀錄"):
                data["history"].append({
                    "start": s1, "dest": d1, "trans": mode, "weather": weather, 
                    "time": st.session_state.last_dur, "status": status, 
                    "diff": diff, "period": cur_period, "class": matched_class
                })
                save_data(data, user_name)
                msg = "紀錄已儲存！"
                if matched_class: msg += f" (已自動綁定課程: {matched_class})"
                st.success(msg)
                del st.session_state.last_dur
                st.rerun()

    with tab2:
        s2 = st.selectbox("出發地", locs + ["其他"], key="s2")
        d2 = st.selectbox("目的地", locs + ["其他"], key="d2")
        if st.button("查詢數據"):
            recs = [h for h in data["history"] if h["start"] == s2 and h["dest"] == d2]
            if not recs: st.error("查無紀錄")
            else: st.info(f"平均通勤時間：{round(sum([r['time'] for r in recs])/len(recs), 1)} 分鐘")
                
    with tab3:
        s3 = st.selectbox("預測起點", locs, key="s3")
        d3 = st.selectbox("預測終點", locs, key="d3")
        
        relevant = [h for h in data["history"] if h["start"] == s3 and h["dest"] == d3]
        pred_time = None
        if relevant:
            matches = [h["time"] for h in relevant if h["trans"] == mode and h["weather"] == weather]
            if matches:
                pred_time = sum(matches) / len(matches)
            else:
                base = relevant[0]["time"]
                if mode != relevant[0]["trans"]:
                    pred_time = base * 3.5 if mode == "走路" else base / 3.5
                elif weather != relevant[0]["weather"]:
                    pred_time = base * 1.5 if weather == "雨天" else base / 1.5
                else:
                    pred_time = base

        if pred_time:
            st.info(f"推算耗時：{round(pred_time, 1)} 分鐘")
            st.caption("* 此數據為基於您的歷史經驗法則推算，實際狀況請依路況調整。")
        else:
            st.warning("尚無足夠數據進行推算，請多記錄幾次通勤！")
        
        s3_extra = st.selectbox("出發地", locs + ["其他"], key="s3_extra")
        q_day = st.selectbox("星期", ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六"])
        q_p = st.selectbox("節次", list(NTU_PERIODS.keys()))
        if st.button("計算出發時間"):
            info = data["schedule"].get(f"{q_day}_{q_p}")
            if not info: st.warning("請先設定課表")
            else:
                recs = [h for h in data["history"] if h["start"] == s3_extra and h["dest"] == info["location"] and h["trans"] == mode and h["weather"] == weather]
                if not recs: st.error("無符合條件的數據，嘗試關閉模式/天氣篩選或多記錄幾次通勤")
                else:
                    avg = sum([r['time'] for r in recs]) / len(recs)
                    latest = int((NTU_PERIODS[q_p]["start"][0]*60 + NTU_PERIODS[q_p]["start"][1]) - avg)
                    st.metric("最晚出發時間", f"{latest//60:02d}:{latest%60:02d}")

    with tab4:
        c_day = st.selectbox("上課星期", ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六"])
        c_p = st.selectbox("上課節次", list(NTU_PERIODS.keys()))
        c_loc = st.selectbox("教室", [l for l in locs if l not in ["公館捷運站", "科技大樓捷運站"]] + ["其他"])
        if st.button("儲存課表"):
            data["schedule"][f"{c_day}_{c_p}"] = {"location": c_loc if c_loc != "其他" else st.text_input("輸入教室", key="loco")}
            save_data(data, user_name)
            st.success("課表已更新")

    with tab5: 
        ACH = {
            "時間管理大師": ("green", "⏰", "早到 1 分鐘以上，累積 3 次", True),
            "早起的鳥兒": ("yellow", "🐦", "早8以前的課累計早到3次", False),
            "請問你現在那邊是幾點": ("red", "🤡", "累積遲到 5 次", True),
            "全勤獎": ("orange", "✨", "累積 30 次通勤", False),
            "舟山河泳將": ("blue", "🏊", "雨天早到", True)
        }
        
        current_unlocked = get_unlocked_titles(data["history"])
        if "unlocked_history" not in st.session_state: st.session_state.unlocked_history = set()
        if len(current_unlocked) > len(st.session_state.unlocked_history):
            st.balloons()
            st.session_state.unlocked_history = current_unlocked
            
        cols = st.columns(2)
        for i, (t, (col, icon, desc, is_hidden)) in enumerate(ACH.items()):
            with cols[i % 2]:
                if t in current_unlocked:
                    st.markdown(f"**{icon} :{col}[{t}]**")
                    with st.expander("查看條件 (已達成)"): st.caption(desc)
                else:
                    st.markdown(f"🔒 :gray[{t}]")
                    with st.expander("查看條件"): st.caption("？？？" if is_hidden else desc)
else: st.info("請輸入ID開始")

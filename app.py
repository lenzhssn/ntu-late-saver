import json
import os
import time
import datetime
import streamlit as st

# 節次時間定義 (保持不變)
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
    # 時間管理大師：早到 1 分鐘以上，累積 3 次
    if len([h for h in history if h.get("status") == "早到" and h.get("diff", 0) >= 1]) >= 3: 
        unlocked.add("時間管理大師")
    # 全勤獎：累積 30 次通勤
    if len(history) >= 30: unlocked.add("全勤獎")
    # 早起的鳥兒：第0/1節早到3次
    if len([h for h in history if h.get("period") in ["第 0 節", "第 1 節"] and h.get("status") == "早到"]) >= 3: 
        unlocked.add("早起的鳥兒")
    # 舟山河泳將：雨天早到
    if any(h.get("weather") == "雨天" and h.get("status") == "早到" for h in history): 
        unlocked.add("舟山河泳將")
    # 請問你現在那邊是幾點：累積遲到 5 次
    if len([h for h in history if h.get("status") == "遲到"]) >= 5: 
        unlocked.add("請問你現在那邊是幾點")
    return unlocked

st.set_page_config(page_title="NTU Late Saver", layout="centered")
st.title("NTU Late Saver")
user_name = st.text_input("請輸入您的個人ID")

if user_name:
    data = load_data(user_name)
    cur_day, cur_period = get_current_period() # 自動抓取當前節次
    locs = data["locations"]
    
    st.sidebar.info(f"當前時間節次：{cur_period}") # 顯示給使用者確認
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["記錄通勤", "情境查詢", "智慧防遲到", "課表設定", "成就中心"])
    mode = st.sidebar.radio("通勤方式", ["走路", "腳踏車"])
    weather = st.sidebar.radio("天氣", ["晴天", "雨天"])

    with tab1:
        s1 = st.selectbox("出發地", locs + ["其他"], key="s1")
        d1 = st.selectbox("目的地", locs + ["其他"], key="d1")
        
        if not st.session_state.get("is_timing", False):
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
            # 強制要求至少 1 分鐘，作為判定依據
            diff = st.number_input("與目標時間差 (分鐘)", min_value=1, value=1)
            
            if st.button("確認提交紀錄"):
                data["history"].append({
                    "start": s1, "dest": d1, "trans": mode, "weather": weather, 
                    "time": st.session_state.last_dur, "status": status, 
                    "diff": diff, "period": cur_period # 自動儲存當前自動偵測到的節次
                })
                save_data(data, user_name)
                st.success(f"紀錄已存入：{cur_period}")
                del st.session_state.last_dur
                st.rerun()

    # ... (其餘 tab 維持原樣)
    with tab5:
        st.subheader("🏆 成就收藏櫃")
        ACH = {
            "時間管理大師": ("blue", "⏰", "早到 1 分鐘以上，累積 3 次", True),
            "早起的鳥兒": ("yellow", "🐦", "早8以前的課累計早到3次", False),
            "請問你現在那邊是幾點": ("red", "🤡", "累積遲到 5 次", True),
            "全勤獎": ("orange", "✨", "累積 30 次通勤", False),
            "舟山河泳將": ("cyan", "🏊", "雨天早到", True)
        }
        unlocked = get_unlocked_titles(data["history"])
        # (成就顯示邏輯保持不變)
        cols = st.columns(2)
        for i, (t, (col, icon, desc, is_hidden)) in enumerate(ACH.items()):
            with cols[i % 2]:
                if t in unlocked:
                    st.markdown(f"**{icon} :{col}[{t}]**")
                    with st.expander("查看條件 (已達成)"): st.caption(desc)
                else:
                    st.markdown(f"🔒 :gray[{t}]")
                    display_desc = "？？？" if is_hidden else desc
                    with st.expander("查看條件"): st.caption(display_desc)
else: st.info("請輸入ID開始")

import json
import os
import time
import datetime
import streamlit as st

DATA_FILE = "ntu_personal_data.json"

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

def load_data():
    default_locations = [
        "公館捷運站", "科技大樓捷運站", "新生教學館", "綜合體育館", "女九", "博雅教學館",
        "共同教學館", "台大管院1管", "台大管院2管", "綜合教學館", "活大", "二活", "舊體育館", "戶外泳池"
    ]
    if not os.path.exists(DATA_FILE):
        return {"history": [], "locations": default_locations, "schedule": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "locations" not in data:
        data["locations"] = default_locations
    else:
        for loc in default_locations:
            if loc not in data["locations"]:
                data["locations"].append(loc)
    if "schedule" not in data:
        data["schedule"] = {}
    return data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_current_ntu_period_info():
    now = datetime.datetime.now()
    weekday_idx = now.weekday()
    days = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    current_day = days[weekday_idx] if weekday_idx < 6 else "星期一"
    current_time_val = now.hour * 60 + now.minute
    current_period = "第 1 節"
    for period, t_range in NTU_PERIODS.items():
        start_val = t_range["start"][0] * 60 + t_range["start"][1]
        if current_time_val <= start_val + 50:
            current_period = period
            break
    return current_day, current_period

# --- 網頁全域外觀設定（高級感深色調）---
st.set_page_config(page_title="NTU Late Saver", layout="centered")

# 修正相容性：移除舊版 markdown 注入法，改用最新的 st.html 來穩定渲染極簡純黑風格
st.html("""
    <style>
    .stApp {
        background-color: #12131a;
        color: #e2e8f0;
    }
    h1 {
        font-weight: 400 !important;
        letter-spacing: 0.5px;
        color: #f7fafc;
        margin-bottom: 25px !important;
    }
    .stButton>button {
        background-color: #2b5c8f !important;
        color: white !important;
        border-radius: 4px !important;
        border: none !important;
        padding: 6px 20px !important;
        transition: background-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #1f446c !important;
    }
    div[data-baseweb="tab-list"] {
        gap: 8px;
    }
    button[data-baseweb="tab"] {
        color: #a0aec0 !important;
        font-size: 14px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #f7fafc !important;
        border-bottom-color: #2b5c8f !important;
    }
    </style>
""")

st.title("NTU Late Saver")

data = load_data()
cur_day_init, cur_period_init = get_current_ntu_period_info()
classroom_options = [loc for loc in data["locations"] if loc not in ["公館捷運站", "科技大樓捷運站"]]

tab1, tab2, tab3, tab4 = st.tabs(["紀錄通勤", "情境查詢", "智慧防遲到", "課表設定"])

st.sidebar.markdown("### 全域環境設定")
trans_mode = st.sidebar.radio("通勤方式", ["走路", "腳踏車"])
weather_condition = st.sidebar.radio("當前天氣", ["晴天", "雨天"])

# --- 分頁 1：紀錄通勤 ---
with tab1:
    st.markdown("<br>", unsafe_with_html_allowed=True)
    s1 = st.selectbox("出發地", data["locations"] + ["其他"], key="s1")
    s1_other = st.text_input("新起點名稱", placeholder="請輸入自訂起點", key="s1_o") if s1 == "其他" else ""
    
    d1 = st.selectbox("目的地", data["locations"] + ["其他"], key="d1")
    d1_other = st.text_input("新終點名稱", placeholder="請輸入自訂終點", key="d1_o") if d1 == "其他" else ""
    
    if "is_timing" not in st.session_state:
        st.session_state.is_timing = False
        st.session_state.start_time = 0

    if not st.session_state.is_timing:
        if st.button("開始計時", key="btn_t1"):
            st.session_state.is_timing = True
            st.session_state.start_time = time.time()
            st.rerun()
    else:
        st.warning("系統正持續記錄通勤時間中...")
        if st.button("停止計時並儲存", key="btn_t2"):
            duration = round((time.time() - st.session_state.start_time) / 60, 1)
            st.session_state.is_timing = False
            
            start_loc = s1 if s1 != "其他" else s1_other
            dest_loc = d1 if d1 != "其他" else d1_other
            
            if start_loc and dest_loc:
                if start_loc not in data["locations"] and s1 == "其他":
                    data["locations"].append(start_loc)
                if dest_loc not in data["locations"] and d1 == "其他":
                    data["locations"].append(dest_loc)
                
                data["history"].append({
                    "start": start_loc, "dest": dest_loc, "trans": trans_mode,
                    "weather": weather_condition, "time": duration
                })
                save_data(data)
                st.success(f"數據儲存完成。自 {start_loc} 至 {dest_loc} 實測耗時 {duration} 分鐘。")
                time.sleep(1)
                st.rerun()

# --- 分頁 2：情境查詢 ---
with tab2:
    st.markdown("<br>", unsafe_with_html_allowed=True)
    s2 = st.selectbox("出發地", data["locations"] + ["其他"], key="s2")
    s2_other = st.text_input("新起點名稱", placeholder="請輸入自訂起點", key="s2_o") if s2 == "其他" else ""
    
    d2 = st.selectbox("目的地", data["locations"] + ["其他"], key="d2")
    d2_other = st.text_input("新終點名稱", placeholder="請輸入自訂終點", key="d2_o") if d2 == "其他" else ""
    
    if st.button("查詢歷史數據"):
        start_loc = s2 if s2 != "其他" else s2_other
        dest_loc = d2 if d2 != "其他" else d2_other
        records = [h for h in data["history"] if h["start"] == start_loc and h["dest"] == dest_loc and h["trans"] == trans_mode and h["weather"] == weather_condition]
        
        if not records:
            st.error(f"資料庫查無歷史數據。請先建立自 {start_loc} 至 {dest_loc} 的通勤紀錄。")
        else:
            avg_commute = round(sum(r["time"] for r in records) / len(records), 1)
            st.info(f"分析結果：在該情境下，歷史平均通勤時間為 {avg_commute} 分鐘。")

# --- 分頁 3：智慧防遲到 ---
with tab3:
    st.markdown("<br>", unsafe_with_html_allowed=True)
    s3 = st.selectbox("出發地", data["locations"] + ["其他"], key="s3")
    s3_other = st.text_input("新起點名稱", placeholder="請輸入自訂起點", key="s3_o") if s3 == " campaigners" else ""
    
    q_day = st.selectbox("查詢星期", ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六"], index=["星期一", "星期二", "星期三", "星期四", "星期五", "星期六"].index(cur_day_init))
    q_period = st.selectbox("查詢節次", list(NTU_PERIODS.keys()), index=list(NTU_PERIODS.keys()).index(cur_period_init))
    
    if st.button("計算出發時限"):
        start_loc = s3 if s3 != "其他" else s3_other
        schedule_key = f"{q_day}_{q_period}"
        class_info = data.get("schedule", {}).get(schedule_key, None)
        
        if not class_info or not class_info.get("has_class"):
            st.warning(f"查無課程排定資料。請先至【課表設定】分頁綁定教室。")
        else:
            d3 = class_info.get("location")
            records = [h for h in data["history"] if h["start"] == start_loc and h["dest"] == d3 and h["trans"] == trans_mode and h["weather"] == weather_condition]
            
            if not records:
                st.error(f"已識別課程教室為 【{d3}】。但系統缺少自 【{start_loc}】 至該教室的通勤數據，無法推算。")
            else:
                avg_commute = round(sum(r["time"] for r in records) / len(records), 1)
                p_info = NTU_PERIODS[q_period]
                class_start_in_mins = p_info["start"][0] * 60 + p_info["start"][1]
                latest_dep = int(class_start_in_mins - avg_commute)
                
                st.html(f"""
                <div style="padding: 20px; border: 1px solid #2d3748; background-color: #16171f; border-radius: 4px; margin-top: 15px;">
                    <span style="color: #a0aec0; font-size: 13px;">課程定位：{q_day} {q_period} 於 {d3}</span><br>
                    <span style="color: #a0aec0; font-size: 13px;">上課時間：{p_info["start"][0]:02d}:{p_info["start"][1]:02d}</span>
                    <hr style="border-color: #2d3748; margin: 12px 0;">
                    <div style="font-size: 14px; color: #cbd5e1; font-weight: 300; letter-spacing: 0.5px;">最晚出發防線</div>
                    <div style="font-size: 36px; font-weight: 600; color: #e53e3e; margin-top: 5px; font-family: monospace;">
                        {latest_dep // 60:02d}:{latest_dep % 60:02d}
                    </div>
                </div>
                """)

# --- 分頁 4：課表設定 ---
with tab4:
    st.markdown("<br>", unsafe_with_html_allowed=True)
    c_day = st.selectbox("上課星期", ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六"])
    c_period = st.selectbox("上課節次", list(NTU_PERIODS.keys()))
    c_loc = st.selectbox("教室位置", classroom_options)
    
    if st.button("儲存課表綁定"):
        key = f"{c_day}_{c_period}"
        data["schedule"][key] = {"has_class": True, "location": c_loc}
        save_data(data)
        st.success(f"設定已更新：{c_day} {c_period} 教室已綁定為 【{c_loc}】")

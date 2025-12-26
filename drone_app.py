import streamlit as st
import requests
import pandas as pd
import urllib3

urllib3.disable_warnings()

st.set_page_config(page_title="左營飛行控制 Pro", layout="centered")

# --- UI 樣式升級 ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; border-radius: 15px; padding: 20px; border: 1px solid #f0f2f6; }
    [data-testid="stMetricValue"] { font-size: 2.5rem !important; color: #007bff; font-weight: 800; }
    .stButton>button { width: 100%; border-radius: 25px; background: linear-gradient(135deg, #007bff, #0056b3); color: white; height: 3.5em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("📱 雲端終極版 (V9.0 數據全開)")

API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"
url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"

if st.button('🔄 點我更新左營數據'):
    try:
        response = requests.get(url, verify=False).json()
        recs = response.get('records', {}).get('locations', [{}])[0].get('location', [])
        target = next((l for l in recs if "左營" in l.get('locationName', '')), None)
        
        if target:
            pop, ws = "無資料", "無資料"
            data_time = ""
            wind_trend, time_labels = [], []

            for elem in target.get('weatherElement', []):
                name = elem.get('elementName')
                times = elem.get('time', [])
                
                # 尋找最近一個有數據的時段
                for idx, t in enumerate(times):
                    val = t.get('elementValue', [{}])[0].get('value', '')
                    if val.strip() != "":
                        if name == "PoP12h" and pop == "無資料":
                            pop = val
                            data_time = t.get('startTime', '')[5:16] # 記錄時間點
                        if name == "WS":
                            if ws == "無資料": ws = val
                            if idx < 6:
                                wind_trend.append(float(val))
                                time_labels.append(t.get('startTime', t.get('dataTime', ''))[11:16])
                
            # --- 🚀 飛行決策 ---
            pop_val = float(pop) if str(pop).replace('.','',1).isdigit() else 0
            ws_val = float(ws) if str(ws).replace('.','',1).isdigit() else 0
            
            if pop_val > 30 or ws_val > 7:
                st.error(f"## 🛑 建議停飛\n(數據時間: {data_time})")
            else:
                st.success(f"## ✅ 適合起飛\n(數據時間: {data_time})")

            col1, col2 = st.columns(2)
            col1.metric("💨 風速預估", f"{ws} m/s")
            col2.metric("🌧️ 降雨機率", f"{pop} %")

            if wind_trend:
                st.write("📈 風速趨勢圖")
                st.area_chart(pd.DataFrame({"風速": wind_trend}, index=time_labels))
        else:
            st.error("❌ 找不到左營區資料")
    except Exception as e:
        st.error(f"⚠️ 解析異常: {e}")
else:
    st.info("👋 飛手你好！請點擊上方按鈕獲取最新預報。")
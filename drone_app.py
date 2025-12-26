import streamlit as st
import requests
import pandas as pd
import urllib3

urllib3.disable_warnings()

st.set_page_config(page_title="左營飛行控制 Pro", layout="centered")

# --- UI 樣式強化 ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; border-radius: 15px; padding: 20px; border: 1px solid #f0f2f6; }
    [data-testid="stMetricValue"] { font-size: 2.6rem !important; color: #007bff; font-weight: 800; }
    .stButton>button { width: 100%; border-radius: 25px; background: linear-gradient(135deg, #007bff, #0056b3); color: white; height: 3.5em; font-weight: bold; border: none; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("📱 雲端終極版 (V8.0 鋼鐵解析)")

API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"
url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"

if st.button('🔄 點我更新左營數據'):
    try:
        data = requests.get(url, verify=False).json()
        
        # 1. 深度尋找 Location
        recs = data.get('records', {})
        locs_root = recs.get('locations', recs.get('Locations', [{}]))
        all_locs = locs_root[0].get('location', locs_root[0].get('Location', []))
        
        # 2. 定位左營
        target = next((l for l in all_locs if "左營" in l.get('locationName', l.get('LocationName', ''))), None)
        
        if target:
            elements = target.get('weatherElement', target.get('WeatherElement', []))
            pop, ws = 0.0, 0.0
            wind_trend, time_labels = [], []

            for elem in elements:
                en = str(elem.get('elementName', elem.get('ElementName', ''))).upper()
                times = elem.get('time', elem.get('Time', []))
                
                # --- 智慧解析降雨機率 (掃描所有時段找非 0) ---
                if "POP" in en:
                    for t in times:
                        vals = t.get('elementValue', t.get('ElementValue', []))
                        if vals:
                            try:
                                v = float(vals[0].get('value', 0))
                                if pop == 0 and v > 0: pop = v # 優先抓非0預報
                            except: continue
                
                # --- 智慧解析風速與趨勢 ---
                if "WS" in en:
                    for idx, t in enumerate(times):
                        vals = t.get('elementValue', t.get('ElementValue', []))
                        if vals:
                            try:
                                v = float(vals[0].get('value', 0))
                                if ws == 0 and v > 0: ws = v
                                if idx < 8:
                                    wind_trend.append(v)
                                    t_label = t.get('startTime', t.get('dataTime', '00:00:00'))[11:16]
                                    time_labels.append(t_label)
                            except: continue

            # --- 🚀 飛行決策 ---
            st.markdown("### 🚦 實時飛行建議")
            if pop > 30 or ws > 7:
                st.error(f"## 🛑 建議停飛\n降雨機率({int(pop)}%) 或 風速({ws}m/s) 過高")
            elif ws > 5:
                st.warning(f"## ⚠️ 謹慎操作\n風力稍大，請保持在視距內飛行")
            else:
                st.success(f"## ✅ 適合起飛\n目前左營天氣理想，祝飛行愉快！")

            col1, col2 = st.columns(2)
            col1.metric("💨 風速預估", f"{ws} m/s")
            col2.metric("🌧️ 降雨機率", f"{int(pop)} %")

            if wind_trend:
                st.write("📈 未來風速趨勢")
                st.area_chart(pd.DataFrame({"風速(m/s)": wind_trend}, index=time_labels), height=200)
        else:
            st.error("❌ 找不到左營區資料。")

    except Exception as e:
        st.error(f"⚠️ 解析異常: {e}")
else:
    st.info("👋 歡迎！請點擊按鈕獲取最新左營區數據。")
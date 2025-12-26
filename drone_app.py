import streamlit as st
import requests
import pandas as pd
import urllib3

urllib3.disable_warnings()

st.set_page_config(page_title="左營飛行決策", layout="centered")

# --- UI 樣式優化 ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; border-radius: 15px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; color: #1f1f1f; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #007bff; color: white; height: 3.5em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制")
st.caption("📱 雲端終極版 (V5.0 智慧解析)")

API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"
url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"

if st.button('🔄 點我更新左營數據'):
    try:
        response = requests.get(url, verify=False).json()
        
        # 1. 確保進入 records -> locations -> location
        recs = response.get('records', {})
        locs_root = recs.get('locations', recs.get('Locations', [{}]))
        all_locs = locs_root[0].get('location', locs_root[0].get('Location', []))
        
        # 2. 定位左營區
        target = next((loc for loc in all_locs if "左營" in loc.get('locationName', loc.get('LocationName', ''))), None)
        
        if target:
            elements = target.get('weatherElement', target.get('WeatherElement', []))
            pop, ws = None, None
            wind_trend, time_labels = [], []

            for elem in elements:
                en = elem.get('elementName', elem.get('ElementName', ''))
                times = elem.get('time', elem.get('Time', []))
                
                # --- 智慧抓取邏輯：自動掃描有效數值 ---
                if en == "PoP12h": # 降雨機率
                    for t in times:
                        v = t.get('elementValue', t.get('ElementValue', [{}]))[0].get('value', '')
                        if v.strip() and v != " ":
                            pop = int(v)
                            break
                
                if en == "WS": # 風速
                    for idx, t in enumerate(times):
                        v = t.get('elementValue', t.get('ElementValue', [{}]))[0].get('value', '')
                        if v.strip() and v != " ":
                            if ws is None: ws = int(v) # 抓第一筆當前風速
                            if idx < 6: # 抓前 6 筆做趨勢
                                wind_trend.append(int(v))
                                st_time = t.get('startTime', t.get('dataTime', '00:00:00'))[11:16]
                                time_labels.append(st_time)

            # 設定預設值以防萬一
            pop = pop if pop is not None else 0
            ws = ws if ws is not None else 0

            # --- 🚀 飛行決策燈號 ---
            st.markdown("### 🚦 飛行建議")
            if pop > 30 or ws > 7:
                st.error(f"## 🛑 嚴禁起飛\n風險極高 (降雨 {pop}%, 風速 {ws}m/s)")
            elif ws > 5:
                st.warning(f"## ⚠️ 謹慎飛行\n風力偏強，注意環境變化。")
            else:
                st.success(f"## ✅ 適合飛行\n天氣理想，祝拍攝順利！")

            # --- 📊 數據展示 ---
            col1, col2 = st.columns(2)
            col1.metric("💨 目前風速", f"{ws} m/s")
            col2.metric("🌧️ 降雨機率", f"{pop} %")

            if wind_trend:
                st.write("📈 未來 18 小時風速變化")
                chart_data = pd.DataFrame({"風速": wind_trend}, index=time_labels)
                st.area_chart(chart_data, height=200)
        else:
            st.error("❌ 找不到左營區資料，請稍後再試。")

    except Exception as e:
        st.error(f"⚠️ 系統更新失敗: {e}")
else:
    st.info("👋 飛手你好！請點擊上方按鈕獲取最新左營預報。")
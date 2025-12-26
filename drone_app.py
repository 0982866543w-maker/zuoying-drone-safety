import streamlit as st
import requests
import pandas as pd
import urllib3

urllib3.disable_warnings()

st.set_page_config(page_title="左營飛行控制 Pro", layout="centered")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; border-radius: 15px; padding: 20px; border: 1px solid #f0f2f6; }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; color: #007bff; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 25px; background: #007bff; color: white; height: 3.5em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("📱 雲端終極版 (V10.0 智慧解析)")

API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"
url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"

if st.button('🔄 點我更新左營數據'):
    try:
        data = requests.get(url, verify=False).json()
        
        # 使用最穩定的迴圈搜尋法
        recs = data.get('records', {}).get('locations', [{}])[0].get('location', [])
        # 如果上面路徑失敗，嘗試大寫開頭
        if not recs:
            recs = data.get('Records', {}).get('Locations', [{}])[0].get('Location', [])
            
        target = next((l for l in recs if "左營" in l.get('locationName', l.get('LocationName', ''))), None)
        
        if target:
            pop, ws = "0", "0"
            wind_trend, time_labels = [], []

            for elem in target.get('weatherElement', target.get('WeatherElement', [])):
                name = elem.get('elementName', elem.get('ElementName', ''))
                times = elem.get('time', elem.get('Time', []))
                
                # 掃描時段，跳過空格，抓取第一個有數字的資料
                for idx, t in enumerate(times):
                    vals = t.get('elementValue', t.get('ElementValue', []))
                    if not vals: continue
                    v = str(vals[0].get('value', '0')).strip()
                    
                    if v != "" and v != " ":
                        if name == "PoP12h" and pop == "0": pop = v
                        if name == "WS":
                            if ws == "0": ws = v
                            if idx < 6:
                                wind_trend.append(float(v))
                                time_labels.append(t.get('startTime', t.get('dataTime', ''))[11:16])
            
            # --- 🚀 呈現結果 ---
            st.markdown("### 🚦 實時飛行建議")
            f_pop, f_ws = float(pop), float(ws)
            if f_pop > 30 or f_ws > 7:
                st.error(f"## 🛑 建議停飛\n(風速或降雨過高)")
            else:
                st.success(f"## ✅ 適合起飛\n(天氣理想，祝飛行順利)")

            col1, col2 = st.columns(2)
            col1.metric("💨 目前風速", f"{ws} m/s")
            col2.metric("🌧️ 降雨機率", f"{pop} %")

            if wind_trend:
                st.write("📈 未來風速趨勢")
                st.area_chart(pd.DataFrame({"風速": wind_trend}, index=time_labels))
        else:
            st.error("❌ 找不到左營區資料，請稍後再試。")
    except Exception as e:
        st.error(f"⚠️ 數據解析異常: {e}")
else:
    st.info("👋 辛苦了！點擊上方按鈕，讓我們完成這最後一步。")
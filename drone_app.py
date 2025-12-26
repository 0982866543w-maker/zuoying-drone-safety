import streamlit as st
import requests
import pandas as pd
import urllib3

urllib3.disable_warnings()

st.set_page_config(page_title="左營飛行控制 Pro", layout="centered")

# --- UI 樣式強化 ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; border-radius: 15px; padding: 20px; border: 1px solid #eee; }
    [data-testid="stMetricValue"] { font-size: 2.5rem !important; color: #007bff; font-weight: 800; }
    .stButton>button { width: 100%; border-radius: 25px; background: linear-gradient(135deg, #007bff, #0056b3); color: white; height: 3.5em; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("📱 雲端穩定版 (V6.0 超強魯棒版)")

# 側邊欄除錯工具
show_debug = st.sidebar.checkbox("🐞 開啟數據開發者模式")

API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"
url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"

if st.button('🔄 獲取左營即時決策數據'):
    try:
        res_raw = requests.get(url, verify=False)
        data = res_raw.json()
        
        # 1. 導航至地點清單
        recs = data.get('records', {})
        locs_container = recs.get('locations', recs.get('Locations', [{}]))
        all_locs = locs_container[0].get('location', locs_container[0].get('Location', []))
        
        # 2. 鎖定左營區
        target = next((l for l in all_locs if "左營" in l.get('locationName', l.get('LocationName', ''))), None)
        
        if target:
            elements = target.get('weatherElement', target.get('WeatherElement', []))
            if show_debug:
                st.sidebar.write("✅ 偵測到的欄位:", [e.get('elementName') for e in elements])

            pop, ws = 0, 0
            wind_trend, time_labels = [], []

            for elem in elements:
                name = str(elem.get('elementName', '')).upper()
                times = elem.get('time', elem.get('Time', []))
                
                # --- 智能解析：降雨機率 ---
                if "POP" in name: # 兼容 PoP12h, PoP6h 等
                    for t in times:
                        vals = t.get('elementValue', t.get('ElementValue', []))
                        v = vals[0].get('value', '') if vals else ''
                        if v.strip() and v.isdigit() and int(v) > 0:
                            pop = int(v)
                            break
                
                # --- 智能解析：風速 ---
                if "WS" in name or "WIND" in name:
                    for idx, t in enumerate(times):
                        vals = t.get('elementValue', t.get('ElementValue', []))
                        v = vals[0].get('value', '') if vals else ''
                        if v.strip() and v.isdigit():
                            if ws == 0 and int(v) > 0: ws = int(v)
                            if idx < 8: # 抓取更長趨勢
                                wind_trend.append(int(v))
                                t_label = t.get('startTime', t.get('dataTime', '00:00:00'))[11:16]
                                time_labels.append(t_label)

            # --- 🚀 飛行決策顯示 ---
            st.markdown("### 🚦 實時飛行建議")
            if pop > 30 or ws > 7:
                st.error(f"## 🛑 建議停飛\n降雨({pop}%) 或 風速({ws}m/s) 超標")
            elif ws > 5:
                st.warning(f"## ⚠️ 謹慎操作\n風力較強，請保持視距內飛行")
            else:
                st.success(f"## ✅ 適合起飛\n左營天氣良好，祝飛行愉快！")

            col1, col2 = st.columns(2)
            col1.metric("💨 風速預估", f"{ws} m/s")
            col2.metric("🌧️ 降雨機率", f"{pop} %")

            if wind_trend:
                st.write("📈 未來風速動態趨勢")
                st.line_chart(pd.DataFrame({"風速(m/s)": wind_trend}, index=time_labels))
        else:
            st.error("❌ 無法定位左營區數據。")

    except Exception as e:
        st.error(f"⚠️ 資料解析異常: {e}")
else:
    st.info("👋 歡迎使用左營無人機儀表板。請點擊按鈕獲取數據。")
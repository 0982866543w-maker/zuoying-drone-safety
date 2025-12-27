import streamlit as st
import requests
import pandas as pd
import urllib3

urllib3.disable_warnings()

st.set_page_config(page_title="左營飛行控制 Pro", layout="centered")

# --- 專業介面樣式 ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; border-radius: 15px; padding: 15px; border: 1px solid #eee; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; color: #d63384; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 25px; background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); color: white; height: 3.5em; border: none; font-weight: bold; }
    .info-box { background-color: #f0f7ff; border-radius: 10px; padding: 15px; border-left: 5px solid #2575fc; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制中心")
st.caption("🎯 V18.0 鄉鎮精緻校準版")

API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"
# 切換回鄉鎮級精緻預報 API
URL = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"

if st.button('🔄 獲取左營精確預報資料'):
    try:
        res = requests.get(URL, verify=False, timeout=15)
        data = res.json()
        
        # 深入解析精緻預報結構
        locations = data.get('records', {}).get('locations', [{}])[0].get('location', [])
        # 精確搜尋左營區
        target = next((l for l in locations if "左營" in l.get('locationName', '')), None)

        if target:
            elements = target.get('weatherElement', [])
            weather = {"Temp": "N/A", "Apparent": "N/A", "WS": "0", "PoP": "0", "Desc": "", "Time": ""}

            for elem in elements:
                en = elem.get('elementName', '')
                times = elem.get('time', [])
                if not times: continue
                
                # 鄉鎮預報的標籤名稱與全區 API 不同，需精準比對
                val = times[0].get('elementValue', [{}])[0].get('value', '0')
                
                if en == "T": weather["Temp"] = val # 溫度
                elif en == "AT": weather["Apparent"] = val # 體感
                elif en == "WS": weather["WS"] = val # 風速
                elif en == "PoP12h": weather["PoP"] = val # 降雨機率
                elif en == "WeatherDescription": weather["Desc"] = val # 描述
                
                if not weather["Time"]:
                    weather["Time"] = times[0].get('startTime', '')[5:16].replace('T', ' ')

            # --- 🚀 飛行決策 ---
            f_ws = float(weather["WS"])
            f_pop = int(weather["PoP"]) if weather["PoP"].isdigit() else 0

            st.success(f"📍 觀測地點：左營區 (精緻預報)")
            st.info(f"🕒 資料時段：{weather['Time']}")

            if f_ws > 7 or f_pop > 30:
                st.error(f"## 🛑 建議停飛\n目前預報風速 ({f_ws} m/s) 或降雨 ({f_pop}%) 較高")
            else:
                st.success(f"## ✅ 適合起飛\n左營區預報氣候良好！")

            # --- 📊 數據格位 ---
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🌡️ 預報溫度", f"{weather['Temp']} °C")
                st.metric("💨 預報風速", f"{weather['WS']} m/s")
            with col2:
                st.metric("🧥 體感溫度", f"{weather['Apparent']} °C")
                st.metric("🌧️ 降雨機率", f"{weather['PoP']} %")

            st.markdown(f"""<div class="info-box"><strong>📝 預報摘要：</strong><br>{weather['Desc']}</div>""", unsafe_allow_html=True)
            
        else:
            st.error("❌ 無法在高雄市資料中定位『左營區』，請稍後再試。")

    except Exception as e:
        st.error(f"⚠️ 解析異常: {e}")
else:
    st.info("👋 飛手你好！點擊按鈕獲取與氣象局網頁同步的左營精確預報。")
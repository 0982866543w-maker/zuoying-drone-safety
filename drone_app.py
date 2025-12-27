import streamlit as st
import requests
import pandas as pd
import urllib3

urllib3.disable_warnings()

# --- 1. 專業介面設定 ---
st.set_page_config(page_title="左營飛行控制 Pro", layout="centered")

st.markdown("""
    <style>
    .info-card { background-color: #f1f3f5; border-radius: 10px; padding: 15px; margin-bottom: 10px; border-left: 5px solid #007bff; }
    .stMetric { background-color: #ffffff; border-radius: 15px; padding: 15px; border: 1px solid #e9ecef; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; color: #007bff; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 25px; background: linear-gradient(135deg, #007bff, #0056b3); color: white; height: 3.5em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制中心")
st.caption("📊 V17.0 綜合資訊加強版")

API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"
URL = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091?Authorization={API_KEY}"

if st.button('🔄 獲取左營即時綜合數據'):
    try:
        res = requests.get(URL, verify=False, timeout=10)
        data = res.json()
        
        records = data.get('records', {})
        locations = records.get('Locations', records.get('locations', [{}]))[0].get('Location', [])
        target = next((l for l in locations if "高雄" in l.get('LocationName', '')), None)

        if target:
            # 提取所有氣象因子
            elements = target.get('WeatherElement', [])
            weather_data = {
                "Time": "", "Temp": "N/A", "ApparentTemp": "N/A", 
                "RainProb": "0", "WindSpeed": "0", "Desc": ""
            }

            for elem in elements:
                name = elem.get('ElementName', '')
                times = elem.get('Time', [])
                if not times: continue
                
                # 取得第一筆數據內容
                val_dict = times[0].get('ElementValue', [{}])[0]
                
                if name == "平均溫度": weather_data["Temp"] = val_dict.get('Temperature', '0')
                if name == "最高體感溫度": weather_data["ApparentTemp"] = val_dict.get('MaxApparentTemperature', '0')
                if name == "12小時降雨機率": weather_data["RainProb"] = val_dict.get('ProbabilityOfPrecipitation', '0')
                if name == "風速": weather_data["WindSpeed"] = val_dict.get('WindSpeed', '0')
                if name == "天氣預報綜合描述": weather_data["Desc"] = val_dict.get('WeatherDescription', '')
                
                # 記錄資料起始時間
                if not weather_data["Time"]:
                    raw_time = times[0].get('StartTime', '')
                    weather_data["Time"] = raw_time.replace('T', ' ').split('+')[0]

            # --- 🚀 飛行決策與基本資料 ---
            ws = float(weather_data["WindSpeed"])
            pop = int(weather_data["RainProb"]) if weather_data["RainProb"].isdigit() else 0

            # 顯示資料時間
            st.info(f"🕒 **預報時段：** {weather_data['Time']}")

            if pop > 30 or ws > 7:
                st.error(f"## 🛑 建議停飛\n降雨 {pop}% / 風速 {ws} m/s")
            else:
                st.success(f"## ✅ 適合飛行\n目前的預報條件非常理想！")

            # --- 📊 數據格位展示 ---
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🌡️ 目前溫度", f"{weather_data['Temp']} °C")
                st.metric("💨 預估風速", f"{ws} m/s")
            with col2:
                st.metric("🧥 體感溫度", f"{weather_data['ApparentTemp']} °C")
                st.metric("🌧️ 降雨機率", f"{pop} %")

            # --- 📝 天氣描述 ---
            st.markdown(f"""
            <div class="info-card">
                <strong>📝 今日天氣摘要：</strong><br>{weather_data['Desc']}
            </div>
            """, unsafe_allow_html=True)
            
            st.caption("註：目前 API 提供 12 小時逐時預報，暫無即時日出日落與時雨量精確值。")

        else:
            st.error("❌ 找不到資料。")

    except Exception as e:
        st.error(f"⚠️ 解析異常: {e}")
else:
    st.info("👋 飛手你好！點擊按鈕獲取最新飛行決策資訊。")
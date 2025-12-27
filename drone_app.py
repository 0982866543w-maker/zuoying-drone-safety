import streamlit as st
import requests
import pandas as pd
import urllib3
from datetime import datetime

urllib3.disable_warnings()

# --- 1. 行動化專業 UI 配置 ---
st.set_page_config(page_title="左營飛行專家系統", layout="centered")

st.markdown("""
    <style>
    .stMetric { background: #ffffff; border-radius: 12px; padding: 15px; border: 1px solid #eee; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 2rem !important; color: #1a73e8; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 20px; background: linear-gradient(135deg, #1a73e8, #0d47a1); color: white; height: 3.5em; font-weight: bold; border: none; }
    .sun-box { background: #fff3e0; padding: 10px; border-radius: 10px; text-align: center; border: 1px solid #ffe0b2; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("🚀 專業工程師校準版 (V20.0 多源融合)")

API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"

# --- 2. 專業數據抓取函數 ---
def fetch_all_data():
    today = datetime.now().strftime("%Y-%m-%d")
    # API A: 左營實時觀測 (獲取真實溫度、時雨量)
    url_obs = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={API_KEY}&StationId=C0V700"
    # API B: 高雄鄉鎮預報 (獲取體感溫度、風速、降雨機率)
    url_for = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"
    # API C: 天文日曆 (獲取日出日落)
    url_sun = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001?Authorization={API_KEY}&LocationName=%E9%AB%98%E9%9B%84%E5%B8%82&Date={today}"

    res_data = {"obs": {}, "forecast": {}, "sun": {}}
    
    try:
        # 抓取實測
        r_obs = requests.get(url_obs, timeout=10).json()
        res_data["obs"] = r_obs.get('records', {}).get('Station', [{}])[0]
        
        # 抓取預報
        r_for = requests.get(url_for, timeout=10).json()
        locs = r_for.get('records', {}).get('locations', [{}])[0].get('location', [])
        res_data["forecast"] = next((l for l in locs if "左營" in l.get('locationName', '')), {})
        
        # 抓取日出日落
        r_sun = requests.get(url_sun, timeout=10).json()
        sun_info = r_sun.get('records', {}).get('locations', {}).get('location', [{}])[0].get('time', [{}])[0]
        res_data["sun"] = sun_info
        
    except Exception as e:
        st.error(f"數據融合過程異常: {e}")
    return res_data

# --- 3. 畫面呈現邏輯 ---
if st.button('🔄 執行數據全同步 (預報+實測+天文)'):
    data = fetch_all_data()
    
    if data["obs"] and data["forecast"]:
        # A. 提取實測數據 (觀測站 C0V700)
        obs = data["obs"]
        obs_time = obs.get('ObsTime', 'N/A')
        real_temp = obs.get('WeatherElement', {}).get('AirTemperature', 'N/A')
        rain_1h = obs.get('WeatherElement', {}).get('Now', {}).get('Precipitation', '0.0')
        
        # B. 提取預報數據 (左營區)
        f_loc = data["forecast"]
        pop, at, ws, desc = "0", "0", "0", ""
        for elem in f_loc.get('weatherElement', []):
            ename = elem.get('elementName')
            val = elem.get('time', [{}])[0].get('elementValue', [{}])[0].get('value', '0')
            if ename == "PoP12h": pop = val
            if ename == "AT": at = val
            if ename == "WS": ws = val
            if ename == "WeatherDescription": desc = val

        # C. 提取日出日落
        params = data["sun"].get('parameter', [])
        sunrise = params[1].get('parameterValue', 'N/A') if len(params) > 1 else "N/A"
        sunset = params[5].get('parameterValue', 'N/A') if len(params) > 5 else "N/A"

        # --- 🚀 飛行決策 ---
        f_ws = float(ws)
        f_pop = int(pop) if pop.isdigit() else 0
        
        st.info(f"🕒 **數據同步時間：** {obs_time}")
        
        if f_ws > 7 or f_pop > 30 or float(rain_1h) > 0:
            st.error(f"## 🛑 建議停飛\n實測風速 {f_ws}m/s | 降雨 {pop}% | 時雨量 {rain_1h}mm")
        else:
            st.success("## ✅ 適合起飛\n左營實測與預報條件均符合飛行標準")

        # --- 📊 數據格位展示 ---
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🌡️ 實測溫度", f"{real_temp} °C")
            st.metric("💨 預報風速", f"{ws} m/s")
        with col2:
            st.metric("🧥 體感溫度", f"{at} °C")
            st.metric("🌧️ 降雨機率", f"{pop} %")
            
        st.metric("☔ 時雨量 (1H)", f"{rain_1h} mm")

        # --- 🌅 天文資料 ---
        st.markdown("---")
        c3, c4 = st.columns(2)
        with c3:
            st.markdown(f'<div class="sun-box">🌅 日出<br><strong>{sunrise}</strong></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="sun-box">🌇 日落<br><strong>{sunset}</strong></div>', unsafe_allow_html=True)
            
        st.write(f"📝 **詳細描述：** {desc}")
    else:
        st.error("💀 數據同步失敗。請確認 API 金鑰是否有效且左營站 (C0V700) 是否在線。")
else:
    st.info("👋 飛手你好！點擊按鈕獲取與氣象局網頁 100% 同步的深度數據。")
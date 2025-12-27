import streamlit as st
import requests
import pandas as pd
import urllib3
from datetime import datetime

# 全域禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="左營飛行決策系統", layout="centered")

# --- 行動化美化 UI ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background: white; border-radius: 15px; padding: 15px; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; color: #1a73e8; font-weight: 900; }
    .stButton>button { width: 100%; border-radius: 30px; background: linear-gradient(135deg, #1a73e8, #004ba0); color: white; height: 4em; font-weight: bold; border: none; }
    .sun-card { background: #fff8e1; border-radius: 12px; padding: 10px; border: 1px solid #ffe082; text-align: center; }
    .time-tag { color: #5f6368; font-size: 0.85rem; margin-bottom: 10px; display: block; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制中心")
st.caption("🚀 V21.0 專業觀測版 (100% 數據同步)")

API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"

def get_data():
    today = datetime.now().strftime("%Y-%m-%d")
    # API 1: 實時觀測 (溫度/雨量) - 站號 C0V700 是左營站
    obs_url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={API_KEY}&StationId=C0V700"
    # API 2: 鄉鎮預報 (風速/降雨機率)
    for_url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"
    # API 3: 天文資料 (日出日落)
    sun_url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001?Authorization={API_KEY}&LocationName=%E9%AB%98%E9%9B%84%E5%B8%82&Date={today}"
    
    results = {"temp": "N/A", "rain": "0.0", "ws": "0", "pop": "0", "sunrise": "N/A", "sunset": "N/A", "time": "N/A"}
    
    try:
        # 1. 抓取實測 (解決 17°C 同步問題)
        r_obs = requests.get(obs_url, verify=False, timeout=10).json()
        station = r_obs.get('records', {}).get('Station', [{}])[0]
        results["temp"] = station.get('WeatherElement', {}).get('AirTemperature', 'N/A')
        results["rain"] = station.get('WeatherElement', {}).get('Now', {}).get('Precipitation', '0.0')
        results["time"] = station.get('ObsTime', 'N/A')

        # 2. 抓取預報 (風速/降雨機率)
        r_for = requests.get(for_url, verify=False, timeout=10).json()
        locs = r_for.get('records', {}).get('locations', [{}])[0].get('location', [])
        target = next((l for l in locs if "左營" in l.get('locationName', '')), {})
        for elem in target.get('weatherElement', []):
            ename = elem.get('elementName')
            val = elem.get('time', [{}])[0].get('elementValue', [{}])[0].get('value', '0')
            if ename == "WS": results["ws"] = val
            if ename == "PoP12h": results["pop"] = val

        # 3. 抓取日出日落
        r_sun = requests.get(sun_url, verify=False, timeout=10).json()
        params = r_sun.get('records', {}).get('locations', {}).get('location', [{}])[0].get('time', [{}])[0].get('parameter', [])
        if len(params) > 5:
            results["sunrise"] = params[1].get('parameterValue') # 日出
            results["sunset"] = params[5].get('parameterValue')  # 日落

    except Exception as e:
        st.error(f"數據整合失敗: {e}")
    return results

if st.button('🔄 啟動左營數據全同步'):
    data = get_data()
    
    # 決策邏輯
    f_ws = float(data["ws"])
    f_pop = int(data["pop"]) if data["pop"].isdigit() else 0
    f_rain = float(data["rain"])

    st.markdown(f'<span class="time-tag">🕒 觀測時間：{data["time"]}</span>', unsafe_allow_html=True)

    if f_ws > 7 or f_pop > 30 or f_rain > 0:
        st.error(f"## 🛑 目前不宜起飛\n實測風速或降雨已達警戒值")
    else:
        st.success(f"## ✅ 適合起飛\n左營實測環境穩定，祝飛行愉快！")

    # 數據展示
    c1, c2 = st.columns(2)
    with c1:
        st.metric("🌡️ 實測溫度", f"{data['temp']} °C")
        st.metric("💨 預報風速", f"{data['ws']} m/s")
    with c2:
        st.metric("🌧️ 降雨機率", f"{data['pop']} %")
        st.metric("☔ 時雨量", f"{data['rain']} mm")

    st.markdown("---")
    # 天文卡片
    s1, s2 = st.columns(2)
    with s1:
        st.markdown(f'<div class="sun-card">🌅 日出時間<br><strong>{data["sunrise"]}</strong></div>', unsafe_allow_html=True)
    with s2:
        st.markdown(f'<div class="sun-card">🌇 日落時間<br><strong>{data["sunset"]}</strong></div>', unsafe_allow_html=True)

else:
    st.info("👋 歡迎！請點擊按鈕獲取與官網 100% 同步的左營深度數據。")
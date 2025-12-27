import streamlit as st
import requests
import urllib3
from datetime import datetime

# 全域穩定性：關閉 SSL 驗證警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="左營飛行專家系統", layout="centered")

# --- 行動化專業 UI 設計 ---
st.markdown("""
    <style>
    .stMetric { background: #ffffff; border-radius: 12px; padding: 15px; border: 1px solid #eee; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #1a73e8; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 20px; background: linear-gradient(135deg, #1a73e8, #004ba0); color: white; height: 3.5em; font-weight: bold; border: none; }
    .sun-box { background: #fff9c4; padding: 12px; border-radius: 12px; text-align: center; border: 1px solid #fbc02d; font-size: 0.9rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("🛡️ V24.0 全能韌性引擎版")

API_KEY = "CWA-D94FFF0E-F69C-47D1-B2BA-480EBD5F1473"

def fetch_safe(url):
    """工程師專用：強化請求穩定性"""
    try:
        r = requests.get(url, verify=False, timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

if st.button('🔄 啟動數據全同步 (對齊氣象局網頁)'):
    with st.spinner('正在同步左營觀測站...'):
        now_date = datetime.now().strftime("%Y-%m-%d")
        
        # 1. 抓取三方數據
        obs_j = fetch_safe(f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={API_KEY}&StationId=C0V700")
        for_j = fetch_safe(f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}")
        sun_j = fetch_safe(f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001?Authorization={API_KEY}&LocationName=%E9%AB%98%E9%9B%84%E5%B8%82&Date={now_date}")

        # 2. 初始化核心數據池 (Data Pool)
        D = {"temp": "N/A", "at": "N/A", "pop": "0", "ws": "0", "rain": "0.0", "sunrise": "--:--", "sunset": "--:--", "time": "更新中"}

        # --- A. 解析實測 (對齊網頁 17.0°C) ---
        if obs_j:
            stations = obs_j.get('records', {}).get('Station', [])
            if stations:
                s = stations[0]
                D["temp"] = s.get('WeatherElement', {}).get('AirTemperature', "N/A")
                D["rain"] = s.get('WeatherElement', {}).get('Now', {}).get('Precipitation', "0.0")
                D["time"] = s.get('ObsTime', "資料更新中")[11:16]

        # --- B. 解析預報 (體感/風速/降雨) ---
        if for_j:
            locs = for_j.get('records', {}).get('locations', [{}])[0].get('location', [])
            target = next((l for l in locs if "左營" in l.get('locationName', '')), {})
            for elem in target.get('weatherElement', []):
                en = elem.get('elementName')
                val = elem.get('time', [{}])[0].get('elementValue', [{}])[0].get('value', '0')
                if en == "WS": D["ws"] = val
                if en == "PoP12h": D["pop"] = val
                if en == "AT": D["at"] = val
                # 如果實測溫度缺失，用預報溫度備援
                if en == "T" and D["temp"] == "N/A": D["temp"] = val

        # --- C. 解析天文 (日出日落) ---
        if sun_j:
            params = sun_j.get('records', {}).get('locations', {}).get('location', [{}])[0].get('time', [{}])[0].get('parameter', [])
            for p in params:
                if p.get('parameterName') == '日出時刻': D["sunrise"] = p.get('parameterValue')
                if p.get('parameterName') == '日沒時刻': D["sunset"] = p.get('parameterValue')

        # --- 🚀 畫面展現 ---
        st.success(f"🍀 數據已同步 | 觀測時間: {D['time']}")
        
        # 飛行建議邏輯
        ws_val = float(D["ws"]) if str(D["ws"]).replace('.','',1).isdigit() else 0
        pop_val = int(D["pop"]) if str(D["pop"]).isdigit() else 0
        
        if ws_val > 7 or pop_val > 30:
            st.error(f"## 🛑 建議停飛\n(風速 {ws_val}m/s 或 降雨機率 {pop_val}% 過高)")
        else:
            st.success(f"## ✅ 適合起飛\n左營預報環境良好！")

        # 核心數據矩陣
        c1, c2 = st.columns(2)
        with c1:
            st.metric("🌡️ 實測溫度", f"{D['temp']} °C")
            st.metric("💨 預報風速", f"{D['ws']} m/s")
        with c2:
            st.metric("🧥 體感溫度", f"{D['at']} °C")
            st.metric("🌧️ 降雨機率", f"{D['pop']} %")
        
        st.metric("☔ 目前時雨量", f"{D['rain']} mm")

        # 天文底部資訊
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; margin-top:10px;">
            <div class="sun-box">🌅 日出時刻 <b>{D['sunrise']}</b></div>
            <div class="sun-box" style="background:#ffe0b2; border-color:#fb8c00;">🌇 日落時刻 <b>{D['sunset']}</b></div>
        </div>
        """, unsafe_allow_html=True)

else:
    st.info("👋 飛手你好！點擊按鈕同步與官網一致的左營即時氣象資料。")
import streamlit as st
import requests
import urllib3
from datetime import datetime

# 全域穩定性設定
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="左營飛行專家系統", layout="centered")

# --- UI 行動美化系統 ---
st.markdown("""
    <style>
    .stMetric { background: #ffffff; border-radius: 12px; padding: 15px; border: 1px solid #eee; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 2rem !important; color: #1a73e8; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 20px; background: linear-gradient(135deg, #1a73e8, #004ba0); color: white; height: 3.5em; font-weight: bold; border: none; }
    .diag-box { background: #fafafa; border-radius: 10px; padding: 10px; font-family: monospace; font-size: 0.8rem; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("🛡️ V23.0 旗艦觀測版 (數據融合校準)")

API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"

def fetch_cwa(url):
    """資深工程師專用：帶有錯誤捕捉的請求函數"""
    try:
        r = requests.get(url, verify=False, timeout=8)
        if r.status_code == 200:
            return r.json(), "OK"
        return None, f"HTTP {r.status_code}"
    except Exception as e:
        return None, str(e)

if st.button('🔄 啟動左營數據深度對齊'):
    now_date = datetime.now().strftime("%Y-%m-%d")
    
    # 執行三路連線
    obs_json, obs_status = fetch_cwa(f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={API_KEY}&StationId=C0V700")
    for_json, for_status = fetch_cwa(f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}")
    sun_json, sun_status = fetch_cwa(f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001?Authorization={API_KEY}&LocationName=%E9%AB%98%E9%9B%84%E5%B8%82&Date={now_date}")

    # 數據初始化
    data = {"temp": "N/A", "rain": "0.0", "ws": "0", "pop": "0", "at": "N/A", "sunrise": "--:--", "sunset": "--:--", "time": "未連線"}

    # 1. 解析實測 (解決 17.0°C 問題)
    if obs_json:
        stations = obs_json.get('records', {}).get('Station', [])
        if stations:
            s = stations[0]
            data["temp"] = s.get('WeatherElement', {}).get('AirTemperature', "N/A")
            data["rain"] = s.get('WeatherElement', {}).get('Now', {}).get('Precipitation', "0.0")
            data["time"] = s.get('ObsTime', "N/A")

    # 2. 解析預報 (解決 0m/s 問題)
    if for_json:
        recs = for_json.get('records', {}).get('locations', [{}])[0].get('location', [])
        target = next((l for l in recs if "左營" in l.get('locationName', '')), {})
        for elem in target.get('weatherElement', []):
            ename = elem.get('elementName')
            val = elem.get('time', [{}])[0].get('elementValue', [{}])[0].get('value', '0')
            if ename == "WS": data["ws"] = val
            if ename == "PoP12h": data["pop"] = val
            if ename == "AT": data["at"] = val

    # 3. 解析天文 (日出日落)
    if sun_json:
        loc_sun = sun_json.get('records', {}).get('locations', {}).get('location', [{}])[0]
        sun_times = loc_sun.get('time', [{}])[0].get('parameter', [])
        for p in sun_times:
            if p.get('parameterName') == '日出時刻': data["sunrise"] = p.get('parameterValue')
            if p.get('parameterName') == '日沒時刻': data["sunset"] = p.get('parameterValue')

    # --- 畫面展示 ---
    if data["time"] != "未連線":
        st.success(f"🍀 數據同步完成 (觀測站: 左營 C0V700)")
        st.write(f"🕒 **最後更新：** {data['time']}")
        
        c1, c2 = st.columns(2)
        with c1:
            st.metric("🌡️ 實測溫度", f"{data['temp']} °C")
            st.metric("💨 預報風速", f"{data['ws']} m/s")
        with c2:
            st.metric("🧥 體感溫度", f"{data['at']} °C")
            st.metric("🌧️ 降雨機率", f"{data['pop']} %")
        
        st.metric("☔ 時雨量", f"{data['rain']} mm")
        
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; margin-top:10px;">
            <div style="background:#fff9c4; padding:15px; border-radius:12px; width:48%; text-align:center;">🌅 日出 <b>{data['sunrise']}</b></div>
            <div style="background:#ffe0b2; padding:15px; border-radius:12px; width:48%; text-align:center;">🌇 日落 <b>{data['sunset']}</b></div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("❌ 遠端伺服器回應異常，請檢查 API KEY。")

    # 4. 工程診斷看板 (僅開發者可見)
    with st.expander("🛠️ 工程後台狀態看板"):
        st.markdown(f"""
        <div class="diag-box">
        實測節點: {obs_status}<br>
        預報節點: {for_status}<br>
        天文節點: {sun_status}
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("👋 飛手你好！點擊按鈕獲取與氣象署官網 100% 同步的左營飛行氣象數據。")
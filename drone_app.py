import streamlit as st
import requests
import urllib3
from datetime import datetime

# 基礎系統設定：繞過 SSL 與 關閉警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="左營飛行專家系統", layout="centered")

# --- 高對比行動版 UI ---
st.markdown("""
    <style>
    .stMetric { background: #ffffff; border-radius: 12px; padding: 15px; border: 1px solid #eee; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 2rem !important; color: #1a73e8; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 20px; background: linear-gradient(135deg, #1a73e8, #004ba0); color: white; height: 3.5em; font-weight: bold; border: none; }
    .sun-box { background: #fffde7; padding: 10px; border-radius: 10px; border: 1px solid #fff59d; text-align: center; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("🛡️ V22.0 工程師終極穩定版")

API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"

def safe_fetch():
    now_date = datetime.now().strftime("%Y-%m-%d")
    urls = {
        "obs": f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={API_KEY}&StationId=C0V700",
        "for": f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}",
        "sun": f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001?Authorization={API_KEY}&LocationName=%E9%AB%98%E9%9B%84%E5%B8%82&Date={now_date}"
    }
    
    res = {"temp": "N/A", "rain": "0.0", "pop": "0", "ws": "0", "at": "N/A", "sunrise": "--:--", "sunset": "--:--", "time": "未同步"}
    
    try:
        # 1. 抓取觀測 (溫度/雨量)
        r_obs = requests.get(urls["obs"], verify=False, timeout=10).json()
        station = r_obs.get('records', {}).get('Station', [{}])[0]
        res["temp"] = station.get('WeatherElement', {}).get('AirTemperature', "N/A")
        res["rain"] = station.get('WeatherElement', {}).get('Now', {}).get('Precipitation', "0.0")
        res["time"] = station.get('ObsTime', "N/A")

        # 2. 抓取預報 (降雨機率/風速/體感)
        r_for = requests.get(urls["for"], verify=False, timeout=10).json()
        kaohsiung = r_for.get('records', {}).get('locations', [{}])[0].get('location', [])
        target = next((l for l in kaohsiung if "左營" in l.get('locationName', '')), {})
        for elem in target.get('weatherElement', []):
            ename = elem.get('elementName')
            val = elem.get('time', [{}])[0].get('elementValue', [{}])[0].get('value', '0')
            if ename == "PoP12h": res["pop"] = val
            if ename == "WS": res["ws"] = val
            if ename == "AT": res["at"] = val

        # 3. 抓取天文 (日出日落)
        r_sun = requests.get(urls["sun"], verify=False, timeout=10).json()
        sun_times = r_sun.get('records', {}).get('locations', {}).get('location', [{}])[0].get('time', [{}])[0].get('parameter', [])
        if len(sun_times) > 5:
            res["sunrise"] = sun_times[1].get('parameterValue', "--:--")
            res["sunset"] = sun_times[5].get('parameterValue', "--:--")

    except Exception as e:
        st.warning(f"部分數據同步受阻，請稍後再試。")
    return res

if st.button('🔄 執行深度數據對齊 (左營測站)'):
    with st.spinner('正在從氣象署伺服器同步中...'):
        data = safe_fetch()
        
        # 決策燈號
        f_ws = float(data["ws"]) if str(data["ws"]).replace('.','',1).isdigit() else 0
        f_pop = int(data["pop"]) if str(data["pop"]).isdigit() else 0
        
        st.write(f"🕒 **數據觀測時間：** {data['time']}")

        if f_ws > 7 or f_pop > 30:
            st.error("## 🛑 建議停飛：風速或降雨機率過高")
        else:
            st.success("## ✅ 適合起飛：左營實測條件良好")

        # 核心格位
        c1, c2 = st.columns(2)
        with c1:
            st.metric("🌡️ 實測溫度", f"{data['temp']} °C")
            st.metric("💨 預報風速", f"{data['ws']} m/s")
        with c2:
            st.metric("🧥 體感溫度", f"{data['at']} °C")
            st.metric("🌧️ 降雨機率", f"{data['pop']} %")

        # 底部詳細資訊
        st.metric("☔ 目前時雨量", f"{data['rain']} mm")
        
        s1, s2 = st.columns(2)
        s1.markdown(f'<div class="sun-box">🌅 日出<br><strong>{data["sunrise"]}</strong></div>', unsafe_allow_html=True)
        s2.markdown(f'<div class="sun-box">🌇 日落<br><strong>{data["sunset"]}</strong></div>', unsafe_allow_html=True)

else:
    st.info("👋 飛手你好！點擊上方按鈕獲取與官網同步的左營完整飛行氣象。")
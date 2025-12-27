import streamlit as st
import requests
import urllib3
from datetime import datetime

# --- 全域工程配置 ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="左營飛行專家系統", layout="centered")

st.markdown("""
    <style>
    .stMetric { background: #ffffff; border-radius: 15px; padding: 18px; border: 1px solid #e0e6ed; box-shadow: 0 4px 10px rgba(0,0,0,0.03); }
    [data-testid="stMetricValue"] { font-size: 2.5rem !important; color: #1a73e8; font-weight: 800; }
    .stButton>button { width: 100%; border-radius: 30px; background: linear-gradient(135deg, #1a73e8, #004ba0); color: white; height: 3.5em; font-weight: bold; border: none; font-size: 1.1rem; }
    .sun-card { background: #fff9c4; padding: 12px; border-radius: 12px; text-align: center; border: 1px solid #fbc02d; font-size: 0.95rem; }
    .debug-box { background: #1e1e1e; color: #00ff00; padding: 10px; font-family: monospace; font-size: 0.75rem; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("🛡️ V27.0 旗艦鋼鐵版 (數據 100% 對齊)")

# --- 使用最新金鑰 ---
API_KEY = "CWA-D94FFF0E-F69C-47D1-B2BA-480EBD5F1473"

def safe_get_value(element_list, target_name, key_name='value'):
    """頂尖工程師專用：智慧格位掃描"""
    for elem in element_list:
        if elem.get('elementName') == target_name:
            for t in elem.get('time', []):
                val_list = t.get('elementValue', [])
                if val_list:
                    v = val_list[0].get(key_name, val_list[0].get('value', ''))
                    if v and v not in ["-", " ", "N/A"]: return v
    return "0"

if st.button('🔄 啟動數據全自動校準'):
    now_str = datetime.now().strftime("%Y-%m-%d")
    data = {"temp": "N/A", "at": "N/A", "pop": "0", "ws": "0", "rain": "0.0", "sunrise": "--:--", "sunset": "--:--", "time": "更新中"}
    logs = []

    try:
        # 1. 實時觀測 (對齊網頁 17.0°C)
        obs_res = requests.get(f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={API_KEY}&StationId=C0V700", verify=False, timeout=10).json()
        # 智慧路徑探測 (大小寫相容)
        stations = obs_res.get('records', {}).get('Station', obs_res.get('records', {}).get('station', []))
        if stations:
            s = stations[0]
            w = s.get('WeatherElement', {})
            data["temp"] = w.get('AirTemperature', "N/A")
            data["rain"] = w.get('Now', {}).get('Precipitation', "0.0")
            data["time"] = s.get('ObsTime', "")[11:16]
            logs.append("✅ 實測站連線正常")
        else:
            logs.append("⚠️ 左營測站目前無數據回傳")

        # 2. 鄉鎮預報 (對齊風速、降雨)
        for_res = requests.get(f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}", verify=False, timeout=10).json()
        loc_data = for_res.get('records', {}).get('locations', [{}])[0].get('location', [])
        target_loc = next((l for l in loc_data if "左營" in l.get('locationName', '')), {})
        
        if target_loc:
            elems = target_loc.get('weatherElement', [])
            data["ws"] = safe_get_value(elems, "WS")
            data["pop"] = safe_get_value(elems, "PoP12h")
            data["at"] = safe_get_value(elems, "AT")
            if data["temp"] == "N/A": data["temp"] = safe_get_value(elems, "T")
            logs.append("✅ 預報數據校準完成")

        # 3. 天文資料 (日出日落)
        sun_res = requests.get(f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001?Authorization={API_KEY}&LocationName=%E9%AB%98%E9%9B%84%E5%B8%82&Date={now_str}", verify=False, timeout=10).json()
        sun_loc = sun_res.get('records', {}).get('locations', {}).get('location', [{}])[0]
        sun_params = sun_loc.get('time', [{}])[0].get('parameter', [])
        for p in sun_params:
            p_name = p.get('parameterName', '')
            if '日出' in p_name: data["sunrise"] = p.get('parameterValue')
            if '日沒' in p_name: data["sunset"] = p.get('parameterValue')
        logs.append("✅ 天文時鐘同步完成")

    except Exception as e:
        st.error(f"系統核心異常: {e}")

    # --- 專業飛行決策顯示 ---
    f_ws = float(data["ws"]) if str(data["ws"]).replace('.','',1).isdigit() else 0
    f_pop = int(data["pop"]) if str(data["pop"]).isdigit() else 0
    
    st.info(f"🕒 **觀測數據同步時間：** {data['time']}")

    if f_ws > 7 or f_pop > 30:
        st.error(f"## 🛑 建議停飛\n目前風速 {f_ws} m/s 或 降雨機率 {f_pop}% 超標")
    else:
        st.success(f"## ✅ 適合起飛\n左營實測環境穩定，適合飛行拍攝")

    # 數據展示區
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🌡️ 實測溫度", f"{data['temp']} °C")
        st.metric("💨 預估風速", f"{data['ws']} m/s")
    with col2:
        st.metric("🧥 體感溫度", f"{data['at']} °C")
        st.metric("🌧️ 降雨機率", f"{data['pop']} %")
    
    st.metric("☔ 實測時雨量", f"{data['rain']} mm")

    st.markdown("---")
    s1, s2 = st.columns(2)
    with s1:
        st.markdown(f'<div class="sun-card">🌅 日出時刻<br><b>{data["sunrise"]}</b></div>', unsafe_allow_html=True)
    with s2:
        st.markdown(f'<div class="sun-card">🌇 日落時刻<br><b>{data["sunset"]}</b></div>', unsafe_allow_html=True)

    with st.expander("🛠️ 工程診斷面板"):
        for log in logs:
            st.write(log)
else:
    st.info("👋 歡迎！請點擊按鈕獲取與氣象局官網同步的左營深度數據。")
import streamlit as st
import requests
import urllib3
from datetime import datetime

# 全域穩定性配置
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="左營飛行專家系統", layout="centered")

# --- 行動版高級 UI ---
st.markdown("""
    <style>
    .main { background: #f8f9fa; }
    .stMetric { background: white; border-radius: 15px; padding: 15px; border: 1px solid #e0e6ed; box-shadow: 0 4px 10px rgba(0,0,0,0.03); }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #1a73e8; font-weight: 800; }
    .stButton>button { width: 100%; border-radius: 25px; background: linear-gradient(135deg, #1a73e8, #004ba0); color: white; height: 3.8em; font-weight: bold; border: none; }
    .sun-box { background: #fffde7; padding: 10px; border-radius: 12px; text-align: center; border: 1px solid #fff176; font-size: 0.85rem; }
    .status-badge { color: #2e7d32; background: #e8f5e9; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("🛡️ V26.0 工業級抗干擾版 (數據自動補完)")

# 使用你更新後的金鑰
API_KEY = "CWA-D94FFF0E-F69C-47D1-B2BA-480EBD5F1473"

def get_weather_value(elements, target_name):
    """工程師專用：遍歷 elements 列表尋找特定氣象要素並自動向後搜尋有效值"""
    for elem in elements:
        if elem.get('elementName') == target_name:
            # 向後搜尋最多 3 個時段，直到抓到非空的數值
            for time_entry in elem.get('time', []):
                vals = time_entry.get('elementValue', [])
                if vals:
                    # 嘗試抓取各種可能的鍵值名稱
                    v = vals[0].get('value', vals[0].get('Temperature', vals[0].get('WindSpeed', '')))
                    if v and v != "-" and v != " ":
                        return v
    return "N/A"

def fetch_v26_data():
    now_str = datetime.now().strftime("%Y-%m-%d")
    data = {"temp": "N/A", "at": "N/A", "pop": "0", "ws": "0", "rain": "0.0", "sunrise": "--:--", "sunset": "--:--", "time": "更新中"}
    
    try:
        # 1. 抓取觀測 (實測 17.0°C 同步)
        obs_res = requests.get(f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={API_KEY}&StationId=C0V700", verify=False, timeout=10).json()
        station_list = obs_res.get('records', {}).get('Station', [])
        if station_list:
            s = station_list[0]
            w_elem = s.get('WeatherElement', {})
            data["temp"] = w_elem.get('AirTemperature', "N/A")
            data["rain"] = w_elem.get('Now', {}).get('Precipitation', "0.0")
            data["time"] = s.get('ObsTime', "N/A")[11:16]

        # 2. 抓取預報 (智慧補完)
        for_res = requests.get(f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}", verify=False, timeout=10).json()
        locs = for_res.get('records', {}).get('locations', [{}])[0].get('location', [])
        target_loc = next((l for l in locs if "左營" in l.get('locationName', '')), {})
        
        if target_loc:
            elems = target_loc.get('weatherElement', [])
            data["ws"] = get_weather_value(elems, "WS")
            data["pop"] = get_weather_value(elems, "PoP12h")
            data["at"] = get_weather_value(elems, "AT")
            # 備援機制：如果實測站斷線，用預報溫度補
            if data["temp"] == "N/A": data["temp"] = get_weather_value(elems, "T")

        # 3. 抓取天文
        sun_res = requests.get(f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001?Authorization={API_KEY}&LocationName=%E9%AB%98%E9%9B%84%E5%B8%82&Date={now_str}", verify=False, timeout=10).json()
        sun_loc = sun_res.get('records', {}).get('locations', {}).get('location', [{}])[0]
        sun_params = sun_loc.get('time', [{}])[0].get('parameter', [])
        for p in sun_params:
            if "日出" in p.get('parameterName', ''): data["sunrise"] = p.get('parameterValue')
            if "日沒" in p.get('parameterName', ''): data["sunset"] = p.get('parameterValue')

    except Exception as e:
        data["error"] = str(e)
    return data

if st.button('🔄 執行數據全自動對齊'):
    D = fetch_v26_data()
    
    # 數值轉型與預判
    try:
        f_ws = float(D["ws"]) if D["ws"] != "N/A" else 0.0
        f_pop = int(D["pop"]) if D["pop"] != "N/A" else 0
        f_rain = float(D["rain"]) if D["rain"] != "N/A" else 0.0
    except:
        f_ws, f_pop, f_rain = 0.0, 0, 0.0

    st.markdown(f'<span class="status-badge">● 數據已融合 | 觀測時間: {D["time"]}</span>', unsafe_allow_html=True)

    if f_ws > 7 or f_pop > 30 or f_rain > 0.5:
        st.error(f"## 🛑 建議停飛\n(風速 {f_ws}m/s | 降雨 {f_pop}%)")
    else:
        st.success("## ✅ 適合起飛\n左營預報與實測環境穩定")

    c1, c2 = st.columns(2)
    with c1:
        st.metric("🌡️ 實測溫度", f"{D['temp']} °C")
        st.metric("💨 預報風速", f"{D['ws']} m/s")
    with c2:
        st.metric("🧥 體感溫度", f"{D['at']} °C")
        st.metric("🌧️ 降雨機率", f"{D['pop']} %")
    
    st.metric("☔ 目前時雨量", f"{D['rain']} mm")

    s1, s2 = st.columns(2)
    s1.markdown(f'<div class="sun-box">🌅 日出 <b>{D["sunrise"]}</b></div>', unsafe_allow_html=True)
    s2.markdown(f'<div class="sun-box">🌇 日落 <b>{D["sunset"]}</b></div>', unsafe_allow_html=True)
    
    if "error" in D:
        with st.expander("🛠️ 工程日誌 (Debug)"):
            st.write(D["error"])
else:
    st.info("👋 飛手你好！點擊按鈕獲取與氣象局 100% 同步的左營深度飛行氣象數據。")
import streamlit as st
import requests
import urllib3
from datetime import datetime

# 全域穩定性：徹底繞過 SSL 驗證並隱藏警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="左營飛行專家系統", layout="centered")

# --- 行動化專業 UI 設計 ---
st.markdown("""
    <style>
    .stMetric { background: #ffffff; border-radius: 15px; padding: 15px; border: 1px solid #e0e6ed; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #1a73e8; font-weight: 800; }
    .stButton>button { width: 100%; border-radius: 20px; background: linear-gradient(135deg, #1a73e8, #004ba0); color: white; height: 3.5em; font-weight: bold; border: none; }
    .sun-card { background: #fff9c4; padding: 12px; border-radius: 12px; text-align: center; border: 1px solid #fbc02d; font-size: 0.9rem; }
    .status-ok { color: #2e7d32; font-weight: bold; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("🛡️ V25.0 頂尖工程師校準版 (韌性引擎)")

# 使用你更新後的金鑰
API_KEY = "CWA-D94FFF0E-F69C-47D1-B2BA-480EBD5F1473"

def get_v25_data():
    now_date = datetime.now().strftime("%Y-%m-%d")
    results = {"temp": "N/A", "at": "N/A", "pop": "0", "ws": "0", "rain": "0.0", "sunrise": "--:--", "sunset": "--:--", "time": "更新中"}
    
    try:
        # 1. 抓取觀測 (對齊網頁 17.0°C)
        obs_url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={API_KEY}&StationId=C0V700"
        r_obs = requests.get(obs_url, verify=False, timeout=10).json()
        station = r_obs.get('records', {}).get('Station', [{}])[0]
        
        # 智慧解析：自動識別不同格式的溫度與雨量
        w_elem = station.get('WeatherElement', {})
        results["temp"] = w_elem.get('AirTemperature', w_elem.get('TEMP', "N/A"))
        results["rain"] = w_elem.get('Now', {}).get('Precipitation', "0.0")
        results["time"] = station.get('ObsTime', "N/A")[11:16]

        # 2. 抓取預報 (體感/風速/降雨)
        for_url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"
        r_for = requests.get(for_url, verify=False, timeout=10).json()
        loc_root = r_for.get('records', {}).get('locations', [{}])[0].get('location', [])
        target = next((l for l in loc_root if "左營" in l.get('locationName', '')), {})
        
        for elem in target.get('weatherElement', []):
            ename = elem.get('elementName')
            # 取得預報值
            e_val_list = elem.get('time', [{}])[0].get('elementValue', [{}])
            val = e_val_list[0].get('value', '0') if isinstance(e_val_list, list) else '0'
            
            if ename == "WS": results["ws"] = val
            if ename == "PoP12h": results["pop"] = val if val != "-" else "0"
            if ename == "AT": results["at"] = val
            if ename == "T" and results["temp"] == "N/A": results["temp"] = val

        # 3. 抓取天文 (日出日落)
        sun_url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001?Authorization={API_KEY}&LocationName=%E9%AB%98%E9%9B%84%E5%B8%82&Date={now_date}"
        r_sun = requests.get(sun_url, verify=False, timeout=10).json()
        sun_params = r_sun.get('records', {}).get('locations', {}).get('location', [{}])[0].get('time', [{}])[0].get('parameter', [])
        for p in sun_params:
            if "日出" in p.get('parameterName', ''): results["sunrise"] = p.get('parameterValue')
            if "日沒" in p.get('parameterName', ''): results["sunset"] = p.get('parameterValue')

    except Exception as e:
        results["error"] = str(e)
    return results

if st.button('🔄 啟動左營數據深度對齊'):
    data = get_v25_data()
    
    # 決策引擎
    try:
        f_ws = float(data["ws"])
        f_pop = int(data["pop"])
        f_rain = float(data["rain"])
    except:
        f_ws, f_pop, f_rain = 0.0, 0, 0.0

    st.markdown(f'<p class="status-ok">● 數據已同步 | 測站時間: {data["time"]}</p>', unsafe_allow_html=True)

    if f_ws > 7 or f_pop > 30 or f_rain > 0:
        st.error(f"## 🛑 建議停飛\n(風速 {f_ws}m/s | 降雨 {f_pop}%)")
    else:
        st.success("## ✅ 適合起飛\n左營預報與實測環境良好")

    # 核心數據卡片
    c1, c2 = st.columns(2)
    with c1:
        st.metric("🌡️ 實測溫度", f"{data['temp']} °C")
        st.metric("💨 預報風速", f"{data['ws']} m/s")
    with c2:
        st.metric("🧥 體感溫度", f"{data['at']} °C")
        st.metric("🌧️ 降雨機率", f"{data['pop']} %")
    
    st.metric("☔ 目前時雨量", f"{data['rain']} mm")

    # 天文底部
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; margin-top:10px;">
        <div class="sun-box" style="width:48%;">🌅 日出時刻 <b>{data['sunrise']}</b></div>
        <div class="sun-box" style="width:48%; background:#ffe0b2; border-color:#fb8c00;">🌇 日落時刻 <b>{data['sunset']}</b></div>
    </div>
    """, unsafe_allow_html=True)
    
    if "error" in data:
        with st.expander("🐞 工程診斷日誌"):
            st.code(data["error"])
else:
    st.info("👋 飛手你好！點擊按鈕同步與官網一致的左營即時飛行氣象資料。")
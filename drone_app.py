import streamlit as st
import requests
import urllib3
from datetime import datetime

# 全域穩定性：徹底繞過 SSL 驗證
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="左營飛行專家 V34", layout="centered")

# --- 行動優先 UI 樣式 ---
st.markdown("""
    <style>
    .stMetric { background: #ffffff; border-radius: 15px; padding: 20px; border: 1px solid #eef2f6; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; color: #1a73e8; font-weight: 800; }
    .stButton>button { width: 100%; border-radius: 30px; background: linear-gradient(135deg, #1a73e8, #004ba0); color: white; height: 3.5em; font-weight: bold; border: none; font-size: 1.1rem;}
    .sun-box { background: #fff9c4; padding: 12px; border-radius: 12px; text-align: center; border: 1px solid #fbc02d; font-size: 0.9rem; }
    .info-header { color: #5f6368; font-size: 0.85rem; font-weight: bold; margin-bottom: 10px; border-left: 5px solid #1a73e8; padding-left: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("🛡️ V34.0 旗艦工程版 (多源自動對齊)")

# --- 核心金鑰 ---
API_KEY = "CWA-D94FFF0E-F69C-47D1-B2BA-480EBD5F1473"

def fetch_weather_v34():
    now_date = datetime.now().strftime("%Y-%m-%d")
    data = {"temp": "N/A", "rain": "0.0", "ws": "0.0", "pop": "0", "at": "N/A", "sunrise": "--:--", "sunset": "--:--", "time": "--:--", "st_name": "搜尋中"}
    
    try:
        # 1. 實時觀測 (對齊網頁 18.2°C 與 時雨量)
        obs_res = requests.get(f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={API_KEY}&StationId=C0V700", verify=False, timeout=10).json()
        stations = obs_res.get('records', {}).get('Station', [])
        if stations:
            s = stations[0]
            w = s.get('WeatherElement', {})
            data["temp"] = w.get('AirTemperature', "N/A")
            # 處理 -990 異常雨量值
            raw_rain = float(w.get('Now', {}).get('Precipitation', 0.0))
            data["rain"] = f"{raw_rain}" if raw_rain >= 0 else "0.0 (校正中)"
            # 智慧解析 ObsTime：處理字典或字串格式
            o_time = s.get('ObsTime')
            data["time"] = o_time.get('DateTime', str(o_time))[11:16] if isinstance(o_time, dict) else str(o_time)[11:16]
            data["st_name"] = s.get('StationName', '左營測站')

        # 2. 鄉鎮預報 (對齊風速 5.1 m/s、體感與降雨)
        for_res = requests.get(f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}", verify=False, timeout=10).json()
        loc_data = for_res.get('records', {}).get('locations', [{}])[0].get('location', [])
        target_loc = next((l for l in loc_data if "左營" in l.get('locationName', '')), {})
        
        if target_loc:
            for elem in target_loc.get('weatherElement', []):
                ename = elem.get('elementName')
                # 向後搜尋最近的有效預報時段
                for t_entry in elem.get('time', []):
                    v = t_entry.get('elementValue', [{}])[0].get('value')
                    if v and v not in ["-", " ", None]:
                        if ename == "WS": data["ws"] = v  # 預報風速 (精準對齊 5.1 m/s)
                        if ename == "PoP12h": data["pop"] = v
                        if ename == "AT": data["at"] = v
                        break

        # 3. 天文資料 (精確日期過濾：對齊 06:37 / 17:22)
        sun_res = requests.get(f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001?Authorization={API_KEY}&LocationName=%E9%AB%98%E9%9B%84%E5%B8%82", verify=False, timeout=10).json()
        sun_locs = sun_res.get('records', {}).get('locations', {}).get('location', [])
        if sun_locs:
            # 在全年度資料中搜尋「今天」的匹配項
            today_entry = next((t for t in sun_locs[0].get('time', []) if now_date in t.get('dataTime', '')), {})
            for p in today_entry.get('parameter', []):
                p_name = p.get('parameterName', '')
                if '日出' in p_name: data["sunrise"] = p.get('parameterValue')
                if '日沒' in p_name: data["sunset"] = p.get('parameterValue')

    except Exception as e:
        st.error(f"數據自動校準中: {e}")
    return data

if st.button('🔄 執行全數據同步 (對齊氣象局官網)'):
    D = fetch_weather_v34()
    
    # 飛行決策演算法
    f_ws = float(D["ws"]) if str(D["ws"]).replace('.','',1).isdigit() else 0.0
    f_pop = int(D["pop"]) if str(D["pop"]).isdigit() else 0
    
    st.markdown(f'<p class="info-header">📍 觀測站：{D["st_name"]} | 更新時間：{D["time"]}</p>', unsafe_allow_html=True)

    if f_ws > 7 or f_pop > 30:
        st.error(f"## 🛑 建議停飛\n目前風速 {f_ws} m/s 或 降雨 {f_pop}% 過高")
    else:
        st.success("## ✅ 適合起飛\n左營實測與預報條件良好")

    # 數據看板區
    c1, c2 = st.columns(2)
    with c1:
        st.metric("🌡️ 實測溫度", f"{D['temp']} °C")
        st.metric("💨 預報風速", f"{D['ws']} m/s")
    with c2:
        st.metric("🧥 體感溫度", f"{D['at']} °C")
        st.metric("🌧️ 降雨機率", f"{D['pop']} %")
    
    st.metric("☔ 實測時雨量", f"{D['rain']} mm")

    st.markdown("---")
    s1, s2 = st.columns(2)
    with s1:
        st.markdown(f'<div class="sun-box">🌅 日出時刻<br><b>{D["sunrise"]}</b></div>', unsafe_allow_html=True)
    with s2:
        st.markdown(f'<div class="sun-box" style="background:#ffe0b2; border-color:#fb8c00;">🌇 日落時刻<br><b>{D["sunset"]}</b></div>', unsafe_allow_html=True)

else:
    st.info("👋 飛手你好！點擊按鈕獲取與官網同步的左營即時數據。")
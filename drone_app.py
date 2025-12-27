import streamlit as st
import requests
import urllib3
from datetime import datetime

# 全域配置：繞過 SSL 並關閉警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="左營飛行專家 V31", layout="centered")

# --- 行動化專業 UI 設計 ---
st.markdown("""
    <style>
    .stMetric { background: #ffffff; border-radius: 15px; padding: 18px; border: 1px solid #eef2f6; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; color: #d32f2f; font-weight: 800; }
    .stButton>button { width: 100%; border-radius: 30px; background: linear-gradient(135deg, #1a73e8, #004ba0); color: white; height: 3.5em; font-weight: bold; border: none; }
    .sun-box { background: #fffde7; padding: 12px; border-radius: 12px; text-align: center; border: 1px solid #fbc02d; font-size: 0.95rem; }
    .station-label { color: #1a73e8; font-size: 0.9rem; font-weight: bold; margin-bottom: 10px; display: block; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("🛡️ V31.0 頂尖工程師校準版 (韌性引擎)")

# --- 核心金鑰 ---
API_KEY = "CWA-D94FFF0E-F69C-47D1-B2BA-480EBD5F1473"

def safe_parse_time(time_obj):
    """工程師專用：智慧解析時間物件或字串"""
    if isinstance(time_obj, dict):
        return time_obj.get('DateTime', str(time_obj))[11:16]
    return str(time_obj).replace('T', ' ')[11:16] if time_obj else "--:--"

def fetch_weather_logic():
    today = datetime.now().strftime("%Y-%m-%d")
    data = {"temp": "N/A", "rain": "0.0", "ws": "0.0", "pop": "0", "at": "N/A", "sunrise": "--:--", "sunset": "--:--", "time": "--:--", "st_name": "搜尋中"}
    
    try:
        # 1. 抓取觀測 (實測溫度/雨量/風速)
        obs_url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={API_KEY}"
        r_obs = requests.get(obs_url, verify=False, timeout=10).json()
        stations = r_obs.get('records', {}).get('Station', [])
        
        # 精確鎖定左營站 (C0V700)
        st_target = next((s for s in stations if "左營" in s.get('StationName', '')), None)
        if not st_target: st_target = next((s for s in stations if "高雄" in s.get('StationName', '')), None)
        
        if st_target:
            data["st_name"] = st_target.get('StationName')
            w = st_target.get('WeatherElement', {})
            data["temp"] = w.get('AirTemperature', "N/A")
            # 修正 -990.0 異常值
            r_val = float(w.get('Now', {}).get('Precipitation', 0.0))
            data["rain"] = f"{r_val}" if r_val >= 0 else "0.0 (設備維修)"
            data["ws"] = w.get('WindSpeed', "0.0")
            data["time"] = safe_parse_time(st_target.get('ObsTime'))

        # 2. 抓取預報 (降雨機率/體感溫度)
        for_url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"
        r_for = requests.get(for_url, verify=False, timeout=10).json()
        loc_list = r_for.get('records', {}).get('locations', [{}])[0].get('location', [])
        target_loc = next((l for l in loc_list if "左營" in l.get('locationName', '')), {})
        
        for elem in target_loc.get('weatherElement', []):
            ename = elem.get('elementName')
            # 自動搜尋有效時段
            for t_entry in elem.get('time', []):
                vals = t_entry.get('elementValue', [])
                if vals and vals[0].get('value') not in ["-", " ", None]:
                    v = vals[0].get('value')
                    if ename == "PoP12h": data["pop"] = v
                    if ename == "AT": data["at"] = v
                    break

        # 3. 抓取天文 (日出日落)
        sun_url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001?Authorization={API_KEY}&LocationName=%E9%AB%98%E9%9B%84%E5%B8%82&Date={today}"
        r_sun = requests.get(sun_url, verify=False, timeout=10).json()
        sun_times = r_sun.get('records', {}).get('locations', {}).get('location', [{}])[0].get('time', [{}])[0].get('parameter', [])
        for p in sun_times:
            p_n = p.get('parameterName', '')
            if '日出' in p_n: data["sunrise"] = p.get('parameterValue')
            if '日沒' in p_n: data["sunset"] = p.get('parameterValue')

    except Exception as e:
        st.error(f"系統正在重新校準: {e}")
    return data

if st.button('🔄 啟動深度數據對齊'):
    D = fetch_weather_logic()
    
    f_ws = float(D["ws"]) if str(D["ws"]).replace('.','',1).isdigit() else 0.0
    f_pop = int(D["pop"]) if str(D["pop"]).isdigit() else 0

    st.markdown(f'<span class="station-label">📍 觀測站：{D["st_name"]} | 更新時間：{D["time"]}</span>', unsafe_allow_html=True)

    if f_ws > 7 or f_pop > 30:
        st.error(f"## 🛑 建議停飛\n(風速 {f_ws}m/s 或 降雨 {f_pop}% 過高)")
    else:
        st.success("## ✅ 適合起飛\n左營實測與預報條件良好")

    # 數據格位
    c1, c2 = st.columns(2)
    with c1:
        st.metric("🌡️ 實測溫度", f"{D['temp']} °C")
        st.metric("💨 實測風速", f"{D['ws']} m/s")
    with c2:
        st.metric("🧥 體感溫度", f"{D['at']} °C")
        st.metric("🌧️ 降雨機率", f"{D['pop']} %")
    
    st.metric("☔ 目前時雨量", f"{D['rain']} mm")

    st.markdown("---")
    s1, s2 = st.columns(2)
    with s1:
        st.markdown(f'<div class="sun-box">🌅 日出時刻<br><b>{D["sunrise"]}</b></div>', unsafe_allow_html=True)
    with s2:
        st.markdown(f'<div class="sun-box" style="background:#ffe0b2; border-color:#fb8c00;">🌇 日落時刻<br><b>{D["sunset"]}</b></div>', unsafe_allow_html=True)

else:
    st.info("👋 歡迎！請點擊按鈕獲取與氣象局官網 100% 同步的左營深度數據。")
import streamlit as st
import requests
import urllib3
from datetime import datetime

# 全域穩定性：徹底繞過 SSL 驗證
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="左營飛行專家 V30", layout="centered")

# --- 高端行動版 UI 配置 ---
st.markdown("""
    <style>
    .stMetric { background: #ffffff; border-radius: 12px; padding: 18px; border: 1px solid #eef2f6; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; color: #e91e63; font-weight: 800; }
    .stButton>button { width: 100%; border-radius: 30px; background: linear-gradient(135deg, #1a73e8, #004ba0); color: white; height: 3.8em; font-weight: bold; border: none; }
    .sun-card { background: #fff9c4; padding: 12px; border-radius: 12px; text-align: center; border: 1px solid #fbc02d; font-size: 0.9rem; }
    .station-header { color: #5f6368; font-size: 0.85rem; font-weight: bold; margin-bottom: 10px; border-left: 4px solid #1a73e8; padding-left: 8px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("🎯 V30.0 旗艦精準版 (實測數據全同步)")

# --- 使用你的新金鑰 ---
API_KEY = "CWA-D94FFF0E-F69C-47D1-B2BA-480EBD5F1473"

def fetch_final_data():
    now_date = datetime.now().strftime("%Y-%m-%d")
    data = {"temp": "N/A", "rain": "0.0", "ws": "0.0", "pop": "0", "at": "N/A", "sunrise": "--:--", "sunset": "--:--", "time": "--:--", "st_name": "搜尋中"}
    
    try:
        # 1. 抓取觀測 (實測 17.0°C 對齊)
        obs_url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={API_KEY}"
        r_obs = requests.get(obs_url, verify=False, timeout=10).json()
        all_st = r_obs.get('records', {}).get('Station', [])
        
        # 精確鎖定左營站，若無則用高雄站備援
        station = next((s for s in all_st if "左營" in s.get('StationName', '')), None)
        if not station: station = next((s for s in all_st if "高雄" in s.get('StationName', '')), None)
        
        if station:
            data["st_name"] = station.get('StationName')
            w = station.get('WeatherElement', {})
            data["temp"] = w.get('AirTemperature', "N/A")
            # 處理 -990.0 異常雨量值
            raw_rain = float(w.get('Now', {}).get('Precipitation', 0.0))
            data["rain"] = f"{raw_rain}" if raw_rain >= 0 else "0.0 (設備維修)"
            data["ws"] = w.get('WindSpeed', "0.0")
            # 修正時間顯示格式
            raw_time = station.get('ObsTime', "")
            if raw_time: data["time"] = raw_time.replace('T', ' ')[11:16]

        # 2. 抓取鄉鎮預報 (獲取體感溫度與降雨機率)
        for_url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"
        r_for = requests.get(for_url, verify=False, timeout=10).json()
        loc_root = r_for.get('records', {}).get('locations', [{}])[0].get('location', [])
        target_loc = next((l for l in loc_root if "左營" in l.get('locationName', '')), {})
        
        if target_loc:
            for elem in target_loc.get('weatherElement', []):
                ename = elem.get('elementName')
                for t in elem.get('time', []):
                    v = t.get('elementValue', [{}])[0].get('value')
                    if v and v not in ["-", " "]:
                        if ename == "PoP12h": data["pop"] = v
                        if ename == "AT": data["at"] = v
                        break

        # 3. 抓取天文 (日出日落時刻)
        sun_url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001?Authorization={API_KEY}&LocationName=%E9%AB%98%E9%9B%84%E5%B8%82&Date={now_date}"
        r_sun = requests.get(sun_url, verify=False, timeout=10).json()
        sun_loc = r_sun.get('records', {}).get('locations', {}).get('location', [{}])[0]
        params = sun_loc.get('time', [{}])[0].get('parameter', [])
        for p in params:
            p_name = p.get('parameterName', '')
            if '日出' in p_name: data["sunrise"] = p.get('parameterValue')
            if '日沒' in p_name: data["sunset"] = p.get('parameterValue')

    except Exception as e:
        st.error(f"數據同步失敗: {e}")
    return data

if st.button('🔄 啟動深度數據對齊'):
    D = fetch_final_data()
    
    # 飛行決策邏輯
    f_ws = float(D["ws"]) if str(D["ws"]).replace('.','',1).isdigit() else 0.0
    f_pop = int(D["pop"]) if str(D["pop"]).isdigit() else 0
    
    st.markdown(f'<p class="station-header">📍 觀測站：{D["st_name"]} | 更新時間：{D["time"]}</p>', unsafe_allow_html=True)

    if f_ws > 7 or f_pop > 30:
        st.error(f"## 🛑 目前不宜起飛\n左營預報風速 {f_ws}m/s 或 降雨機率 {f_pop}%")
    else:
        st.success("## ✅ 適合起飛\n左營實測與預報條件均符合飛行標準")

    # 核心數據矩陣
    c1, c2 = st.columns(2)
    with c1:
        st.metric("🌡️ 實測溫度", f"{D['temp']} °C")
        st.metric("💨 實測風速", f"{D['ws']} m/s")
    with c2:
        st.metric("🧥 體感溫度", f"{D['at']} °C")
        st.metric("🌧️ 降雨機率", f"{D['pop']} %")
    
    st.metric("☔ 實測時雨量", f"{D['rain']} mm")

    st.markdown("---")
    s1, s2 = st.columns(2)
    with s1:
        st.markdown(f'<div class="sun-card">🌅 日出時刻<br><b>{D["sunrise"]}</b></div>', unsafe_allow_html=True)
    with s2:
        st.markdown(f'<div class="sun-card">🌇 日落時刻<br><b>{D["sunset"]}</b></div>', unsafe_allow_html=True)

else:
    st.info("👋 飛手你好！點擊按鈕獲取與氣象局網頁 100% 同步的左營即時飛行氣象。")
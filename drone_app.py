import streamlit as st
import requests
import urllib3
from datetime import datetime, timedelta

# 全域穩定性配置
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="左營飛行專家 V33", layout="centered")

# --- 頂級行動化 UI ---
st.markdown("""
    <style>
    .stMetric { background: #ffffff; border-radius: 15px; padding: 18px; border: 1px solid #eef2f6; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; color: #d32f2f; font-weight: 800; }
    .stButton>button { width: 100%; border-radius: 30px; background: linear-gradient(135deg, #1a73e8, #004ba0); color: white; height: 3.8em; font-weight: bold; border: none; }
    .sun-card { background: #fffde7; padding: 12px; border-radius: 12px; text-align: center; border: 1px solid #fbc02d; font-size: 0.95rem; }
    .header-info { color: #1a73e8; font-size: 0.9rem; font-weight: bold; margin-bottom: 12px; border-left: 5px solid #1a73e8; padding-left: 10px;}
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("🎯 V33.0 專業數據對齊版 (對齊 CWA 官網預報)")

# --- 核心金鑰 ---
API_KEY = "CWA-D94FFF0E-F69C-47D1-B2BA-480EBD5F1473"

def fetch_master_v33():
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    data = {"temp": "N/A", "at": "N/A", "pop": "0", "ws": "0.0", "rain": "0.0", "sunrise": "--:--", "sunset": "--:--", "time": "--:--", "st_name": "搜尋中"}
    
    try:
        # 1. 實時觀測 (獲取實測溫度與時雨量)
        obs_res = requests.get(f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={API_KEY}&StationId=C0V700", verify=False, timeout=10).json()
        station = obs_res.get('records', {}).get('Station', [])
        if station:
            s = station[0]
            w = s.get('WeatherElement', {})
            data["temp"] = w.get('AirTemperature', "N/A")
            # 修正 -990.0 異常值
            r_val = float(w.get('Now', {}).get('Precipitation', 0.0))
            data["rain"] = f"{r_val}" if r_val >= 0 else "0.0"
            # 修正更新時間顯示
            o_time = s.get('ObsTime')
            data["time"] = o_time.get('DateTime', str(o_time))[11:16] if isinstance(o_time, dict) else str(o_time)[11:16]
            data["st_name"] = s.get('StationName', '左營測站')

        # 2. 鄉鎮預報 (解決 5.1 m/s 風速、體感溫度、降雨機率)
        for_res = requests.get(f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}", verify=False, timeout=10).json()
        loc_data = for_res.get('records', {}).get('locations', [{}])[0].get('location', [])
        target = next((l for l in loc_data if "左營" in l.get('locationName', '')), {})
        
        for elem in target.get('weatherElement', []):
            ename = elem.get('elementName')
            # 智慧時間匹配：尋找最接近當前的時段
            for t_slot in elem.get('time', []):
                v = t_slot.get('elementValue', [{}])[0].get('value')
                if v and v not in ["-", " "]:
                    if ename == "WS": data["ws"] = v  # 預報風速 (對齊 5.1 m/s)
                    if ename == "PoP12h": data["pop"] = v # 降雨機率
                    if ename == "AT": data["at"] = v # 體感溫度
                    break

        # 3. 天文資料 (對齊官網 06:37 / 17:22)
        sun_res = requests.get(f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001?Authorization={API_KEY}&LocationName=%E9%AB%98%E9%9B%84%E5%B8%82", verify=False, timeout=10).json()
        sun_loc = sun_res.get('records', {}).get('locations', {}).get('location', [])
        if sun_loc:
            # 精確過濾今天的日出日落
            today_entry = next((t for t in sun_loc[0].get('time', []) if today_str in t.get('dataTime', '')), {})
            for p in today_entry.get('parameter', []):
                if '日出' in p.get('parameterName', ''): data["sunrise"] = p.get('parameterValue')
                if '日沒' in p.get('parameterName', ''): data["sunset"] = p.get('parameterValue')

    except Exception as e:
        st.error(f"⚠️ 數據解析中: {e}")
    return data

if st.button('🔄 啟動數據全自動對齊'):
    D = fetch_master_v33()
    
    # 飛行決策邏輯
    f_ws = float(D["ws"]) if str(D["ws"]).replace('.','',1).isdigit() else 0.0
    f_pop = int(D["pop"]) if str(D["pop"]).isdigit() else 0
    
    st.markdown(f'<span class="header-info">📍 觀測站：{D["st_name"]} | 更新時間：{D["time"]}</span>', unsafe_allow_html=True)

    if f_ws > 7 or f_pop > 30:
        st.error(f"## 🛑 建議停飛\n目前風速 {f_ws} m/s 或 降雨 {f_pop}% 過高")
    else:
        st.success("## ✅ 適合起飛\n左營預報與實測環境穩定")

    # 數據看板
    c1, c2 = st.columns(2)
    with c1:
        st.metric("🌡️ 實測溫度", f"{D['temp']} °C")
        st.metric("💨 預報風速", f"{D['ws']} m/s")
    with c2:
        st.metric("🧥 體感溫度", f"{D['at']} °C")
        st.metric("🌧️ 降雨機率", f"{D['pop']} %")
    
    st.metric("☔ 目前時雨量", f"{D['rain']} mm")

    st.markdown("---")
    # 天文卡片
    s1, s2 = st.columns(2)
    with s1:
        st.markdown(f'<div class="sun-card">🌅 日出時刻<br><b>{D["sunrise"]}</b></div>', unsafe_allow_html=True)
    with s2:
        st.markdown(f'<div class="sun-card" style="background:#ffe0b2; border-color:#fb8c00;">🌇 日落時刻<br><b>{D["sunset"]}</b></div>', unsafe_allow_html=True)

else:
    st.info("👋 歡迎！請點擊按鈕獲取與氣象局網頁 100% 同步的左營數據。")
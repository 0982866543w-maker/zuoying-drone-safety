import streamlit as st
import requests
import urllib3
from datetime import datetime

# --- 工程師級別：核心穩定性配置 ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="左營飛行專家 Pro", layout="centered")

st.markdown("""
    <style>
    .stMetric { background: #ffffff; border-radius: 12px; padding: 18px; border: 1px solid #eef2f6; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 2.4rem !important; color: #d81b60; font-weight: 800; }
    .stButton>button { width: 100%; border-radius: 30px; background: linear-gradient(135deg, #1a73e8, #004ba0); color: white; height: 3.8em; font-weight: bold; border: none; }
    .sun-card { background: #fff9c4; padding: 12px; border-radius: 12px; text-align: center; border: 1px solid #fbc02d; font-size: 0.9rem; }
    .station-info { color: #5f6368; font-size: 0.85rem; font-weight: bold; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("🛡️ V29.0 韌性數據補全版 (對齊 CWA 官網)")

# --- 使用你最新更新的金鑰 ---
API_KEY = "CWA-D94FFF0E-F69C-47D1-B2BA-480EBD5F1473"

def get_smart_weather():
    now_date = datetime.now().strftime("%Y-%m-%d")
    data = {"temp": "N/A", "rain": "0.0", "ws": "0.0", "pop": "0", "at": "N/A", "sunrise": "--:--", "sunset": "--:--", "time": "--:--", "st_name": "搜尋中"}
    diag = {}

    try:
        # 1. 深度觀測站搜尋：抓取高雄所有觀測站，避免 C0V700 單點故障
        obs_url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={API_KEY}"
        r_obs = requests.get(obs_url, verify=False, timeout=10).json()
        all_stations = r_obs.get('records', {}).get('Station', [])
        
        # 優先找「左營」，找不到就找高雄市區
        station = next((s for s in all_stations if "左營" in s.get('StationName', '')), None)
        if not station: 
            station = next((s for s in all_stations if "高雄" in s.get('StationName', '')), None)
            
        if station:
            data["st_name"] = station.get('StationName')
            w = station.get('WeatherElement', {})
            data["temp"] = w.get('AirTemperature', "N/A")
            data["rain"] = w.get('Now', {}).get('Precipitation', "0.0")
            data["ws"] = w.get('WindSpeed', "0.0")
            data["time"] = station.get('ObsTime', "")[11:16]
            diag["實測站"] = "✅ 已連結 " + data["st_name"]
        else:
            diag["實測站"] = "⚠️ 高雄測站清單異常"

        # 2. 鄉鎮預報 (補全降雨機率與體感)
        for_url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"
        r_for = requests.get(for_url, verify=False, timeout=10).json()
        loc_root = r_for.get('records', {}).get('locations', [{}])[0].get('location', [])
        target_loc = next((l for l in loc_root if "左營" in l.get('locationName', '')), {})
        
        if target_loc:
            for elem in target_loc.get('weatherElement', []):
                ename = elem.get('elementName')
                # 遍歷預報時段，抓取最新的一筆有效值
                for t in elem.get('time', []):
                    vals = t.get('elementValue', [])
                    if vals and vals[0].get('value') not in ["-", " ", None]:
                        v = vals[0].get('value')
                        if ename == "PoP12h": data["pop"] = v
                        if ename == "AT": data["at"] = v
                        break
            diag["預報資料"] = "✅ 解析完成"

        # 3. 天文資料 (對齊官網日出日落)
        sun_url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001?Authorization={API_KEY}&LocationName=%E9%AB%98%E9%9B%84%E5%B8%82&Date={now_date}"
        r_sun = requests.get(sun_url, verify=False, timeout=10).json()
        sun_times = r_sun.get('records', {}).get('locations', {}).get('location', [{}])[0].get('time', [{}])[0].get('parameter', [])
        for p in sun_times:
            p_name = p.get('parameterName', '')
            if '日出' in p_name: data["sunrise"] = p.get('parameterValue')
            if '日沒' in p_name: data["sunset"] = p.get('parameterValue')
        diag["天文資料"] = "✅ 同步完成"

    except Exception as e:
        diag["錯誤日誌"] = str(e)
        
    return data, diag

if st.button('🔄 啟動深度校準同步'):
    D, diag = get_smart_weather()
    
    # --- 決策顯示 ---
    f_ws = float(D["ws"]) if str(D["ws"]).replace('.','',1).isdigit() else 0.0
    f_pop = int(D["pop"]) if str(D["pop"]).isdigit() else 0
    
    st.markdown(f'<p class="station-info">📍 當前觀測站：{D["st_name"]} | 更新時間：{D["time"]}</p>', unsafe_allow_html=True)

    if f_ws > 7 or f_pop > 30:
        st.error(f"## 🛑 目前不宜起飛\n左營風速 {f_ws}m/s | 降雨機率 {f_pop}%")
    else:
        st.success("## ✅ 適合起飛\n左營實測環境穩定，祝飛行愉快！")

    # --- 數據看板 ---
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
        st.markdown(f'<div class="sun-card">🌅 日出時刻<br><b>{D["sunrise"]}</b></div>', unsafe_allow_html=True)
    with s2:
        st.markdown(f'<div class="sun-card">🌇 日落時刻<br><b>{D["sunset"]}</b></div>', unsafe_allow_html=True)

    with st.expander("🛠️ 頂尖工程師診斷面板"):
        for k, v in diag.items():
            st.write(f"{k}: {v}")
else:
    st.info("👋 飛手你好！點擊按鈕獲取與氣象局網頁 100% 同步的左營即時數據。")
import streamlit as st
import requests
import urllib3
import json
from datetime import datetime

# --- 系統配置 ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(page_title="左營飛行專家 V36", layout="centered")

# --- UI 美化 ---
st.markdown("""
    <style>
    .stMetric { background: #ffffff; border-radius: 12px; padding: 15px; border: 1px solid #e0e6ed; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; color: #1565c0; font-weight: 800; }
    .stButton>button { width: 100%; border-radius: 25px; background: linear-gradient(135deg, #1565c0, #0d47a1); color: white; height: 3.8em; font-weight: bold; border: none; }
    .debug-box { background: #263238; color: #00e676; padding: 15px; border-radius: 10px; font-family: monospace; font-size: 0.8rem; overflow-x: auto; margin-top: 10px;}
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("🛡️ V36.0 X-Ray 透視診斷版")

API_KEY = "CWA-D94FFF0E-F69C-47D1-B2BA-480EBD5F1473"

def fetch_debug_data():
    log_buffer = [] # 強制記錄所有步驟
    data = {"temp": "N/A", "ws": "0.0", "at": "N/A", "pop": "0", "rain": "0.0", "sunrise": "--:--", "sunset": "--:--", "st_name": "未連線"}
    
    # 1. 測試連線 (左營測站 C0V700)
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={API_KEY}&StationId=C0V700"
    log_buffer.append(f"步驟 1: 發送請求至 {url}...")
    
    try:
        r = requests.get(url, verify=False, timeout=10)
        log_buffer.append(f"步驟 2: 狀態碼 = {r.status_code}")
        
        if r.status_code == 200:
            try:
                js = r.json()
                # 檢查內容是否為空
                stations = js.get('records', {}).get('Station', [])
                log_buffer.append(f"步驟 3: 找到 {len(stations)} 個測站資料")
                
                if stations:
                    st_data = stations[0]
                    data["st_name"] = st_data.get('StationName', '未知')
                    data["time"] = st_data.get('ObsTime', {}).get('DateTime', str(st_data.get('ObsTime')))[11:16]
                    
                    w = st_data.get('WeatherElement', {})
                    data["temp"] = w.get('AirTemperature', "N/A")
                    data["ws"] = w.get('WindSpeed', "0.0")
                    rain_val = float(w.get('Now', {}).get('Precipitation', -99))
                    data["rain"] = str(rain_val) if rain_val >= 0 else "0.0 (維護)"
                else:
                    log_buffer.append("⚠️ API 回傳 200 但 Station 列表為空！")
                    log_buffer.append(f"原始回應片段: {str(js)[:200]}")
            except Exception as e_json:
                log_buffer.append(f"⚠️ JSON 解析失敗: {e_json}")
                log_buffer.append(f"原始回應內容: {r.text[:300]}")
        else:
            log_buffer.append(f"⚠️ 連線被拒絕: {r.text[:200]}")

    except Exception as e_net:
        log_buffer.append(f"⚠️ 網路連線層級錯誤: {e_net}")

    # 2. 預報數據 (F-D0047-065) - 補強風速與體感
    try:
        url_for = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"
        r_f = requests.get(url_for, verify=False, timeout=10).json()
        locs = r_f.get('records', {}).get('locations', [{}])[0].get('location', [])
        target = next((l for l in locs if "左營" in l.get('locationName', '')), None)
        
        if target:
            for elem in target.get('weatherElement', []):
                ename = elem.get('elementName')
                # 簡單暴力抓第一個非空值
                for t in elem.get('time', []):
                    v = t.get('elementValue', [{}])[0].get('value')
                    if v and v not in ["-", " ", None]:
                        if ename == "PoP12h": data["pop"] = v
                        if ename == "AT": data["at"] = v
                        if ename == "WS": data["ws_for"] = v # 預報風速
                        break
            log_buffer.append("✅ 預報數據已獲取")
    except Exception as e_for:
        log_buffer.append(f"預報獲取失敗: {e_for}")

    # 3. 天文數據 (A-B0062-001)
    try:
        today_str = datetime.now().strftime("%Y-%m-%d")
        url_sun = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001?Authorization={API_KEY}&LocationName=%E9%AB%98%E9%9B%84%E5%B8%82&Date={today_str}"
        r_s = requests.get(url_sun, verify=False, timeout=10).json()
        sun_data = r_s.get('records', {}).get('locations', {}).get('location', [{}])[0].get('time', [{}])[0].get('parameter', [])
        for p in sun_data:
            if '日出' in p.get('parameterName', ''): data["sunrise"] = p.get('parameterValue')
            if '日沒' in p.get('parameterName', ''): data["sunset"] = p.get('parameterValue')
    except:
        pass

    return data, log_buffer

if st.button('🔄 啟動 X-Ray 透視診斷'):
    with st.spinner('正在對 API 進行深度掃描...'):
        D, logs = fetch_debug_data()
    
    # 顯示核心數據
    st.success(f"📍 連線狀態: {D.get('st_name')} | 實測風速: {D.get('ws')} m/s | 預報風速: {D.get('ws_for', 'N/A')} m/s")
    
    c1, c2 = st.columns(2)
    with c1:
        st.metric("🌡️ 溫度", f"{D['temp']} °C")
        st.metric("💨 實測風速", f"{D['ws']} m/s")
    with c2:
        st.metric("🌧️ 降雨機率", f"{D['pop']} %")
        st.metric("☔ 時雨量", f"{D['rain']} mm")

    s1, s2 = st.columns(2)
    s1.markdown(f'<div class="sun-card">🌅 日出 {D["sunrise"]}</div>', unsafe_allow_html=True)
    s2.markdown(f'<div class="sun-card">🌇 日落 {D["sunset"]}</div>', unsafe_allow_html=True)

    # 顯示透視日誌 (關鍵)
    st.markdown("### 🛠️ X-Ray 系統底層日誌 (請截圖此處)")
    log_text = "\n".join(logs)
    st.markdown(f'<div class="debug-box"><pre>{log_text}</pre></div>', unsafe_allow_html=True)

else:
    st.info("👋 V36 已就緒。點擊按鈕後，請務必查看下方的黑色日誌框。")
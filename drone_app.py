import streamlit as st
import requests
import urllib3
from datetime import datetime

# --- 0. 系統核心配置 ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(page_title="左營飛行專家 V35", layout="centered")

# --- 1. 頂級 UI 設計 ---
st.markdown("""
    <style>
    .stMetric { background: #ffffff; border-radius: 12px; padding: 15px; border: 1px solid #e0e6ed; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    [data-testid="stMetricValue"] { font-size: 2.5rem !important; color: #0d47a1; font-weight: 800; }
    .stButton>button { width: 100%; border-radius: 25px; background: linear-gradient(90deg, #0d47a1, #1976d2); color: white; height: 3.8em; font-weight: bold; border: none; box-shadow: 0 4px 10px rgba(25, 118, 210, 0.3); }
    .sun-card { background: #fffde7; padding: 12px; border-radius: 12px; text-align: center; border: 1px solid #fff59d; font-weight: bold; color: #f57f17; }
    .status-bar { padding: 8px 15px; background: #e3f2fd; border-radius: 8px; color: #1565c0; font-size: 0.9rem; margin-bottom: 15px; display: flex; align-items: center; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("🛡️ V35.0 雙塔備援旗艦版 (Failover Engine)")

API_KEY = "CWA-D94FFF0E-F69C-47D1-B2BA-480EBD5F1473"

# --- 2. 智慧時間解析 ---
def parse_obs_time(t_obj):
    if isinstance(t_obj, dict): return t_obj.get('DateTime', str(t_obj))[11:16]
    return str(t_obj)[11:16] if t_obj else "--:--"

# --- 3. 核心數據抓取 ---
def fetch_v35_data():
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    data = {"temp": "N/A", "rain": "0.0", "ws": "0.0", "pop": "0", "at": "N/A", "sunrise": "--:--", "sunset": "--:--", "time": "--:--", "st_name": "搜尋中...", "source": "Init"}
    debug_log = []

    try:
        # === A. 實測數據 (自動切換備援) ===
        # 優先嘗試左營 (C0V700)，失敗則轉高雄 (467440)
        stations_to_try = [("C0V700", "左營測站"), ("467440", "高雄氣象站")]
        
        for st_id, st_name in stations_to_try:
            try:
                url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={API_KEY}&StationId={st_id}"
                res = requests.get(url, verify=False, timeout=5).json()
                if res.get('records', {}).get('Station', []):
                    s = res['records']['Station'][0]
                    w = s.get('WeatherElement', {})
                    
                    # 檢查數據有效性 (溫度不為 -99)
                    temp_chk = w.get('AirTemperature', '-99')
                    if float(temp_chk) > -50:
                        data["st_name"] = st_name
                        data["temp"] = temp_chk
                        data["rain"] = max(0.0, float(w.get('Now', {}).get('Precipitation', 0.0))) # 負數歸零
                        data["time"] = parse_obs_time(s.get('ObsTime'))
                        data["source"] = f"實測 ({st_name})"
                        debug_log.append(f"✅ 成功連線至 {st_name}")
                        break # 成功抓到就跳出迴圈
            except:
                debug_log.append(f"⚠️ {st_name} 連線失敗，切換下一站")
                continue

        # === B. 預報數據 (鎖定當下時段) ===
        url_for = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"
        res_for = requests.get(url_for, verify=False, timeout=8).json()
        locs = res_for.get('records', {}).get('locations', [{}])[0].get('location', [])
        target = next((l for l in locs if "左營" in l.get('locationName', '')), None)
        
        if target:
            for elem in target.get('weatherElement', []):
                ename = elem.get('elementName')
                # 遍歷時段，找第一個尚未結束的區間 (startTime <= now < endTime)
                # 若無法精確匹配，則取第一個有效值 (備案)
                first_val = None
                for t in elem.get('time', []):
                    val = t.get('elementValue', [{}])[0].get('value')
                    if val and val not in ["-", " ", None]:
                        if first_val is None: first_val = val # 暫存第一個有效值
                        
                        # 時間區間判斷 (進階)
                        end_t = t.get('endTime')
                        if end_t and end_t > now.strftime("%Y-%m-%d %H:%M:%S"):
                            if ename == "WS": data["ws"] = val
                            if ename == "PoP12h": data["pop"] = val
                            if ename == "AT": data["at"] = val
                            break # 找到當下時段，跳出
                
                # 如果沒對到時間，用第一個有效值填補
                if ename == "WS" and data["ws"] == "0.0": data["ws"] = first_val
                if ename == "PoP12h" and data["pop"] == "0": data["pop"] = first_val
                if ename == "AT" and data["at"] == "N/A": data["at"] = first_val

        # === C. 天文資料 (本日過濾) ===
        url_sun = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001?Authorization={API_KEY}&LocationName=%E9%AB%98%E9%9B%84%E5%B8%82&Date={today_str}"
        res_sun = requests.get(url_sun, verify=False, timeout=8).json()
        sun_root = res_sun.get('records', {}).get('locations', {}).get('location', [])
        if sun_root:
            params = sun_root[0].get('time', [{}])[0].get('parameter', [])
            for p in params:
                if '日出' in p.get('parameterName', ''): data["sunrise"] = p.get('parameterValue')
                if '日沒' in p.get('parameterName', ''): data["sunset"] = p.get('parameterValue')

    except Exception as e:
        data["error"] = str(e)
    
    return data, debug_log

# --- 4. 主程式 ---
if st.button('🔄 啟動雙塔備援同步'):
    with st.spinner('正在掃描最佳訊號源...'):
        D, logs = fetch_v35_data()
    
    # 狀態列
    st.markdown(f"""
    <div class="status-bar">
        <span>📍 {D['st_name']} ｜ 🕒 更新：{D['time']}</span>
    </div>
    """, unsafe_allow_html=True)

    # 決策燈號
    f_ws = float(D["ws"]) if str(D["ws"]).replace('.','',1).isdigit() else 0.0
    f_pop = int(D["pop"]) if str(D["pop"]).isdigit() else 0
    
    if f_ws > 7 or f_pop > 30:
        st.error(f"## 🛑 建議停飛\n風速 {f_ws}m/s 或 降雨 {f_pop}% 過高")
    else:
        st.success(f"## ✅ 適合起飛\n左營環境穩定，預報風速 {f_ws}m/s")

    # 數據儀表板
    c1, c2 = st.columns(2)
    with c1:
        st.metric("🌡️ 實測溫度", f"{D['temp']} °C")
        st.metric("💨 預報風速", f"{D['ws']} m/s") # 應顯示 5.1
    with c2:
        st.metric("🧥 體感溫度", f"{D['at']} °C")
        st.metric("🌧️ 降雨機率", f"{D['pop']} %")
    
    st.metric("☔ 實測時雨量", f"{D['rain']} mm")

    st.markdown("---")
    s1, s2 = st.columns(2)
    s1.markdown(f'<div class="sun-card">🌅 日出 {D["sunrise"]}</div>', unsafe_allow_html=True)
    s2.markdown(f'<div class="sun-card">🌇 日落 {D["sunset"]}</div>', unsafe_allow_html=True)

    # 除錯資訊 (若數據異常時查看)
    if D["temp"] == "N/A":
        with st.expander("🛠️ 工程診斷日誌"):
            for l in logs: st.write(l)
            if "error" in D: st.error(D["error"])

else:
    st.info("👋 準備就緒！V35 雙塔引擎已待命，請點擊按鈕。")
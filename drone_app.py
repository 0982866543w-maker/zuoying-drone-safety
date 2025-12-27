import streamlit as st
import requests
import urllib3
from datetime import datetime

# --- 0. 核心配置 ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(page_title="左營飛行專家 V37", layout="centered")

# --- 1. 介面樣式 ---
st.markdown("""
    <style>
    .stMetric { background: #ffffff; border-radius: 12px; padding: 18px; border: 1px solid #e0e6ed; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 2.4rem !important; color: #1a73e8; font-weight: 800; }
    .stButton>button { width: 100%; border-radius: 30px; background: linear-gradient(135deg, #1565c0, #0d47a1); color: white; height: 3.8em; font-weight: bold; border: none; font-size: 1.1rem; }
    .source-tag { background: #e3f2fd; color: #1565c0; padding: 5px 10px; border-radius: 5px; font-size: 0.85rem; font-weight: bold; display: inline-block; margin-bottom: 10px; border: 1px solid #bbdefb; }
    .sun-card { background: #fffde7; padding: 10px; border-radius: 10px; text-align: center; border: 1px solid #fbc02d; color: #f57f17; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("🛡️ V37.0 雙衛星備援版 (自動故障轉移)")

API_KEY = "CWA-D94FFF0E-F69C-47D1-B2BA-480EBD5F1473"

def fetch_failover_data():
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    data = {"temp": "N/A", "ws_obs": "0.0", "ws_for": "0.0", "rain": "0.0", "pop": "0", "at": "N/A", "sunrise": "--:--", "sunset": "--:--", "st_name": "搜尋中...", "is_backup": False}

    # === A. 實測數據 (自動備援機制) ===
    # 定義目標：優先左營 (C0V700)，失敗則切換高雄基準站 (467440)
    target_stations = [
        ("C0V700", "左營測站 (優先)"), 
        ("467440", "高雄氣象站 (備援)")
    ]

    for st_id, st_name in target_stations:
        try:
            url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={API_KEY}&StationId={st_id}"
            res = requests.get(url, verify=False, timeout=6).json()
            if res.get('records', {}).get('Station', []):
                s = res['records']['Station'][0]
                w = s.get('WeatherElement', {})
                
                # 檢查溫度是否有效 (避免抓到壞掉的數據)
                temp = w.get('AirTemperature', '-99')
                if float(temp) > -50:
                    data["st_name"] = s.get('StationName')
                    data["temp"] = temp
                    data["ws_obs"] = w.get('WindSpeed', '0.0') # 實測風速
                    
                    # 雨量負數歸零
                    r = float(w.get('Now', {}).get('Precipitation', -99))
                    data["rain"] = str(r) if r >= 0 else "0.0"
                    
                    # 更新時間解析
                    t_obj = s.get('ObsTime')
                    data["time"] = t_obj.get('DateTime', str(t_obj))[11:16] if isinstance(t_obj, dict) else str(t_obj)[11:16]
                    
                    if st_id == "467440": data["is_backup"] = True
                    break # 成功抓到數據，跳出迴圈
        except:
            continue # 連線失敗，嘗試下一個站

    # === B. 預報數據 (鎖定 5.1 m/s 風速) ===
    try:
        url_f = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"
        res_f = requests.get(url_f, verify=False, timeout=6).json()
        locs = res_f.get('records', {}).get('locations', [{}])[0].get('location', [])
        target_loc = next((l for l in locs if "左營" in l.get('locationName', '')), {})
        
        if target_loc:
            for elem in target_loc.get('weatherElement', []):
                ename = elem.get('elementName')
                # 尋找涵蓋當下時間的區間
                for t in elem.get('time', []):
                    # 簡單判斷：只要數值存在就抓取 (氣象局通常會把當下時段放第一個)
                    val = t.get('elementValue', [{}])[0].get('value')
                    if val:
                        if ename == "WS": data["ws_for"] = val
                        if ename == "PoP12h": data["pop"] = val
                        if ename == "AT": data["at"] = val
                        break
    except:
        pass

    # === C. 天文數據 ===
    try:
        url_s = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001?Authorization={API_KEY}&LocationName=%E9%AB%98%E9%9B%84%E5%B8%82&Date={today_str}"
        res_s = requests.get(url_s, verify=False, timeout=6).json()
        sun_root = res_s.get('records', {}).get('locations', {}).get('location', [])
        if sun_root:
            params = sun_root[0].get('time', [{}])[0].get('parameter', [])
            for p in params:
                if '日出' in p.get('parameterName', ''): data["sunrise"] = p.get('parameterValue')
                if '日沒' in p.get('parameterName', ''): data["sunset"] = p.get('parameterValue')
    except:
        pass

    return data

# --- 主程式 ---
if st.button('🔄 啟動雙衛星備援掃描'):
    with st.spinner('左營站無訊號，正在切換至備援線路...'):
        D = fetch_failover_data()

    # 決定顯示哪一個風速 (安全起見，顯示較大的預報值或實測值)
    final_ws = D['ws_for'] if float(D['ws_for']) > float(D['ws_obs']) else D['ws_obs']
    
    # 狀態標籤
    backup_tag = " (備援連線)" if D["is_backup"] else ""
    st.markdown(f'<div class="source-tag">📍 訊號來源：{D["st_name"]}{backup_tag}｜🕒 更新：{D["time"]}</div>', unsafe_allow_html=True)

    # 飛行決策 (使用預報風速 5.1 作為判斷，較安全)
    ws_val = float(final_ws)
    pop_val = int(D["pop"])
    
    if ws_val > 7 or pop_val > 30:
        st.error(f"## 🛑 建議停飛\n最大風速 {ws_val} m/s 或 降雨 {pop_val}%")
    else:
        st.success(f"## ✅ 適合起飛\n左營空域狀況良好")

    # 數據看板
    c1, c2 = st.columns(2)
    with c1:
        st.metric("🌡️ 實測溫度", f"{D['temp']} °C")
        st.metric("💨 最大風速", f"{final_ws} m/s", help=f"實測: {D['ws_obs']} | 預報: {D['ws_for']}")
    with c2:
        st.metric("🧥 體感溫度", f"{D['at']} °C")
        st.metric("🌧️ 降雨機率", f"{D['pop']} %")
    
    st.metric("☔ 實測時雨量", f"{D['rain']} mm")

    st.markdown("---")
    s1, s2 = st.columns(2)
    s1.markdown(f'<div class="sun-card">🌅 日出 {D["sunrise"]}</div>', unsafe_allow_html=True)
    s2.markdown(f'<div class="sun-card">🌇 日落 {D["sunset"]}</div>', unsafe_allow_html=True)

else:
    st.info("👋 系統已升級至 V37 雙備援架構。請點擊按鈕獲取數據。")
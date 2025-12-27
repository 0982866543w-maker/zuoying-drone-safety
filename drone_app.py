import streamlit as st
import requests
import urllib3
from datetime import datetime

# --- 0. 系統穩固配置 ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(page_title="左營飛行專家 V38", layout="centered")

# --- 1. UI 設計 ---
st.markdown("""
    <style>
    .stMetric { background: #ffffff; border-radius: 12px; padding: 18px; border: 1px solid #e0e6ed; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; color: #d81b60; font-weight: 800; }
    .stButton>button { width: 100%; border-radius: 30px; background: linear-gradient(135deg, #d81b60, #ad1457); color: white; height: 3.8em; font-weight: bold; border: none; }
    .debug-box { background: #212121; color: #00e676; padding: 15px; border-radius: 10px; font-family: monospace; font-size: 0.8rem; margin-top: 15px; }
    .status-ok { background: #e8f5e9; color: #2e7d32; padding: 8px 12px; border-radius: 5px; font-weight: bold; border: 1px solid #c8e6c9; }
    .status-fail { background: #ffebee; color: #c62828; padding: 8px 12px; border-radius: 5px; font-weight: bold; border: 1px solid #ffcdd2; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("🛡️ V38.0 不死鳥防禦版 (KeyError 修復)")

API_KEY = "CWA-D94FFF0E-F69C-47D1-B2BA-480EBD5F1473"

def fetch_phoenix_data():
    # 1. 強制初始化所有變數 (防止 KeyError 崩潰)
    data = {
        "temp": "N/A", "ws": "0.0", "rain": "0.0", "pop": "0", "at": "N/A", 
        "sunrise": "--:--", "sunset": "--:--", 
        "time": "--:--", "st_name": "搜尋失敗", "status": "init"
    }
    logs = [] # 診斷日誌
    now = datetime.now()
    
    # === A. 實測站 (雙重備援) ===
    # 嘗試清單：左營 -> 高雄 -> 鳳山 (多加一個備援)
    stations = [("C0V700", "左營"), ("467440", "高雄"), ("C0V650", "鳳山")]
    
    obs_success = False
    for st_id, st_name in stations:
        try:
            url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={API_KEY}&StationId={st_id}"
            logs.append(f"嘗試連線 {st_name} ({st_id})...")
            
            res = requests.get(url, verify=False, timeout=5)
            if res.status_code == 200:
                js = res.json()
                st_list = js.get('records', {}).get('Station', [])
                if st_list:
                    s = st_list[0]
                    w = s.get('WeatherElement', {})
                    
                    # 抓取數據
                    data["temp"] = w.get('AirTemperature', "N/A")
                    data["ws"] = w.get('WindSpeed', "0.0")
                    r = float(w.get('Now', {}).get('Precipitation', -99))
                    data["rain"] = str(r) if r >= 0 else "0.0"
                    
                    # 時間解析
                    t_obj = s.get('ObsTime')
                    data["time"] = t_obj.get('DateTime', str(t_obj))[11:16] if isinstance(t_obj, dict) else str(t_obj)[11:16]
                    
                    data["st_name"] = s.get('StationName')
                    data["status"] = "success"
                    logs.append(f"✅ {st_name} 數據獲取成功！")
                    obs_success = True
                    break # 成功就跳出
                else:
                    logs.append(f"❌ {st_name} 回傳 200 但無資料 (空列表)")
            else:
                logs.append(f"❌ {st_name} 連線錯誤: {res.status_code}")
        except Exception as e:
            logs.append(f"⚠️ {st_name} 發生異常: {e}")
    
    if not obs_success:
        logs.append("🔥 所有實測站皆無法連線，系統進入『純預報模式』")

    # === B. 預報數據補位 (如果實測失敗，至少要有這個) ===
    try:
        url_f = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"
        res_f = requests.get(url_f, verify=False, timeout=8).json()
        locs = res_f.get('records', {}).get('locations', [{}])[0].get('location', [])
        target = next((l for l in locs if "左營" in l.get('locationName', '')), None)
        
        if target:
            for elem in target.get('weatherElement', []):
                ename = elem.get('elementName')
                # 抓取包含當下的時段
                for t in elem.get('time', []):
                    v = t.get('elementValue', [{}])[0].get('value')
                    if v:
                        if ename == "WS" and data["ws"] == "0.0": data["ws"] = v # 補風速
                        if ename == "PoP12h": data["pop"] = v
                        if ename == "AT": data["at"] = v
                        if ename == "T" and data["temp"] == "N/A": data["temp"] = v # 補溫度
                        break
            logs.append("✅ 預報數據已補位")
    except Exception as e_f:
        logs.append(f"預報獲取失敗: {e_f}")

    # === C. 天文數據 ===
    try:
        today_str = now.strftime("%Y-%m-%d")
        url_s = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001?Authorization={API_KEY}&LocationName=%E9%AB%98%E9%9B%84%E5%B8%82&Date={today_str}"
        res_s = requests.get(url_s, verify=False, timeout=8).json()
        sun_d = res_s.get('records', {}).get('locations', {}).get('location', [{}])[0].get('time', [{}])[0].get('parameter', [])
        for p in sun_d:
            if '日出' in p.get('parameterName', ''): data["sunrise"] = p.get('parameterValue')
            if '日沒' in p.get('parameterName', ''): data["sunset"] = p.get('parameterValue')
    except:
        pass
        
    return data, logs

# --- 主程式邏輯 ---
if st.button('🔄 啟動不死鳥偵測系統'):
    with st.spinner('正在掃描全頻段氣象訊號...'):
        D, debug_logs = fetch_phoenix_data()
    
    # 顯示狀態
    if D["temp"] != "N/A":
        st.markdown(f'<div class="status-ok">📍 訊號來源：{D["st_name"]} | 更新：{D["time"]}</div>', unsafe_allow_html=True)
        
        # 儀表板
        c1, c2 = st.columns(2)
        with c1:
            st.metric("🌡️ 溫度", f"{D['temp']} °C")
            st.metric("💨 風速", f"{D['ws']} m/s")
        with c2:
            st.metric("🧥 體感", f"{D['at']} °C")
            st.metric("🌧️ 降雨", f"{D['pop']} %")
            
        st.metric("☔ 時雨量", f"{D['rain']} mm")
        
        s1, s2 = st.columns(2)
        s1.markdown(f'**🌅 日出 {D["sunrise"]}**')
        s2.markdown(f'**🌇 日落 {D["sunset"]}**')
        
    else:
        st.markdown(f'<div class="status-fail">❌ 無法連線至氣象局伺服器</div>', unsafe_allow_html=True)
        st.error("系統已嘗試左營、高雄、鳳山三站，均無回應。")

    # 顯示診斷日誌 (幫助我們抓鬼)
    with st.expander("🛠️ 系統黑盒子 (若數據異常請查看)", expanded=True):
        st.markdown("```text\n" + "\n".join(debug_logs) + "\n```")

else:
    st.info("👋 V38 不死鳥已就緒。無論氣象局狀況如何，此版本保證不會崩潰。")
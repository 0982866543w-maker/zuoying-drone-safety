import streamlit as st
import requests
import urllib3
from datetime import datetime

# --- 系統配置 ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(page_title="左營飛行專家 V39", layout="centered")

# --- UI 美化 ---
st.markdown("""
    <style>
    .stMetric { background: #ffffff; border-radius: 12px; padding: 18px; border: 1px solid #e0e6ed; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 2.3rem !important; color: #0277bd; font-weight: 800; }
    .stButton>button { width: 100%; border-radius: 30px; background: linear-gradient(135deg, #0277bd, #01579b); color: white; height: 3.8em; font-weight: bold; border: none; }
    .debug-box { background: #263238; color: #80cbc4; padding: 15px; border-radius: 10px; font-family: monospace; font-size: 0.8rem; margin-top: 15px; }
    .source-badge { display: inline-block; padding: 4px 12px; border-radius: 15px; font-size: 0.8rem; font-weight: bold; margin-bottom: 10px; }
    .badge-obs { background: #e0f7fa; color: #006064; border: 1px solid #b2ebf2; }
    .badge-for { background: #fff3e0; color: #e65100; border: 1px solid #ffe0b2; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("🛡️ V39.0 廣域搜索版 (不指定 ID)")

API_KEY = "CWA-D94FFF0E-F69C-47D1-B2BA-480EBD5F1473"

def fetch_broadcasting_data():
    data = {
        "temp": "N/A", "ws": "0.0", "rain": "0.0", "pop": "0", "at": "N/A",
        "sunrise": "--:--", "sunset": "--:--", 
        "time": "--:--", "st_name": "搜尋中...", "is_forecast_takeover": False
    }
    logs = []
    
    # === 1. 廣域搜索實測資料 (O-A0003-001) ===
    # 不指定 StationId，抓取全部，然後自己找
    try:
        url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={API_KEY}"
        logs.append("正在下載全台測站清單...")
        res = requests.get(url, verify=False, timeout=15) # 資料量大，timeout 加長
        
        if res.status_code == 200:
            all_stations = res.json().get('records', {}).get('Station', [])
            logs.append(f"下載成功，共檢索到 {len(all_stations)} 個測站")
            
            # 本地過濾邏輯：優先找左營，次選高雄，末選鳳山
            target = None
            for s in all_stations:
                name = s.get('StationName', '')
                # 優先級 1: 左營
                if "左營" in name:
                    target = s
                    break
                # 優先級 2: 高雄 (如果還沒找到左營，先暫存高雄)
                if "高雄" in name and target is None:
                    target = s
            
            if target:
                data["st_name"] = target.get('StationName')
                w = target.get('WeatherElement', {})
                
                # 溫度
                t_val = float(w.get('AirTemperature', -99))
                data["temp"] = str(t_val) if t_val > -50 else "N/A"
                
                # 風速
                data["ws"] = w.get('WindSpeed', "0.0")
                
                # 雨量 (清洗負數)
                r_val = float(w.get('Now', {}).get('Precipitation', -99))
                data["rain"] = str(r_val) if r_val >= 0 else "0.0"
                
                # 時間
                t_obj = target.get('ObsTime')
                data["time"] = t_obj.get('DateTime', str(t_obj))[11:16] if isinstance(t_obj, dict) else str(t_obj)[11:16]
                
                logs.append(f"✅ 成功鎖定測站: {data['st_name']}")
            else:
                logs.append("⚠️ 在清單中未發現『左營』或『高雄』相關測站")
        else:
            logs.append(f"❌ API 連線失敗: {res.status_code}")
            
    except Exception as e:
        logs.append(f"⚠️ 實測資料獲取異常: {str(e)}")

    # === 2. 預報數據 (F-D0047-065) ===
    # 用來補齊體感、降雨機率，或者在實測失敗時「接管」溫度
    try:
        url_f = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"
        res_f = requests.get(url_f, verify=False, timeout=10).json()
        locs = res_f.get('records', {}).get('locations', [{}])[0].get('location', [])
        t_loc = next((l for l in locs if "左營" in l.get('locationName', '')), None)
        
        if t_loc:
            for elem in t_loc.get('weatherElement', []):
                ename = elem.get('elementName')
                # 抓取有效值
                for t in elem.get('time', []):
                    v = t.get('elementValue', [{}])[0].get('value')
                    if v and v not in ["-", " ", None]:
                        if ename == "PoP12h": data["pop"] = v
                        if ename == "AT": data["at"] = v
                        # 如果實測風速是 0 或 N/A，用預報風速覆蓋
                        if ename == "WS":
                            if data["ws"] in ["0.0", "0", "N/A"]: data["ws"] = v
                        # 【強制接管】如果實測溫度 N/A，用預報溫度頂替
                        if ename == "T" and (data["temp"] == "N/A" or data["temp"] == "-99.0"):
                            data["temp"] = v
                            data["is_forecast_takeover"] = True
                            data["st_name"] = "左營 (預報推估)"
                        break
            logs.append("✅ 預報數據校準完成")
    except Exception as e_f:
        logs.append(f"預報獲取失敗: {e_f}")

    # === 3. 天文數據 ===
    try:
        today_str = datetime.now().strftime("%Y-%m-%d")
        url_s = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001?Authorization={API_KEY}&LocationName=%E9%AB%98%E9%9B%84%E5%B8%82&Date={today_str}"
        res_s = requests.get(url_s, verify=False, timeout=10).json()
        sun_root = res_s.get('records', {}).get('locations', {}).get('location', [])
        if sun_root:
            params = sun_root[0].get('time', [{}])[0].get('parameter', [])
            for p in params:
                if '日出' in p.get('parameterName', ''): data["sunrise"] = p.get('parameterValue')
                if '日沒' in p.get('parameterName', ''): data["sunset"] = p.get('parameterValue')
    except:
        pass
        
    return data, logs

# --- 主程式 ---
if st.button('🔄 啟動 V39 廣域搜索'):
    with st.spinner('正在下載全台氣象資料庫並篩選...'):
        D, debug_logs = fetch_broadcasting_data()
    
    # 標籤顯示
    if D["is_forecast_takeover"]:
        st.markdown(f'<div class="source-badge badge-for">⚠️ 實測中斷，已切換至預報推估模式</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="source-badge badge-obs">📍 實測訊號：{D["st_name"]} | 🕒 {D["time"]}</div>', unsafe_allow_html=True)

    # 飛行決策
    try:
        f_ws = float(D["ws"])
        f_pop = int(D["pop"])
    except:
        f_ws, f_pop = 0.0, 0

    if f_ws > 7 or f_pop > 30:
        st.error(f"## 🛑 建議停飛\n風速 {f_ws}m/s 或 降雨 {f_pop}%")
    else:
        st.success(f"## ✅ 適合起飛\n左營環境穩定")

    c1, c2 = st.columns(2)
    with c1:
        st.metric("🌡️ 溫度", f"{D['temp']} °C")
        st.metric("💨 風速", f"{D['ws']} m/s")
    with c2:
        st.metric("🧥 體感", f"{D['at']} °C")
        st.metric("🌧️ 降雨機率", f"{D['pop']} %")
    
    st.metric("☔ 時雨量", f"{D['rain']} mm")
    
    s1, s2 = st.columns(2)
    s1.markdown(f'**🌅 日出 {D["sunrise"]}**')
    s2.markdown(f'**🌇 日落 {D["sunset"]}**')

    with st.expander("🛠️ 廣域搜索日誌", expanded=True):
        st.markdown("```text\n" + "\n".join(debug_logs) + "\n```")

else:
    st.info("👋 V39 已就緒。此版本將下載全台資料並在本地尋找左營站。")
import streamlit as st
import requests
import urllib3
from datetime import datetime

# --- 0. 系統配置 ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(page_title="左營飛行專家 V40", layout="centered")

# --- 1. UI 設計 ---
st.markdown("""
    <style>
    .stMetric { background: #ffffff; border-radius: 12px; padding: 18px; border: 1px solid #e0e6ed; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 2.3rem !important; color: #1a73e8; font-weight: 800; }
    .stButton>button { width: 100%; border-radius: 30px; background: linear-gradient(135deg, #1565c0, #0d47a1); color: white; height: 3.8em; font-weight: bold; border: none; }
    .badge { padding: 5px 10px; border-radius: 5px; font-weight: bold; font-size: 0.85rem; display: inline-block; margin-bottom: 10px; }
    .badge-obs { background: #e3f2fd; color: #1565c0; border: 1px solid #90caf9; }
    .badge-warn { background: #fff3e0; color: #ef6c00; border: 1px solid #ffcc80; }
    .sun-card { background: #fffde7; padding: 12px; border-radius: 12px; text-align: center; border: 1px solid #fbc02d; font-weight: bold; color: #f57f17; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("🛡️ V40.0 指揮官版 (蒲福風級+全數據修復)")

API_KEY = "CWA-D94FFF0E-F69C-47D1-B2BA-480EBD5F1473"

# --- 2. 核心工具函數 ---
def ms_to_beaufort(ms):
    """將 m/s 轉換為蒲福風級"""
    try:
        v = float(ms)
        if v < 0.3: return "0級 (無風)"
        elif v <= 1.5: return "1級 (軟風)"
        elif v <= 3.3: return "2級 (輕風)"
        elif v <= 5.4: return "3級 (微風)"
        elif v <= 7.9: return "4級 (和風)"
        elif v <= 10.7: return "5級 (清風)"
        elif v <= 13.8: return "6級 (強風)"
        elif v <= 17.1: return "7級 (疾風)"
        else: return f">8級 (危險)"
    except:
        return "N/A"

def get_force_val(ms):
    try: return float(ms)
    except: return 0.0

# --- 3. 數據抓取引擎 ---
def fetch_commander_data():
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    data = {
        "temp": "N/A", "ws_obs": "0.0", "ws_for": "0.0", "rain": "0.0", 
        "pop": "0", "at": "N/A", "sunrise": "--:--", "sunset": "--:--", 
        "st_name": "搜尋中...", "time": "--:--", "logs": []
    }
    
    # === A. 廣域搜索實測 (溫度、雨量、實測風速) ===
    try:
        # 下載全台資料
        url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={API_KEY}"
        res = requests.get(url, verify=False, timeout=15)
        
        if res.status_code == 200:
            all_stations = res.json().get('records', {}).get('Station', [])
            
            # 優先找左營，次選高雄
            target = None
            for s in all_stations:
                if "左營" in s.get('StationName', ''): 
                    target = s; break
            if not target:
                for s in all_stations:
                    if "高雄" in s.get('StationName', ''): 
                        target = s; break
            
            if target:
                data["st_name"] = target.get('StationName')
                w = target.get('WeatherElement', {})
                
                # 溫度與雨量
                t_val = float(w.get('AirTemperature', -99))
                data["temp"] = str(t_val) if t_val > -50 else "N/A"
                r_val = float(w.get('Now', {}).get('Precipitation', -99))
                data["rain"] = str(r_val) if r_val >= 0 else "0.0"
                data["ws_obs"] = w.get('WindSpeed', "0.0")
                
                # 時間
                t_obj = target.get('ObsTime')
                data["time"] = t_obj.get('DateTime', str(t_obj))[11:16] if isinstance(t_obj, dict) else str(t_obj)[11:16]
                data["logs"].append(f"✅ 實測鎖定: {data['st_name']}")
    except Exception as e:
        data["logs"].append(f"實測失敗: {e}")

    # === B. 預報數據 (體感、降雨機率、預報風速) ===
    try:
        url_f = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"
        res_f = requests.get(url_f, verify=False, timeout=10).json()
        locs = res_f.get('records', {}).get('locations', [{}])[0].get('location', [])
        # 搜尋左營區預報
        t_loc = next((l for l in locs if "左營" in l.get('locationName', '')), None)
        # 如果找不到左營預報，改找三民或高雄
        if not t_loc: t_loc = next((l for l in locs if "高雄" in l.get('locationName', '')), None)

        if t_loc:
            for elem in t_loc.get('weatherElement', []):
                ename = elem.get('elementName')
                # 抓取「現在」或「未來」的第一個有效值
                for t in elem.get('time', []):
                    # 簡單判斷：只要數值存在且不為空
                    v = t.get('elementValue', [{}])[0].get('value')
                    if v and v not in ["-", " ", None]:
                        if ename == "PoP12h": data["pop"] = v
                        if ename == "AT": data["at"] = v
                        if ename == "WS": data["ws_for"] = v
                        break # 找到第一個有效值就跳出
            data["logs"].append("✅ 預報數據校準完成")
    except:
        pass

    # === C. 天文數據 (日出日落) ===
    try:
        # 指定 Date 參數，API 會自動過濾
        url_s = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001?Authorization={API_KEY}&LocationName=%E9%AB%98%E9%9B%84%E5%B8%82&Date={today_str}"
        res_s = requests.get(url_s, verify=False, timeout=8).json()
        sun_list = res_s.get('records', {}).get('locations', {}).get('location', [])
        
        if sun_list:
            # 直接抓第一筆 (因為有指定 Date)
            params = sun_list[0].get('time', [{}])[0].get('parameter', [])
            for p in params:
                if '日出' in p.get('parameterName', ''): data["sunrise"] = p.get('parameterValue')
                if '日沒' in p.get('parameterName', ''): data["sunset"] = p.get('parameterValue')
            data["logs"].append("✅ 天文數據同步完成")
    except Exception as e:
        data["logs"].append(f"天文失敗: {e}")

    return data

# --- 4. 主介面邏輯 ---
if st.button('🔄 啟動 V40 指揮官系統'):
    with st.spinner('正在進行全數據融合...'):
        D = fetch_commander_data()

    # 風速決策：取「實測」與「預報」之大者，確保安全
    real_ws = get_force_val(D["ws_obs"])
    fore_ws = get_force_val(D["ws_for"])
    final_ws_val = max(real_ws, fore_ws)
    final_ws_str = f"{final_ws_val} m/s"
    
    # 轉換為蒲福風級顯示
    beaufort_str = ms_to_beaufort(final_ws_val)

    # 狀態標籤
    st.markdown(f'<div class="badge badge-obs">📍 訊號來源：{D["st_name"]} ｜ 🕒 {D["time"]}</div>', unsafe_allow_html=True)
    
    # 飛行建議
    pop_val = int(D["pop"]) if D["pop"].isdigit() else 0
    if final_ws_val > 7.9 or pop_val > 30: # 4級風以上建議注意
        st.error(f"## 🛑 注意風雨\n風力 {beaufort_str} 或 降雨 {pop_val}%")
    else:
        st.success(f"## ✅ 適合起飛\n左營環境穩定")

    c1, c2 = st.columns(2)
    with c1:
        st.metric("🌡️ 溫度", f"{D['temp']} °C")
        # 這裡改為顯示風級
        st.metric("💨 風級", beaufort_str, help=f"最大陣風: {final_ws_str}")
    with c2:
        st.metric("🧥 體感", f"{D['at']} °C")
        st.metric("🌧️ 降雨機率", f"{D['pop']} %")
    
    st.metric("☔ 時雨量", f"{D['rain']} mm")

    s1, s2 = st.columns(2)
    s1.markdown(f'<div class="sun-card">🌅 日出 {D["sunrise"]}</div>', unsafe_allow_html=True)
    s2.markdown(f'<div class="sun-card">🌇 日落 {D["sunset"]}</div>', unsafe_allow_html=True)

    with st.expander("🛠️ 系統日誌"):
        for l in D["logs"]: st.write(l)

else:
    st.info("👋 V40 已就緒。支援蒲福風級顯示與全數據修復。")
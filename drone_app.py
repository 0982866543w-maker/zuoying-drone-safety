import streamlit as st
import requests
import urllib3
from datetime import datetime

# --- 0. 系統核心配置 ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(page_title="左營飛行專家 V41", layout="centered")

# --- 1. UI 戰術面板 ---
st.markdown("""
    <style>
    .stMetric { background: #ffffff; border-radius: 12px; padding: 18px; border: 1px solid #cfd8dc; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 2.3rem !important; color: #0277bd; font-weight: 800; }
    .stButton>button { width: 100%; border-radius: 30px; background: linear-gradient(135deg, #0277bd, #01579b); color: white; height: 3.8em; font-weight: bold; border: none; }
    .sun-card { background: #fffde7; padding: 12px; border-radius: 12px; text-align: center; border: 1px solid #fbc02d; font-weight: bold; color: #f57f17; }
    .status-badge { display: inline-block; padding: 6px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; margin-bottom: 12px; background: #e1f5fe; color: #0277bd; border: 1px solid #81d4fa; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("🛡️ V41.0 戰術指揮版 (全數據暴力修復)")

API_KEY = "CWA-D94FFF0E-F69C-47D1-B2BA-480EBD5F1473"

# --- 2. 工具函數 ---
def ms_to_beaufort(ms):
    """m/s 轉蒲福風級 (標準表)"""
    try:
        v = float(ms)
        if v < 0.3: return "0級 (無風)"
        elif v <= 1.5: return "1級 (軟風)"
        elif v <= 3.3: return "2級 (輕風)"
        elif v <= 5.4: return "3級 (微風)" # 5.1 對應這裡
        elif v <= 7.9: return "4級 (和風)"
        elif v <= 10.7: return "5級 (清風)"
        elif v <= 13.8: return "6級 (強風)"
        else: return f">6級 (危險)"
    except: return "N/A"

def fetch_tactical_data():
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    data = {
        "temp": "N/A", "ws_obs": "0.0", "ws_for": "0.0", "rain": "0.0", 
        "pop": "0", "at": "N/A", "sunrise": "--:--", "sunset": "--:--", 
        "st_name": "搜尋中...", "time": "--:--", "logs": []
    }
    
    # === A. 實測數據 (廣域搜索) ===
    try:
        url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={API_KEY}"
        res = requests.get(url, verify=False, timeout=15)
        if res.status_code == 200:
            stations = res.json().get('records', {}).get('Station', [])
            # 優先級：左營 -> 高雄 -> 鳳山
            target = next((s for s in stations if "左營" in s.get('StationName', '')), None)
            if not target: target = next((s for s in stations if "高雄" in s.get('StationName', '')), None)
            if not target: target = next((s for s in stations if "鳳山" in s.get('StationName', '')), None)
            
            if target:
                data["st_name"] = target.get('StationName')
                w = target.get('WeatherElement', {})
                # 溫度
                t_val = float(w.get('AirTemperature', -99))
                data["temp"] = str(t_val) if t_val > -50 else "N/A"
                # 雨量
                r_val = float(w.get('Now', {}).get('Precipitation', -99))
                data["rain"] = str(r_val) if r_val >= 0 else "0.0"
                # 實測風速
                data["ws_obs"] = w.get('WindSpeed', "0.0")
                # 時間
                t_obj = target.get('ObsTime')
                data["time"] = t_obj.get('DateTime', str(t_obj))[11:16] if isinstance(t_obj, dict) else str(t_obj)[11:16]
                data["logs"].append(f"✅ 實測來源: {data['st_name']}")
    except Exception as e:
        data["logs"].append(f"實測異常: {e}")

    # === B. 預報數據 (關鍵修復：體感 + 3級風) ===
    try:
        # 下載鄉鎮預報
        url_f = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"
        res_f = requests.get(url_f, verify=False, timeout=10)
        
        if res_f.status_code == 200:
            locs = res_f.json().get('records', {}).get('locations', [{}])[0].get('location', [])
            
            # 搜尋策略：精確匹配 "左營區" -> 模糊 "左營" -> 鄰近 "三民區"
            t_loc = next((l for l in locs if "左營區" == l.get('locationName', '')), None)
            if not t_loc: t_loc = next((l for l in locs if "左營" in l.get('locationName', '')), None)
            if not t_loc: t_loc = next((l for l in locs if "三民區" in l.get('locationName', '')), None) # 備援
            
            if t_loc:
                data["logs"].append(f"✅ 預報鎖定: {t_loc.get('locationName')}")
                for elem in t_loc.get('weatherElement', []):
                    ename = elem.get('elementName')
                    # 抓取數值
                    for t in elem.get('time', []):
                        v = t.get('elementValue', [{}])[0].get('value')
                        if v and v not in ["-", " ", None]:
                            if ename == "PoP12h": data["pop"] = v
                            if ename == "AT": data["at"] = v
                            if ename == "WS": data["ws_for"] = v # 預報風速 (應為 5.1)
                            break
            else:
                data["logs"].append("⚠️ 預報清單中未找到左營區")
    except Exception as e:
        data["logs"].append(f"預報異常: {e}")

    # === C. 天文數據 (關鍵修復：暴力解析) ===
    try:
        # 移除 URL 中的 Date 過濾，改為全部抓下來再找 (比較穩)
        url_s = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001?Authorization={API_KEY}&LocationName=%E9%AB%98%E9%9B%84%E5%B8%82"
        res_s = requests.get(url_s, verify=False, timeout=10)
        if res_s.status_code == 200:
            days = res_s.json().get('records', {}).get('locations', {}).get('location', [{}])[0].get('time', [])
            
            # 尋找今天
            today_data = next((d for d in days if today_str in d.get('dataTime', '')), None)
            
            if today_data:
                for p in today_data.get('parameter', []):
                    # 模糊匹配參數名稱
                    p_name = p.get('parameterName', '')
                    if '日出' in p_name: data["sunrise"] = p.get('parameterValue')
                    if '日沒' in p.get('parameterName', '') or '日落' in p_name: data["sunset"] = p.get('parameterValue')
                data["logs"].append("✅ 天文數據同步成功")
            else:
                data["logs"].append(f"⚠️ 天文資料中找不到日期 {today_str}")
    except Exception as e:
        data["logs"].append(f"天文異常: {e}")

    return data

# --- 4. 主程式 ---
if st.button('🔄 啟動戰術數據融合'):
    with st.spinner('正在同步氣象局全頻道數據...'):
        D = fetch_tactical_data()

    # 風速決策：MAX(實測, 預報)
    try:
        obs_w = float(D["ws_obs"])
        for_w = float(D["ws_for"])
        final_ws = max(obs_w, for_w)
    except:
        final_ws = 0.0

    # 狀態列
    st.markdown(f'<div class="status-badge">📍 訊號：{D["st_name"]} ｜ 🕒 更新：{D["time"]}</div>', unsafe_allow_html=True)

    # 顯示指標
    c1, c2 = st.columns(2)
    with c1:
        st.metric("🌡️ 溫度", f"{D['temp']} °C")
        # 顯示蒲福風級 (例如: 3級)
        st.metric("💨 風級", ms_to_beaufort(final_ws), help=f"最大風速: {final_ws} m/s")
    with c2:
        st.metric("🧥 體感", f"{D['at']} °C")
        st.metric("🌧️ 降雨機率", f"{D['pop']} %")
    
    st.metric("☔ 時雨量", f"{D['rain']} mm")

    s1, s2 = st.columns(2)
    s1.markdown(f'<div class="sun-card">🌅 日出 {D["sunrise"]}</div>', unsafe_allow_html=True)
    s2.markdown(f'<div class="sun-card">🌇 日落 {D["sunset"]}</div>', unsafe_allow_html=True)

    # 飛行建議
    pop_v = int(D["pop"]) if D["pop"].isdigit() else 0
    if final_ws > 7.9 or pop_v > 30:
        st.warning(f"⚠️ 注意：風速達 {ms_to_beaufort(final_ws)}")
    else:
        st.success("✅ 適合起飛：左營環境穩定")

    with st.expander("🛠️ 系統日誌"):
        for l in D["logs"]: st.write(l)

else:
    st.info("👋 V41 就緒。全數據修復完成，請點擊按鈕。")
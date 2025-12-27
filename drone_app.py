import streamlit as st
import requests
import pandas as pd
import urllib3
from datetime import datetime

urllib3.disable_warnings()

# --- 1. 高端行動版 UI 配置 ---
st.set_page_config(page_title="左營飛行控制 Pro", layout="centered")

st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    .stMetric { background-color: #ffffff; border-radius: 15px; padding: 20px; border: 1px solid #e0e6ed; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; color: #1a73e8; font-weight: 800; }
    .stButton>button { width: 100%; border-radius: 30px; background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%); color: white; height: 3.8em; border: none; font-weight: bold; font-size: 1.1rem; transition: 0.3s; }
    .info-tag { background: #e3f2fd; color: #0d47a1; padding: 4px 12px; border-radius: 10px; font-size: 0.8rem; font-weight: bold; }
    .data-card { background: white; padding: 15px; border-radius: 15px; margin: 10px 0; border-left: 6px solid #1a73e8; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制系統")
st.caption("📱 雲端終極穩定版 (V19.0 精準對焦)")

# --- 2. 數據抓取核心 ---
API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"
# 鎖定高雄市鄉鎮預報
URL = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"

if st.button('🔄 點我同步左營即時氣象數據'):
    try:
        res = requests.get(URL, verify=False, timeout=15)
        data = res.json()
        
        # 深度搜尋邏輯：遍歷所有層級尋找 location
        locs_list = []
        if 'records' in data and 'locations' in data['records']:
            locs_list = data['records']['locations'][0].get('location', [])
        
        # 寬鬆匹配：只要名字包含「左營」就抓取
        target = next((l for l in locs_list if "左營" in l.get('locationName', '')), None)

        if target:
            # 初始化數據字典
            weather = {
                "Time": "更新中...", "T": "N/A", "AT": "N/A", 
                "WS": "0", "PoP": "0", "Desc": "讀取中...", "RH": "N/A"
            }
            
            elements = target.get('weatherElement', [])
            for elem in elements:
                ename = elem.get('elementName', '')
                times = elem.get('time', [])
                if not times: continue
                
                # 抓取第一筆預報
                val = times[0].get('elementValue', [{}])[0].get('value', '0')
                
                if ename == "T": weather["T"] = val      # 溫度
                elif ename == "AT": weather["AT"] = val  # 體感
                elif ename == "WS": weather["WS"] = val  # 風速
                elif ename == "PoP12h": weather["PoP"] = val if val != "-" else "0" # 降雨
                elif ename == "RH": weather["RH"] = val  # 濕度
                elif ename == "WeatherDescription": weather["Desc"] = val
                
                if not weather["Time"]:
                    weather["Time"] = times[0].get('startTime', '').replace('T', ' ')[5:16]

            # --- 🚀 飛行決策與 UI 展示 ---
            f_ws = float(weather["WS"])
            f_pop = int(weather["PoP"]) if weather["PoP"].isdigit() else 0

            # 決策燈號
            if f_ws > 7 or f_pop > 30:
                st.error(f"## 🛑 建議停飛\n目前降雨機率 {f_pop}% 或 風速 {f_ws}m/s 超過標準")
            else:
                st.success(f"## ✅ 適合起飛\n左營預報良好，祝飛行順利！")

            # 基本資料卡
            st.markdown(f"""
            <div class="data-card">
                <span class="info-tag">📍 地點：高雄市左營區</span>
                <span class="info-tag">🕒 數據時段：{weather['Time']}</span>
                <div style="margin-top:10px;">
                    <strong>📝 天氣摘要：</strong><br>{weather['Desc']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 數據格位
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🌡️ 預報溫度", f"{weather['T']} °C")
                st.metric("💨 預估風速", f"{weather['WS']} m/s")
            with col2:
                st.metric("🧥 體感溫度", f"{weather['AT']} °C")
                st.metric("🌧️ 降雨機率", f"{weather['PoP']} %")

            # 額外資訊（濕度與建議）
            st.write(f"💧 相對濕度：{weather['RH']}%")
            st.caption("註：預報 API 未提供精確即時日出日落時間，建議參考中央氣象署天文日曆。")

        else:
            st.error("❌ 診斷失敗：無法在高雄市清單中定位『左營』。")
            if locs_list:
                st.info(f"💡 目前 API 回傳的地區包含：{', '.join([l.get('locationName') for l in locs_list[:5]])}...")

    except Exception as e:
        st.error(f"⚠️ 工程診斷異常: {e}")
else:
    st.info("👋 飛手早安！請點擊上方按鈕獲取與官網同步的左營精確預報。")
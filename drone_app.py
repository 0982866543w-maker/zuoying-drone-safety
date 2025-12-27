import streamlit as st
import requests
import pandas as pd
import urllib3

urllib3.disable_warnings()

# --- 介面設定 ---
st.set_page_config(page_title="左營飛行控制 Pro", layout="centered")

st.markdown("""
    <style>
    .stMetric { background-color: #f8f9fa; border-radius: 15px; padding: 20px; border: 2px solid #dee2e6; }
    [data-testid="stMetricValue"] { font-size: 2.8rem !important; color: #007bff; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 25px; background: #007bff; color: white; height: 3.5em; font-weight: bold; font-size: 1.2rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制中心")
st.caption("✨ 專案首航版 (V15.0 數據全通)")

# 使用你剛剛測試成功的金鑰
API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"

# 同時掃描「鄉鎮版」與「縣市版」確保萬無一失
URL_ZUOYING = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"
URL_KAOHSIUNG = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091?Authorization={API_KEY}"

if st.button('🔄 立即獲取左營即時數據'):
    try:
        # 優先嘗試抓取左營 (065)
        res = requests.get(URL_ZUOYING, verify=False, timeout=10)
        data = res.json()
        
        # 進入解析流程
        recs = data.get('records', {}).get('locations', [{}])[0].get('location', [])
        target = next((l for l in recs if "左營" in l.get('locationName', '')), None)
        
        # 如果 065 沒資料，改抓 091 (高雄市)
        if not target:
            st.info("📡 正在切換至縣市級備援數據...")
            res = requests.get(URL_KAOHSIUNG, verify=False, timeout=10)
            data = res.json()
            recs = data.get('records', {}).get('Locations', [{}])[0].get('Location', [])
            target = next((l for l in recs if "高雄" in l.get('locationName', l.get('LocationName', ''))), None)

        if target:
            st.success(f"🎯 已連線至：{target.get('locationName', target.get('LocationName'))}")
            
            pop, ws = "0", "0"
            # 遍歷氣象要素 (注意大小寫兼容)
            elements = target.get('weatherElement', target.get('WeatherElement', []))
            for elem in elements:
                name = elem.get('elementName', elem.get('ElementName', ''))
                times = elem.get('time', elem.get('Time', []))
                
                # 抓取數值 (搜尋 12小時降雨機率 或 Wind Speed)
                if name in ["PoP12h", "12小時降雨機率", "ProbabilityOfPrecipitation"]:
                    v = times[0].get('elementValue', [{}])[0].get('value', times[0].get('elementValue', [{}])[0].get('ProbabilityOfPrecipitation', '0'))
                    pop = v if v != "-" else "0"
                if name in ["WS", "風速", "WindSpeed"]:
                    ws = times[0].get('elementValue', [{}])[0].get('value', times[0].get('elementValue', [{}])[0].get('WindSpeed', '0'))

            # --- 🚀 飛行建議判斷 ---
            f_pop = float(pop) if pop.replace('.','',1).isdigit() else 0
            f_ws = float(ws) if ws.replace('.','',1).isdigit() else 0
            
            if f_pop > 30 or f_ws > 7:
                st.error(f"## 🛑 建議停飛\n降雨 {pop}% / 風速 {ws} m/s")
            elif f_ws > 5:
                st.warning(f"## ⚠️ 謹慎飛行\n目前風速 {ws} m/s")
            else:
                st.success(f"## ✅ 適合飛行\n天氣理想，祝拍攝順利！")

            # --- 📊 數據展示 ---
            col1, col2 = st.columns(2)
            col1.metric("💨 風速", f"{ws} m/s")
            col2.metric("🌧️ 降雨", f"{pop} %")
        else:
            st.error("❌ 依然抓不到地點。請檢查氣象署網站是否正在維護中。")

    except Exception as e:
        st.error(f"⚠️ 系統錯誤: {e}")
else:
    st.info("👋 飛手早安！數據已準備就緒，點擊按鈕開啟你的左營首航。")
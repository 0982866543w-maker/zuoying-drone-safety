import streamlit as st
import requests
import pandas as pd
import urllib3

urllib3.disable_warnings()

# --- 1. 頁面介面設定 ---
st.set_page_config(page_title="左營飛行控制 Pro", layout="centered")

st.markdown("""
    <style>
    .stMetric { background-color: #f8f9fa; border-radius: 15px; padding: 20px; border: 2px solid #dee2e6; }
    [data-testid="stMetricValue"] { font-size: 3rem !important; color: #007bff; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 25px; background: #007bff; color: white; height: 3.5em; font-weight: bold; font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制中心")
st.caption("🎯 V16.0 數據精準對焦版")

# 使用你測試成功的金鑰
API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"
# 使用最穩定的縣市級資料源
URL = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091?Authorization={API_KEY}"

if st.button('🔄 立即獲取最新數據'):
    try:
        res = requests.get(URL, verify=False, timeout=10)
        data = res.json()
        
        # 進入 JSON 結構
        records = data.get('records', {})
        locations = records.get('Locations', records.get('locations', [{}]))[0].get('Location', [])
        
        # 精準鎖定「高雄市」
        target = next((l for l in locations if "高雄" in l.get('LocationName', '')), None)

        if target:
            st.success(f"🎯 已連線至：{target.get('LocationName')}")
            
            pop, ws = "0", "0"
            elements = target.get('WeatherElement', [])
            
            for elem in elements:
                name = elem.get('ElementName', '')
                times = elem.get('Time', [])
                if not times: continue
                
                # 取得第一筆數據的所有可能值
                val_dict = times[0].get('ElementValue', [{}])[0]
                
                # --- 智慧數據匹配邏輯 ---
                if name == "風速":
                    # 優先嘗試 WindSpeed 標籤，若無則試 value
                    ws = val_dict.get('WindSpeed', val_dict.get('value', '0'))
                
                if name == "12小時降雨機率":
                    # 優先嘗試 ProbabilityOfPrecipitation 標籤，若無則試 value
                    pop = val_dict.get('ProbabilityOfPrecipitation', val_dict.get('value', '0'))

            # 轉換為浮點數進行判斷
            f_pop = float(pop) if str(pop).replace('.','',1).isdigit() else 0
            f_ws = float(ws) if str(ws).replace('.','',1).isdigit() else 0

            # --- 🚀 飛行建議區 ---
            if f_pop > 30 or f_ws > 7:
                st.error(f"## 🛑 目前不建議起飛\n降雨機率 {pop}% / 風速 {ws} m/s")
            elif f_ws > 5:
                st.warning(f"## ⚠️ 謹慎飛行\n環境風力偏強 ({ws} m/s)")
            else:
                st.success(f"## ✅ 適合飛行\n天氣理想，祝首航順利！")

            # --- 📊 數據大字體展示 ---
            col1, col2 = st.columns(2)
            col1.metric("💨 目前風速", f"{ws} m/s")
            col2.metric("🌧️ 降雨機率", f"{pop} %")
            
            # 額外小撇步：顯示描述
            desc_elem = next((e for e in elements if e.get('ElementName') == '天氣預報綜合描述'), None)
            if desc_elem:
                st.info(f"📝 天氣摘要：{desc_elem['Time'][0]['ElementValue'][0]['WeatherDescription']}")

        else:
            st.error("❌ 無法在清單中找到高雄市，請檢查 API 回傳內容。")

    except Exception as e:
        st.error(f"⚠️ 解析異常: {e}")
else:
    st.info("👋 飛手早安！API 已通訊成功，請點擊按鈕獲取數值。")
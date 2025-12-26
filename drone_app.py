import streamlit as st
import requests
import pandas as pd
import urllib3

urllib3.disable_warnings()

# --- 1. 手機版頁面設定 ---
st.set_page_config(
    page_title="左營飛行決策", 
    layout="centered",  # 手機版建議使用 centered 佈局
    initial_sidebar_state="collapsed" # 預設隱藏側邊欄，增加畫面空間
)

# 強制優化手機端顯示的 CSS
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; border-radius: 15px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    [data-testid="stMetricValue"] { font-size: 2.5rem !important; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; font-size: 1.2rem; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制")
st.caption("📱 手機專用決策版")

API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"
url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"

# 將刷新按鈕放在最上方，方便手機點擊
if st.button('🔄 點我更新左營數據'):
    try:
        response = requests.get(url, verify=False).json()
        locations = response['records']['Locations'][0]['Location']
        target = next((loc for loc in locations if "左營" in loc['LocationName']), None)
        
        if target:
            elements = target['WeatherElement']
            pop, ws = 0, 0
            wind_trend, time_labels = [], []

            for elem in elements:
                if elem['ElementName'] == "PoP12h": pop = int(elem['Time'][0]['ElementValue'][0]['Value'])
                if elem['ElementName'] == "WS":
                    ws = int(elem['Time'][0]['ElementValue'][0]['Value'])
                    for i in range(6): # 手機版顯示未來 18 小時即可
                        wind_trend.append(int(elem['Time'][i]['ElementValue'][0]['Value']))
                        time_labels.append(elem['Time'][i]['StartTime'][11:16])

            # --- 🚀 手機版決策大燈號 ---
            st.markdown("### 🚦 飛行建議")
            if pop > 30 or ws > 7:
                st.error("## 🛑 嚴禁起飛\n風險極高，請即刻收機。")
            elif ws > 5:
                st.warning("## ⚠️ 謹慎飛行\n風力偏強，注意電池電量。")
            else:
                st.success("## ✅ 適合飛行\n氣候理想，祝拍攝順利！")

            # --- 📊 數據卡片 (垂直堆疊) ---
            st.metric("💨 風速", f"{ws} m/s")
            st.metric("🌧️ 降雨", f"{pop} %")

            # --- 📈 趨勢圖表 ---
            st.write("📈 未來風速趨勢")
            df = pd.DataFrame({"風速": wind_trend}, index=time_labels)
            st.area_chart(df, height=200) # 縮小圖表高度以符合手機螢幕

            st.sidebar.warning("🚩 **法規提醒**：左營區內有軍港與禁飛區，請務必開啟 Drone Map 確認。")

    except Exception as e:
        st.error(f"連線失敗，請確認網路狀態。")
else:
    st.info("👋 飛手你好！準備在左營起飛嗎？請點擊上方按鈕獲取最新預報。")
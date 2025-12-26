import streamlit as st
import requests
import pandas as pd
import urllib3

urllib3.disable_warnings()

# --- 1. 手機版頁面設定 ---
st.set_page_config(
    page_title="左營飛行決策", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# 手機端 CSS 優化
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; border-radius: 15px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    [data-testid="stMetricValue"] { font-size: 2.5rem !important; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; font-size: 1.2rem; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制")
st.caption("📱 手機專用決策版 (已優化數據抓取)")

API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"
# 使用高雄市鄉鎮預報 API
url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"

# 將刷新按鈕放在最上方
if st.button('🔄 點我更新左營數據'):
    try:
        response = requests.get(url, verify=False).json()
        
        # --- 數據路徑容錯處理 ---
        # 同時嘗試大寫 Records 與小寫 records
        records = response.get('records', response.get('Records', {}))
        # 同時嘗試大寫 Locations 與小寫 locations
        locs_wrapper = records.get('Locations', records.get('locations', [{}]))
        # 取得行政區清單
        locations = locs_wrapper[0].get('Location', locs_wrapper[0].get('location', []))
        
        # 搜尋左營區
        target = None
        for loc in locations:
            loc_name = loc.get('LocationName', loc.get('locationName', ''))
            if "左營" in loc_name:
                target = loc
                break
        
        if target:
            # 取得天氣因子列表
            elements = target.get('WeatherElement', target.get('weatherElement', []))
            pop, ws = 0, 0
            wind_trend, time_labels = [], []

            for elem in elements:
                e_name = elem.get('ElementName', elem.get('elementName'))
                
                # 抓取降雨機率 (PoP12h)
                if e_name == "PoP12h":
                    val = elem['Time'][0]['ElementValue'][0]['Value']
                    pop = int(val) if str(val).isdigit() else 0
                
                # 抓取風速 (WS)
                if e_name == "WS":
                    # 目前風速
                    ws_val = elem['Time'][0]['ElementValue'][0]['Value']
                    ws = int(ws_val) if str(ws_val).isdigit() else 0
                    # 未來趨勢
                    for i in range(min(6, len(elem['Time']))):
                        t_val = elem['Time'][i]['ElementValue'][0]['Value']
                        wind_trend.append(int(t_val) if str(t_val).isdigit() else 0)
                        # 格式化時間標籤
                        start_time = elem['Time'][i].get('StartTime', elem['Time'][i].get('dataTime', ''))
                        time_labels.append(start_time[11:16])

            # --- 🚀 手機版決策大燈號 ---
            st.markdown("### 🚦 飛行建議")
            if pop > 30 or ws > 7:
                st.error(f"## 🛑 嚴禁起飛\n風險極高 (降雨 {pop}%, 風速 {ws}m/s)")
            elif ws > 5:
                st.warning(f"## ⚠️ 謹慎飛行\n風力偏強，請注意操控。")
            else:
                st.success(f"## ✅ 適合飛行\n氣候理想，祝拍攝順利！")

            # --- 📊 數據卡片 ---
            st.metric("💨 風速", f"{ws} m/s")
            st.metric("🌧️ 降雨", f"{pop} %")

            # --- 📈 趨勢圖表 ---
            if wind_trend:
                st.write("📈 未來風速趨勢 (m/s)")
                df = pd.DataFrame({"風速": wind_trend}, index=time_labels)
                st.area_chart(df, height=200)

            st.sidebar.warning("🚩 **法規提醒**：左營區內有重要禁飛區，起飛前請確認地圖。")
        else:
            st.error("❌ 找不到左營區資料，請稍後再試。")

    except Exception as e:
        st.error(f"⚠️ 資料抓取失敗。原因：{e}")
else:
    st.info("👋 飛手你好！準備在左營起飛嗎？請點擊上方按鈕獲取最新預報。")
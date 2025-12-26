import streamlit as st
import requests
import pandas as pd
import urllib3

urllib3.disable_warnings()

# --- 1. 頁面美化設定 ---
st.set_page_config(page_title="左營飛行決策", layout="centered")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; border-radius: 15px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; color: #1f1f1f; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #007bff; color: white; height: 3.5em; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制")
st.caption("📱 雲端終極版 (V4.0 穩定診斷)")

# --- 2. 資料抓取邏輯 ---
API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"
# 抓取高雄市全區，避免網址中文編碼問題
url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"

if st.button('🔄 點我更新左營數據'):
    try:
        # 發送請求
        res = requests.get(url, verify=False)
        data = res.json()
        
        # 解析路徑：records -> locations[0] -> location (清單)
        recs = data.get('records', {})
        locs_wrapper = recs.get('locations', recs.get('Locations', [{}]))
        all_locations = locs_wrapper[0].get('location', locs_wrapper[0].get('Location', []))
        
        # 在 Python 內部尋找左營區
        target = None
        for loc in all_locations:
            if "左營" in loc.get('locationName', loc.get('LocationName', '')):
                target = loc
                break
        
        if target:
            # 提取天氣因子
            elements = target.get('weatherElement', target.get('WeatherElement', []))
            pop, ws = 0, 0
            wind_trend, time_labels = [], []

            for elem in elements:
                e_name = elem.get('elementName', elem.get('ElementName', ''))
                times = elem.get('time', elem.get('Time', []))
                
                if not times: continue
                
                # 取得第一筆數據數值
                val_list = times[0].get('elementValue', times[0].get('ElementValue', []))
                if not val_list: continue
                val = val_list[0].get('value', val_list[0].get('Value', '0'))

                if e_name == "PoP12h":
                    pop = int(val) if str(val).strip().isdigit() else 0
                elif e_name == "WS":
                    ws = int(val) if str(val).strip().isdigit() else 0
                    # 抓取趨勢
                    for t in times[:6]:
                        tv = t.get('elementValue', t.get('ElementValue', [{}]))[0].get('value', '0')
                        wind_trend.append(int(tv) if str(tv).strip().isdigit() else 0)
                        st_time = t.get('startTime', t.get('StartTime', t.get('dataTime', '0000-00-00 00:00')))
                        time_labels.append(st_time[11:16])

            # --- 🚀 UI 呈現 ---
            st.markdown("### 🚦 飛行建議")
            if pop > 30 or ws > 7:
                st.error(f"## 🛑 嚴禁起飛\n風險極高 (降雨 {pop}%, 風速 {ws}m/s)")
            elif ws > 5:
                st.warning(f"## ⚠️ 謹慎飛行\n風力偏強，注意電池續航。")
            else:
                st.success(f"## ✅ 適合飛行\n氣候理想，祝拍攝順利！")

            st.metric("💨 目前預估風速", f"{ws} m/s")
            st.metric("🌧️ 當前降雨機率", f"{pop} %")

            if wind_trend:
                st.write("📈 未來風速趨勢")
                st.area_chart(pd.DataFrame({"風速": wind_trend}, index=time_labels), height=200)
        else:
            st.error("❌ 找不到左營區資料。")

    except Exception as e:
        st.error(f"⚠️ 更新失敗：{e}")
else:
    st.info("👋 飛手你好！請點擊上方按鈕開始獲取左營預報。")
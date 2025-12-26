import streamlit as st
import requests
import pandas as pd
import urllib3

urllib3.disable_warnings()

st.set_page_config(page_title="左營飛行決策", layout="centered")

# 手機端 UI 優化
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; border-radius: 15px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; color: #1f1f1f; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #007bff; color: white; height: 3.5em; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚁 左營飛行控制")
st.caption("📱 手機專用決策版 (V2.0 自動修正版)")

API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"
# 加上 &format=JSON 確保回傳格式正確
url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}&format=JSON"

if st.button('🔄 點我更新左營數據'):
    try:
        response = requests.get(url, verify=False).json()
        
        # 1. 進入資料層 (容忍大小寫)
        recs = response.get('records', response.get('Records', {}))
        locs_list = recs.get('locations', recs.get('Locations', [{}]))
        loc_data = locs_list[0].get('location', locs_list[0].get('Location', []))
        
        # 2. 定位左營區
        target = next((l for l in loc_data if "左營" in l.get('locationName', l.get('LocationName', ''))), None)
        
        if target:
            elements = target.get('weatherElement', target.get('WeatherElement', []))
            pop, ws = 0, 0
            wind_trend, time_labels = [], []

            for elem in elements:
                # 取得元素名稱 (PoP12h, WS 等)
                e_name = elem.get('elementName', elem.get('ElementName', ''))
                
                # 取得時間列表 (容忍大小寫)
                times = elem.get('time', elem.get('Time', []))
                if not times: continue
                
                # 取得數值列表 (容忍大小寫)
                val_list = times[0].get('elementValue', times[0].get('ElementValue', []))
                if not val_list: continue
                
                # 抓取數值
                raw_val = val_list[0].get('value', val_list[0].get('Value', '0'))
                
                if e_name == "PoP12h":
                    pop = int(raw_val) if str(raw_val).strip().isdigit() else 0
                elif e_name == "WS":
                    ws = int(raw_val) if str(raw_val).strip().isdigit() else 0
                    # 抓取前 6 筆時間點做趨勢圖
                    for t in times[:6]:
                        v = t.get('elementValue', t.get('ElementValue', [{}]))[0].get('value', '0')
                        wind_trend.append(int(v) if str(v).strip().isdigit() else 0)
                        # 格式化時間 (從 2025-12-26 12:00:00 擷取 12:00)
                        st_time = t.get('startTime', t.get('StartTime', t.get('dataTime', '0000-00-00 00:00')))
                        time_labels.append(st_time[11:16])

            # --- 🚀 決策燈號 ---
            st.markdown("### 🚦 飛行建議")
            if pop > 30 or ws > 7:
                st.error(f"## 🛑 嚴禁起飛\n風險極高 (降雨 {pop}%, 風速 {ws}m/s)")
            elif ws > 5:
                st.warning(f"## ⚠️ 謹慎飛行\n風力偏強，請注意環境狀況。")
            else:
                st.success(f"## ✅ 適合飛行\n氣候理想，祝拍攝順利！")

            # --- 📊 數據展示 ---
            st.metric("💨 目前預估風速", f"{ws} m/s")
            st.metric("🌧️ 當前降雨機率", f"{pop} %")

            if wind_trend:
                st.write("📈 未來風速趨勢")
                st.area_chart(pd.DataFrame({"風速": wind_trend}, index=time_labels), height=200)
        else:
            st.error("❌ 找不到左營區資料，請檢查 API 回傳內容。")

    except Exception as e:
        st.error(f"⚠️ 更新失敗：{e}")
else:
    st.info("👋 飛手你好！請點擊上方按鈕開始獲取左營預報。")
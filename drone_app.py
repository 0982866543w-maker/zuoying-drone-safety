import streamlit as st
import requests
import pandas as pd
import urllib3

urllib3.disable_warnings()

st.set_page_config(page_title="左營飛行決策", layout="centered")

st.title("🚁 左營飛行控制")
st.caption("📱 雲端正式版 (V3.0 深度解析)")

API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"
# 加入 locationName 參數直接讓氣象署幫我們過濾，減少程式負擔
url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}&locationName=左營區"

if st.button('🔄 點我更新左營數據'):
    try:
        response = requests.get(url, verify=False).json()
        
        # 深度解析路徑：records -> locations[0] -> location[0]
        # 使用 .get() 確保不會因為標籤不存在而崩潰
        recs = response.get('records', {})
        locs = recs.get('locations', [{}])[0].get('location', [{}])
        target = locs[0] # 因為我們 URL 已經過濾了左營區，所以抓第一個

        if target and 'weatherElement' in target:
            pop, ws = 0, 0
            wind_trend, time_labels = [], []

            for elem in target['weatherElement']:
                # PoP12h: 12小時降雨機率, WS: 風速
                name = elem.get('elementName')
                times = elem.get('time', [])
                
                if name == "PoP12h" and times:
                    # 抓取第一個時段的數值
                    val = times[0]['elementValue'][0]['value']
                    pop = int(val) if val != " " else 0
                
                if name == "WS" and times:
                    # 抓取目前的風速
                    curr_ws = times[0]['elementValue'][0]['value']
                    ws = int(curr_ws) if curr_ws != " " else 0
                    
                    # 抓取趨勢數據
                    for t in times[:6]:
                        t_ws = t['elementValue'][0]['value']
                        wind_trend.append(int(t_ws) if t_ws != " " else 0)
                        time_labels.append(t['startTime'][11:16])

            # --- 🚀 視覺化呈現 ---
            st.markdown("### 🚦 飛行建議")
            if pop > 30 or ws > 7:
                st.error(f"## 🛑 嚴禁起飛\n風險偏高 (降雨{pop}%, 風速{ws}m/s)")
            elif ws > 5:
                st.warning(f"## ⚠️ 謹慎飛行\n風力稍大，請注意環境")
            else:
                st.success(f"## ✅ 適合飛行\n天氣理想，祝拍攝順利！")

            col1, col2 = st.columns(2)
            col1.metric("💨 風速", f"{ws} m/s")
            col2.metric("🌧️ 降雨機率", f"{pop} %")

            if wind_trend:
                st.write("📈 未來風速變化")
                st.area_chart(pd.DataFrame({"風速": wind_trend}, index=time_labels))
        else:
            st.error("❌ 抓取不到左營區數據，請確認 API 授權碼是否有效。")

    except Exception as e:
        st.error(f"⚠️ 解析錯誤: {e}")
else:
    st.info("👋 點擊上方按鈕，獲取最新左營飛行氣象預報。")
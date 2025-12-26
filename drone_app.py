import streamlit as st
import requests
import pandas as pd
import urllib3

urllib3.disable_warnings()

st.set_page_config(page_title="左營飛行決策", layout="centered")

st.title("🚁 左營飛行控制")
st.caption("📱 雲端終極版 (V4.0 穩定診斷)")

# 你的 API KEY
API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"
# 抓取高雄市全區資料，避開 URL 中文編碼問題
url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"

if st.button('🔄 點我更新左營數據'):
    try:
        res = requests.get(url, verify=False)
        data = res.json()
        
        # 1. 檢查 API 是否成功回傳資料
        if 'records' not in data:
            st.error(f"❌ API 授權碼可能失效或流量上限。錯誤訊息：{data.get('message', '無')}")
        else:
            # 2. 兼容大小寫路徑導航
            recs = data.get('records', {})
            locs_root = recs.get('locations', recs.get('Locations', [{}]))
            location_list = locs_root[0].get('location', locs_root[0].get('Location', []))
            
            # 3. 在清單中精準搜尋「左營」
            target = None
            for loc in location_list:
                ln = loc.get('locationName', loc.get('LocationName', ''))
                if "左營" in ln:
                    target = loc
                    break
            
            if target:
                # 4. 提取天氣因子
                elements = target.get('weatherElement', target.get('WeatherElement', []))
                pop, ws = 0, 0
                wind_trend, time_labels = [], []

                for elem in elements:
                    en = elem.get('elementName', elem.get('ElementName', ''))
                    times = elem.get('time', elem.get('Time', []))
                    
                    if en == "PoP12h" and times:
                        # 降雨機率
                        ev = times[0].get('elementValue', times[0].get('ElementValue', [{}]))
                        v = ev[0].get('value', ev[0].get('Value', '0'))
                        pop = int(v) if str(v).strip().isdigit() else 0
                    
                    if en == "WS" and times:
                        # 當前風速
                        ev = times[0].get('elementValue', times[0].get('ElementValue', [{}]))
                        v = ev[0].get('value', ev[0].get('Value', '0'))
                        ws = int(v) if str(v).strip().isdigit() else 0
                        
                        # 未來趨勢 (前 6 筆)
                        for t in times[:6]:
                            tev = t.get('elementValue', t.get('ElementValue', [{}]))
                            tv = tev[0].get('value', tev[0].get('Value', '0'))
                            wind_trend.append(int(tv) if str(tv).strip().isdigit() else 0)
                            st_time = t.get('startTime', t.get('StartTime', t.get('dataTime', '0000-00-00 00:00:00')))
                            time_labels.append(st_time[11:16])

                # --- 🚀 UI 顯示區 ---
                st.markdown("### 🚦 飛行建議")
                if pop > 30 or ws > 7:
                    st.error(f"## 🛑 嚴禁起飛\n風險極高 (降雨 {pop}%, 風速 {ws}m/s)")
                elif ws > 5:
                    st.warning(f"## ⚠️ 謹慎飛行\n風力偏強，請注意操控")
                else:
                    st.success(f"## ✅ 適合飛行\n氣候理想，祝拍攝順利！")

                col1, col2 = st.columns(2)
                col1.metric("💨 風速", f"{ws} m/s")
                col2.metric("🌧️ 降雨", f"{pop} %")

                if wind_trend:
                    st.write("📈 未來風速變化")
                    st.area_chart(pd.DataFrame({"風速": wind_trend}, index=time_labels))
            else:
                st.error("❌ 找不到左營區資料。請確認 API ID 是否為高雄市 (F-D0047-065)。")
                # 診斷用：印出前三個區域名稱
                names = [loc.get('locationName', loc.get('LocationName')) for loc in location_list[:3]]
                st.write(f"系統看到的區域名稱舉例：{names}")

    except Exception as e:
        st.error(f"⚠️ 系統解析錯誤: {e}")
else:
    st.info("👋 飛手你好！請點擊按鈕獲取最新預報。")
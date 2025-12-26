import streamlit as st
import requests
import pandas as pd
import urllib3

urllib3.disable_warnings()

st.set_page_config(page_title="左營飛行控制 Pro", layout="centered")

st.title("🚁 左營飛行控制系統")
st.caption("📱 雲端終極版 (V11.0 穩定診斷)")

API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"
url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}"

if st.button('🔄 點我獲取最新左營數據'):
    try:
        response = requests.get(url, verify=False, timeout=10).json()
        
        # 深度定位 Location 清單
        recs = response.get('records', {}).get('locations', [{}])[0].get('location', [])
        if not recs: # 嘗試大寫
            recs = response.get('Records', {}).get('Locations', [{}])[0].get('Location', [])
            
        # 尋找左營
        target = next((l for l in recs if "左營" in l.get('locationName', l.get('LocationName', ''))), None)
        
        if target:
            pop, ws = "0", "0"
            for elem in target.get('weatherElement', target.get('WeatherElement', [])):
                name = elem.get('elementName', elem.get('ElementName', ''))
                times = elem.get('time', elem.get('Time', []))
                if not times: continue
                
                # 遍歷時段找第一個非空數值
                for t in times:
                    val_list = t.get('elementValue', t.get('ElementValue', []))
                    if not val_list: continue
                    v = str(val_list[0].get('value', '0')).strip()
                    if v and v != " ":
                        if name == "PoP12h" and pop == "0": pop = v
                        if name == "WS" and ws == "0": ws = v
                        break

            # --- 顯示結果 ---
            st.success(f"✅ 資料更新成功！")
            col1, col2 = st.columns(2)
            col1.metric("💨 風速", f"{ws} m/s")
            col2.metric("🌧️ 降雨", f"{pop} %")
            
            f_ws = float(ws)
            if f_ws > 7: st.error("🛑 風速過高，禁飛！")
            elif f_ws > 5: st.warning("⚠️ 強風警告，請小心！")
            else: st.success("🍀 天氣理想，適合飛行")

        else:
            st.error("❌ 暫時搜尋不到「左營區」。")
            # 診斷訊息：看看 API 到底傳了什麼回來
            if recs:
                names = [l.get('locationName', l.get('LocationName')) for l in recs[:10]]
                st.info(f"💡 目前系統看得到的地區有：{', '.join(names)}...")
            else:
                st.warning("📡 氣象署伺服器目前未回傳任何地點資料，可能正在維護中。")

    except Exception as e:
        st.error(f"⚠️ 異常報錯: {e}")
else:
    st.info("👋 辛苦了一整晚，明天早上點擊刷新試試看！")
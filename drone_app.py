import streamlit as st
import requests
import pandas as pd
import urllib3

urllib3.disable_warnings()

st.set_page_config(page_title="左營飛行控制 Pro", layout="centered")

st.title("🚁 左營飛行控制系統")
st.caption("📱 雲端終極版 (V12.0 雙路備援版)")

API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"

# 同時準備兩個資料源，增加穩定性
URL_A = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-065?Authorization={API_KEY}" # 鄉鎮
URL_B = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091?Authorization={API_KEY}" # 全區

if st.button('🔄 點我獲取最新左營數據'):
    try:
        # 第一路徑測試 (鄉鎮)
        res = requests.get(URL_A, verify=False, timeout=10)
        data = res.json()
        recs = data.get('records', {}).get('locations', [{}])[0].get('location', [])
        
        # 如果第一路徑沒資料，嘗試第二路徑 (全區)
        if not recs:
            st.warning("📡 鄉鎮資料庫維護中，正在啟動備援系統...")
            res = requests.get(URL_B, verify=False, timeout=10)
            data = res.json()
            recs = data.get('records', {}).get('locations', [{}])[0].get('location', [])

        target = next((l for l in recs if "左營" in l.get('locationName', '')), None)
        
        if target:
            pop, ws = "0", "0"
            for elem in target.get('weatherElement', []):
                name = elem.get('elementName')
                times = elem.get('time', [])
                if not times: continue
                # 搜尋有效數據
                for t in times:
                    val = t.get('elementValue', [{}])[0].get('value', '0')
                    if val.strip() != "":
                        if name == "PoP12h" and pop == "0": pop = val
                        if name == "WS" and ws == "0": ws = val
                        break

            st.success(f"✅ 數據獲取成功！")
            col1, col2 = st.columns(2)
            col1.metric("💨 風速預估", f"{ws} m/s")
            col2.metric("🌧️ 降雨機率", f"{pop} %")
            
            f_ws = float(ws)
            if f_ws > 7: st.error("🛑 風速過高，禁飛！")
            elif f_ws > 5: st.warning("⚠️ 強風警告，請小心！")
            else: st.success("🍀 天氣理想，適合飛行")
        else:
            st.error("❌ 依然找不到「左營區」，這極大可能是 API Key 流量已達上限。")
            st.info(f"API 回傳訊息: {data.get('message', '無')}")

    except Exception as e:
        st.error(f"⚠️ 異常報錯: {e}")
else:
    st.info("👋 飛手早安！請點擊按鈕獲取最新預報。")
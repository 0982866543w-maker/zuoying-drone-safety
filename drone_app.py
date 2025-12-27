import streamlit as st
import requests
import pandas as pd
import urllib3

urllib3.disable_warnings()

st.set_page_config(page_title="左營飛行診斷 Pro", layout="centered")

st.title("🚁 左營飛行控制系統")
st.caption("📱 雲端終極版 (V14.0 數據真相診斷)")

API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"

# 使用最廣泛的資料源
URL = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091?Authorization={API_KEY}"

if st.button('🔍 執行深度診斷與數據抓取'):
    try:
        res = requests.get(URL, verify=False, timeout=15)
        raw_data = res.json()
        
        # --- 診斷 A: 結構揭露 ---
        st.sidebar.subheader("📡 API 原始結構")
        st.sidebar.write("JSON 頂層標籤:", list(raw_data.keys()))
        
        # 嘗試進入 records
        records = raw_data.get('records', {})
        locations_wrapper = records.get('locations', [{}])
        location_list = locations_wrapper[0].get('location', [])

        if location_list:
            # --- 診斷 B: 找出所有地點名稱 ---
            all_names = [str(l.get('locationName', '未知')) for l in location_list]
            st.sidebar.write("📍 目前可用的地點:", all_names)
            
            # --- 執行搜尋 ---
            # 改用更寬鬆的關鍵字搜尋
            target = None
            for loc in location_list:
                name = str(loc.get('locationName', ''))
                if "左營" in name:
                    target = loc
                    break
            
            if target:
                st.success(f"🎯 成功鎖定地點：{target.get('locationName')}")
                # 數據解析邏輯... (略，維持 V12 解析方式)
                pop, ws = "0", "0"
                for elem in target.get('weatherElement', []):
                    en = elem.get('elementName')
                    times = elem.get('time', [])
                    if times:
                        val = times[0].get('elementValue', [{}])[0].get('value', '0')
                        if en == "PoP12h": pop = val
                        if en == "WS": ws = val
                
                col1, col2 = st.columns(2)
                col1.metric("💨 風速", f"{ws} m/s")
                col2.metric("🌧️ 降雨", f"{pop} %")
                
                # 法規檢查邏輯
                if float(ws) > 7: st.error("🛑 風速超標，禁飛！")
                else: st.success("🍀 天氣理想，適合飛行")
            else:
                st.error("❌ 清單中找不到包含『左營』的地區。")
                st.info(f"💡 請查看側邊欄的地區清單，確認名稱是否正確。")
        else:
            st.error("💀 氣象署回傳了空數據包 (Empty location list)。")
            st.json(raw_data) # 直接印出原始 JSON 幫助除錯

    except Exception as e:
        st.error(f"⚠️ 診斷異常: {e}")
else:
    st.info("👋 飛手早安！目前左營天氣顯示為陣雨，點擊按鈕獲取精確數值。")
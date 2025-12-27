import streamlit as st
import requests
import pandas as pd
import urllib3

urllib3.disable_warnings()

st.set_page_config(page_title="左營飛行診斷 Pro", layout="centered")

st.title("🚁 左營飛行控制系統")
st.caption("📱 雲端終極版 (V13.0 全透明診斷版)")

API_KEY = "CWA-A5D64001-383B-43D4-BC10-F956196BA22B"

# 使用最穩定的全區資料源
URL = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091?Authorization={API_KEY}"

if st.button('🔍 執行深度數據掃描'):
    try:
        res = requests.get(URL, verify=False, timeout=10)
        data = res.json()
        
        # 診斷 A: 檢查 API 成功標誌
        st.sidebar.write("📡 API 狀態:", data.get('success', '未知'))
        
        # 診斷 B: 深度挖掘 Location
        recs = data.get('records', {}).get('locations', [{}])[0].get('location', [])
        
        if not recs:
            # 嘗試另一種 JSON 結構 (大寫開頭)
            recs = data.get('Records', {}).get('Locations', [{}])[0].get('Location', [])

        if recs:
            # 診斷 C: 列出所有區域供檢查
            all_names = [l.get('locationName', l.get('LocationName', '無名')) for l in recs]
            st.sidebar.write("📍 偵測到的地區清單:", all_names)
            
            # 模糊比對搜尋「左營」
            target = next((l for l in recs if "左營" in str(l.get('locationName', l.get('LocationName', '')))), None)
            
            if target:
                st.success("🎯 成功定位左營區資料！")
                pop, ws = "0", "0"
                for elem in target.get('weatherElement', target.get('WeatherElement', [])):
                    en = elem.get('elementName', elem.get('ElementName', ''))
                    # 抓取第一筆有效數據
                    times = elem.get('time', elem.get('Time', []))
                    if times:
                        val = times[0].get('elementValue', times[0].get('ElementValue', [{}]))[0].get('value', '0')
                        if en == "PoP12h": pop = val
                        if en == "WS": ws = val

                col1, col2 = st.columns(2)
                col1.metric("💨 風速", f"{ws} m/s")
                col2.metric("🌧️ 降雨", f"{pop} %")
            else:
                st.error("❌ 清單中有資料，但裡面沒有包含『左營』的地區。")
                st.write("目前清單前三名:", all_names[:3])
        else:
            st.error("💀 氣象署回傳了空包裹 (無 Location 資料)。")
            st.info("建議：請前往氣象署官網重新申請一組新的 API Key 試試看！")

    except Exception as e:
        st.error(f"⚠️ 診斷異常: {e}")
else:
    st.info("👋 飛手早安！請執行掃描來確認資料流狀態。")
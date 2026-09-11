#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tw-nfc-guide 콘텐츠 정의 → dist/data.json 생성.

    python3 data3.py            # dist/data.json 재생성

규약
- 텍스트 필드는 전부 T(zh, en, ko) → {"zh","en","ko"} dict. app.js의 t()가 현재 언어로 꺼내고 없으면 zh로 폴백.
- 아이템 종류
    poi(...)   장소 카드 (정보 / 도보 / 자동차 길찾기 버튼). origin=페이지의 client.
    route(...) 교통 카드 (대중교통 / 택시 버튼). from→dest 길찾기.
    tip(...)   안내 박스
    info(...)  key/value 표 (개관시간·연락처)
- 구글맵 링크는 좌표가 아니라 "장소명 + 주소" 텍스트 쿼리로 만든다(app.js에서 조립). 좌표(lat/lng)는
  거리·시간 추정에만 쓴다 → 인쇄 전 구글맵으로 재확인 권장.
"""
import json, math, os

def T(zh, en=None, ko=None):
    return {"zh": zh, "en": en if en is not None else zh, "ko": ko if ko is not None else (en if en is not None else zh)}

def place(name, address, lat=None, lng=None, **kw):
    d = {"name": name, "address": address}
    if lat is not None: d["lat"] = lat; d["lng"] = lng
    d.update(kw)
    return d

def _hav(a, b):
    if not a or not b or a.get("lat") is None or b.get("lat") is None: return None
    R = 6371.0
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dp, dl = p2 - p1, math.radians(b["lng"] - a["lng"])
    h = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(h))

def _est(origin, dest, walk=True, drive=True):
    """직선거리 기반 추정. 도로 우회계수 1.35, 도보 75 m/min, 시내 차량 28 km/h(장거리 55 km/h)."""
    d = _hav(origin, dest)
    if d is None: return {}
    road = d * 1.35
    out = {"km": round(road, 1) if road >= 1 else round(road, 1)}
    if walk and road <= 3.0:
        out["walk_min"] = max(2, int(round(road*1000/75/5.0))*5)
    if drive:
        speed = 28 if road < 15 else 55
        out["drive_min"] = max(3, int(round(road/speed*60/5.0))*5)
    return out

def poi(name, address, desc=None, lat=None, lng=None, tag=None, hours=None, modes=None, origin=None, walk=True, km=None, drive_min=None):
    it = {"kind": "poi", "name": name, "address": address}
    if desc: it["desc"] = desc
    if tag: it["tag"] = tag
    if hours: it["hours"] = hours
    if lat is not None:
        it["lat"], it["lng"] = lat, lng
        it.update(_est(origin, it, walk=walk))
    if km is not None: it["km"] = km
    if drive_min is not None: it["drive_min"] = drive_min
    if modes: it["modes"] = modes
    return it

def route(name, frm=None, desc=None, steps=None, tag=None, modes=None, dest=None, origin_for_est=None, km=None, drive_min=None):
    it = {"kind": "route", "name": name}
    if frm: it["from"] = frm
    if desc: it["desc"] = desc
    if steps: it["steps"] = steps
    if tag: it["tag"] = tag
    if modes: it["modes"] = modes
    if dest: it["dest"] = dest
    if frm and origin_for_est and frm.get("lat") is not None:
        it.update(_est(frm, origin_for_est, walk=False))
    if km is not None: it["km"] = km
    if drive_min is not None: it["drive_min"] = drive_min
    return it

def tip(title, text=None, html=None):
    it = {"kind": "tip", "tip": title}
    if html: it["html"] = html
    else: it["text"] = text
    return it

def info(rows):
    return {"kind": "info", "rows": [dict(k=k, v=v, **({"href": h} if h else {})) for (k, v, h) in rows]}

def section(title, items):
    return {"title": title, "items": items}

PAGES = {}
# ---- 콘텐츠는 아래 CONTENT 블록에서 채운다 ----

# ============================================================== lin — The Lin Hotel 林酒店
LIN = place(T("林酒店", "The Lin Hotel Taichung", "린 호텔 타이중"),
            T("台中市西屯區朝富路99號", "No. 99, Chaofu Rd, Xitun District, Taichung", "台中市西屯區朝富路99號"),
            24.1653, 120.6372, phone="+886-4-2255-5555", website="https://www.thelin.com.tw",
            short=T("林酒店", "The Lin Hotel", "린 호텔"))
_o = LIN
PAGES["lin"] = {
    "client": LIN, "origin": LIN,
    "kicker": T("Taichung Hotel Association", "Taichung Hotel Association", "Taichung Hotel Association"),
    "title": T("周邊美食與景點", "Nearby Food & Sights", "주변 맛집·명소"),
    "subtitle": T("從林酒店出發，步行或短程車程即可抵達。點選按鈕以 Google 地圖導航。",
                  "All within a walk or a short ride from The Lin Hotel. Tap a button to navigate with Google Maps.",
                  "린 호텔에서 도보 또는 짧은 차량 이동으로 갈 수 있는 곳들입니다. 버튼을 누르면 구글맵으로 길안내가 열립니다."),
    "sections": [
        section(T("周邊美食", "Food & Drink", "주변 맛집"), [
            poi(T("春水堂 朝富店", "Chun Shui Tang (Chaofu)", "춘수이탕 차오푸점"), T("台中市西屯區朝馬三街12號"),
                T("珍珠奶茶發源品牌，步行即達的人文茶館。", "Birthplace brand of bubble tea, a short walk from the hotel.", "버블티 원조 브랜드, 호텔에서 걸어갈 수 있는 찻집."),
                24.1666, 120.6362, tag=T("珍奶 / 茶館", "Bubble tea", "버블티"), hours=T("08:30–23:00"), origin=_o),
            poi(T("屋馬燒肉 中港店", "Umai Yakiniku (Zhonggang)", "우마 야키니쿠 중강점"), T("台中市西屯區台灣大道三段300號1F"),
                T("台中最難訂位的人氣燒肉名店，建議先訂位。", "Taichung's most sought-after yakiniku; book ahead.", "타이중에서 예약이 가장 어려운 인기 야키니쿠. 예약 필수."),
                24.1664, 120.6436, tag=T("燒肉", "Yakiniku", "야키니쿠"), hours=T("11:00–01:00"), origin=_o),
            poi(T("鼎泰豐 台中大遠百店", "Din Tai Fung (Top City)", "딘타이펑 탑시티점"), T("台中市西屯區台灣大道三段251號B2"),
                T("世界知名小籠包，位於大遠百 B2。", "World-famous xiaolongbao on Top City's B2 floor.", "세계적으로 유명한 샤오롱바오, 탑시티 백화점 B2."),
                24.1646, 120.6445, tag=T("小籠包", "Dumplings", "샤오롱바오"), hours=T("週一–五 11:00–21:30 · 週六日 10:30–21:30", "Mon–Fri 11:00–21:30 · Sat–Sun 10:30–21:30", "월–금 11:00–21:30 · 토·일 10:30–21:30"), origin=_o),
            poi(T("阿秋大肥鵝海鮮樓", "A-Chiu Roast Goose & Seafood", "아추 다페이어 해산물 레스토랑"), T("台中市西屯區市政南一路128號"),
                T("台中老字號燒鵝與現撈海鮮合菜餐廳。", "Long-running Taichung favorite for roast goose and live seafood.", "타이중의 오랜 명가. 구운 거위와 활어 해산물 요리."),
                24.1600, 120.6345, tag=T("台菜 / 海鮮", "Taiwanese", "대만 요리"), hours=T("11:00–14:30 · 17:00–22:00"), origin=_o),
            poi(T("無老鍋 台中公益店", "Wulao Hot Pot (Gongyi)", "우라오궈 공익점"), T("台中市南屯區公益路二段74號"),
                T("鼎王旗下養生麻辣鴛鴦鍋，營業到凌晨。", "Herbal and spicy dual hot pot by Tripod King, open till late.", "딩왕 계열의 약선·마라 훠궈. 새벽까지 영업."),
                24.1512, 120.6455, tag=T("火鍋", "Hot pot", "훠궈"), hours=T("11:30–04:00"), origin=_o),
            poi(T("宏香火雞肉飯 黎明店", "Hong Xiang Turkey Rice (Liming)", "훙샹 훠지로우판 리밍점"), T("台中市西屯區黎明路三段45號"),
                T("24 小時營業的平價台式小吃：火雞肉飯、爌肉飯。", "24-hour local eatery for turkey rice and braised pork rice.", "24시간 영업 서민 식당. 칠면조 덮밥과 돼지고기 덮밥."),
                24.1690, 120.6350, tag=T("台式小吃", "Local eats", "로컬 푸드"), hours=T("24 小時", "24 hours", "24시간"), origin=_o),
        ]),
        section(T("周邊景點", "Sights", "주변 명소"), [
            poi(T("秋紅谷景觀生態公園", "Maple Garden (Qiuhonggu)", "추홍구 생태공원"), T("台中市西屯區朝富路30號"),
                T("飯店旁的下凹式湖景公園，夜景迷人。", "Sunken lakeside park next to the hotel, lovely at night.", "호텔 바로 옆 움푹 파인 호수 공원. 야경이 아름다움."),
                24.1659, 120.6388, tag=T("公園", "Park", "공원"), hours=T("24 小時", "24 hours", "24시간"), origin=_o),
            poi(T("臺中國家歌劇院", "National Taichung Theater", "타이중 국가가극원"), T("台中市西屯區惠來路二段101號"),
                T("伊東豊雄設計的曲牆建築地標，免費參觀。", "Toyo Ito's curved-wall landmark; free to explore.", "이토 도요가 설계한 곡면 건축 랜드마크. 무료 입장."),
                24.1626, 120.6403, tag=T("建築 / 藝文", "Architecture", "건축"), hours=T("11:30–21:00（週一休）", "11:30–21:00 (closed Mon)", "11:30–21:00 (월요일 휴관)"), origin=_o),
            poi(T("Top City 台中大遠百", "Top City (Far Eastern Dept. Store)", "탑시티 타이중 다위안바이"), T("台中市西屯區台灣大道三段251號"),
                T("台中最大百貨，鄰新光三越，餐廳影城齊全。", "Taichung's largest mall, next to Shin Kong Mitsukoshi.", "타이중 최대 백화점. 신광미츠코시와 인접."),
                24.1646, 120.6445, tag=T("購物", "Shopping", "쇼핑"), hours=T("週一–五 11:00–22:00 · 週六日 10:30–22:00", "Mon–Fri 11:00–22:00 · Sat–Sun 10:30–22:00", "월–금 11:00–22:00 · 토·일 10:30–22:00"), origin=_o),
            poi(T("臺中市政府（新市政中心）", "Taichung City Hall", "타이중 시청"), T("台中市西屯區台灣大道三段99號"),
                T("瑞士建築師設計的市政大樓與廣場。", "Swiss-designed city hall and civic plaza.", "스위스 건축가가 설계한 시청사와 광장."),
                24.1615, 120.6474, tag=T("地標", "Landmark", "랜드마크"), origin=_o),
            poi(T("逢甲夜市", "Fengjia Night Market", "펑자 야시장"), T("台中市西屯區文華路"),
                T("全台規模最大的夜市，小吃創意百出。", "Taiwan's largest night market, packed with creative snacks.", "대만 최대 규모 야시장. 창의적인 길거리 음식 천국."),
                24.1773, 120.6466, tag=T("夜市", "Night market", "야시장"), hours=T("約 17:00–01:00", "approx. 17:00–01:00", "약 17:00–01:00"), origin=_o),
            poi(T("文心森林公園", "Wenxin Forest Park", "원신 삼림공원"), T("台中市南屯區文心路一段289號"),
                T("8.8 公頃綠地，內有圓滿戶外劇場。", "8.8-hectare green space with the Fulfillment Amphitheater.", "8.8헥타르 녹지 공원. 야외 원형극장 보유."),
                24.1460, 120.6448, tag=T("公園", "Park", "공원"), hours=T("24 小時", "24 hours", "24시간"), origin=_o),
        ]),
        section(T("小提醒", "Good to know", "안내"), [
            tip(T("回飯店", "Back to the hotel", "호텔로 돌아오기"),
                T("向計程車司機出示：林酒店 台中市西屯區朝富路99號（電話 04-2255-5555）。",
                  "Show the driver: 林酒店 台中市西屯區朝富路99號 (The Lin Hotel, tel. 04-2255-5555).",
                  "택시 기사에게 보여주세요: 林酒店 台中市西屯區朝富路99號 (린 호텔, 전화 04-2255-5555).")),
        ]),
    ],
    "footer": T("店家資訊以現場公告為準。", "Opening hours may change; check before you go.", "영업 정보는 현장 안내를 우선합니다."),
}

# ============================================================== comin — 康茵行旅 Comin' Place (烏日, 高鐵台中站 근처)
COMIN = place(T("康茵行旅", "Comin' Place", "코민 플레이스 (康茵行旅)"),
              T("台中市烏日區大同九街73號", "No. 73, Datong 9th St, Wuri District, Taichung", "台中市烏日區大同九街73號"),
              24.1126, 120.6283, phone="+886-4-2338-9333", website="https://comingplace.com",
              short=T("康茵行旅", "Comin' Place", "康茵行旅"))
_oC = COMIN
PAGES["comin"] = {
    "client": COMIN, "origin": COMIN,
    "kicker": T("Taichung Hotel Association", "Taichung Hotel Association", "Taichung Hotel Association"),
    "title": T("周邊美食與景點", "Nearby Food & Sights", "주변 맛집·명소"),
    "subtitle": T("飯店距高鐵台中站約 1 公里。點選按鈕以 Google 地圖導航。",
                  "The hotel is about 1 km from THSR Taichung Station. Tap a button to navigate with Google Maps.",
                  "호텔은 고속철도 타이중역에서 약 1 km. 버튼을 누르면 구글맵으로 길안내가 열립니다."),
    "sections": [
        section(T("周邊美食", "Food & Drink", "주변 맛집"), [
            poi(T("這隻雞全席美食", "This Chicken Taiwanese Kitchen", "저즈지 대만 가정요리"), T("台中市烏日區中山路三段164號"),
                T("烏日人氣台式合菜，招牌脆皮烤雞外酥內嫩，附免費停車。", "Popular Taiwanese family-style restaurant famous for crispy roast chicken.", "바삭한 통닭구이로 유명한 대만식 가정요리 식당. 무료 주차."),
                24.1150, 120.6200, tag=T("台菜", "Taiwanese", "대만 요리"), hours=T("11:00–14:00 · 17:00–21:30（週二休）", "11:00–14:00 · 17:00–21:30 (closed Tue)", "11:00–14:00 · 17:00–21:30 (화요일 휴무)"), origin=_oC),
            poi(T("拾捌號粥鋪 烏日本鋪", "No. 18 Congee House (Wuri)", "18호 죽집 우르 본점"), T("台中市烏日區中華路591-1號"),
                T("在地人氣海鮮粥，魚骨雞骨熬湯、料多實在，每日限量。", "Local favorite for hearty seafood congee with daily-simmered broth.", "매일 우려낸 육수로 끓인 푸짐한 해산물 죽. 현지인 맛집."),
                24.1085, 120.6330, tag=T("粥品", "Congee", "죽"), hours=T("11:00–14:00 · 16:30–21:00（週日休）", "11:00–14:00 · 16:30–21:00 (closed Sun)", "11:00–14:00 · 16:30–21:00 (일요일 휴무)"), origin=_oC),
            poi(T("五花馬水餃館 烏日門市", "Wu Hua Ma Dumpling House (Xinwuri)", "우화마 만두관 신우르점"), T("台中市烏日區高鐵東一路26號2樓"),
                T("新烏日站 2 樓的水餃麵食館，水餃、紅燒牛肉麵快速上桌。", "Dumplings and beef noodle soup on the 2F of TRA Xinwuri Station.", "신우르역 2층 만두·우육면 전문점. 빠르고 든든한 식사."),
                24.1105, 120.6168, tag=T("水餃 / 麵", "Dumplings", "만두·면"), hours=T("11:00–20:30"), origin=_oC),
            poi(T("一風堂 台中高鐵店", "IPPUDO Ramen (Taichung HSR)", "잇푸도 라멘 타이중 고속철도점"), T("台中市烏日區站區二路8號 高鐵台中站"),
                T("博多豚骨拉麵名店，就在高鐵台中站內。", "Hakata-style tonkotsu ramen right inside THSR Taichung Station.", "고속철도 타이중역 안에 있는 하카타식 돈코츠 라멘."),
                24.1120, 120.6160, tag=T("拉麵", "Ramen", "라멘"), hours=T("11:00–22:00"), origin=_oC),
            poi(T("台中高鐵食堂", "Taichung HSR Shokudo", "타이중 고속철도 식당"), T("台中市烏日區站區二路8號2F 高鐵台中站"),
                T("日式庶民食堂，自助式選菜、出餐快速，平價又下飯。", "Japanese cafeteria-style set meals: quick, affordable, pick your dishes.", "원하는 반찬을 골라 담는 일본식 식당. 빠르고 저렴한 한 끼."),
                24.1122, 120.6160, tag=T("日式食堂", "Japanese", "일식"), hours=T("11:00–21:00"), origin=_oC),
            poi(T("老先覺麻辣鍋 烏日高鐵店", "Lao Xian Jue Hot Pot (Wuri HSR)", "라오셴줴 마라궈 우르 고속철도점"), T("台中市烏日區健行路761號"),
                T("個人小火鍋連鎖，多種湯頭，可加價蔬食自助吧。", "Individual hot pot chain with many broths and an optional veggie bar.", "1인 훠궈 체인. 다양한 육수와 채소 무한리필 바 옵션."),
                24.1120, 120.6210, tag=T("火鍋", "Hot pot", "훠궈"), hours=T("11:30–21:00"), origin=_oC),
        ]),
        section(T("周邊景點", "Sights", "주변 명소"), [
            poi(T("烏日啤酒觀光工廠", "Wuri Brewery (Taiwan Beer)", "우르 맥주 관광공장"), T("台中市烏日區光華街1號"),
                T("台灣啤酒生產基地，巨型啤酒箱打卡與產品推廣中心免費參觀。", "Taiwan Beer's brewery with a giant beer-crate photo spot and free product center.", "타이완 맥주 양조장. 대형 맥주 상자 포토존과 무료 매장·전시관."),
                24.1110, 120.6220, tag=T("觀光工廠", "Factory", "관광공장"), hours=T("09:00–18:00"), origin=_oC),
            poi(T("筏子溪門戶迎賓水岸廊道", "Fazi River TAICHUNG Landmark", "파즈시 TAICHUNG 랜드마크"), T("台中市南屯區筏子東街一段33-59號"),
                T("1.8 公里河岸步道與 4 公尺高 TAICHUNG 立體字，夜間點燈。", "1.8 km riverside walk with the 4 m TAICHUNG sign, lit up at night.", "1.8 km 강변 산책로와 밤에 빛나는 4 m TAICHUNG 조형물."),
                24.1305, 120.6197, tag=T("河岸 / 打卡", "Riverside", "강변 포토존"), hours=T("24 小時 · 點燈 17:00–22:00", "24 hours · lit 17:00–22:00", "24시간 · 점등 17:00–22:00"), origin=_oC),
            poi(T("彩虹眷村", "Rainbow Village", "무지개 마을 (차이훙 쥐안춘)"), T("台中市南屯區春安路56巷25號"),
                T("彩虹爺爺的繽紛彩繪村，2023 年整修後重新開放，免費參觀。", "Colorful painted village by “Rainbow Grandpa”, reopened in 2023, free entry.", "‘레인보우 할아버지’의 알록달록 벽화 마을. 2023년 재개장, 무료."),
                24.1336, 120.6098, tag=T("藝術", "Art", "예술"), hours=T("約 09:00–17:00", "approx. 09:00–17:00", "약 09:00–17:00"), origin=_oC, walk=False),
            poi(T("望高寮夜景公園", "Wanggaoliao Night View Park", "왕가오랴오 야경공원"), T("台中市南屯區中台路601號"),
                T("大肚山上的百萬夜景平台，可眺望台中市區與台中港。", "Hilltop lookout on Dadu Mountain with sweeping Taichung night views.", "다두산 언덕의 무료 전망대. 타이중 시내 야경 명소."),
                24.1436, 120.5813, tag=T("夜景", "Night view", "야경"), hours=T("24 小時", "24 hours", "24시간"), origin=_oC, walk=False),
            poi(T("東海大學 路思義教堂", "Luce Memorial Chapel, Tunghai University", "동해대학 루스 기념 예배당"), T("台中市西屯區台灣大道四段1727號 東海大學"),
                T("貝聿銘與陳其寬設計的帆形教堂，台中經典現代建築地標。", "Iconic sail-shaped chapel by I. M. Pei and Chen Chi-kwan on a leafy campus.", "I. M. 페이가 설계한 돛 모양 예배당. 타이중 대표 건축 명소."),
                24.1788, 120.6005, tag=T("建築", "Architecture", "건축"), hours=T("外觀全天 · 內部平日 16:00–18:00", "Exterior anytime · interior weekdays 16:00–18:00", "외관 상시 · 내부 평일 16:00–18:00"), origin=_oC, walk=False),
        ]),
        section(T("小提醒", "Good to know", "안내"), [
            tip(T("回飯店", "Back to the hotel", "호텔로 돌아오기"),
                T("向計程車司機出示：康茵行旅 台中市烏日區大同九街73號（電話 04-2338-9333）。從高鐵台中站步行約 15 分鐘。",
                  "Show the driver: 康茵行旅 台中市烏日區大同九街73號 (Comin' Place, tel. 04-2338-9333). About 15 min on foot from THSR Taichung Station.",
                  "택시 기사에게 보여주세요: 康茵行旅 台中市烏日區大同九街73號 (전화 04-2338-9333). 고속철도 타이중역에서 도보 약 15분.")),
        ]),
    ],
    "footer": T("店家資訊以現場公告為準。", "Opening hours may change; check before you go.", "영업 정보는 현장 안내를 우선합니다."),
}

# ============================================================== miso — 台灣味噌釀造文化館 (豐原)
MISO = place(T("台灣味噌釀造文化館", "Taiwan Miso Brewing Culture Museum", "타이완 미소 양조 문화관"),
             T("台中市豐原區西勢路701號", "No. 701, Xishi Rd, Fengyuan District, Taichung", "台中市豐原區西勢路701號"),
             24.2342, 120.7007, phone="+886-4-2532-0279", website="https://www.sauceco.com.tw/",
             short=T("味噌釀造文化館", "Miso Culture Museum", "미소 양조 문화관"))
FENGYUAN = place(T("臺鐵豐原車站", "TRA Fengyuan Station", "타이완철도 펑위안역"), T("台中市豐原區中正路1號"), 24.2543, 120.7237)
HSR_TC  = place(T("高鐵台中站", "THSR Taichung Station", "고속철도 타이중역"), T("台中市烏日區站區二路8號"), 24.1121, 120.6157)
TRA_TC  = place(T("臺鐵臺中車站", "TRA Taichung Station", "타이완철도 타이중역"), T("台中市中區臺灣大道一段1號"), 24.1369, 120.6852)
PAGES["miso"] = {
    "client": MISO, "origin": MISO, "dest": MISO,
    "kicker": T("味榮食品 Wei Jung Foods", "Wei Jung Foods", "味榮食品 Wei Jung Foods"),
    "title": T("交通方式與參觀資訊", "Getting Here & Visitor Info", "오시는 길·관람 안내"),
    "subtitle": T("文化館位於豐原（非烏日）。以下路線皆可一鍵開啟 Google 地圖導航。",
                  "The museum is in Fengyuan, north of central Taichung. Tap any route to open it in Google Maps.",
                  "문화관은 타이중 북쪽 펑위안(豐原)에 있습니다. 아래 경로를 누르면 구글맵 길안내가 열립니다."),
    "sections": [
        section(T("交通方式", "Getting here", "오시는 길"), [
            route(T("從臺鐵豐原車站", "From TRA Fengyuan Station", "타이완철도 펑위안역에서"), frm=FENGYUAN,
                  desc=T("最近的車站。計程車約 10 分鐘。", "Nearest station. About 10 min by taxi.", "가장 가까운 역. 택시로 약 10분."),
                  steps=[T("公車：豐原轉運中心搭 921 路 → 「台灣味噌文化館」站下車，步行 1–4 分鐘。",
                           "Bus: Route 921 from Fengyuan Transfer Station → alight at “台灣味噌文化館 (Taiwan Miso Culture Museum)”, 1–4 min walk.",
                           "버스: 펑위안 환승센터에서 921번 → ‘台灣味噌文化館’ 정류장 하차 후 도보 1~4분."),
                         T("亦可搭 12、63 路至「承德三社東路口」，步行約 4 分鐘。",
                           "Routes 12 / 63 to “承德三社東路口” also work, about 4 min on foot.",
                           "12번·63번 ‘承德三社東路口’ 정류장 하차 후 도보 약 4분도 가능.")],
                  tag=T("最近", "Nearest", "최단"), modes=["transit", "driving"], km=4, drive_min=10),
            route(T("從高鐵台中站", "From THSR Taichung Station", "고속철도 타이중역에서"), frm=HSR_TC,
                  desc=T("約 25 公里。計程車／開車約 35–45 分鐘（國道 1 號北上，豐原交流道下）。",
                         "About 25 km. Taxi or car 35–45 min via National Freeway 1 north, Fengyuan exit.",
                         "약 25 km. 택시·자동차로 35~45분 (국도 1호선 북행, 펑위안 IC)."),
                  steps=[T("大眾運輸：步行至臺鐵新烏日站 → 區間車至豐原站（約 35–40 分）→ 轉 921 路或計程車。",
                           "Transit: walk to TRA Xinwuri Station → local train to Fengyuan (35–40 min) → Bus 921 or taxi.",
                           "대중교통: 타이완철도 신우르역까지 도보 → 일반열차로 펑위안역(35~40분) → 921번 버스 또는 택시.")],
                  modes=["driving", "transit"], km=25, drive_min=40),
            route(T("從臺鐵臺中車站", "From TRA Taichung Station", "타이완철도 타이중역에서"), frm=TRA_TC,
                  desc=T("約 14 公里。計程車／開車約 30–40 分鐘。", "About 14 km. Taxi or car 30–40 min.", "약 14 km. 택시·자동차로 30~40분."),
                  steps=[T("臺鐵至豐原站（15–20 分）再轉 921 路；或搭公車 12 路至「承德三社東路口」（約 60 分）。",
                           "Train to Fengyuan (15–20 min) then Bus 921; or City Bus 12 direct to “承德三社東路口” (about 60 min).",
                           "열차로 펑위안역(15~20분) 후 921번 환승, 또는 시내버스 12번으로 ‘承德三社東路口’ 직행(약 60분).")],
                  modes=["transit", "driving"], km=14, drive_min=35),
            route(T("自行開車：國道 1 號 豐原交流道", "By car: National Freeway 1, Fengyuan Interchange", "자동차: 국도 1호선 펑위안 IC"),
                  frm=place(T("國道1號 豐原交流道", "National Freeway 1 Fengyuan Interchange", "국도1호 펑위안 IC"), T("台中市豐原區 國道一號豐原交流道")),
                  desc=T("交流道至館約 3 公里、5–8 分鐘。館內有免費停車場。", "About 3 km / 5–8 min from the exit. Free on-site parking.", "IC에서 약 3 km, 5~8분. 무료 주차장 있음."),
                  steps=[T("豐原交流道（約 168K）下 → 往豐原方向沿中山路直行 → 右轉豐原大道",
                           "Exit at Fengyuan IC (≈ km 168) toward Fengyuan → straight on Zhongshan Rd → right onto Fengyuan Blvd",
                           "펑위안 IC(약 168K)에서 펑위안 방면 → 중산로 직진 → 펑위안대도로 우회전"),
                         T("見 TOYOTA 服務廠右轉豐栗路 → 左轉西勢路 → 第二個紅綠燈前約 100 公尺，左側大樹旁即 701 號",
                           "Right at the TOYOTA service center (Fengli Rd) → left onto Xishi Rd → No. 701 is on the left by a large tree, ~100 m before the 2nd light",
                           "TOYOTA 서비스센터에서 펑리로로 우회전 → 시스로로 좌회전 → 두 번째 신호등 약 100 m 전 왼쪽 큰 나무 옆이 701호")],
                  tag=T("開車", "Car", "자동차"), modes=["driving"], km=3.0, drive_min=8),
        ]),
        section(T("參觀資訊", "Visitor info", "관람 안내"), [
            info([
                (T("開館時間", "Hours", "개관 시간"), T("每日 09:00–17:00（最後入館約 16:00）", "Daily 09:00–17:00 (last entry ~16:00)", "매일 09:00–17:00 (최종 입장 약 16:00)"), None),
                (T("門票", "Admission", "입장료"), T("免費入館，自由參觀；味噌湯／醋飲免費試喝", "Free entry, self-guided; free miso soup & vinegar tasting", "무료 입장, 자유 관람. 미소국·식초 음료 무료 시음"), None),
                (T("導覽", "Guided tour", "가이드 투어"), T("每日 10:00／13:00／15:00，NT$100（可折抵消費 100 元），需預約", "Daily 10:00 / 13:00 / 15:00, NT$100 (NT$100 shop credit), reservation required", "매일 10:00 / 13:00 / 15:00, NT$100 (매장 이용권 NT$100 포함), 예약 필수"), None),
                (T("DIY 體驗", "DIY workshop", "DIY 체험"), T("導覽 + DIY NT$300（味噌／味噌手工皂／醬油），需預約", "Tour + DIY NT$300 (miso / miso soap / soy sauce), reservation required", "투어+DIY NT$300 (미소·미소 비누·간장), 예약 필수"), None),
                (T("預約", "Reservation", "예약"), T("線上預約 sauceco.com.tw/booking", "Book online: sauceco.com.tw/booking", "온라인 예약: sauceco.com.tw/booking"), "https://www.sauceco.com.tw/booking/"),
                (T("電話", "Phone", "전화"), T("04-2532-0279 #43", "+886-4-2532-0279 ext. 43", "+886-4-2532-0279 (내선 43)"), "tel:+88642532027943"),
                (T("停車", "Parking", "주차"), T("館內免費停車場（汽車、遊覽車）", "Free on-site parking (cars & coaches)", "무료 주차장 (승용차·관광버스)"), None),
                (T("官網", "Website", "홈페이지"), T("www.sauceco.com.tw"), "https://www.sauceco.com.tw/"),
            ]),
            tip(T("注意", "Note", "주의"),
                T("地址是「豐原區」西勢路，並非烏日。若請司機導航，請出示：台灣味噌釀造文化館 台中市豐原區西勢路701號。",
                  "The museum is on Xishi Rd in FENGYUAN District, not Wuri. Show the driver: 台灣味噌釀造文化館 台中市豐原區西勢路701號.",
                  "주소는 우르(烏日)가 아니라 펑위안(豐原)구 시스로입니다. 기사에게 보여주세요: 台灣味噌釀造文化館 台中市豐原區西勢路701號.")),
        ]),
    ],
    "footer": T("開館時間與導覽場次以官網公告為準。", "Hours and tour times per the official website.", "개관 시간·투어 회차는 공식 홈페이지 공지를 우선합니다."),
}

# ============================================================== ncnu — 暨南國際大學 觀光休閒與餐旅管理學系 (埔里)
NCNU = place(T("國立暨南國際大學 觀光休閒與餐旅管理學系", "NCNU Dept. of Tourism, Leisure & Hospitality Management", "국립지난국제대학 관광레저·호텔경영학과"),
             T("南投縣埔里鎮大學路1號", "No. 1, Daxue Rd, Puli Township, Nantou County", "南投縣埔里鎮大學路1號"),
             23.9530, 120.9347, phone="+886-49-291-0960", website="https://www.tourism.ncnu.edu.tw/",
             short=T("暨大 觀餐系", "NCNU Tourism & Hospitality", "지난대 관광호텔학과"))
# 자동차 목적지는 管理學院 (大學路470號) — 핸드오프 §3
NCNU_MGMT = place(T("國立暨南國際大學 管理學院", "NCNU College of Management", "지난대 경영대학(관리학원)"), T("南投縣埔里鎮大學路470號"), 23.9535, 120.9330)
NCNU_BUSSTOP = place(T("暨南大學站（公車）", "National Chi Nan University bus stop", "지난대학 버스 정류장"), T("南投縣埔里鎮大學路1號 暨南大學"))
PULI_TERM = place(T("埔里轉運站", "Puli Bus Terminal", "푸리 버스터미널"), T("南投縣埔里鎮中正路338號"), 23.9660, 120.9636)
TC_GANCHENG = place(T("台中干城站", "Taichung Gancheng Bus Station", "타이중 간청 버스터미널"), T("台中市東區雙十路一段35-8號"), 24.1394, 120.6880)
_oN = NCNU_MGMT
PAGES["ncnu"] = {
    "client": NCNU, "origin": NCNU, "dest": NCNU,
    "kicker": T("管理學院 338 室", "College of Management, Room 338", "경영대학(관리학원) 338호"),
    "title": T("交通方式與周邊景點", "Getting Here & Nearby Sights", "오시는 길·주변 명소"),
    "subtitle": T("校園位於南投埔里。由高鐵台中站搭台灣好行 6670 直達，或走國道 6 號愛蘭交流道。",
                  "The campus is in Puli, Nantou. Take Taiwan Tourist Shuttle 6670 direct from THSR Taichung, or drive via National Freeway 6, Ailan exit.",
                  "캠퍼스는 난터우 푸리(埔里)에 있습니다. 고속철도 타이중역에서 타이완 하오싱 6670 버스로 직행하거나, 국도 6호선 아이란 IC로 오세요."),
    "sections": [
        section(T("交通方式", "Getting here", "오시는 길"), [
            route(T("從高鐵台中站：台灣好行 6670", "From THSR Taichung: Tourist Shuttle 6670", "고속철도 타이중역에서: 하오싱 6670"), frm=HSR_TC,
                  desc=T("直達「暨南大學」站，約 55–65 分鐘，約每小時一班。", "Direct to the “National Chi Nan University” stop, about 55–65 min, roughly hourly.", "‘暨南大學’ 정류장 직행, 약 55~65분, 약 1시간 간격."),
                  steps=[T("高鐵台中站 5 號出口 客運轉運站 → 南投客運 6670 日月潭線（6670A–F 皆可）",
                           "Exit 5 bus terminal → Nantou Bus 6670 Sun Moon Lake Line (any 6670A–F)",
                           "5번 출구 버스터미널 → 난터우버스 6670 일월담선 (6670A~F 모두 가능)"),
                         T("經國道 6 號 → 埔里轉運站 → 「暨南大學」下車（6670B/E/F 進校內停學人會館；A/C/D 停校門口）",
                           "Via Freeway 6 → Puli Terminal → alight “暨南大學” (6670B/E/F enter campus to Scholar House; A/C/D stop at the main gate)",
                           "국도 6호선 경유 → 푸리 터미널 → ‘暨南大學’ 하차 (6670B/E/F는 교내 학인회관, A/C/D는 정문)"),
                         T("票價：高鐵台中站→埔里 全票約 NT$135", "Fare THSR Taichung → Puli about NT$135", "요금: 고속철도역→푸리 약 NT$135"),
                         T("計程車約 45–55 分鐘、約 NT$1,500–1,900", "Taxi about 45–55 min, roughly NT$1,500–1,900", "택시 약 45~55분, 약 NT$1,500~1,900")],
                  tag=T("推薦", "Recommended", "추천"), modes=["transit", "driving"], dest=NCNU_BUSSTOP, km=58, drive_min=50),
            route(T("從台中市區：干城站／臺中車站", "From downtown Taichung: Gancheng / TRA station", "타이중 시내에서: 간청역·타이중역"), frm=TC_GANCHENG,
                  desc=T("6670 自台中干城站發車，停臺中車站（民族路口）、高鐵台中站後上國道 6 號。到暨大約 70–80 分鐘。",
                         "Bus 6670 starts at Gancheng Station, calls at Taichung Railway Station (Minzu Rd) and THSR Taichung, then Freeway 6. About 70–80 min to NCNU.",
                         "6670은 간청역 출발, 타이중역(민족로)·고속철도역 경유 후 국도 6호선. 지난대까지 약 70~80분."),
                  steps=[T("台中→埔里 全票約 NT$110，平日約每小時一班，首班約 07:15", "Taichung → Puli about NT$110, hourly on weekdays, first bus ≈ 07:15", "타이중→푸리 약 NT$110, 평일 약 1시간 간격, 첫차 약 07:15")],
                  modes=["transit", "driving"], dest=NCNU_BUSSTOP, km=62, drive_min=60),
            route(T("自行開車：國道 6 號 愛蘭交流道", "By car: Freeway 6, Ailan Interchange", "자동차: 국도 6호선 아이란 IC"),
                  frm=place(T("國道6號 愛蘭交流道", "Freeway 6 Ailan Interchange", "국도6호 아이란 IC"), T("南投縣埔里鎮 國道六號愛蘭交流道"), 23.9770, 120.9280),
                  desc=T("導航請設「大學路470號」（管理學院）。交流道到校門約 10 分鐘。", "Navigate to “大學路470號” (College of Management). About 10 min from the exit to the gate.", "내비는 ‘大學路470號’(경영대학)로 설정. IC에서 정문까지 약 10분."),
                  steps=[T("國道 1／3 號 → 霧峰系統交流道 轉國道 6 號 → 愛蘭交流道（約 29K）下",
                           "Freeway 1 or 3 → Wufeng System Interchange onto Freeway 6 → exit Ailan (≈ km 29)",
                           "국도 1·3호 → 우펑 시스템 IC에서 국도 6호선 → 아이란 IC(약 29K) 진출"),
                         T("左轉台 14 線往日月潭 → 過牛耳藝術渡假村後右轉台 21 線 → 大學路進校門",
                           "Left onto Hwy 14 toward Sun Moon Lake → past Niu-Er Art Resort turn right onto Hwy 21 → Daxue Rd to the main gate",
                           "성도 14호선 좌회전(일월담 방향) → 니우얼 아트리조트 지나 성도 21호선 우회전 → 대학로 정문"),
                         T("請勿在牛耳之前右轉投 77 鄉道（路窄無法會車，Google 常優先規劃）",
                           "Do NOT turn right onto County Rd 77 before Niu-Er (too narrow; Google often suggests it)",
                           "니우얼 전에 투77 향도로 우회전 금지 (도로가 매우 좁음, 구글맵이 자주 추천함)"),
                         T("校內停車：車牌辨識，30 分鐘內免費，之後每小時 NT$20、單次上限 NT$100",
                           "Campus parking: plate recognition, first 30 min free, then NT$20/h, NT$100 cap",
                           "교내 주차: 번호판 인식, 30분 무료, 이후 시간당 NT$20, 1회 최대 NT$100")],
                  tag=T("開車", "Car", "자동차"), modes=["driving"], dest=NCNU_MGMT, km=6.0, drive_min=10),
            route(T("從埔里轉運站到校園", "From Puli Bus Terminal to campus", "푸리 버스터미널에서 캠퍼스로"), frm=PULI_TERM,
                  desc=T("約 10 分鐘。南投客運市區公車「1 路區間車」埔里⇄暨南大學，約每 30 分鐘一班，NT$25–30。",
                         "About 10 min. Nantou Bus local route 1 (short-turn) Puli ⇄ NCNU every ~30 min, NT$25–30.",
                         "약 10분. 난터우버스 시내 1번 구간차 푸리⇄지난대, 약 30분 간격, NT$25~30."),
                  steps=[T("亦可搭 6670 或 6668（埔里→日月潭）在「暨南大學」站下車", "Or take 6670 / 6668 (Puli → Sun Moon Lake) and alight at “暨南大學”", "6670 또는 6668(푸리→일월담) 탑승 후 ‘暨南大學’ 하차도 가능")],
                  modes=["transit", "driving"], dest=NCNU_BUSSTOP, km=6, drive_min=10),
            info([
                (T("系辦公室", "Department office", "학과 사무실"), T("管理學院 338 室", "College of Management, Room 338", "경영대학(관리학원) 338호"), None),
                (T("電話", "Phone", "전화"), T("049-291-0960 #3723（觀光組）／#3721（餐旅組）", "+886-49-291-0960 ext. 3723 (Tourism) / 3721 (Hospitality)", "+886-49-291-0960 내선 3723 (관광) / 3721 (호텔)"), "tel:+886492910960"),
                (T("Email", "Email", "이메일"), T("tourism@ncnu.edu.tw"), "mailto:tourism@ncnu.edu.tw"),
                (T("網站", "Website", "홈페이지"), T("www.tourism.ncnu.edu.tw"), "https://www.tourism.ncnu.edu.tw/"),
            ]),
        ]),
        section(T("周邊景點", "Nearby sights", "주변 명소"), [
            poi(T("紙教堂（新故鄉見學園區）", "Paper Dome (Taomi Eco-Village)", "종이 교회 (타오미 생태마을)"), T("南投縣埔里鎮桃米里桃米巷52-12號"),
                T("來自神戶的 921 重建紀念紙管教堂，坐落桃米生態村荷花池畔。", "Paper-tube church from Kobe, a 921-quake memorial beside Taomi's lotus pond.", "고베에서 옮겨온 종이 교회. 타오미 생태마을 연꽃 연못 옆 921 지진 기념지."),
                23.9257, 120.9316, tag=T("生態", "Eco", "생태"), hours=T("09:30–17:00（週三休）· 入園 NT$70", "09:30–17:00 (closed Wed) · NT$70", "09:30–17:00 (수요일 휴관) · NT$70"), origin=_oN, walk=False, drive_min=9),
            poi(T("埔里酒廠", "Puli Winery", "푸리 주조장"), T("南投縣埔里鎮中山路三段219號"),
                T("紹興酒故鄉，免門票參觀酒甕隧道、酒文化館與伴手禮。", "Home of Shaoxing wine; free entry to the wine-jar tunnel, museum and gift shop.", "사오싱주의 고향. 술항아리 터널·주류문화관 무료 관람과 기념품."),
                23.9697, 120.9650, tag=T("觀光工廠", "Factory tour", "관광공장"), hours=T("09:00–17:00（假日至 17:30）", "09:00–17:00 (to 17:30 on holidays)", "09:00–17:00 (휴일 17:30까지)"), origin=_oN, walk=False, drive_min=13),
            poi(T("18度C巧克力工房", "Feeling 18 Chocolate", "18도C 초콜릿 공방"), T("南投縣埔里鎮慈恩街20號"),
                T("埔里人氣巧克力與義式冰淇淋名店，免門票順遊。", "Puli's popular chocolate and gelato shop; free to visit.", "푸리 인기 초콜릿·젤라토 매장. 무료 입장."),
                23.9668, 120.9688, tag=T("甜點", "Dessert", "디저트"), hours=T("10:00–18:00（假日至 19:00）", "10:00–18:00 (to 19:00 on holidays)", "10:00–18:00 (휴일 19:00까지)"), origin=_oN, walk=False, drive_min=13),
            poi(T("廣興紙寮", "Guangxing Paper Mill", "광싱 종이공방"), T("南投縣埔里鎮鐵山路310號"),
                T("台灣第一家手工造紙觀光工廠，免費導覽與造紙、拓印 DIY。", "Taiwan's first handmade-paper tourist factory with free tours and DIY.", "타이완 최초 수제 종이 관광공장. 무료 가이드와 종이 만들기 체험."),
                23.9808, 120.9520, tag=T("文化", "Culture", "문화"), hours=T("09:00–17:00"), origin=_oN, walk=False, drive_min=16),
            poi(T("中台禪寺", "Chung Tai Chan Monastery", "중타이찬쓰"), T("南投縣埔里鎮中台路2號"),
                T("李祖原設計的宏偉現代佛寺，園區免費，附設中台世界博物館。", "Monumental modern Buddhist monastery by C.Y. Lee; free grounds, museum ticketed.", "리쭈위안 설계의 웅장한 현대 불교 사원. 경내 무료, 박물관 유료."),
                24.0028, 120.9435, tag=T("寺院", "Temple", "사원"), hours=T("08:00–17:30（11–2 月至 17:00）", "08:00–17:30 (to 17:00 Nov–Feb)", "08:00–17:30 (11~2월 17:00까지)"), origin=_oN, walk=False, drive_min=22),
            poi(T("日月潭（向山遊客中心）", "Sun Moon Lake (Xiangshan Visitor Center)", "일월담 (샹산 방문자센터)"), T("南投縣魚池鄉中山路599號"),
                T("台灣最大高山湖泊，清水模遊客中心可眺望湖景、租自行車環湖。", "Taiwan's largest alpine lake; lakeside visitor center, cycling and boat cruises.", "타이완 최대 산정호수. 호숫가 방문자센터와 자전거·유람선 코스."),
                23.8523, 120.8967, tag=T("湖景", "Lake", "호수"), hours=T("遊客中心 09:00–17:00", "Visitor center 09:00–17:00", "방문자센터 09:00–17:00"), origin=_oN, walk=False, drive_min=28),
        ]),
    ],
    "footer": T("公車班次與票價以南投客運／台灣好行公告為準。", "Bus times and fares per Nantou Bus / Taiwan Tourist Shuttle notices.", "버스 시간표·요금은 난터우버스/타이완 하오싱 공지를 우선합니다."),
}

# ---------------------------------------------------------------- write
def main():
    out = {"generated_by": "data3.py", "langs": ["zh", "en", "ko"], "pages": PAGES}
    here = os.path.dirname(os.path.abspath(__file__))
    dst = os.path.join(here, "dist", "data.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("wrote", dst, os.path.getsize(dst), "bytes;", ", ".join(PAGES))

if __name__ == "__main__":
    main()

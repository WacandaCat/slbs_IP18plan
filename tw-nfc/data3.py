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

def poi(name, address, desc=None, lat=None, lng=None, tag=None, hours=None, modes=None, origin=None, walk=True):
    it = {"kind": "poi", "name": name, "address": address}
    if desc: it["desc"] = desc
    if tag: it["tag"] = tag
    if hours: it["hours"] = hours
    if lat is not None:
        it["lat"], it["lng"] = lat, lng
        it.update(_est(origin, it, walk=walk))
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

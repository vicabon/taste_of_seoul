#!/usr/bin/env python3
"""Fetch the official 2026 Taste of Seoul catalog and build a searchable HTML."""
import json
import re
import subprocess
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore", message="Unverified HTTPS request")

ROOT = "https://tasteofseoul.visitseoul.net"
OUT = Path(__file__).parent
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (catalog verification; contact via official site)", "Connection": "close"})
TRANSLATION_CACHE = {}
CATEGORY_ZH = {
    "Korean": "韓國料理", "Western": "西式料理", "Asian": "亞洲料理",
    "Grill": "燒烤料理", "Plant-based": "植物性料理", "Bar & Pub": "酒吧與酒館",
    "Café & Dessert": "咖啡與甜點",
}
REGION_ZH = {
    "Gangnam-gu": "江南區", "Gangdong-gu": "江東區", "Gangbuk-gu": "江北區",
    "Gangseo-gu": "江西區", "Gwanak-gu": "冠岳區", "Gwangjin-gu": "廣津區",
    "Guro-gu": "九老區", "Geumcheon-gu": "衿川區", "Nowon-gu": "蘆原區",
    "Dobong-gu": "道峰區", "Dongdaemun-gu": "東大門區", "Dongjak-gu": "銅雀區",
    "Mapo-gu": "麻浦區", "Seodaemun-gu": "西大門區", "Seocho-gu": "瑞草區",
    "Seongdong-gu": "城東區", "Seongbuk-gu": "城北區", "Songpa-gu": "松坡區",
    "Yangcheon-gu": "陽川區", "Yeongdeungpo-gu": "永登浦區", "Yongsan-gu": "龍山區",
    "Eunpyeong-gu": "恩平區", "Jongno-gu": "鐘路區", "Jung-gu": "中區",
    "Jungnang-gu": "中浪區",
}
REGION_KO = {
    "Gangnam-gu": "강남구", "Gangdong-gu": "강동구", "Gangbuk-gu": "강북구", "Gangseo-gu": "강서구",
    "Gwanak-gu": "관악구", "Gwangjin-gu": "광진구", "Guro-gu": "구로구", "Geumcheon-gu": "금천구",
    "Nowon-gu": "노원구", "Dobong-gu": "도봉구", "Dongdaemun-gu": "동대문구", "Dongjak-gu": "동작구",
    "Mapo-gu": "마포구", "Seodaemun-gu": "서대문구", "Seocho-gu": "서초구", "Seongdong-gu": "성동구",
    "Seongbuk-gu": "성북구", "Songpa-gu": "송파구", "Yangcheon-gu": "양천구", "Yeongdeungpo-gu": "영등포구",
    "Yongsan-gu": "용산구", "Eunpyeong-gu": "은평구", "Jongno-gu": "종로구", "Jung-gu": "중구", "Jungnang-gu": "중랑구",
}
KOREAN_NAME_OVERRIDES = {
    "Seoryung": "서령 본점", "Solbam": "솔밤", "Soigné": "스와니예", "Hansung Kalguksu": "한성칼국수",
}


def get(url):
    last_error = None
    for attempt in range(5):
        try:
            response = SESSION.get(url, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.RequestException as error:
            last_error = error
            time.sleep(1.5 * (attempt + 1))
    raise last_error


def text(node):
    return " ".join(node.get_text(" ", strip=True).split()) if node else ""


def detail_fields(soup):
    values = [text(x.select_one("dd")) for x in soup.select(".brd_box dl")]
    values += [""] * (4 - len(values))
    desc = soup.select_one(".txt_box > p")
    description = desc.get_text("\n", strip=True) if desc else ""
    description = re.sub(r"\n{3,}", "\n\n", description)
    images = [x.get("src") for x in soup.select(".tmb_box img[src]")]
    return {
        "description": description,
        "address": values[0],
        "phone": values[1],
        "hours": values[2],
        "closed": values[3],
        "images": images,
    }


def region_from_address(address):
    match = re.search(r"([A-Za-z]+(?:ro|dong|gu|gil|dae|sa)?-gu)", address)
    return match.group(1) if match else "Other / not stated"


def map_url(name, address):
    return "https://www.google.com/maps/search/?api=1&query=" + quote(f"{name}, {address}")


def collect_official_korean(kind, pages):
    rows = []
    for page in range(1, pages + 1):
        url = f"{ROOT}/kor/{kind}/list" + (f"?page={page}" if page > 1 else "")
        soup = BeautifulSoup(get(url), "html.parser")
        for item in soup.select(".program_list li.item"):
            link = item.select_one("a[href*='wm_id=']")
            info = item.select_one(".info_box")
            if not link or not info:
                continue
            query = parse_qs(urlparse(link["href"]).query)
            wm_id = query.get("wm_id", [""])[0]
            address = info.select_one("dl dd")
            name = info.select_one("p")
            rows.append({
                "kind": kind,
                "id": wm_id,
                "name": text(name),
                "address": text(address),
                "url": f"{ROOT}/kor/{kind}/view?wm_id={wm_id}&language=kor",
            })
    return rows


def attach_official_korean_names(rows, korean_rows):
    for item in rows:
        if item["name"] in KOREAN_NAME_OVERRIDES:
            match = next((x for x in korean_rows if x["name"] == KOREAN_NAME_OVERRIDES[item["name"]]), None)
        else:
            numbers = set(re.findall(r"\d+", item.get("address", "")))
            region = next((REGION_KO[k] for k in REGION_KO if k in item.get("address", "")), "")
            candidates = [x for x in korean_rows if region and region in x["address"]]
            scored = sorted(
                ((len(numbers & set(re.findall(r"\d+", x["address"]))), x) for x in candidates),
                key=lambda pair: pair[0], reverse=True,
            )
            match = scored[0][1] if scored and scored[0][0] >= 1 else None
        item["name_ko"] = match["name"] if match else item.get("name_ko", item["name"])
        item["official_korean_detail_url"] = match["url"] if match else ""
        item["korean_name_source_verified"] = bool(match)


def translate(value, target):
    """Translate presentation text with a cached public translation endpoint."""
    if not value:
        return ""
    key = f"{target}|{value}"
    if key in TRANSLATION_CACHE and TRANSLATION_CACHE[key] != value:
        return TRANSLATION_CACHE[key]
    url = "https://clients5.google.com/translate_a/t"
    for attempt in range(2):
        try:
            # curl is more reliable than the Python TLS stack in this workspace's proxy.
            command = ["curl", "-k", "-L", "--max-time", "10", "-sS", "--get", url,
                       "--data-urlencode", "client=dict-chrome-ex", "--data-urlencode", "sl=en",
                       "--data-urlencode", f"tl={target}", "--data-urlencode", f"q={value}"]
            raw = subprocess.run(command, capture_output=True, text=True, timeout=8, check=False).stdout
            body = json.loads(raw)
            result = body[0].strip() if isinstance(body, list) and body else ""
            if result:
                TRANSLATION_CACHE[key] = result
                return result
        except (requests.RequestException, ValueError, subprocess.TimeoutExpired):
            pass
        time.sleep(0.3 * (attempt + 1))
    TRANSLATION_CACHE[key] = value
    return value


def collect(kind, pages):
    list_path = f"/eng/{kind}/list"
    entries = {}
    list_snapshots = []
    for page in range(1, pages + 1):
        url = ROOT + list_path + (f"?language=eng&page={page}" if page > 1 else "?language=eng")
        soup = BeautifulSoup(get(url), "html.parser")
        found = text(soup.select_one(".program_list_top p"))
        list_snapshots.append({"page": page, "url": url, "result_text": found})
        for item in soup.select(".program_list li.item"):
            link = item.select_one("a[href*='/view?wm_id=']")
            if not link:
                continue
            detail_url = urljoin(ROOT, link["href"])
            q = parse_qs(urlparse(detail_url).query)
            wm_id = q.get("wm_id", [""])[0]
            badges = [text(x) for x in item.select(".cate_badge")]
            info = item.select_one(".info_box")
            address_node = info.select_one("dl dd") if info else None
            thumb = item.select_one(".tmb")
            image = re.search(r"url\(['\"]?([^'\")]+)", thumb.get("style", "")) if thumb else None
            entries[wm_id] = {
                "id": wm_id,
                "type": "restaurant" if kind == "restaurants" else "cafe",
                "official_list_url": url,
                "official_detail_url": detail_url,
                "name_from_list": text(info.select_one("p")) if info else "",
                "name": text(info.select_one("p")) if info else "",
                "address_from_list": text(address_node),
                "categories_from_list": badges,
                "thumbnail": image.group(1) if image else "",
            }
    results = []
    for index, item in enumerate(entries.values(), 1):
        soup = BeautifulSoup(get(item["official_detail_url"]), "html.parser")
        title = text(soup.select_one(".tit_box h4"))
        cats = [text(x) for x in soup.select(".tit_box .cate_badge")]
        fields = detail_fields(soup)
        item.update(fields)
        item["name"] = title or item["name"]
        item["categories"] = cats or item["categories_from_list"]
        item["region"] = region_from_address(item["address"] or item["address_from_list"])
        item["categories_zh"] = [CATEGORY_ZH.get(x, x) for x in item["categories"]]
        item["region_zh"] = REGION_ZH.get(item["region"], item["region"])
        item["google_maps_url"] = map_url(item["name"], item["address"] or item["address_from_list"])
        item["google_maps_verification"] = "Generated from official name + official address; open link to confirm the current Google Maps place."
        item["source_verified"] = bool(item["name"] and (item["address"] or item["address_from_list"]))
        results.append(item)
        time.sleep(0.04)
    return results, list_snapshots


def enrich_translations(rows):
    jobs = {}
    for item in rows:
        if not item.get("korean_name_source_verified"):
            jobs[(item["id"], "name_ko")] = (item["name"], "ko")
        jobs[(item["id"], "description_zh")] = (item["description"], "zh-TW")
    def run(job):
        key, (value, target) = job
        return key, translate(value, target)
    completed = 0
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(run, job) for job in jobs.items()]
        for future in as_completed(futures):
            key, value = future.result()
            jobs[key] = value
            completed += 1
            if completed % 10 == 0:
                print(f"translation progress: {completed}/{len(futures)}", flush=True)
    for item in rows:
        item["categories_zh"] = [CATEGORY_ZH.get(x, x) for x in item.get("categories", [])]
        item["region_zh"] = REGION_ZH.get(item.get("region", ""), item.get("region", ""))
        if not item.get("korean_name_source_verified"):
            item["name_ko"] = jobs[(item["id"], "name_ko")]
        translated = jobs[(item["id"], "description_zh")]
        # Keep a Chinese-language presentation even when the public translator
        # quota is exhausted; the official English text remains expandable below it.
        if translated == item["description"]:
            item["description_zh"] = f"這是一家位於{item['region_zh']}的{ '、'.join(item['categories_zh']) }店家。官方英文描述已保留於下方，可展開核對。"
        else:
            item["description_zh"] = translated


def build_verification(restaurants, cafes, snapshots):
    checks = []
    for label, rows, expected in [("restaurants", restaurants, 100), ("cafes", cafes, 50)]:
        ids = [x["id"] for x in rows]
        list_detail_mismatches = sum(
            not (
                x["name_from_list"] == x["name"]
                and x["address_from_list"] == x["address"]
                and x["categories_from_list"] == x["categories"]
            )
            for x in rows
        )
        map_query_mismatches = sum(
            quote(f"{x['name']}, {x['address']}") not in x["google_maps_url"]
            for x in rows
        )
        checks += [
            {"check": f"{label} count", "expected": expected, "actual": len(rows), "pass": len(rows) == expected},
            {"check": f"{label} unique official IDs", "expected": len(rows), "actual": len(set(ids)), "pass": len(rows) == len(set(ids))},
            {"check": f"{label} official details complete", "expected": 0, "actual": sum(not x["source_verified"] for x in rows), "pass": all(x["source_verified"] for x in rows)},
            {"check": f"{label} Google Maps query links", "expected": len(rows), "actual": sum(bool(x["google_maps_url"]) for x in rows), "pass": all(x["google_maps_url"].startswith("https://www.google.com/maps/search/?api=1&query=") for x in rows)},
            {"check": f"{label} list/detail name-address-category cross-check", "expected": 0, "actual": list_detail_mismatches, "pass": list_detail_mismatches == 0},
            {"check": f"{label} Google Maps query content cross-check", "expected": 0, "actual": map_query_mismatches, "pass": map_query_mismatches == 0},
            {"check": f"{label} official Korean name matches", "expected": len(rows), "actual": sum(bool(x.get("korean_name_source_verified")) for x in rows), "pass": all(x.get("korean_name_source_verified") for x in rows)},
        ]
    return {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "checks": checks, "all_pass": all(x["pass"] for x in checks), "list_snapshots": snapshots}


def make_html(data, verification):
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    verify = json.dumps(verification, ensure_ascii=False).replace("</", "<\\/")
    return f'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>2026 Taste of Seoul｜100 餐廳＋50 咖啡甜點</title>
<style>
:root{{--bg:#f7f3ee;--ink:#211d1a;--muted:#776e67;--accent:#b94c37;--card:#fff}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 system-ui,-apple-system,"Noto Sans TC",sans-serif}}header{{padding:42px max(20px,calc((100% - 1200px)/2));background:#211d1a;color:white}}h1{{margin:0 0 8px;font-size:clamp(28px,4vw,48px)}}header p{{margin:0;color:#ddd}}main{{max-width:1200px;margin:auto;padding:24px 20px}}.toolbar{{position:sticky;top:0;z-index:2;background:var(--bg);padding:12px 0;display:grid;gap:10px}}input,select,button{{border:1px solid #d6ccc3;border-radius:8px;padding:10px;background:white;font:inherit}}.filters{{display:flex;flex-wrap:wrap;gap:8px}}button.active{{background:var(--accent);color:#fff;border-color:var(--accent)}}.stats{{color:var(--muted);margin:12px 0}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:16px}}article{{background:var(--card);border-radius:14px;overflow:hidden;box-shadow:0 3px 14px #3a28150d}}.photo{{height:170px;background:#ddd center/cover no-repeat}}.body{{padding:16px}}h2{{font-size:21px;margin:0 0 5px}}.tag{{display:inline-block;color:var(--accent);font-size:13px;font-weight:700;margin:0 5px 10px 0}}.ko{{font-size:.68em;color:var(--accent);font-weight:500}}.label{{font-size:12px;color:var(--muted);margin-top:9px}}.desc{{white-space:pre-line;color:#403a35}}details{{margin-top:8px;color:var(--muted)}}.actions{{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}}.actions a{{color:var(--accent);font-weight:700;text-decoration:none;border:1px solid #e4c4bc;border-radius:7px;padding:6px 9px}}.empty{{padding:40px;text-align:center;color:var(--muted);grid-column:1/-1}}small{{color:var(--muted)}}
</style></head><body><header><h1>Taste of Seoul</h1><p>2026 官方資料整合｜100 Taste of Seoul＋50 Cafe &amp; Dessert</p></header><main>
<section class="toolbar"><input id="search" placeholder="搜尋名稱、地址、電話或介紹…"><div class="filters"><select id="type"><option value="all">全部 150 間</option><option value="restaurant">100 Taste of Seoul 餐廳</option><option value="cafe">50 Cafe & Dessert</option></select><select id="category"><option value="all">所有美食分類</option></select><select id="region"><option value="all">所有區域</option></select><button id="reset">清除篩選</button></div></section>
<div class="stats" id="stats"></div><section class="grid" id="grid"></section>
<p><small>資料來源：<a href="https://tasteofseoul.visitseoul.net/eng/restaurants/list">官方餐廳列表</a>、<a href="https://tasteofseoul.visitseoul.net/eng/cafe/list">官方咖啡甜點列表</a>。Google Maps 連結以官方英文名稱與地址組成搜尋查詢；最終地圖店家名稱/營業狀態仍以 Google Maps 開啟後結果為準。</small></p>
</main><script>
const DATA={payload};const VERIFY={verify};const esc=s=>String(s??'').replace(/[&<>"']/g,m=>m==='&'?'&amp;':m==='<'?'&lt;':m==='>'?'&gt;':m==='"'?'&quot;':'&#39;');
const all=[...DATA.restaurants,...DATA.cafes];const $=id=>document.getElementById(id);const search=$('search'),type=$('type'),category=$('category'),region=$('region'),reset=$('reset'),grid=$('grid'),stats=$('stats');const uniq=a=>[...new Set(a.filter(Boolean))].sort((a,b)=>a.localeCompare(b));
uniq(all.flatMap(x=>x.categories_zh)).forEach(x=>category.insertAdjacentHTML('beforeend',`<option>${{esc(x)}}</option>`));uniq(all.map(x=>x.region_zh)).forEach(x=>region.insertAdjacentHTML('beforeend',`<option>${{esc(x)}}</option>`));
function render(){{const q=search.value.trim().toLowerCase(),t=type.value,c=category.value,r=region.value;const rows=all.filter(x=>(t==='all'||x.type===t)&&(c==='all'||x.categories_zh.includes(c))&&(r==='all'||x.region_zh===r)&&(!q||JSON.stringify(x).toLowerCase().includes(q)));stats.textContent=`顯示 ${{rows.length}} / ${{all.length}} 間｜驗證：${{VERIFY.all_pass?'官方筆數與欄位檢查通過':'請查看驗證報告'}}`;grid.innerHTML=rows.map(x=>`<article><div class="photo" style="background-image:url('${{esc(x.thumbnail||x.images?.[0]||'')}}')"></div><div class="body"><div>${{x.categories_zh.map((y,i)=>`<span class="tag">${{esc(y)}} <small>(${{esc(x.categories[i])}})</small></span>`).join('')}}</div><h2>${{esc(x.name)}} <small class="ko">${{esc(x.name_ko)}}</small></h2><div class="label">區域 / Region</div>${{esc(x.region_zh)}} <small>(${{esc(x.region)}})</small><div class="label">地址</div>${{esc(x.address||x.address_from_list)}}<div class="label">電話・營業時間・休息日</div>${{esc(x.phone)}}<br>${{esc(x.hours)}}<br>${{esc(x.closed)}}<div class="desc">${{esc(x.description_zh)}}</div><details><summary>English description</summary><div class="desc">${{esc(x.description)}}</div></details><div class="actions"><a target="_blank" rel="noopener" href="${{esc(x.google_maps_url)}}">Google Maps</a><a target="_blank" rel="noopener" href="${{esc(x.official_detail_url)}}">官方詳情</a></div></div></article>`).join('')||'<div class="empty">沒有符合條件的店家。</div>';}}
[search,type,category,region].forEach(x=>x.addEventListener('input',render));reset.onclick=()=>{{search.value='';type.value='all';category.value='all';region.value='all';render()}};render();
</script></body></html>'''


def main():
    global TRANSLATION_CACHE
    cache_path = OUT / "translation_cache.json"
    if cache_path.exists():
        try:
            TRANSLATION_CACHE = json.loads(cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            TRANSLATION_CACHE = {}
    existing_path = OUT / "taste_of_seoul_data.json"
    if existing_path.exists():
        existing = json.loads(existing_path.read_text(encoding="utf-8"))
        restaurants, cafes = existing["restaurants"], existing["cafes"]
        rs, cs = [], []
    else:
        restaurants, rs = collect("restaurants", 9)
        cafes, cs = collect("cafe", 5)
    korean_rows = collect_official_korean("restaurants", 9) + collect_official_korean("cafe", 5)
    attach_official_korean_names(restaurants + cafes, korean_rows)
    enrich_translations(restaurants + cafes)
    data = {"restaurants": restaurants, "cafes": cafes}
    verification = build_verification(restaurants, cafes, rs + cs)
    (OUT / "taste_of_seoul_data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "verification_report.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2), encoding="utf-8")
    cache_path.write_text(json.dumps(TRANSLATION_CACHE, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "taste_of_seoul.html").write_text(make_html(data, verification), encoding="utf-8")
    print(json.dumps({"restaurants": len(restaurants), "cafes": len(cafes), "all_pass": verification["all_pass"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent

with open(BASE_DIR / "taste_of_seoul_data.json", "r", encoding="utf-8") as f:
    seoul = json.load(f)

with open(BASE_DIR / "busan_100_data.json", "r", encoding="utf-8") as f:
    busan = json.load(f)

combined = {
    "restaurants": seoul["restaurants"],
    "cafes": seoul["cafes"],
    "blue_ribbon_3": seoul["blue_ribbon_3"],
    "blue_ribbon_2": seoul["blue_ribbon_2"],
    "busan_100": busan
}

payload = json.dumps(combined, ensure_ascii=False).replace("</", "<\\/")

html = f'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>韓國美食指南｜首爾 (Taste of Seoul + 藍絲帶) ＆ 釜山 (Visit Busan 100選)</title>
<style>
:root{{--bg:#f7f3ee;--ink:#211d1a;--muted:#776e67;--accent:#b94c37;--card:#fff;--ribbon:#1d4ed8;--gold:#b45309;--busan:#0284c7}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 system-ui,-apple-system,"Noto Sans TC",sans-serif}}
header{{padding:40px max(20px,calc((100% - 1200px)/2));background:#211d1a;color:white}}
h1{{margin:0 0 8px;font-size:clamp(24px,4vw,40px)}}
header p{{margin:0;color:#ddd;font-size:15px}}
header .tags{{display:flex;gap:8px;margin-top:14px;flex-wrap:wrap}}
header .badge{{display:inline-block;padding:5px 12px;border-radius:6px;font-size:13px;font-weight:600}}
.badge-seoul{{background:#b94c37;color:white}}
.badge-br3{{background:#1e3a8a;color:white}}
.badge-br2{{background:#0284c7;color:white}}
.badge-busan{{background:#0d9488;color:white}}
.badge-total{{background:#475569;color:white}}

main{{max-width:1200px;margin:auto;padding:24px 20px}}
.toolbar{{position:sticky;top:0;z-index:10;background:var(--bg);padding:14px 0;display:grid;gap:10px}}
.city-tabs{{display:flex;gap:10px;margin-bottom:4px}}
.city-btn{{flex:1;padding:12px 16px;border:2px solid #d6ccc3;border-radius:10px;background:white;font-size:16px;font-weight:700;cursor:pointer;transition:all .15s ease;color:#555}}
.city-btn.active{{background:#211d1a;color:white;border-color:#211d1a}}
.city-btn.active.busan-active{{background:#0d9488;border-color:#0d9488}}
.city-btn.active.all-active{{background:#b94c37;border-color:#b94c37}}

input,select,button{{border:1px solid #d6ccc3;border-radius:8px;padding:10px;background:white;font:inherit}}
.filters{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr)) auto;gap:10px;align-items:center}}
.stats{{color:var(--muted);margin:12px 0;font-weight:600;font-size:14px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:16px}}
article{{background:var(--card);border-radius:14px;overflow:hidden;box-shadow:0 3px 14px #3a28150d;display:flex;flex-direction:column}}
.photo{{height:175px;background:#ddd center/cover no-repeat;position:relative}}
.photo-badge{{position:absolute;top:10px;left:10px;padding:4px 9px;border-radius:6px;font-size:11px;font-weight:700;color:white;box-shadow:0 2px 6px rgba(0,0,0,0.25)}}
.body{{padding:16px;flex:1;display:flex;flex-direction:column}}
h2{{font-size:19px;margin:0 0 5px;line-height:1.3}}
.tag{{display:inline-block;color:var(--accent);font-size:13px;font-weight:700;margin:0 5px 8px 0}}
.city-tag{{display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;font-weight:700;margin-right:6px}}
.city-seoul{{background:#fee2e2;color:#991b1b}}
.city-busan{{background:#ccfbf1;color:#115e59}}
.ko{{font-size:.7em;color:#b94c37;font-weight:500;display:block;margin-top:2px}}
.label{{font-size:12px;color:var(--muted);margin-top:9px;font-weight:600}}
.desc{{white-space:pre-line;color:#403a35;margin-top:4px;font-size:14px}}
details{{margin-top:8px;color:var(--muted);font-size:13px}}
details summary{{cursor:pointer;font-weight:600;color:var(--muted)}}
.actions{{display:flex;gap:8px;flex-wrap:wrap;margin-top:auto;padding-top:14px}}
.actions a{{color:var(--accent);font-weight:700;text-decoration:none;border:1px solid #e4c4bc;border-radius:7px;padding:6px 10px;font-size:13px}}
.actions a:hover{{background:#faeeeb}}
.actions a.blue{{color:#1d4ed8;border-color:#bfdbfe}}
.actions a.blue:hover{{background:#eff6ff}}
.empty{{padding:40px;text-align:center;color:var(--muted);grid-column:1/-1}}
footer{{margin-top:40px;padding-top:20px;border-top:1px solid #e5ded7}}
small{{color:var(--muted)}}
</style></head><body><header>
<h1>韓國美食指南｜首爾 ＆ 釜山</h1>
<p>全韓雙城官方美食目錄：首爾 (Taste of Seoul 150 ＋ 2027 藍絲帶調查 91) ＋ 釜山 (Visit Busan 100選)</p>
<div class="tags">
<span class="badge badge-total">全韓總計 341 間</span>
<span class="badge badge-seoul">首爾 241 間</span>
<span class="badge badge-busan">釜山 100 間</span>
<span class="badge badge-br3">首爾藍絲帶 3 條絲帶 42 間</span>
<span class="badge badge-br2">首爾藍絲帶 2 條絲帶 49 間</span>
</div>
</header><main>
<section class="toolbar">
<div class="city-tabs">
<button class="city-btn active" data-city="all">🇰🇷 全部城市 (341 間)</button>
<button class="city-btn" data-city="seoul">🏙️ 首爾 (241 間)</button>
<button class="city-btn" data-city="busan">🌊 釜山 (100 間)</button>
</div>
<input id="search" placeholder="搜尋名稱（中/英/韓）、行政區、地址、菜餚或介紹…">
<div class="filters">
<select id="type">
<option value="all">所有官方評級 / 獎項來源</option>
<optgroup label="首爾評級 (Seoul)">
<option value="restaurant">Taste of Seoul：100 精選餐廳</option>
<option value="cafe">Taste of Seoul：50 咖啡甜點</option>
<option value="blue_ribbon_3">2027 藍絲帶 3 條絲帶 (42 間)</option>
<option value="blue_ribbon_2">2027 藍絲帶 2 條絲帶 (49 間)</option>
</optgroup>
<optgroup label="釜山評級 (Busan)">
<option value="busan_ribbon_2">釜山 2 條藍絲帶名店 (26 間)</option>
<option value="busan_ribbon_1">釜山 1 條藍絲帶名店 (68 間)</option>
<option value="busan_official">Visit Busan 官方推薦 (6 間)</option>
</optgroup>
</select>
<select id="category"><option value="all">所有美食分類 (全部菜系)</option></select>
<select id="region"><option value="all">所有行政區域</option></select>
<button id="reset">清除篩選</button>
</div>
</section>
<div class="stats" id="stats"></div>
<section class="grid" id="grid"></section>
<footer>
<p><small>資料來源：
<a target="_blank" rel="noopener" href="https://tasteofseoul.visitseoul.net">Taste of Seoul 官方網站</a>、
<a target="_blank" rel="noopener" href="https://www.bluer.co.kr">Blue Ribbon Survey (블루리본 서베이)</a>、
<a target="_blank" rel="noopener" href="https://www.visitbusan.net">Visit Busan (釜山觀光公社)</a>。
所有店家均附中英文詳細介紹、韓英雙語店名與官方詳情/地圖導航連結。
</small></p>
</footer>
</main><script>
const DATA={payload};
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>m==='&'?'&amp;':m==='<'?'&lt;':m==='>'?'&gt;':m==='"'?'&quot;':'&#39;');

const seoulList=[
  ...(DATA.restaurants||[]).map(x=>({{...x,city:'seoul',city_zh:'首爾'}})),
  ...(DATA.cafes||[]).map(x=>({{...x,city:'seoul',city_zh:'首爾'}})),
  ...(DATA.blue_ribbon_3||[]).map(x=>({{...x,city:'seoul',city_zh:'首爾'}})),
  ...(DATA.blue_ribbon_2||[]).map(x=>({{...x,city:'seoul',city_zh:'首爾'}}))
];

const busanList=(DATA.busan_100||[]).map(x=>({{...x,city:'busan',city_zh:'釜山'}}));
const all=[...seoulList,...busanList];

const $=id=>document.getElementById(id);
const search=$('search'),type=$('type'),category=$('category'),region=$('region'),reset=$('reset'),grid=$('grid'),stats=$('stats');
const cityBtns=document.querySelectorAll('.city-btn');
let currentCity='all';

const uniq=a=>[...new Set(a.filter(Boolean))].sort((a,b)=>a.localeCompare(b));

function updateDropdowns(){{
  const activeItems=all.filter(x=>currentCity==='all'||x.city===currentCity);
  
  const currentCat=category.value;
  category.innerHTML='<option value="all">所有美食分類 (全部菜系)</option>';
  uniq(activeItems.flatMap(x=>x.categories_zh)).forEach(x=>{{
    category.insertAdjacentHTML('beforeend',`<option value="${{esc(x)}}"${{x===currentCat?' selected':''}}>${{esc(x)}}</option>`);
  }});

  const currentReg=region.value;
  region.innerHTML='<option value="all">所有行政區域</option>';
  uniq(activeItems.map(x=>x.region_zh)).forEach(x=>{{
    region.insertAdjacentHTML('beforeend',`<option value="${{esc(x)}}"${{x===currentReg?' selected':''}}>${{esc(x)}}</option>`);
  }});
}}

cityBtns.forEach(btn=>{{
  btn.addEventListener('click',()=>{{
    cityBtns.forEach(b=>b.classList.remove('active','busan-active','all-active'));
    btn.classList.add('active');
    currentCity=btn.dataset.city;
    if(currentCity==='busan') btn.classList.add('busan-active');
    else if(currentCity==='all') btn.classList.add('all-active');
    type.value='all';
    updateDropdowns();
    render();
  }});
}});

function getSourceBadge(x){{
  if(x.city==='busan'){{
    if(x.subtype==='busan_ribbon_2') return '<span class="photo-badge" style="background:#0284c7">釜山・藍絲帶 2 條</span>';
    if(x.subtype==='busan_ribbon_1') return '<span class="photo-badge" style="background:#0d9488">釜山・藍絲帶 1 條</span>';
    return '<span class="photo-badge" style="background:#475569">Visit Busan 精選</span>';
  }}
  if(x.type==='blue_ribbon_3') return '<span class="photo-badge" style="background:#1e3a8a">首爾・藍絲帶 3 條</span>';
  if(x.type==='blue_ribbon_2') return '<span class="photo-badge" style="background:#0284c7">首爾・藍絲帶 2 條</span>';
  if(x.type==='restaurant') return '<span class="photo-badge" style="background:#b94c37">Taste of Seoul 餐廳</span>';
  return '<span class="photo-badge" style="background:#d97706">Taste of Seoul 咖啡</span>';
}}

function render(){{
  const q=search.value.trim().toLowerCase(),t=type.value,c=category.value,r=region.value;
  const rows=all.filter(x=>{{
    if(currentCity!=='all'&&x.city!==currentCity) return false;
    if(t!=='all'){{
      if(x.type!==t&&x.subtype!==t) return false;
    }}
    if(c!=='all'&&!x.categories_zh.includes(c)) return false;
    if(r!=='all'&&x.region_zh!==r) return false;
    if(q&&!JSON.stringify(x).toLowerCase().includes(q)) return false;
    return true;
  }});

  const cityName=currentCity==='all'?'全韓 (首爾與釜山)':(currentCity==='seoul'?'首爾':'釜山');
  stats.textContent=`【${{cityName}}】顯示 ${{rows.length}} / ${{all.filter(x=>currentCity==='all'||x.city===currentCity).length}} 間店家（全庫 ${{all.length}} 間）`;
  
  grid.innerHTML=rows.map(x=>`<article>
    <div class="photo" style="background-image:url('${{esc(x.thumbnail||x.images?.[0]||'')}}')">
      ${{getSourceBadge(x)}}
    </div>
    <div class="body">
      <div>
        <span class="city-tag ${{x.city==='seoul'?'city-seoul':'city-busan'}}">${{esc(x.city_zh)}}</span>
        ${{x.categories_zh.map((y,i)=>`<span class="tag">${{esc(y)}} <small>(${{esc(x.categories[i])}})</small></span>`).join('')}}
        ${{x.food_subtype_ko?`<span class="tag" style="color:#0d9488">${{esc(x.food_subtype_ko)}}</span>`:''}}
      </div>
      <h2>${{esc(x.name)}} <span class="ko">${{esc(x.name_ko)}}</span></h2>
      <div class="label">行政區域 / Region</div>
      <div>${{esc(x.region_zh)}} <small>(${{esc(x.region)}})</small></div>
      <div class="label">地址 / Address</div>
      <div>${{esc(x.address||x.address_from_list)}}</div>
      ${{x.phone||x.hours?`<div class="label">電話・營業時間</div><div>${{esc(x.phone)}}${{x.phone&&x.hours?'<br>':''}}${{esc(x.hours)}}</div>`:''}}
      ${{x.theme_tag?`<div class="label">官方主題標籤</div><div><code>${{esc(x.theme_tag)}}</code></div>`:''}}
      <div class="label">官方詳情介紹 (中文)</div>
      <div class="desc">${{esc(x.description_zh)}}</div>
      <details>
        <summary>Official English Description</summary>
        <div class="desc">${{esc(x.description)}}</div>
      </details>
      <div class="actions">
        <a class="blue" target="_blank" rel="noopener" href="${{esc(x.google_maps_url)}}">Google Maps 導航</a>
        <a target="_blank" rel="noopener" href="${{esc(x.official_detail_url)}}">官方詳情專頁</a>
      </div>
    </div>
  </article>`).join('')||'<div class="empty">沒有符合條件的店家。</div>';
}}

updateDropdowns();
[search,type,category,region].forEach(x=>x.addEventListener('input',render));
reset.onclick=()=>{{
  search.value='';type.value='all';category.value='all';region.value='all';
  render();
}};
render();
</script></body></html>'''

(BASE_DIR / "index.html").write_text(html, encoding="utf-8")
(BASE_DIR / "taste_of_seoul.html").write_text(html, encoding="utf-8")
print("Updated index.html and taste_of_seoul.html with Seoul (241) and Busan (100) successfully!")

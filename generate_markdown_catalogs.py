#!/usr/bin/env python3
import json
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).parent

with open(BASE_DIR / "taste_of_seoul_data.json", "r", encoding="utf-8") as f:
    seoul = json.load(f)

with open(BASE_DIR / "busan_100_data.json", "r", encoding="utf-8") as f:
    busan = json.load(f)

categories_order = [
    "Korean",
    "Grill",
    "Asian",
    "Western",
    "Bar & Pub",
    "Café & Dessert",
    "Plant-based",
]

cat_names_zh = {
    "Korean": "韓國料理 (Korean)",
    "Grill": "燒烤料理 (Grill)",
    "Asian": "亞洲料理 (Asian)",
    "Western": "西式料理 (Western)",
    "Bar & Pub": "酒吧與酒館 (Bar & Pub)",
    "Café & Dessert": "咖啡與甜點 (Café & Dessert)",
    "Plant-based": "蔬食與植物性料理 (Plant-based)",
}

def generate_markdown(city_name_zh, city_name_en, items, output_filename):
    by_cat = defaultdict(list)
    for it in items:
        cat = it.get("categories", ["Other"])[0]
        by_cat[cat].append(it)
    
    md = []
    md.append(f"# 韓國{city_name_zh}美食指南：全分類完整清單 ({city_name_en} Gourmet Guide)\n")
    md.append(f"> 本指南完整收錄 **{city_name_zh}精選共 {len(items)} 間餐廳與咖啡廳**。")
    md.append("> 嚴格依據美食種類、所在行政區域精準分類，包含**韓文/英文店名**、**中英文詳細介紹**、**特色招牌菜單**、**Google Maps 導航連結**與**官方詳情專頁**。\n")
    md.append("---\n")
    
    md.append("## 📌 美食分類快速導覽 (Table of Contents)\n")
    for cat in categories_order:
        if cat in by_cat:
            count = len(by_cat[cat])
            zh_name = cat_names_zh.get(cat, cat)
            anchor = zh_name.lower().replace(" ", "-").replace("(", "").replace(")", "").replace("&", "").replace("/", "")
            md.append(f"- [{zh_name} ({count} 間)](#{anchor})")
    md.append("\n---\n")
    
    for cat in categories_order:
        if cat not in by_cat:
            continue
        cat_items = by_cat[cat]
        zh_title = cat_names_zh.get(cat, cat)
        md.append(f"## {zh_title} (共 {len(cat_items)} 間)\n")
        
        md.append("| 編號 | 店名 (英文 / 韓文) | 評級 / 獎項 | 行政區域 | 料理細項 | 地圖導航 | 官方詳情 |")
        md.append("| :---: | :--- | :--- | :--- | :--- | :---: | :---: |")
        for idx, item in enumerate(cat_items, 1):
            name_en = item.get("name", "")
            name_ko = item.get("name_ko", "")
            award = item.get("award_short") or item.get("award")
            if not award:
                award = "Taste of Seoul 精選" if item.get("type") in ["restaurant", "cafe"] else "官方推薦"
            reg = f"{item.get('region_zh', '')} ({item.get('region', '')})"
            subtype = item.get("food_subtype_ko", "") or item.get("categories_zh", [""])[0]
            gmap = f"[📍 Google Map]({item.get('google_maps_url', '#')})"
            detail = f"[🔗 官方詳情]({item.get('official_detail_url', '#')})"
            md.append(f"| {idx} | **{name_en}**<br>({name_ko}) | {award} | {reg} | {subtype} | {gmap} | {detail} |")
        md.append("\n")
        
        md.append(f"### 📖 {zh_title} 詳細資訊卡片\n")
        for idx, item in enumerate(cat_items, 1):
            name_en = item.get("name", "")
            name_ko = item.get("name_ko", "")
            award = item.get("award") or "官方推薦"
            reg = f"{item.get('region_zh', '')} ({item.get('region', '')})"
            addr_en = item.get("address", "")
            addr_ko = item.get("address_ko", "")
            phone = item.get("phone", "未提供")
            hours = item.get("hours", "未提供")
            gmap = item.get("google_maps_url", "#")
            detail = item.get("official_detail_url", "#")
            desc_zh = item.get("description_zh", "")
            desc_en = item.get("description", "")
            thumb = item.get("thumbnail", "")
            
            md.append(f"#### {idx}. {name_en} ({name_ko})")
            if thumb:
                md.append(f"![{name_en}]({thumb})\n")
            md.append(f"- **評級榮譽**：{award}")
            md.append(f"- **店名**：{name_en} / 韓文：{name_ko}")
            cat_line = f"{item.get('categories_zh', [''])[0]} ({item.get('categories', [''])[0]})"
            if item.get("food_subtype_ko"):
                cat_line += f" - {item.get('food_subtype_ko')}"
            md.append(f"- **料理分類**：{cat_line}")
            md.append(f"- **所在行政區**：{reg}")
            md.append(f"- **地址 (英文)**：{addr_en}")
            if addr_ko:
                md.append(f"- **地址 (韓文)**：`{addr_ko}`")
            md.append(f"- **電話**：{phone}")
            md.append(f"- **營業時間**：{hours}")
            if item.get("theme_tag"):
                md.append(f"- **官方推薦標籤**：`{item.get('theme_tag')}`")
            md.append(f"- **地圖與導航**：[🗺️ 點此開啟 Google Map 查看位置與街景]({gmap})")
            md.append(f"- **官方專頁**：[🔗 點此開啟官方詳細介紹連結]({detail})")
            if desc_zh:
                formatted_zh = desc_zh.replace("\n", "\n  > ")
                md.append(f"- **中文官方介紹**：\n  > {formatted_zh}")
            if desc_en:
                formatted_en = desc_en.replace("\n", "\n  > ")
                md.append(f"- **英文官方介紹**：\n  > {formatted_en}")
            md.append("\n---\n")
        
    out_file = BASE_DIR / output_filename
    out_file.write_text("\n".join(md), encoding="utf-8")
    print(f"Generated {output_filename} with {len(items)} items.")

def main():
    seoul_items = []
    for k in ["restaurants", "cafes", "blue_ribbon_3", "blue_ribbon_2"]:
        for it in seoul[k]:
            it_copy = dict(it)
            it_copy["city"] = "Seoul"
            it_copy["city_zh"] = "首爾"
            seoul_items.append(it_copy)

    # 1. Seoul Markdown
    generate_markdown("首爾", "Seoul", seoul_items, "SEOUL_RESTAURANTS_BY_CATEGORY.md")
    
    # 2. Busan Markdown
    generate_markdown("釜山", "Busan", busan, "BUSAN_RESTAURANTS_BY_CATEGORY.md")
    
    # 3. Combined All Korea Markdown
    all_korea = seoul_items + busan
    generate_markdown("韓國（首爾與釜山）", "Korea (Seoul & Busan)", all_korea, "KOREA_ALL_RESTAURANTS_BY_CATEGORY.md")

if __name__ == "__main__":
    main()

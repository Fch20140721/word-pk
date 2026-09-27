# -*- coding: utf-8 -*-
"""解析51jiaoxi沪教版初中全部6册单词表页面，提取各册Unit 1-8单词"""
import re
import json
import os

DIR = r"C:\Users\andy\Doubao\chats\2026-09-18\new-chat\word_pk\raw"
BOOKS = [("7a", "七年级上册"), ("7b", "七年级下册"), ("8a", "八年级上册"),
         ("8b", "八年级下册"), ("9a", "九年级上册"), ("9b", "九年级下册")]

# 标题形如：沪教牛津版(新)七年级上册英语Unit 1单词表音频、中文翻译表
#          沪教牛津版八年级上册英语Unit 1 Encyclopaedias单词表音频、中文翻译表
UNIT_TITLE = re.compile(r'英语Unit (\d+).*?单词表音频、中文翻译表', re.S)

data = {}
for code, label in BOOKS:
    path = os.path.join(DIR, code + ".html")
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    # 定位各单元标题，按位置切块
    matches = list(UNIT_TITLE.finditer(html))
    book = {}
    for i, m in enumerate(matches):
        unit = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(html)
        seg = html[start:end]
        items = re.findall(r'<p class="en"[^>]*>(.*?)</p>.*?<p class="cn"[^>]*>翻译：(.*?)</p>', seg, re.S)
        book[unit] = []
        for en, cn in items:
            en = re.sub(r'<[^>]+>', '', en).strip()
            en = re.sub(r'\s+', ' ', en).strip()
            cn = cn.strip()
            if en and cn:
                book[unit].append({"en": en, "cn": cn})
    data[code] = book
    total = sum(len(v) for v in book.values())
    print(f"{code} {label}: {len(book)} 单元, {total} 词")

with open(r"C:\Users\andy\Doubao\chats\2026-09-18\new-chat\word_pk\words_all_raw.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)

# 抽查每个册的前3条
for code, _ in BOOKS:
    u = min(data[code])
    print(f"== {code} Unit {u} 抽查 ==")
    for w in data[code][u][:3]:
        print("   ", w)
print("\n已保存 words_all_raw.json")

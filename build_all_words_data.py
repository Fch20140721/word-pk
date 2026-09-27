# -*- coding: utf-8 -*-
"""生成沪教版初中全部6册单词数据模块 words_data.py（含音标）"""
import json
import re

with open(r"C:\Users\andy\Doubao\chats\2026-09-18\new-chat\word_pk\words_all_raw.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

with open(r"C:\Users\andy\Doubao\chats\2026-09-18\new-chat\word_pk\ipa_all_raw.json", "r", encoding="utf-8") as f:
    ipa_map = json.load(f)

BOOK_META = [
    {"code": "7a", "name": "七年级上册"},
    {"code": "7b", "name": "七年级下册"},
    {"code": "8a", "name": "八年级上册"},
    {"code": "8b", "name": "八年级下册"},
    {"code": "9a", "name": "九年级上册"},
    {"code": "9b", "name": "九年级下册"},
]


def clean_cn(cn):
    cn = re.sub(r'\(\s+', '(', cn)
    cn = re.sub(r'\s+\)', ')', cn)
    cn = re.sub(r'\s*[；;]\s*', '；', cn)
    cn = re.sub(r'\s+', ' ', cn).strip()
    cn = re.sub(r'^/', '', cn)
    return cn


def get_ipa(en):
    item = ipa_map.get(en) or ipa_map.get(en.lower()) or ipa_map.get(en.capitalize())
    if not item:
        return ""
    return item.get("uk") or item.get("us") or ""


words = []
for meta in BOOK_META:
    code = meta["code"]
    for u in sorted(raw[code], key=int):
        for w in raw[code][u]:
            en = w["en"].strip()
            if en == "Sandcastle":
                en = "sandcastle"
            cn = clean_cn(w["cn"])
            ipa = get_ipa(en)
            is_phrase = 1 if (' ' in en or "'" in en or '.' in en or '-' in en) else 0
            words.append({"book": code, "unit": int(u), "en": en, "cn": cn,
                          "ipa": ipa, "phrase": is_phrase})

total = len(words)
ipa_total = sum(1 for w in words if w["ipa"])
print(f"总词条数: {total}，有音标: {ipa_total}")
for meta in BOOK_META:
    code = meta["code"]
    n = sum(1 for w in words if w["book"] == code)
    ip = sum(1 for w in words if w["book"] == code and w["ipa"])
    print(f"  {code} {meta['name']}: {n} 词, {ip} 有音标")


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


lines = ['# -*- coding: utf-8 -*-',
         '"""沪教版初中（七~九年级）英语单词表（含音标）—— 自动生成，请勿手动修改"""',
         '',
         '# 册元数据',
         'BOOKS = [']
for meta in BOOK_META:
    lines.append('    {"code": "%s", "name": "%s"},' % (meta["code"], meta["name"]))
lines.append(']')
lines.append('')
lines.append('# 每个词条: {"book": 册代码, "unit": 单元, "en": 英文, "cn": 中文, "ipa": 音标, "phrase": 是否短语}')
lines.append('WORDS = [')
for w in words:
    lines.append('    {"book": "%s", "unit": %d, "en": "%s", "cn": "%s", "ipa": "%s", "phrase": %d},'
                 % (w["book"], w["unit"], esc(w["en"]), esc(w["cn"]), esc(w["ipa"]), w["phrase"]))
lines.append(']')
lines.append('')
lines.append('def get_words(selection=None):')
lines.append('    """按册+单元选择取词条；selection: {"7a": [1,2,...]}；None/空 = 全部"""')
lines.append('    result = []')
lines.append('    if not selection:')
lines.append('        return list(WORDS)')
lines.append('    for w in WORDS:')
lines.append('        units = selection.get(w["book"])')
lines.append('        if units and w["unit"] in units:')
lines.append('            result.append(w)')
lines.append('    return result')
lines.append('')
lines.append('def count_words(selection=None):')
lines.append('    """返回词条总数（可按选择统计）"""')
lines.append('    return len(get_words(selection))')
lines.append('')

with open(r"C:\Users\andy\Doubao\chats\2026-09-18\new-chat\word_pk\words_data.py", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("已生成 words_data.py")

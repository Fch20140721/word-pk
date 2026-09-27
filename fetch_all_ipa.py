# -*- coding: utf-8 -*-
"""批量从有道词典获取沪教版初中全部6册单词音标，生成 ipa_all_raw.json"""
import json
import time
import urllib.parse
import urllib.request

SRC = r"C:\Users\andy\Doubao\chats\2026-09-18\new-chat\word_pk\words_all_raw.json"
OUT = r"C:\Users\andy\Doubao\chats\2026-09-18\new-chat\word_pk\ipa_all_raw.json"

with open(SRC, "r", encoding="utf-8") as f:
    raw = json.load(f)

entries = []
for code in sorted(raw):
    for u in sorted(raw[code], key=int):
        for w in raw[code][u]:
            entries.append({"book": code, "unit": int(u), "en": w["en"].strip(), "cn": w["cn"]})

print(f"总词条: {len(entries)}")


def fetch_ipa(word):
    q = urllib.parse.quote(word)
    url = f"https://dict.youdao.com/jsonapi?q={q}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=12) as r:
        data = json.loads(r.read().decode("utf-8"))
    ws = data.get("ec", {}).get("word", [])
    if not ws:
        return (None, None)
    w = ws[0]
    return (w.get("ukphone"), w.get("usphone"))


results = {}
fail = []
total = len(entries)
for i, e in enumerate(entries):
    en = e["en"]
    uk, us = None, None
    for attempt in range(3):
        try:
            uk, us = fetch_ipa(en)
            break
        except Exception as exc:
            if attempt == 2:
                fail.append((en, str(exc)[:60]))
            else:
                time.sleep(1.0)
    results[en] = {"uk": uk or "", "us": us or ""}
    if (i + 1) % 25 == 0:
        ok = sum(1 for k in results if results[k]["uk"] or results[k]["us"])
        print(f"进度 {i+1}/{total} 成功音标: {ok}", flush=True)
    time.sleep(0.12)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)

ok = sum(1 for k in results if results[k]["uk"] or results[k]["us"])
print(f"完成: {total} 词条, {ok} 个有音标, {total-ok} 个无音标")
if fail:
    print("失败样例:")
    for en, err in fail[:15]:
        print("  ", en, err)

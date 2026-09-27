# -*- coding: utf-8 -*-
"""生成应用图标 icon.ico（蓝色渐变圆角方块 + 白色PK字样）"""
from PIL import Image, ImageDraw, ImageFont
import os

SIZE = 512
img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# 圆角矩形背景：上下渐变（#1E5EFF -> #0A3FD6）
radius = 110
top_color = (46, 106, 255, 255)
bottom_color = (8, 47, 160, 255)
mask = Image.new("L", (SIZE, SIZE), 0)
md = ImageDraw.Draw(mask)
md.rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=radius, fill=255)
for y in range(SIZE):
    t = y / (SIZE - 1)
    r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
    g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
    b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
    d.line([(0, y), (SIZE, y)], fill=(r, g, b, 255))
img.putalpha(mask)

# 白色 "PK" 文字
try:
    font = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 260)
except Exception:
    font = ImageFont.load_default()
txt = "PK"
bbox = d.textbbox((0, 0), txt, font=font)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
tx = (SIZE - tw) / 2 - bbox[0]
ty = (SIZE - th) / 2 - bbox[1] - 20
d.text((tx, ty), txt, font=font, fill=(255, 255, 255, 255))

# 底部小字 "7年级·沪教"
try:
    font2 = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 72)
except Exception:
    font2 = ImageFont.load_default()
txt2 = "沪教·七上"
bbox2 = d.textbbox((0, 0), txt2, font=font2)
tw2, th2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]
tx2 = (SIZE - tw2) / 2 - bbox2[0]
ty2 = SIZE - 120
d.text((tx2, ty2), txt2, font=font2, fill=(255, 255, 255, 235))

out = r"C:\Users\andy\Doubao\chats\2026-09-18\new-chat\word_pk\icon.png"
img.save(out, "PNG")
# 转 .ico（含多尺寸）
ico = r"C:\Users\andy\Doubao\chats\2026-09-18\new-chat\word_pk\icon.ico"
img.save(ico, "ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("图标已生成:", out, ico, os.path.getsize(ico), "bytes")

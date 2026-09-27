# -*- coding: utf-8 -*-
"""
沪教版初中（七~九年级）英语单词PK 对战软件 —— 白色液体玻璃风格
- 模式：双人对战（轮流） / 双窗对战（两个窗口同时） / 人机对战
- 题型：看英选中 / 看中选英 / 单词拼写 / 音标PK / 混合（可自选）
- 词库：沪教版初中全部 6 册（七上/七下/八上/八下/九上/九下）
       共 1556 个单词和短语，多数含国际音标
- 设置：册与单元选择 / 题数 / 每题时限 / 电脑难度
- 依赖：仅 Python 标准库（tkinter）
作者：冯晨航（主菜单署名）
"""

import tkinter as tk
from tkinter import font as tkfont
import random
import subprocess
import sys
import os
import time

from words_data import BOOKS, WORDS, get_words

# ---------------------------------------------------------------------------
# 样式常量 —— 白色液体玻璃
# ---------------------------------------------------------------------------
GLASS_BG1    = "#EAF1FC"   # 背景渐变：顶部淡蓝
GLASS_BG2    = "#F9FBFE"   # 背景渐变：中部近白
GLASS_BG3    = "#EEF3FC"   # 背景渐变：底部淡蓝
CARD_FILL    = "#FFFFFF"   # 玻璃卡片填充
CARD_LINE    = "#E3EAF7"   # 卡片描边
CARD_LINE2   = "#F3F7FF"   # 卡片内描边（高光）
CARD_SHADOW  = "#D8E2F5"   # 卡片阴影
PRIMARY      = "#2F6BFF"
PRIMARY_D    = "#1D4ED8"
GREEN        = "#16A34A"
GREEN_D      = "#15803D"
GREEN_BG     = "#E8F8EF"
RED          = "#F43F5E"
RED_BG       = "#FDF0F2"
ORANGE       = "#F97316"
GOLD         = "#F59E0B"
TEXT         = "#1B2A4A"
TEXT_SUB     = "#64748B"
P1_RED       = "#F43F5E"
P2_BLUE      = "#3B82F6"
AI_PURPLE    = "#8B5CF6"
WHITE        = "#FFFFFF"
P1_CARD      = "#FFF7F8"   # 玩家1 浅粉玻璃
P1_LINE      = "#F9D8DC"
P2_CARD      = "#F5F9FF"   # 玩家2 浅蓝玻璃
P2_LINE      = "#D8E6FA"

SCORE_CHOICE = 10   # 选择题得分
SCORE_SPELL  = 15   # 拼写题得分

DIFF_CONF = {"easy": 0.70, "normal": 0.85, "hard": 1.00}
DIFF_NAME = {"easy": "简单", "normal": "普通", "hard": "困难"}

FEEDBACK_MS = 1200   # 答题反馈停留时间
AI_THINK_MS = 1100   # 电脑"思考"时间


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def lerp(c1, c2, t):
    a, b = hex_rgb(c1), hex_rgb(c2)
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def round_rect(canvas, x1, y1, x2, y2, r, **kw):
    """在 Canvas 上画圆角矩形"""
    r = max(1, min(r, (x2 - x1) // 2, (y2 - y1) // 2))
    pts = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2, x2-r, y2,
           x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


def draw_gradient(cv, w, h, c1=GLASS_BG1, c2=GLASS_BG2, c3=GLASS_BG3, step=2, tag="grad"):
    """垂直三段渐变背景"""
    cv.delete(tag)
    half = h // 2
    for y in range(0, h, step):
        if y < half:
            t = y / max(1, half - 1)
            col = lerp(c1, c2, t)
        else:
            t = (y - half) / max(1, h - half - 1)
            col = lerp(c2, c3, t)
        cv.create_line(0, y, w, y, fill=col, tags=tag)
    cv.tag_lower(tag)


def draw_glass_card(cv, x1, y1, x2, y2, r=24, fill=CARD_FILL, outline=CARD_LINE,
                    shadow=True, tag="card"):
    """玻璃卡片：柔和阴影 + 白圆角主体 + 内侧高光"""
    if shadow:
        round_rect(cv, x1, y1 + 5, x2, y2 + 5, r, fill=CARD_SHADOW, outline="",
                   tags=tag)
        round_rect(cv, x1, y1 + 2, x2, y2 + 2, r, fill="#EEF3FC", outline="",
                   tags=tag)
    body = round_rect(cv, x1, y1, x2, y2, r, fill=fill, outline=outline, width=1,
                      tags=tag)
    # 内侧高光（玻璃反光）
    if y2 - y1 > 60:
        round_rect(cv, x1 + 3, y1 + 3, x2 - 3, y1 + (y2 - y1) // 3, r // 2,
                   fill="", outline=CARD_LINE2, width=1, tags=tag)
    return body


def draw_pill(cv, cx, cy, text, fg, bg, font, tag="fbk", padx=22, pady=12, r=18):
    """反馈气泡：圆角矩形 + 文字（先删除同 tag 旧内容）"""
    cv.delete(tag)
    w = cv.create_text(0, 0, text=text, fill=fg, font=font, tags=tag)
    bb = cv.bbox(w)
    tw = (bb[2] - bb[0]) if bb else 100
    th = (bb[3] - bb[1]) if bb else 30
    round_rect(cv, cx - tw / 2 - padx, cy - th / 2 - pady,
               cx + tw / 2 + padx, cy + th / 2 + pady, r, fill=bg, outline="",
               tags=tag)
    cv.tag_raise(w)
    return w


def speak(text):
    """Windows SAPI 朗读（失败静默）"""
    try:
        t = text.replace("'", "''")
        ps = ("Add-Type -AssemblyName System.Speech; "
              "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
              "$s.Rate = 0; $s.Speak('{0}')".format(t))
        flags = 0x08000000  # CREATE_NO_WINDOW
        subprocess.Popen(["powershell", "-NoProfile", "-NonInteractive",
                          "-Command", ps], creationflags=flags,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 玻璃按钮
# ---------------------------------------------------------------------------
class GlassButton:
    """Canvas 圆角胶囊按钮：hover 变色、可禁用、可换样式"""

    STYLES = {
        "primary": {"fill": "#2F6BFF", "hover": "#1E52E0", "outline": "#2F6BFF", "fg": "#FFFFFF"},
        "white":   {"fill": "#FFFFFF", "hover": "#EAF1FF", "outline": "#D9E4F7", "fg": "#1B2A4A"},
        "green":   {"fill": "#16A34A", "hover": "#15803D", "outline": "#16A34A", "fg": "#FFFFFF"},
        "red":     {"fill": "#F43F5E", "hover": "#E11D48", "outline": "#F43F5E", "fg": "#FFFFFF"},
        "purple":  {"fill": "#8B5CF6", "hover": "#7C3AED", "outline": "#8B5CF6", "fg": "#FFFFFF"},
        "orange":  {"fill": "#F97316", "hover": "#EA580C", "outline": "#F97316", "fg": "#FFFFFF"},
        "gray":    {"fill": "#F1F5FB", "hover": "#E5ECF9", "outline": "#D9E4F7", "fg": "#1B2A4A"},
        "dimred":  {"fill": "#FDE8EC", "hover": "#FBCBD4", "outline": "#F9D8DC", "fg": "#F43F5E"},
        "dimblue": {"fill": "#E9F1FF", "hover": "#CFE0FF", "outline": "#D8E6FA", "fg": "#3B82F6"},
        "dimorange":{"fill": "#FEF0E6", "hover": "#FBDDC5", "outline": "#FBD8BC", "fg": "#F97316"},
        "dimpurple":{"fill": "#F2ECFE", "hover": "#E2D6FC", "outline": "#E2D6FC", "fg": "#8B5CF6"},
    }

    def __init__(self, canvas, x1, y1, x2, y2, text, command=None,
                 style="primary", font=None, radius=None, tag=None):
        self.cv = canvas
        self.command = command
        self.enabled = True
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        self.r = radius or min(22, (y2 - y1) // 2)
        self.font = font
        self.cx, self.cy = (x1 + x2) / 2, (y1 + y2) / 2
        self._text = text
        self.rect = None
        self.label = None
        self.btn_tag = "gb%d" % id(self)
        self.group_tag = tag
        self._set_style(style)
        self._create()
        self._bind()

    def _set_style(self, style):
        self.style = style
        s = self.STYLES.get(style, self.STYLES["primary"])
        self.fill, self.hover_fill = s["fill"], s["hover"]
        self.outline, self.fg = s["outline"], s["fg"]

    def _create(self):
        tg = self.btn_tag if not self.group_tag else (self.btn_tag, self.group_tag)
        self.rect = round_rect(self.cv, self.x1, self.y1, self.x2, self.y2, self.r,
                               fill=self.fill, outline=self.outline, width=1,
                               tags=tg)
        self.label = self.cv.create_text(self.cx, self.cy, text=self._text,
                                         fill=self.fg, font=self.font,
                                         tags=tg)

    def _bind(self):
        self.cv.tag_bind(self.btn_tag, "<Enter>", self._on_enter)
        self.cv.tag_bind(self.btn_tag, "<Leave>", self._on_leave)
        self.cv.tag_bind(self.btn_tag, "<Button-1>", self._on_click)

    def _on_enter(self, e):
        if self.enabled:
            self.cv.itemconfig(self.rect, fill=self.hover_fill)

    def _on_leave(self, e):
        if self.enabled:
            self.cv.itemconfig(self.rect, fill=self.fill)

    def _on_click(self, e):
        if self.enabled and self.command:
            self.command()

    def set_text(self, text):
        self._text = text
        self.cv.itemconfig(self.label, text=text)

    def set_style(self, style):
        self._set_style(style)
        self.cv.itemconfig(self.rect, fill=self.fill, outline=self.outline)
        self.cv.itemconfig(self.label, fill=self.fg)

    def set_enabled(self, en):
        self.enabled = en
        st = "normal" if en else "hidden"
        self.cv.itemconfig(self.rect, state=st)
        self.cv.itemconfig(self.label, state=st)

    def set_visible(self, vis):
        st = "normal" if vis else "hidden"
        self.cv.itemconfig(self.rect, state=st)
        self.cv.itemconfig(self.label, state=st)

    def set_pos(self, x1, y1, x2, y2):
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        self.cx, self.cy = (x1 + x2) / 2, (y1 + y2) / 2
        self.r = min(self.r, (y2 - y1) // 2)
        self.cv.coords(self.rect, *self._pts())
        self.cv.coords(self.label, self.cx, self.cy)

    def _pts(self):
        x1, y1, x2, y2, r = self.x1, self.y1, self.x2, self.y2, self.r
        return [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2, x2-r, y2,
                x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]


# ---------------------------------------------------------------------------
# 出题引擎
# ---------------------------------------------------------------------------
class Question:
    """一道题：词条 + 题型"""
    KIND_EN2CN = "en2cn"    # 看英文选中文
    KIND_CN2EN = "cn2en"    # 看中文选英文
    KIND_SPELL = "spell"    # 看中文拼单词
    KIND_IPA_EN = "ipa_en"  # 看音标选英文
    KIND_EN_IPA = "en_ipa"  # 看英文选音标

    def __init__(self, word, kind):
        self.word = word
        self.kind = kind
        if kind in (Question.KIND_CN2EN, Question.KIND_SPELL, Question.KIND_IPA_EN):
            self.correct = word["en"]
        elif kind == Question.KIND_EN_IPA:
            self.correct = word.get("ipa", "")
        else:
            self.correct = word["cn"]
        self.options = None
        self.stem_text = ""
        self.kind_text = ""

    def build_choices(self, pool):
        if self.kind == Question.KIND_EN2CN:
            correct_txt = self.word["cn"]
            others = [w["cn"] for w in pool if w["cn"] != correct_txt]
            self.stem_text = self.word["en"]
            self.kind_text = "看英文 · 选中文"
        elif self.kind == Question.KIND_CN2EN:
            correct_txt = self.word["en"]
            others = [w["en"] for w in pool if w["en"].lower() != correct_txt.lower()]
            self.stem_text = self.word["cn"]
            self.kind_text = "看中文 · 选英文"
        elif self.kind == Question.KIND_IPA_EN:
            correct_txt = self.word["en"]
            others = [w["en"] for w in pool
                      if not w["phrase"] and w["en"].lower() != correct_txt.lower()]
            self.stem_text = self.word.get("ipa", "")
            self.kind_text = "看音标 · 选单词"
        else:
            correct_txt = self.word.get("ipa", "")
            others = [w["ipa"] for w in pool
                      if not w["phrase"] and w.get("ipa") and w["ipa"] != correct_txt]
            self.stem_text = self.word["en"]
            self.kind_text = "看单词 · 选音标"
        distractors = random.sample(others, min(3, len(others)))
        choices = distractors + [correct_txt]
        random.shuffle(choices)
        self.options = [("A", choices[0], choices[0] == correct_txt),
                        ("B", choices[1], choices[1] == correct_txt),
                        ("C", choices[2], choices[2] == correct_txt),
                        ("D", choices[3], choices[3] == correct_txt)]
        return self.options


def make_questions(pool, total, kind="mix"):
    """生成一局题目；kind: mix/en2cn/cn2en/spell/ipa"""
    if kind == "ipa":
        pool = [w for w in pool if w.get("ipa")]
    if len(pool) < total:
        total = len(pool)
    picked = random.sample(pool, total)
    if kind == "spell":
        single = [w for w in picked if not w["phrase"]]
        if len(single) < total:
            picked = single + [w for w in picked if w["phrase"]][:total - len(single)]
            picked = picked[:total]
    questions = []
    for w in picked:
        if kind == "mix":
            if w["phrase"]:
                k = random.choice([Question.KIND_EN2CN, Question.KIND_CN2EN])
            else:
                k = random.choice([Question.KIND_EN2CN, Question.KIND_CN2EN,
                                   Question.KIND_SPELL,
                                   Question.KIND_EN2CN, Question.KIND_CN2EN])
        elif kind == "en2cn":
            k = Question.KIND_EN2CN
        elif kind == "cn2en":
            k = Question.KIND_CN2EN
        elif kind == "spell":
            k = Question.KIND_SPELL
        elif kind == "ipa":
            k = random.choice([Question.KIND_IPA_EN, Question.KIND_EN_IPA])
        else:
            k = Question.KIND_EN2CN
        q = Question(w, k)
        if k != Question.KIND_SPELL:
            q.build_choices(pool)
        else:
            q.stem_text = w["cn"]
            q.kind_text = "看中文 · 拼单词"
        questions.append(q)
    return questions


# ---------------------------------------------------------------------------
# 主程序
# ---------------------------------------------------------------------------
class WordPKApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("沪教版初中 · 英语单词PK")
        self.geometry("920x760")
        self.resizable(False, False)
        self.configure(bg=GLASS_BG2)
        try:
            self.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass
        self.font_title = tkfont.Font(family="Microsoft YaHei UI", size=30, weight="bold")
        self.font_sub   = tkfont.Font(family="Microsoft YaHei UI", size=13)
        self.font_h2    = tkfont.Font(family="Microsoft YaHei UI", size=18, weight="bold")
        self.font_h3    = tkfont.Font(family="Microsoft YaHei UI", size=14, weight="bold")
        self.font_body  = tkfont.Font(family="Microsoft YaHei UI", size=12)
        self.font_small = tkfont.Font(family="Microsoft YaHei UI", size=10)
        self.font_score = tkfont.Font(family="Microsoft YaHei UI", size=24, weight="bold")
        self.font_q     = tkfont.Font(family="Microsoft YaHei UI", size=28, weight="bold")

        self.settings = {
            "mode": "pvp",
            "selection": {b["code"]: sorted(set(w["unit"] for w in WORDS if w["book"] == b["code"]))
                          for b in BOOKS}, "total": 10,
            "time_limit": 0, "difficulty": "normal", "kind": "mix",
        }
        self.scores = {"p1": 0, "p2": 0}
        self.corrects = {"p1": 0, "p2": 0}
        self.questions = []
        self.q_index = 0
        self.cur_player = 1
        self.cur_q = None
        self.answered = False
        self.timer_after = None
        self.time_left = 0
        self.can_speak = True
        self.result_shown = False
        self.duel_windows = None
        self.splash_after = None
        self.canvas = None

        self.show_splash()

    # ------------------------------------------------------------------ 启动画面
    def show_splash(self):
        self.clear()
        self.configure(bg=GLASS_BG2)
        cv = tk.Canvas(self, highlightthickness=0, bd=0, bg=GLASS_BG2)
        cv.pack(fill="both", expand=True)
        self.canvas = cv
        W, H = 920, 760
        draw_gradient(cv, W, H)
        # 光斑装饰
        cv.create_oval(-120, -100, 420, 240, fill="#DCE8FF", stipple="gray50", outline="")
        cv.create_oval(560, 460, 1100, 940, fill="#E8DFFF", stipple="gray50", outline="")

        ft = tkfont.Font(family="Microsoft YaHei UI", size=46, weight="bold")
        cv.create_text(460, 300, text="英语 单词 PK", fill="#14213D", font=ft)
        cv.create_text(460, 356, text="沪教版初中七至九年级", fill="#5B6B8C",
                       font=self.font_sub)
        cv.create_text(460, 706, text="by Andy 711", fill="#8FA3C7",
                       font=tkfont.Font(family="Microsoft YaHei UI", size=16))
        cv.tag_bind("all", "<Button-1>", lambda e: self._skip_splash())
        self.splash_after = self.after(2000, self.show_menu)

    def _skip_splash(self):
        if self.splash_after:
            try:
                self.after_cancel(self.splash_after)
            except Exception:
                pass
            self.splash_after = None
        self.show_menu()

    # ------------------------------------------------------------------ 工具
    def clear(self):
        if getattr(self, "timer_after", None):
            try:
                self.after_cancel(self.timer_after)
            except Exception:
                pass
            self.timer_after = None
        for w in self.winfo_children():
            w.destroy()
        self.canvas = None

    def _text(self, x, y, text, font=None, fill=TEXT, anchor="center", width=None,
              tag=None):
        return self.canvas.create_text(x, y, text=text, font=font or self.font_body,
                                       fill=fill, anchor=anchor, width=width, tags=tag)

    def _window(self, widget, x, y, anchor="nw", tag=None):
        return self.canvas.create_window(x, y, window=widget, anchor=anchor, tags=tag)

    def _toast(self, msg):
        lbl = tk.Label(self, text=msg, bg="#33415C", fg=WHITE,
                       font=self.font_body, padx=20, pady=9)
        lbl.place(relx=0.5, rely=0.13, anchor="center")
        self.after(1800, lbl.destroy)

    # ------------------------------------------------------------------ 主菜单
    def show_menu(self):
        self.clear()
        self.geometry("920x760")
        cv = tk.Canvas(self, highlightthickness=0, bd=0, bg=GLASS_BG2)
        cv.pack(fill="both", expand=True)
        self.canvas = cv
        W, H = 920, 760
        draw_gradient(cv, W, H)
        cv.create_oval(-90, -80, 380, 240, fill="#DCE8FF", stipple="gray50", outline="")
        cv.create_oval(600, 470, 1120, 930, fill="#E9E0FF", stipple="gray50", outline="")

        # 标题区
        cv.create_text(460, 58, text="英语单词 PK", fill="#14213D",
                       font=tkfont.Font(family="Microsoft YaHei UI", size=26, weight="bold"))
        cv.create_text(460, 94, text="沪教版初中七~九年级 · 单词 / 短语 / 音标",
                       fill="#5B6B8C", font=self.font_small)

        # ---- 左卡片：模式与设置 ----
        draw_glass_card(cv, 36, 126, 430, 700)
        cv.create_text(54, 150, text="游戏模式", fill=TEXT_SUB, font=self.font_small,
                       anchor="w")
        self.btn_pvp = GlassButton(cv, 50, 166, 156, 248, "双人对战", self.set_mode_pvp,
                                   style="dimred", font=self.font_h3)
        cv.create_text(103, 232, text="轮流答题", fill="#F48B9D",
                       font=tkfont.Font(family="Microsoft YaHei UI", size=9),
                       tags="sub1")
        self.btn_duel = GlassButton(cv, 164, 166, 270, 248, "双窗对战", self.set_mode_duel,
                                    style="dimorange", font=self.font_h3)
        cv.create_text(217, 232, text="两窗同时", fill="#F5A97C",
                       font=tkfont.Font(family="Microsoft YaHei UI", size=9), tags="sub1")
        self.btn_pve = GlassButton(cv, 278, 166, 384, 248, "人机对战", self.set_mode_pve,
                                   style="dimpurple", font=self.font_h3)
        cv.create_text(331, 232, text="挑战电脑", fill="#B49BE8",
                       font=tkfont.Font(family="Microsoft YaHei UI", size=9), tags="sub1")

        # 题数
        cv.create_text(54, 272, text="每局题数", fill=TEXT_SUB, font=self.font_small,
                       anchor="w")
        self.num_var = tk.IntVar(value=10)
        nr = tk.Frame(cv, bg=CARD_FILL)
        for n in (10, 20, 30):
            rb = tk.Radiobutton(nr, text=f"{n}题", value=n, variable=self.num_var,
                                bg=CARD_FILL, fg=TEXT, font=self.font_body,
                                selectcolor=CARD_FILL, activebackground=CARD_FILL,
                                highlightthickness=0, bd=0)
            rb.pack(side="left", padx=(0, 14))
        self._window(nr, 50, 290)

        # 时限
        cv.create_text(54, 330, text="每题时限", fill=TEXT_SUB, font=self.font_small,
                       anchor="w")
        self.time_var = tk.IntVar(value=0)
        tr = tk.Frame(cv, bg=CARD_FILL)
        for v, t in ((0, "不限时"), (10, "10秒"), (15, "15秒"), (20, "20秒")):
            rb = tk.Radiobutton(tr, text=t, value=v, variable=self.time_var,
                                bg=CARD_FILL, fg=TEXT, font=self.font_body,
                                selectcolor=CARD_FILL, activebackground=CARD_FILL,
                                highlightthickness=0, bd=0)
            rb.pack(side="left", padx=(0, 12))
        self._window(tr, 50, 348)

        # 题型
        cv.create_text(54, 408, text="题目类型", fill=TEXT_SUB, font=self.font_small,
                       anchor="w")
        self.kind_var = tk.StringVar(value="mix")
        kr1 = tk.Frame(cv, bg=CARD_FILL)
        for key, name in (("mix", "混合"), ("en2cn", "看英选中"), ("cn2en", "看中选英")):
            rb = tk.Radiobutton(kr1, text=name, value=key, variable=self.kind_var,
                                bg=CARD_FILL, fg=TEXT, font=self.font_body,
                                selectcolor=CARD_FILL, activebackground=CARD_FILL,
                                highlightthickness=0, bd=0)
            rb.pack(side="left", padx=(0, 14))
        self._window(kr1, 50, 426)
        kr2 = tk.Frame(cv, bg=CARD_FILL)
        for key, name in (("spell", "单词拼写"), ("ipa", "音标PK")):
            rb = tk.Radiobutton(kr2, text=name, value=key, variable=self.kind_var,
                                bg=CARD_FILL, fg=TEXT, font=self.font_body,
                                selectcolor=CARD_FILL, activebackground=CARD_FILL,
                                highlightthickness=0, bd=0)
            rb.pack(side="left", padx=(0, 14))
        self._window(kr2, 50, 454)

        # 难度（人机模式显示）
        cv.create_text(54, 500, text="电脑难度", fill=TEXT_SUB, font=self.font_small,
                       anchor="w", tags="diff")
        self.diff_var = tk.StringVar(value="normal")
        df = tk.Frame(cv, bg=CARD_FILL)
        for key, name in (("easy", "简单"), ("normal", "普通"), ("hard", "困难")):
            rb = tk.Radiobutton(df, text=name, value=key, variable=self.diff_var,
                                bg=CARD_FILL, fg=TEXT, font=self.font_body,
                                selectcolor=CARD_FILL, activebackground=CARD_FILL,
                                highlightthickness=0, bd=0, command=self._on_diff_change)
            rb.pack(side="left", padx=(0, 14))
        self.diff_win = self._window(df, 50, 518, tag="diff")

        # 开始按钮
        GlassButton(cv, 50, 600, 416, 664, "开始 PK", self.start_game,
                    style="green", font=tkfont.Font(family="Microsoft YaHei UI",
                                                    size=20, weight="bold"))

        # ---- 右卡片：册与单元选择 ----
        draw_glass_card(cv, 446, 126, 884, 700)
        cv.create_text(464, 150, text="选择册（默认全部）", fill=TEXT_SUB,
                       font=self.font_small, anchor="w")
        GlassButton(cv, 706, 138, 776, 166, "全不选", self.select_none_units,
                    style="white", font=self.font_small)
        GlassButton(cv, 784, 138, 866, 166, "全选", self.select_all_units,
                    style="white", font=self.font_small)

        # 册复选框：3列2行
        self.book_vars = {}
        self.book_names = {b["code"]: b["name"] for b in BOOKS}
        book_grid = [("7a", "7b", "8a"), ("8b", "9a", "9b")]
        for row, cols in enumerate(book_grid):
            for col, code in enumerate(cols):
                var = tk.BooleanVar(value=True)
                self.book_vars[code] = var
                cb = tk.Checkbutton(cv, text=self.book_names[code], variable=var,
                                    bg=CARD_FILL, fg=TEXT, font=self.font_body,
                                    selectcolor=CARD_FILL, activebackground=CARD_FILL,
                                    anchor="w", highlightthickness=0, bd=0,
                                    command=lambda c=code: self._on_book_toggle(c))
                self._window(cb, 462 + col * 140, 176 + row * 42)

        # 当前册标题（点击册复选框时切换）
        cv.create_text(464, 268, text="", fill=PRIMARY, font=self.font_body,
                       anchor="w", tags="curbook")

        # 当前册单元复选框（每册独立，切册时显示/隐藏）
        self.unit_vars = {}
        self.unit_wins = {}
        for b in BOOKS:
            code = b["code"]
            units = sorted(set(w["unit"] for w in WORDS if w["book"] == code))
            self.unit_vars[code] = {}
            self.unit_wins[code] = {}
            for i, u in enumerate(units):
                var = tk.BooleanVar(value=True)
                self.unit_vars[code][u] = var
                cnt = sum(1 for w in WORDS if w["book"] == code and w["unit"] == u)
                cb = tk.Checkbutton(cv, text=f"Unit {u}（{cnt}词）",
                                    variable=var, bg=CARD_FILL, fg=TEXT,
                                    font=self.font_body, selectcolor=CARD_FILL,
                                    activebackground=CARD_FILL, anchor="w",
                                    highlightthickness=0, bd=0)
                x = 462 if i % 2 == 0 else 660
                y = 298 + (i // 2) * 52
                wid = self._window(cb, x, y, tag="unit-" + code)
                self.unit_wins[code][u] = wid
        self.cur_book = "7a"
        self._set_cur_book(self.cur_book)
        cv.itemconfig("curbook", text=f"当前册：{self.book_names[self.cur_book]} · 单元（默认全部）")

        cv.create_text(460, 716, text=f"共收录 {len(BOOKS)} 册 · {len(WORDS)} 个单词和短语",
                       fill="#8FA3C7", font=self.font_small)
        cv.create_text(460, 740, text="作者：冯晨航", fill="#7C8FB3",
                       font=tkfont.Font(family="Microsoft YaHei UI", size=9))

        self._on_mode_change()

    def _on_book_toggle(self, code):
        # 取消勾选当前册时，自动切到第一个仍勾选的册
        if not self.book_vars[code].get() and code == self.cur_book:
            for c in self.book_vars:
                if c != code and self.book_vars[c].get():
                    self._set_cur_book(c)
                    break
            else:
                self.book_vars[code].set(True)
                self._toast("至少保留一个册")
                return
        self.canvas.itemconfig("curbook", text=f"当前册：{self.book_names[self.cur_book]} · 单元（默认全部）")

    def _set_cur_book(self, code):
        self.cur_book = code
        for c in self.book_vars:
            st = "normal" if c == code else "hidden"
            for wid in self.unit_wins[c].values():
                self.canvas.itemconfig(wid, state=st)
        self.canvas.itemconfig("curbook", text=f"当前册：{self.book_names[code]} · 单元（默认全部）")

    def _mode_btns(self):
        return [self.btn_pvp, self.btn_duel, self.btn_pve]

    def set_mode_pvp(self):
        self.settings["mode"] = "pvp"
        self._on_mode_change()

    def set_mode_duel(self):
        self.settings["mode"] = "duel"
        self._on_mode_change()

    def set_mode_pve(self):
        self.settings["mode"] = "pve"
        self._on_mode_change()

    def _on_mode_change(self):
        mode = self.settings["mode"]
        if not hasattr(self, "btn_pvp"):
            return
        styles = {
            "pvp": ("red", "dimred"), "duel": ("orange", "dimorange"),
            "pve": ("purple", "dimpurple"),
        }
        self.btn_pvp.set_style(styles["pvp"][0] if mode == "pvp" else styles["pvp"][1])
        self.btn_duel.set_style(styles["duel"][0] if mode == "duel" else styles["duel"][1])
        self.btn_pve.set_style(styles["pve"][0] if mode == "pve" else styles["pve"][1])
        # 难度区显示/隐藏
        st = "normal" if mode == "pve" else "hidden"
        self.canvas.itemconfig("diff", state=st)
        try:
            self.canvas.itemconfig(self.diff_win, state=st)
        except Exception:
            pass

    def _on_diff_change(self):
        self.settings["difficulty"] = self.diff_var.get()

    def select_all_units(self):
        for v in self.unit_vars[self.cur_book].values():
            v.set(True)

    def select_none_units(self):
        for v in self.unit_vars[self.cur_book].values():
            v.set(False)

    # ------------------------------------------------------------------ 开始
    def start_game(self):
        selection = {}
        for code, var in self.book_vars.items():
            if not var.get():
                continue
            checked = [u for u, v in self.unit_vars[code].items() if v.get()]
            if checked:
                selection[code] = checked
        if not selection:
            self._toast("请至少选择一个单元")
            return
        self.settings["selection"] = selection
        self.settings["total"] = self.num_var.get()
        self.settings["time_limit"] = self.time_var.get()
        self.settings["difficulty"] = self.diff_var.get()
        self.settings["kind"] = self.kind_var.get()

        pool = get_words(selection)
        if len(pool) < self.settings["total"]:
            self.settings["total"] = len(pool)

        self.questions = make_questions(pool, self.settings["total"], self.settings["kind"])
        self.q_index = 0
        self.cur_player = 1
        self.scores = {"p1": 0, "p2": 0}
        self.corrects = {"p1": 0, "p2": 0}

        if self.settings["mode"] == "duel":
            self.start_duel()
        else:
            self.show_game()

    # ------------------------------------------------------------------ 对战页
    def show_game(self):
        self.clear()
        mode = self.settings["mode"]
        self.p1_name = "玩家1" if mode == "pvp" else "玩家"
        self.p2_name = "玩家2" if mode == "pvp" else "电脑"

        cv = tk.Canvas(self, highlightthickness=0, bd=0, bg=GLASS_BG2)
        cv.pack(fill="both", expand=True)
        self.canvas = cv
        W, H = 920, 760
        draw_gradient(cv, W, H)
        cv.create_oval(-80, -60, 360, 220, fill="#DCE8FF", stipple="gray50", outline="")
        cv.create_oval(600, 480, 1100, 900, fill="#E9E0FF", stipple="gray50", outline="")

        # 顶部条
        GlassButton(cv, 18, 12, 108, 50, "← 返回", self.show_menu,
                    style="white", font=self.font_body)
        cv.create_text(460, 31, text="英语单词PK", fill="#14213D", font=self.font_h3)
        self.lbl_progress = cv.create_text(880, 31, text="", fill="#5B6B8C",
                                           font=self.font_body, anchor="e")

        # 计分板
        draw_glass_card(cv, 24, 70, 380, 168, r=22, fill=P1_CARD, outline=P1_LINE,
                        shadow=False, tag="p1c")
        self.p1_ring = round_rect(cv, 24, 70, 380, 168, 22, fill="", outline=P1_LINE,
                                  width=2, tags="p1c")
        cv.create_oval(44, 92, 66, 114, fill=P1_RED, outline="", tags="p1c")
        cv.create_text(76, 103, text=self.p1_name, fill=TEXT, font=self.font_h3,
                       anchor="w", tags="p1c")
        self.p1_score_t = cv.create_text(44, 138, text="0 分", fill=P1_RED,
                                         font=self.font_score, anchor="w", tags="p1c")
        self.p1_corr_t = cv.create_text(300, 138, text="答对 0 题", fill=TEXT_SUB,
                                        font=self.font_small, anchor="e", tags="p1c")

        self.lbl_timer = cv.create_text(460, 119, text="不限时", fill=TEXT,
                                        font=self.font_h2)

        draw_glass_card(cv, 540, 70, 896, 168, r=22,
                        fill=P2_CARD, outline=P2_LINE, shadow=False, tag="p2c")
        self.p2_ring = round_rect(cv, 540, 70, 896, 168, 22, fill="", outline=P2_LINE,
                                  width=2, tags="p2c")
        p2color = AI_PURPLE if mode == "pve" else P2_BLUE
        cv.create_oval(560, 92, 582, 114, fill=p2color, outline="", tags="p2c")
        cv.create_text(592, 103, text=self.p2_name, fill=TEXT, font=self.font_h3,
                       anchor="w", tags="p2c")
        self.p2_score_t = cv.create_text(560, 138, text="0 分", fill=p2color,
                                         font=self.font_score, anchor="w", tags="p2c")
        self.p2_corr_t = cv.create_text(816, 138, text="答对 0 题", fill=TEXT_SUB,
                                        font=self.font_small, anchor="e", tags="p2c")

        # 题目卡
        draw_glass_card(cv, 24, 184, 896, 730)
        self.lbl_kind = cv.create_text(460, 216, text="", fill=PRIMARY,
                                       font=self.font_h3)
        self.lbl_stem = cv.create_text(460, 288, text="", fill=TEXT,
                                       font=self.font_q, width=820)

        GlassButton(cv, 420, 320, 500, 352, "🔊 朗读", self._speak_cur,
                    style="white", font=self.font_small)

        # 选项 2x2
        self.option_btns = []
        pos = [(48, 378, 448, 458), (472, 378, 872, 458),
               (48, 474, 448, 554), (472, 474, 872, 554)]
        for i, (x1, y1, x2, y2) in enumerate(pos):
            btn = GlassButton(cv, x1, y1, x2, y2, "", style="gray",
                              font=self.font_h3, radius=16, tag="choices")
            btn.command = None
            self.option_btns.append(btn)

        # 拼写区
        self.spell_entry = tk.Entry(cv, font=self.font_q, justify="center", fg=TEXT,
                                    relief="solid", bd=1, highlightthickness=1,
                                    highlightbackground="#D9E4F7", highlightcolor=PRIMARY,
                                    width=24, bg="#FFFFFF")
        self.spell_win = self._window(self.spell_entry, 460, 430, anchor="center", tag="spell")
        self.spell_hint = cv.create_text(460, 492, text="", fill=TEXT_SUB,
                                         font=self.font_body, tags="spell")
        self.btn_submit = GlassButton(cv, 390, 516, 530, 572, "提交答案",
                                      self.submit_spell, style="primary",
                                      font=self.font_h3, tag="spell")
        self.spell_entry.bind("<Return>", lambda e: self.submit_spell())

        # 反馈气泡
        self.fbk = None

        for k in ("1", "2", "3", "4"):
            self.bind(f"<Key-{k}>", self._on_num_key)

        self.load_question()

    def _on_num_key(self, e):
        if getattr(self, "answered", False) or self.cur_q is None:
            return
        q = self.cur_q
        if q.kind == Question.KIND_SPELL or q.options is None:
            return
        idx = {"1": 0, "2": 1, "3": 2, "4": 3}.get(e.keysym)
        if idx is None:
            return
        btn = self.option_btns[idx]
        if not btn.enabled:
            return
        self.answer_choice(btn, q.options[idx][2])

    def _refresh_scores(self):
        cv = self.canvas
        p2color = AI_PURPLE if self.settings["mode"] == "pve" else P2_BLUE
        cv.itemconfig(self.p1_score_t, text=f"{self.scores['p1']} 分")
        cv.itemconfig(self.p2_score_t, text=f"{self.scores['p2']} 分",
                      fill=p2color)
        cv.itemconfig(self.p1_corr_t, text=f"答对 {self.corrects['p1']} 题")
        cv.itemconfig(self.p2_corr_t, text=f"答对 {self.corrects['p2']} 题")
        # 当前答题者高亮
        if self.cur_player == 1:
            cv.itemconfig(self.p1_ring, outline=P1_RED, width=3)
            cv.itemconfig(self.p2_ring, outline=P2_LINE, width=2)
        else:
            cv.itemconfig(self.p1_ring, outline=P1_LINE, width=2)
            cv.itemconfig(self.p2_ring, outline=p2color, width=3)

    def load_question(self):
        cv = self.canvas
        self.answered = False
        self.cur_q = self.questions[self.q_index]
        q = self.cur_q
        who = self.p1_name if self.cur_player == 1 else self.p2_name
        cv.itemconfig(self.lbl_progress, text=f"第 {self.q_index+1} / {len(self.questions)} 题")
        cv.itemconfig(self.lbl_kind, text=f"{who} 答题 · {q.kind_text}")
        cv.itemconfig(self.lbl_stem, text=q.stem_text)
        self.canvas.delete("fbk")

        if q.kind == Question.KIND_SPELL:
            for b in self.option_btns:
                b.set_visible(False)
            self.canvas.itemconfig(self.spell_win, state="normal")
            self.canvas.itemconfig(self.spell_hint, state="normal")
            self.btn_submit.set_visible(True)
            first = q.word["en"].split()[0][0].upper()
            cv.itemconfig(self.spell_hint, text=f"首字母提示：{first}")
            self.spell_entry.config(state="normal")
            self.spell_entry.delete(0, "end")
            self.spell_entry.focus_set()
        else:
            for b in self.option_btns:
                b.set_visible(True)
            self.canvas.itemconfig(self.spell_win, state="hidden")
            self.canvas.itemconfig(self.spell_hint, state="hidden")
            self.btn_submit.set_visible(False)
            for i, (label, text, is_correct) in enumerate(q.options):
                btn = self.option_btns[i]
                btn.set_text(f"  {label}.  {text}")
                btn.set_style("gray")
                btn.set_enabled(True)
                btn.command = (lambda c=is_correct, b=btn: self.answer_choice(b, c))
        self._refresh_scores()
        self._start_timer()

    def _start_timer(self):
        if getattr(self, "timer_after", None):
            try:
                self.after_cancel(self.timer_after)
            except Exception:
                pass
            self.timer_after = None
        limit = self.settings["time_limit"]
        if limit <= 0:
            self.canvas.itemconfig(self.lbl_timer, text="不限时", fill=TEXT)
            return
        self.time_left = limit
        self.canvas.itemconfig(self.lbl_timer, text=f"{self.time_left}s", fill=PRIMARY)
        self._tick_timer()

    def _tick_timer(self):
        self.time_left -= 1
        if self.time_left <= 0:
            self.canvas.itemconfig(self.lbl_timer, text="0s", fill=RED)
            self.timeout_question()
            return
        color = RED if self.time_left <= 3 else PRIMARY
        self.canvas.itemconfig(self.lbl_timer, text=f"{self.time_left}s", fill=color)
        self.timer_after = self.after(1000, self._tick_timer)

    def timeout_question(self):
        if self.answered:
            return
        self.answered = True
        draw_pill(self.canvas, 460, 620, f"⏰ 时间到！正确答案：{self.cur_q.correct}",
                  RED, RED_BG, self.font_h3)
        self.after(FEEDBACK_MS, self.next_question)

    # ------------------------------------------------------------------ 答题
    def answer_choice(self, btn, is_correct):
        if self.answered:
            return
        self.answered = True
        q = self.cur_q
        if is_correct:
            btn.set_style("green")
            self.corrects[self._pk()] += 1
            self.scores[self._pk()] += SCORE_CHOICE
            draw_pill(self.canvas, 460, 620, "✅ 回答正确！+10分", GREEN, GREEN_BG,
                      self.font_h3)
            self._play_sound(True)
        else:
            btn.set_style("red")
            draw_pill(self.canvas, 460, 620, f"❌ 答错了，正确答案：{q.correct}",
                      RED, RED_BG, self.font_h3)
            self._play_sound(False)
            self._highlight_correct(q)
        self._refresh_scores()
        self._after_next()

    def submit_spell(self):
        if self.answered:
            return
        user = self.spell_entry.get().strip().lower()
        user = " ".join(user.split())
        correct = self.cur_q.correct.lower()
        correct = " ".join(correct.split())
        self.answered = True
        if user == correct:
            self.corrects[self._pk()] += 1
            self.scores[self._pk()] += SCORE_SPELL
            draw_pill(self.canvas, 460, 620, "✅ 拼写正确！+15分", GREEN, GREEN_BG,
                      self.font_h3)
            self._play_sound(True)
        else:
            draw_pill(self.canvas, 460, 620, f"❌ 正确拼写：{self.cur_q.correct}",
                      RED, RED_BG, self.font_h3)
            self._play_sound(False)
        self.spell_entry.config(state="disabled")
        self._refresh_scores()
        self._after_next()

    def _highlight_correct(self, q):
        for i, (label, text, is_correct) in enumerate(q.options):
            if is_correct:
                self.option_btns[i].set_style("green")

    def _pk(self):
        return "p1" if self.cur_player == 1 else "p2"

    def _play_sound(self, ok):
        try:
            import winsound
            if ok:
                winsound.MessageBeep(winsound.MB_OK)
            else:
                winsound.MessageBeep(winsound.MB_ICONHAND)
        except Exception:
            pass

    def _after_next(self):
        self.after(FEEDBACK_MS, self.next_question)

    def next_question(self):
        self.q_index += 1
        if self.q_index >= len(self.questions):
            self.show_result()
            return
        self.cur_player = 2 if self.cur_player == 1 else 1
        if self.settings["mode"] == "pve" and self.cur_player == 2:
            self.after(80, self.ai_turn)
            return
        self.load_question()

    def ai_turn(self):
        if self.q_index >= len(self.questions):
            return
        self.load_question()
        self.answered = True
        draw_pill(self.canvas, 460, 620, "🤖 电脑思考中…", AI_PURPLE, "#F2ECFE",
                  self.font_h3)
        self.after(AI_THINK_MS, self._ai_answer)

    def _ai_answer(self):
        q = self.cur_q
        conf = DIFF_CONF[self.settings["difficulty"]]
        ai_ok = random.random() < conf
        if ai_ok:
            self.corrects["p2"] += 1
            pts = SCORE_SPELL if q.kind == Question.KIND_SPELL else SCORE_CHOICE
            self.scores["p2"] += pts
            draw_pill(self.canvas, 460, 620, "🤖 电脑答对了", GREEN, GREEN_BG,
                      self.font_h3)
        else:
            draw_pill(self.canvas, 460, 620, "🤖 电脑答错了", RED, RED_BG,
                      self.font_h3)
        if q.kind != Question.KIND_SPELL:
            for i, (label, text, is_correct) in enumerate(q.options):
                if ai_ok and is_correct:
                    self.option_btns[i].set_style("green")
        self._refresh_scores()
        self.after(FEEDBACK_MS, self.next_question)

    def _speak_cur(self):
        if self.cur_q:
            speak(self.cur_q.word["en"])

    # ------------------------------------------------------------------ 双窗对战
    def start_duel(self):
        self.clear()
        self.result_shown = False
        self.geometry("560x240")
        self.title("单词PK · 裁判台")
        self._build_duel_board()

        w1 = DuelWindow(self, 1, "玩家1", P1_RED, self.questions, self.settings["time_limit"])
        w2 = DuelWindow(self, 2, "玩家2", P2_BLUE, self.questions, self.settings["time_limit"])
        self.duel_windows = [w1, w2]
        now = time.time()
        w1.start_time = now
        w2.start_time = now

        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        left_x = max(20, (sw - 1180) // 2)
        top_y = max(60, (sh - 660) // 2)
        w1.geometry(f"560x650+{left_x}+{top_y}")
        w2.geometry(f"560x650+{left_x + 600}+{top_y}")
        self.geometry(f"560x240+{max(20, (sw - 560) // 2)}+{max(8, top_y - 250)}")
        self.lift()
        self.after(600, self._lift_duel_windows)

    def _lift_duel_windows(self):
        for w in getattr(self, "duel_windows", []) or []:
            try:
                if w.winfo_exists():
                    w.lift()
            except Exception:
                pass

    def _build_duel_board(self):
        cv = tk.Canvas(self, highlightthickness=0, bd=0, bg=GLASS_BG2)
        cv.pack(fill="both", expand=True)
        self.canvas = cv
        W, H = 560, 240
        draw_gradient(cv, W, H)
        draw_glass_card(cv, 14, 10, 546, 230, r=24)
        cv.create_text(280, 40, text="双窗对战 · 裁判台", fill="#14213D",
                       font=self.font_h3)
        cv.create_text(280, 62, text="两个窗口同时作答，实时对比比分", fill=TEXT_SUB,
                       font=self.font_small)
        self.lbl_d1 = cv.create_text(140, 118, text="玩家1\n0分 / 答对0题",
                                     fill=P1_RED, font=self.font_h3, justify="center")
        cv.create_text(280, 118, text="VS", fill=TEXT_SUB, font=self.font_h2)
        self.lbl_d2 = cv.create_text(420, 118, text="玩家2\n0分 / 答对0题",
                                     fill=P2_BLUE, font=self.font_h3, justify="center")
        self.lbl_duel_timer = cv.create_text(280, 164, text="不限时", fill=TEXT_SUB,
                                             font=self.font_body)
        GlassButton(cv, 148, 184, 268, 220, "提前结束", self.end_duel_early,
                    style="red", font=self.font_body)
        GlassButton(cv, 286, 184, 406, 220, "返回首页", self.quit_duel,
                    style="primary", font=self.font_body)

    def _duel_progress(self):
        if not getattr(self, "duel_windows", None) or self.canvas is None:
            return
        try:
            w1, w2 = self.duel_windows
            self.canvas.itemconfig(self.lbl_d1,
                                   text=f"玩家1\n{w1.score}分 / 答对{w1.correct}题")
            self.canvas.itemconfig(self.lbl_d2,
                                   text=f"玩家2\n{w2.score}分 / 答对{w2.correct}题")
        except Exception:
            pass

    def _check_duel_done(self):
        if not getattr(self, "duel_windows", None):
            return
        if all(w.finished for w in self.duel_windows):
            self.after(400, self._show_duel_result)

    def _on_duel_close(self, closed):
        if not getattr(self, "duel_windows", None):
            return
        for w in self.duel_windows:
            if not w.finished:
                w.finished = True
                w.elapsed = time.time() - getattr(w, "start_time", time.time())
        for w in self.duel_windows:
            try:
                w.destroy()
            except Exception:
                pass
        self._show_duel_result()

    def end_duel_early(self):
        if not getattr(self, "duel_windows", None):
            return
        for w in self.duel_windows:
            if not w.finished:
                w.finished = True
                w.elapsed = time.time() - getattr(w, "start_time", time.time())
        for w in self.duel_windows:
            try:
                w.destroy()
            except Exception:
                pass
        self._show_duel_result()

    def quit_duel(self):
        for w in getattr(self, "duel_windows", []) or []:
            try:
                w.destroy()
            except Exception:
                pass
        self.geometry("920x760")
        self.title("沪教版初中 · 英语单词PK")
        self.show_menu()

    def _show_duel_result(self):
        if getattr(self, "result_shown", False) or not getattr(self, "duel_windows", None):
            return
        self.result_shown = True
        w1, w2 = self.duel_windows
        s1, s2 = w1.score, w2.score
        c1, c2 = w1.correct, w2.correct
        t1, t2 = getattr(w1, "elapsed", 0), getattr(w2, "elapsed", 0)
        total = len(self.questions)
        if s1 > s2:
            title, color = "🏆 玩家1 获胜！", P1_RED
        elif s2 > s1:
            title, color = "🏆 玩家2 获胜！", P2_BLUE
        else:
            title, color = "🤝 平局！", GOLD

        win = tk.Toplevel(self)
        win.title("PK 结果")
        win.configure(bg=GLASS_BG2)
        win.resizable(False, False)
        win.protocol("WM_DELETE_WINDOW", lambda: None)
        cv = tk.Canvas(win, highlightthickness=0, bd=0, bg=GLASS_BG2)
        cv.pack(fill="both", expand=True)
        W, H = 620, 500
        win.geometry(f"{W}x{H}")
        draw_gradient(cv, W, H)
        draw_glass_card(cv, 30, 30, 590, 470, r=28)
        cv.create_text(310, 92, text=title, fill=color, font=self.font_title)
        cv.create_text(310, 128, text=f"共 {total} 题 · 双窗同时作答", fill=TEXT_SUB,
                       font=self.font_small)
        for name, sc, cc, tt, col, x in (("玩家1", s1, c1, t1, P1_RED, 150),
                                         ("玩家2", s2, c2, t2, P2_BLUE, 470)):
            round_rect(cv, x - 130, 170, x + 130, 330, 22, fill=col, outline="")
            cv.create_text(x, 208, text=name, fill=WHITE, font=self.font_h3)
            cv.create_text(x, 258, text=f"{sc} 分", fill=WHITE,
                           font=tkfont.Font(family="Microsoft YaHei UI", size=30,
                                            weight="bold"))
            cv.create_text(x, 298, text=f"答对 {cc} 题 · 用时 {tt:.0f} 秒", fill="#FFFFFF",
                           font=self.font_small)
        GlassButton(cv, 130, 380, 300, 440, "再来一局", self._duel_again,
                    style="green", font=self.font_h2)
        GlassButton(cv, 320, 380, 490, 440, "返回首页", self._duel_home,
                    style="primary", font=self.font_h2)
        win.update_idletasks()
        win.geometry(f"+{(self.winfo_screenwidth() - W) // 2}+"
                     f"{(self.winfo_screenheight() - H) // 2}")
        win.transient(self)
        win.grab_set()
        win.lift()
        self.result_win = win

    def _duel_again(self):
        if hasattr(self, "result_win"):
            try:
                self.result_win.destroy()
            except Exception:
                pass
        self.result_shown = False
        self.duel_windows = None
        self.start_game()

    def _duel_home(self):
        if hasattr(self, "result_win"):
            try:
                self.result_win.destroy()
            except Exception:
                pass
        self.result_shown = False
        self.geometry("920x760")
        self.title("沪教版初中 · 英语单词PK")
        self.show_menu()

    # ------------------------------------------------------------------ 结算
    def show_result(self):
        self.clear()
        self.geometry("920x760")
        p1_s, p2_s = self.scores["p1"], self.scores["p2"]
        p1_c, p2_c = self.corrects["p1"], self.corrects["p2"]
        mode = self.settings["mode"]

        if p1_s > p2_s:
            winner, w_color = self.p1_name, P1_RED
            title = f"🏆 {winner} 获胜！"
        elif p2_s > p1_s:
            winner, w_color = self.p2_name, (AI_PURPLE if mode == "pve" else P2_BLUE)
            title = f"🏆 {winner} 获胜！"
        else:
            title, w_color = "🤝 平局！旗鼓相当", GOLD

        cv = tk.Canvas(self, highlightthickness=0, bd=0, bg=GLASS_BG2)
        cv.pack(fill="both", expand=True)
        self.canvas = cv
        W, H = 920, 760
        draw_gradient(cv, W, H)
        cv.create_oval(-80, -60, 360, 220, fill="#DCE8FF", stipple="gray50", outline="")
        cv.create_oval(600, 480, 1100, 900, fill="#E9E0FF", stipple="gray50", outline="")

        draw_glass_card(cv, 60, 50, 860, 710, r=30)
        cv.create_text(460, 178, text=title, fill=w_color, font=self.font_title)
        cv.create_text(460, 222, text="本局结束", fill=TEXT_SUB, font=self.font_sub)

        items = [(self.p1_name, P1_RED, p1_s, p1_c, 250),
                 (self.p2_name, AI_PURPLE if mode == "pve" else P2_BLUE, p2_s, p2_c, 670)]
        for name, color, sc, cc, x in items:
            round_rect(cv, x - 145, 290, x + 145, 450, 24, fill=color, outline="")
            cv.create_text(x, 326, text=name, fill=WHITE, font=self.font_h3)
            cv.create_text(x, 380, text=f"{sc} 分", fill=WHITE,
                           font=tkfont.Font(family="Microsoft YaHei UI", size=32,
                                            weight="bold"))
            cv.create_text(x, 420, text=f"答对 {cc} 题", fill="#FFFFFF",
                           font=self.font_small)
        cv.create_text(460, 370, text="VS", fill="#A9B8D4",
                       font=tkfont.Font(family="Microsoft YaHei UI", size=26,
                                        weight="bold"))

        cv.create_text(460, 506, text=f"共 {len(self.questions)} 题 · 选择题 +{SCORE_CHOICE}分 · 拼写题 +{SCORE_SPELL}分",
                       fill=TEXT_SUB, font=self.font_small)

        GlassButton(cv, 250, 548, 450, 614, "再来一局", self.start_game,
                    style="green", font=self.font_h2)
        GlassButton(cv, 470, 548, 670, 614, "返回首页", self.show_menu,
                    style="primary", font=self.font_h2)


# ---------------------------------------------------------------------------
# 双窗对战：独立答题窗口
# ---------------------------------------------------------------------------
class DuelWindow(tk.Toplevel):
    """双窗对战中的一个独立答题窗口（两名玩家各占一个，同时作答）"""

    def __init__(self, app, player_no, name, color, questions, time_limit):
        super().__init__(app)
        self.app = app
        self.player_no = player_no
        self.name = name
        self.color = color
        self.questions = questions
        self.time_limit = time_limit
        self.q_index = 0
        self.score = 0
        self.correct = 0
        self.answered = False
        self.finished = False
        self.cur_q = None
        self.timer_after = None
        self.time_left = 0
        self.start_time = None
        self.elapsed = 0
        self.canvas = None

        self.title(f"{name} · 单词PK")
        self.geometry("560x650")
        self.resizable(False, False)
        self.configure(bg=GLASS_BG2)
        try:
            self.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.build_ui()
        self.load_question()

    def build_ui(self):
        cv = tk.Canvas(self, highlightthickness=0, bd=0, bg=GLASS_BG2)
        cv.pack(fill="both", expand=True)
        self.canvas = cv
        W, H = 560, 650
        draw_gradient(cv, W, H)

        # 顶部色条
        cv.create_rectangle(0, 0, W, 60, fill=self.color, outline="")
        cv.create_text(20, 30, text=self.name, fill=WHITE, font=self.app.font_h2,
                       anchor="w")
        self.lbl_progress = cv.create_text(540, 30, text="", fill="#FFFFFF",
                                           font=self.app.font_body, anchor="e")

        # 状态行
        self.lbl_score = cv.create_text(28, 92, text="0 分 · 答对 0 题",
                                        fill=self.color, font=self.app.font_h3,
                                        anchor="w")
        self.lbl_timer = cv.create_text(532, 92, text="不限时", fill=TEXT,
                                        font=self.app.font_h3, anchor="e")

        # 题目卡
        draw_glass_card(cv, 20, 116, 540, 630)
        self.lbl_kind = cv.create_text(280, 148, text="", fill=PRIMARY,
                                       font=self.app.font_h3)
        self.lbl_stem = cv.create_text(280, 216, text="", fill=TEXT,
                                       font=self.app.font_q, width=460)
        GlassButton(cv, 245, 250, 315, 282, "🔊 朗读", self._speak_cur,
                    style="white", font=self.app.font_small)

        self.option_btns = []
        pos = [(40, 300, 280, 368), (300, 300, 540, 368),
               (40, 384, 280, 452), (300, 384, 540, 452)]
        for x1, y1, x2, y2 in pos:
            btn = GlassButton(cv, x1, y1, x2, y2, "", style="gray",
                              font=self.app.font_h3, radius=16, tag="choices")
            btn.command = None
            self.option_btns.append(btn)

        self.spell_entry = tk.Entry(cv, font=self.app.font_q, justify="center",
                                    fg=TEXT, relief="solid", bd=1,
                                    highlightthickness=1, highlightbackground="#D9E4F7",
                                    highlightcolor=PRIMARY, width=20, bg="#FFFFFF")
        self.spell_win = cv.create_window(280, 400, window=self.spell_entry, anchor="center", tags="spell")
        self.spell_hint = cv.create_text(280, 452, text="", fill=TEXT_SUB,
                                         font=self.app.font_body, tags="spell")
        self.btn_submit = GlassButton(cv, 230, 478, 330, 528, "提交答案",
                                      self.submit_spell, style="primary",
                                      font=self.app.font_h3, tag="spell")
        self.spell_entry.bind("<Return>", lambda e: self.submit_spell())

        for k in ("1", "2", "3", "4"):
            self.bind(f"<Key-{k}>", self._on_num_key)

    # ------------------------------------------------------------ 题目
    def load_question(self):
        cv = self.canvas
        self.answered = False
        self.cur_q = self.questions[self.q_index]
        q = self.cur_q
        cv.itemconfig(self.lbl_progress,
                      text=f"第 {self.q_index+1} / {len(self.questions)} 题")
        cv.itemconfig(self.lbl_kind, text=q.kind_text)
        cv.itemconfig(self.lbl_stem, text=q.stem_text)
        cv.delete("fbk")
        if q.kind == Question.KIND_SPELL:
            for b in self.option_btns:
                b.set_visible(False)
            cv.itemconfig(self.spell_win, state="normal")
            cv.itemconfig(self.spell_hint, state="normal")
            self.btn_submit.set_visible(True)
            first = q.word["en"].split()[0][0].upper()
            cv.itemconfig(self.spell_hint, text=f"首字母提示：{first}")
            self.spell_entry.config(state="normal")
            self.spell_entry.delete(0, "end")
            self.spell_entry.focus_set()
        else:
            for b in self.option_btns:
                b.set_visible(True)
            cv.itemconfig(self.spell_win, state="hidden")
            cv.itemconfig(self.spell_hint, state="hidden")
            self.btn_submit.set_visible(False)
            for i, (label, text, is_correct) in enumerate(q.options):
                btn = self.option_btns[i]
                btn.set_text(f"  {label}.  {text}")
                btn.set_style("gray")
                btn.set_enabled(True)
                btn.command = (lambda c=is_correct, b=btn: self.answer_choice(b, c))
        self._start_timer()

    def _start_timer(self):
        if self.timer_after:
            try:
                self.after_cancel(self.timer_after)
            except Exception:
                pass
            self.timer_after = None
        if self.time_limit <= 0:
            self.canvas.itemconfig(self.lbl_timer, text="不限时", fill=TEXT)
            return
        self.time_left = self.time_limit
        self.canvas.itemconfig(self.lbl_timer, text=f"{self.time_left}s", fill=PRIMARY)
        self._tick_timer()

    def _tick_timer(self):
        self.time_left -= 1
        if self.time_left <= 0:
            self.canvas.itemconfig(self.lbl_timer, text="0s", fill=RED)
            self.timeout_question()
            return
        color = RED if self.time_left <= 3 else PRIMARY
        self.canvas.itemconfig(self.lbl_timer, text=f"{self.time_left}s", fill=color)
        self.timer_after = self.after(1000, self._tick_timer)

    def timeout_question(self):
        if self.answered or self.finished:
            return
        self.answered = True
        draw_pill(self.canvas, 280, 566, f"⏰ 时间到！正确答案：{self.cur_q.correct}",
                  RED, RED_BG, self.app.font_h3)
        self.after(FEEDBACK_MS, self.next_question)

    # ------------------------------------------------------------ 答题
    def answer_choice(self, btn, is_correct):
        if self.answered or self.finished:
            return
        self.answered = True
        if is_correct:
            btn.set_style("green")
            self.correct += 1
            self.score += SCORE_CHOICE
            draw_pill(self.canvas, 280, 566, "✅ 回答正确！+10分", GREEN, GREEN_BG,
                      self.app.font_h3)
        else:
            btn.set_style("red")
            draw_pill(self.canvas, 280, 566, f"❌ 正确答案：{self.cur_q.correct}",
                      RED, RED_BG, self.app.font_h3)
            self._highlight_correct()
        self._play_sound(is_correct)
        self._refresh_status()
        self.after(FEEDBACK_MS, self.next_question)

    def submit_spell(self):
        if self.answered or self.finished:
            return
        user = self.spell_entry.get().strip().lower()
        user = " ".join(user.split())
        correct = self.cur_q.correct.lower()
        correct = " ".join(correct.split())
        self.answered = True
        ok = user == correct
        if ok:
            self.correct += 1
            self.score += SCORE_SPELL
            draw_pill(self.canvas, 280, 566, "✅ 拼写正确！+15分", GREEN, GREEN_BG,
                      self.app.font_h3)
        else:
            draw_pill(self.canvas, 280, 566, f"❌ 正确拼写：{self.cur_q.correct}",
                      RED, RED_BG, self.app.font_h3)
        self._play_sound(ok)
        self.spell_entry.config(state="disabled")
        self._refresh_status()
        self.after(FEEDBACK_MS, self.next_question)

    def next_question(self):
        if self.finished:
            return
        self.q_index += 1
        if self.q_index >= len(self.questions):
            self.finish()
            return
        self.load_question()

    def finish(self):
        if self.finished:
            return
        self.finished = True
        self.elapsed = time.time() - self.start_time if self.start_time else 0
        if self.timer_after:
            try:
                self.after_cancel(self.timer_after)
            except Exception:
                pass
        cv = self.canvas
        cv.itemconfig(self.lbl_kind, text="🎉 已完成全部题目")
        cv.itemconfig(self.lbl_stem, text="")
        for b in self.option_btns:
            b.set_visible(False)
        cv.itemconfig(self.spell_win, state="hidden")
        cv.itemconfig(self.spell_hint, state="hidden")
        self.btn_submit.set_visible(False)
        draw_pill(cv, 280, 380, "等待对手完成…", TEXT_SUB, "#F1F5FB", self.app.font_h3)
        self.app._check_duel_done()

    def _refresh_status(self):
        self.canvas.itemconfig(self.lbl_score,
                               text=f"{self.score} 分 · 答对 {self.correct} 题")
        self.app._duel_progress()

    def _highlight_correct(self):
        for i, (_, _, is_correct) in enumerate(self.cur_q.options):
            if is_correct:
                self.option_btns[i].set_style("green")

    def _play_sound(self, ok):
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_OK if ok else winsound.MB_ICONHAND)
        except Exception:
            pass

    def _on_num_key(self, e):
        if self.answered or self.finished or self.cur_q is None:
            return
        q = self.cur_q
        if q.kind == Question.KIND_SPELL or q.options is None:
            return
        idx = {"1": 0, "2": 1, "3": 2, "4": 3}.get(e.keysym)
        if idx is None:
            return
        btn = self.option_btns[idx]
        if not btn.enabled:
            return
        self.answer_choice(btn, q.options[idx][2])

    def _speak_cur(self):
        if self.cur_q:
            speak(self.cur_q.word["en"])

    def on_close(self):
        self.app._on_duel_close(self)


def resource_path(rel):
    """兼容 PyInstaller 打包后的资源路径"""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


if __name__ == "__main__":
    app = WordPKApp()
    app.mainloop()

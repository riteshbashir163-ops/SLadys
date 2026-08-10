#!/usr/bin/env python3
"""对 sjie-fashion 技能产出做机械格式质检。用法: python3 format_check.py <output.md> <图片数>"""
import re, sys

path, n_imgs = sys.argv[1], int(sys.argv[2])
text = open(path, encoding='utf-8').read()
lines = text.split('\n')
results = []

def check(name, ok, evidence=""):
    results.append((name, ok, evidence))

# 1. 无破折号
dashes = [i+1 for i, l in enumerate(lines) if '——' in l]
check("全文无破折号——", not dashes, f"出现在行 {dashes}" if dashes else "")

# 2. 图片标记完整且各出现一次
missing, dup = [], []
for i in range(1, n_imgs+1):
    tag = f"【图{i:02d}】"
    c = text.count(tag)
    if c == 0: missing.append(tag)
    if c > 1: dup.append(f"{tag}x{c}")
check(f"【图01】~【图{n_imgs:02d}】齐全", not missing, f"缺 {missing}" if missing else "")
check("图片标记无重复", not dup, str(dup) if dup else "")

# 3. 图片标记独占一行
bad_inline = [i+1 for i, l in enumerate(lines) if re.search(r'【图\d+】', l) and not re.fullmatch(r'\s*【图\d+】\s*', l)]
check("【图XX】独占一行", not bad_inline, f"混排在行 {bad_inline}" if bad_inline else "")

# 4. 标题长度 15-25 字（取第一个 # 标题或首个非空行）
title = ""
for l in lines:
    s = l.strip()
    if s and not s.startswith('>'):
        title = re.sub(r'^#+\s*', '', s)
        break
tlen = len(title)
check(f"标题15~25字(实际{tlen}): {title}", 15 <= tlen <= 25)

# 5. 开篇纯文字：第一个小标题/分组之前不得有【图XX】
first_img = text.find('【图')
subhead_pos = [m.start() for m in re.finditer(r'\n#{2,3}\s|\n[^\n]{2,14}＋[^\n]{2,14}\n', text)]
first_sub = min(subhead_pos) if subhead_pos else -1
if first_sub != -1:
    check("开篇无图（首个小标题前无【图】标记）", first_img > first_sub,
          f"first_img@{first_img}, first_subhead@{first_sub}")
else:
    # 无分组结构：开篇 = 首个【图】之前的纯文字段，至少2段
    opening_paras = [l for l in text[:first_img].split('\n') if l.strip() and not l.strip().startswith('>')]
    check(f"开篇纯文字≥2段（无分组结构，实际{max(len(opening_paras)-1,0)}段）", len(opening_paras) >= 3)

# 6. 左右式拆解禁令
lr = [i+1 for i, l in enumerate(lines) if re.search(r'左边|右边|左侧|右侧', l)]
check("无左右式拆解", not lr, f"行 {lr}" if lr else "")

# 7. AI 腔黑名单
banned = ['希望给你们带来灵感', '每一个步伐', '今天来给大家讲讲', '随着季节的更迭', '在这个', '我认为']
hits = []
for b in banned:
    if b == '在这个':
        if re.search(r'在这个[^\n]{0,6}的季节里', text): hits.append('在这个xx的季节里')
    elif b in text:
        hits.append(b)
check("无AI腔黑名单词", not hits, str(hits) if hits else "")

# 8. "那种…的感觉" ≤1
n_ganjue = len(re.findall(r'那种[^\n，。]{0,12}的感觉', text))
check(f"'那种…的感觉'≤1次(实际{n_ganjue})", n_ganjue <= 1)

# 9. 段落长短参差：正文文字段落字数的极差与方差
paras = [l.strip() for l in lines if l.strip() and not re.fullmatch(r'\s*【图\d+】\s*', l) and not l.strip().startswith('#') and not l.strip().startswith('>')]
plens = [len(p) for p in paras]
if plens:
    spread = max(plens) - min(plens)
    check(f"段落长短参差(最短{min(plens)}/最长{max(plens)})", spread >= 40)

# 9.5 "名词＋一＋动词"动作特写句（S姐原文为零，全篇禁止）
punchy = re.findall(r'一[翻荡束闪甩抖撩掀]|拦腰一|斜斜一系|往身上一[套披罩]|一收尾', text)
check(f"无动作特写句(一翻/一荡/一束/一闪等，实际{len(punchy)}处)", len(punchy) == 0, str(punchy) if punchy else "")

# 9.6 图段短句定调开头（"度假就穿全白。"式，≤2处）
img_paras = re.findall(r'\n\n([^\n]+)\n【图\d+】', text)
short_openers = []
for p in img_paras:
    first = p.split('，')[0].split('。')[0]
    if '。' in p[:14] and len(first) <= 12:
        short_openers.append(first + '。')
check(f"图段短句定调开头≤2处(实际{len(short_openers)})", len(short_openers) <= 2, str(short_openers) if len(short_openers) > 2 else "")

# 9.7 清点式图说：图段里"颜色+单品/量词+单品"锚点≥4，就是在报画面清单（S姐范文单段最多2~3个）
ITEM = r'(?:衬衫|衬衣|上衣|短T|T恤|背心|吊带|针织|开衫|外套|西装|风衣|大衣|马甲|连衣裙|半裙|长裙|短裙|伞裙|裙|长裤|短裤|中裤|阔腿裤|牛仔裤|裤|凉鞋|猫跟|高跟|平底鞋|乐福鞋|玛丽珍|拖|靴|鞋|包|帽|头巾|丝巾|腰带|袜)'
anchor = re.compile(r'一(?:只|双|条|件|顶|枚|袭|身)[^，。；：\n]{0,8}?' + ITEM
                   + r'|(?:黑|白|红|蓝|绿|黄|紫|粉|灰|棕|驼|米|杏|裸|银|金|卡其|藏蓝|宝蓝|墨绿|薄荷|摩卡|香芋|酒红)(?:色|调|白|蓝|绿|紫)?系?的?[^，。；：\n]{0,4}?' + ITEM)
marker_re = re.compile(r'\s*【图\d+】\s*')
listy, seen_p = [], set()
for i, l in enumerate(lines):
    if marker_re.fullmatch(l):
        j = i - 1
        while j >= 0 and (not lines[j].strip() or marker_re.fullmatch(lines[j])):
            j -= 1
        if j < 0 or j in seen_p:
            continue
        seen_p.add(j)
        n = len(list(anchor.finditer(lines[j])))
        if n >= 4:
            listy.append(f"行{j+1}({n}锚点)")
check(f"无清点式图说(图段单品锚点≥4，实际{len(listy)}段)", not listy, str(listy) if listy else "")

# 10. 鞋履动词重复检查
verbs = ['踩上一双', '再穿上一双', '脚下踩双', '脚上搭配', '再配一双', '配上一双', '换成一双', '蹬上一双']
over = [f"{v}x{text.count(v)}" for v in verbs if text.count(v) > 2]
check("鞋履动词无超2次重复", not over, str(over) if over else "")

print(f"{'PASS' if all(ok for _, ok, _ in results) else 'FAIL'}  {path}")
for name, ok, ev in results:
    print(f"  [{'✓' if ok else '✗'}] {name}" + (f"  | {ev}" if ev and not ok else ""))

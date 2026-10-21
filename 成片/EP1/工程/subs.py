"""生成 build/subs.ass：台词字幕（按角色描边配色，底部 20% 安全区内）+ 全部字卡（标题、钩子、知识卡、VS、安全卡、金句、预告）。"""
from plan import plan
from timeline import VOICES

KUAI, QK = 'ZCOOL KuaiLe', 'ZCOOL QingKe HuangYou'
MAXC = 12   # 每行最多字数（66px 字号、左右各 90px 边距）


def ts(t):
    t = max(t, 0)
    h, m = int(t // 3600), int(t % 3600 // 60)
    return f'{h}:{m:02d}:{t % 60:05.2f}'


def wrap(text):
    if len(text) <= MAXC: return text
    if len(text) > 2 * MAXC:   # 超长句先按标点切成多段再逐段折行
        cut = max((i for i, ch in enumerate(text[:2 * MAXC]) if ch in '，、。？！'), default=2 * MAXC - 1) + 1
        return wrap(text[:cut]) + r'\N' + wrap(text[cut:])
    # 优先在中间附近的标点后断行
    mid, best = len(text) / 2, None
    for i, ch in enumerate(text[:-1]):
        if ch in '，、。？！—…' and (best is None or abs(i + 1 - mid) < abs(best - mid)): best = i + 1
    if best is None or not (3 <= best <= len(text) - 2): best = int(mid)
    return text[:best] + r'\N' + text[best:]


HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Dialog,{KUAI},68,&H00FFFFFF,&H00FFFFFF,&H00202020,&H80000000,0,0,0,0,100,100,2,0,1,6,3,2,90,90,250,1
Style: Title,{QK},132,&H0000D8FF,&H00FFFFFF,&H001A1AA0,&H80000000,0,0,0,0,100,100,4,0,1,9,5,8,40,40,0,1
Style: Sub,{KUAI},58,&H00FFFFFF,&H00FFFFFF,&H00202020,&H80000000,0,0,0,0,100,100,2,0,1,5,2,8,40,40,0,1
Style: Hook,{KUAI},76,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,4,0,1,0,0,5,60,60,0,1
Style: Panel,{KUAI},10,&H00F2F8FF,&H00FFFFFF,&H001A1AA0,&H00000000,0,0,0,0,100,100,0,0,1,6,0,7,0,0,0,1
Style: KTitle,{QK},92,&H002030D8,&H00FFFFFF,&H00FFFFFF,&H00000000,0,0,0,0,100,100,4,0,1,4,0,8,60,60,0,1
Style: KBody,{KUAI},52,&H00303030,&H00FFFFFF,&H00FFFFFF,&H00000000,0,0,0,0,100,100,1,0,1,0,0,8,60,60,0,1
Style: Vs,{QK},140,&H00FFFFFF,&H00FFFFFF,&H00202020,&H80000000,0,0,0,0,100,100,4,0,1,9,5,5,40,40,0,1
Style: SafeTitle,{QK},86,&H0000C8FF,&H00FFFFFF,&H00202020,&H00000000,0,0,0,0,100,100,4,0,1,6,0,8,40,40,0,1
Style: SafeBody,{KUAI},56,&H00FFFFFF,&H00FFFFFF,&H00202020,&H00000000,0,0,0,0,100,100,1,0,1,3,0,8,60,60,0,1
Style: Quote,{KUAI},70,&H00302A28,&H00FFFFFF,&H00FFFFFF,&H00000000,0,0,0,0,100,100,2,0,1,0,0,5,120,90,0,1
Style: Next,{QK},96,&H002828E8,&H00FFFFFF,&H00FFFFFF,&H80000000,0,0,0,0,100,100,8,0,1,3,4,8,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

POP = r'{\fscx40\fscy40\t(0,140,\fscx112\fscy112)\t(140,240,\fscx100\fscy100)}'


def rect(x0, y0, x1, y1, r=36):
    return (fr'{{\p1}}m {x0 + r} {y0} l {x1 - r} {y0} b {x1} {y0} {x1} {y0} {x1} {y0 + r} '
            fr'l {x1} {y1 - r} b {x1} {y1} {x1} {y1} {x1 - r} {y1} l {x0 + r} {y1} b {x0} {y1} {x0} {y1} {x0} {y1 - r} '
            fr'l {x0} {y0 + r} b {x0} {y0} {x0} {y0} {x0 + r} {y0}{{\p0}}')


def card(style, text, a, b):
    """返回 (layer, style, text)；位置与动画按卡片类型。"""
    if style == 'Title':
        return [(3, 'Title', r'{\pos(540,330)\fad(0,150)}' + POP + text)]
    if style == 'Sub':
        return [(3, 'Sub', r'{\pos(540,500)\fad(220,150)}' + text)]
    if style == 'Hook':
        return [(3, 'Hook', r'{\fad(300,200)\move(540,1000,540,940,0,600)}' + text)]
    if style == 'KTitle':
        return [(1, 'Panel', r'{\fad(200,200)\1a&H18&\bord6\move(0,-700,0,0,0,260)}' + rect(90, 110, 990, 600)),
                (3, 'KTitle', r'{\fad(200,200)\move(540,-420,540,150,0,260)}' + text)]
    if style == 'KBody':
        return [(3, 'KBody', r'{\fad(300,200)\pos(540,290)}' + text)]
    if style == 'VsTop':
        return [(3, 'Vs', r'{\pos(540,560)\3c&H1A1AA0&\1c&H40E8FF&\fad(0,150)}' + POP + text)]
    if style == 'VsMid':
        return [(3, 'Vs', r'{\pos(540,960)\fs110\1c&H2828E8&\3c&HFFFFFF&\fad(0,150)}' + POP + text)]
    if style == 'VsBot':
        return [(3, 'Vs', r'{\pos(540,1360)\3c&H1A1AA0&\1c&H40E8FF&\fad(0,150)}' + POP + text)]
    if style == 'SafeTitle':
        return [(1, 'Panel', r'{\fad(200,200)\1c&H101010&\1a&H50&\3c&H00C8FF&\bord5}' + rect(60, 560, 1020, 1300)),
                (3, 'SafeTitle', r'{\fad(200,200)\pos(540,620)}' + POP + text)]
    if style == 'SafeBody':
        return [(3, 'SafeBody', r'{\fad(300,200)\pos(540,800)}' + text)]
    if style == 'Quote':
        return [(3, 'Quote', r'{\fad(500,250)\pos(570,880)}' + text)]
    if style == 'QuoteBy':
        return [(3, 'Quote', r'{\fad(400,250)\pos(700,1100)\fs50\1c&H6A6A6A&}' + text)]
    if style == 'Next':
        return [(3, 'Next', r'{\fad(150,150)\pos(540,240)\t(0,300,\fsp20)}' + text)]
    raise KeyError(style)


def main():
    shots, total = plan()
    ev = []
    dlg = []   # (start, end, who, text)
    for s in shots:
        t0, end = s['start'], s['start'] + s['len']
        for l in s['lines']:
            if l['sub']:
                dlg.append([t0 + l['start'] - .05, t0 + l['start'] + l['dur'] + .3, l['who'], l['text'], end])
        for style, text, a, b in s.get('cards', []):
            b = s['len'] if b is None else b
            for layer, st, tx in card(style, text, a, b):
                ev.append(f'Dialogue: {layer},{ts(t0 + a)},{ts(t0 + b)},{st},,0,0,0,,{tx}')
    for i, (a, b, who, text, shot_end) in enumerate(dlg):
        nxt = dlg[i + 1][0] if i + 1 < len(dlg) else total
        b = min(b, nxt - .02, shot_end + .2)
        col = VOICES[who]['color']
        tag = fr'{{\3c{col}&\fad(60,60)}}'
        if who == '旁白':
            tag = r'{\3c&H202020&\1c&H9CF0FF&\fad(60,60)}'
        ev.append(f'Dialogue: 4,{ts(a)},{ts(b)},Dialog,{who},0,0,0,,{tag}{wrap(text)}')
    open('build/subs.ass', 'w', encoding='utf-8').write(HEAD + '\n'.join(ev) + '\n')
    print(len(ev), 'events')


if __name__ == '__main__':
    main()

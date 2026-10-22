"""合成全集音轨：程序化配乐（按镜头切段）+ 程序化音效 + 配音，配乐在台词下自动闪避。
输出 build/mix.wav（48k 立体声）。全部声音由本脚本现场合成，无外部素材、无版权问题。"""
import json
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
from plan import plan

SR = 48000
rng = np.random.default_rng(7)


# ───────────────────────── 基础工具 ─────────────────────────
def T(d):
    return np.arange(int(d * SR)) / SR


def lp(x, f, o=2):
    return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)


def hp(x, f, o=2):
    return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)


def bp(x, lo, hi, o=2):
    return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)


def adsr(n, a=.005, r=.05):
    e = np.ones(n)
    na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e


def noise(d):
    return rng.standard_normal(int(d * SR))


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def place(buf, x, t, g=1.0):
    i = int(t * SR)
    if i >= len(buf) or i + len(x) <= 0: return
    if i < 0: x, i = x[-i:], 0
    x = x[:len(buf) - i]
    buf[i:i + len(x)] += g * x


def norm(x, peak=1.0):
    m = np.abs(x).max()
    return x / m * peak if m > 0 else x


# ───────────────────────── 乐器 ─────────────────────────
def pluck(f, d, bright=1.0):
    t = T(d); x = np.zeros_like(t)
    for k in range(1, 9):
        x += np.sin(2 * np.pi * f * k * t) / k ** (1.6 - .4 * bright) * np.exp(-t * (4 + 2.5 * k))
    return x * adsr(len(t), .002, .02)


def marimba(f, d):
    t = T(d)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * 7) + .35 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 22)
    return x * adsr(len(t), .002, .02)


def bell(f, d, idx=2.0):
    t = T(d)
    x = np.sin(2 * np.pi * f * t + idx * np.exp(-t * 3) * np.sin(2 * np.pi * f * 3.5 * t)) * np.exp(-t * 2.8)
    return x * adsr(len(t), .002, .05)


def bass(f, d):
    t = T(d)
    x = np.sin(2 * np.pi * f * t) + .25 * np.sin(2 * np.pi * 2 * f * t) + .1 * np.sin(2 * np.pi * 3 * f * t)
    return x * np.exp(-t * 3) * adsr(len(t), .004, .04)


def pad(fs, d, a=.4, cut=1800):
    t = T(d); x = np.zeros_like(t)
    for f in fs:
        for det in (-.12, 0, .12):
            ph = rng.random()
            x += ((f * 2 ** (det / 12) * t + ph) % 1.0) * 2 - 1
    return lp(x / (3 * len(fs)), cut) * adsr(len(t), a, min(.6, d / 2))


def brass(fs, d, a=.03):
    t = T(d); x = np.zeros_like(t)
    env = adsr(len(t), a, .15)
    for f in fs:
        for k in range(1, 12):
            x += np.sin(2 * np.pi * f * k * t + k) * np.exp(-k / (1.5 + 5 * env)) / k
    return x / len(fs) * env


def kick(g=1.0):
    t = T(.35); f = 45 + 90 * np.exp(-t * 30)
    return g * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def snare(g=1.0):
    t = T(.2)
    return g * (bp(noise(.2), 1500, 7000) * .6 + .5 * np.sin(2 * np.pi * 190 * t)) * np.exp(-t * 22)


def hat(g=1.0, d=.05):
    t = T(d)
    return g * hp(noise(d), 7000) * np.exp(-t * 80) * .5


def snap(g=1.0):
    t = T(.08)
    return g * bp(noise(.08), 1800, 5000) * np.exp(-t * 60)


def taiko(g=1.0):
    t = T(1.0); f = 60 + 40 * np.exp(-t * 18)
    return g * (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4) + .2 * lp(noise(1.0), 500) * np.exp(-t * 12))


# ───────────────────────── 配乐段落（每段从段首起拍，按需长度生成）─────────────────────────
def seq(d, bpm, bars, chords, fn):
    """通用节拍器：每小节 4 拍，chords 为每小节的根音/和弦（midi 列表），fn(buf, bar_t, beat_len, chord, i)。"""
    buf = np.zeros(int(d * SR) + SR * 4)
    beat = 60 / bpm
    i = 0
    while i * 4 * beat < d:
        fn(buf, i * 4 * beat, beat, chords[i % len(chords)], i)
        i += 1
    return buf[:int(d * SR)]


def cue_comedy(d):
    # C 大调轻快木琴 + 拨弦低音 oom-pah，132bpm
    ch = [[48, 60, 64, 67], [45, 57, 60, 64], [41, 57, 60, 65], [43, 55, 59, 62]]
    mel = [[72, None, 76, 79, None, 76, 72, None], [72, None, 69, 72, None, 76, None, None],
           [77, None, 76, 72, None, 69, 72, None], [74, None, 71, 74, 79, None, 77, 74]]

    def bar(buf, t0, b, c, i):
        for k in range(4):
            place(buf, bass(mtof(c[0] if k % 2 == 0 else c[0] + 7), b * .9), t0 + k * b, .55)
            if k % 2 == 1:
                for n in c[1:]: place(buf, pluck(mtof(n), b * .5), t0 + k * b, .16)
                place(buf, snap(), t0 + k * b, .25)
            place(buf, hat(), t0 + k * b + b / 2, .25)
        for j, n in enumerate(mel[i % 4]):
            if n: place(buf, marimba(mtof(n), b * .9), t0 + j * b / 2, .32)
    return seq(d, 132, 4, ch, bar)


def cue_lazy(d):
    # 埼玉的懒散摇摆：电钢琴感钟声 + 走路低音，84bpm
    ch = [[50, 65, 69, 72], [43, 65, 71, 74], [48, 64, 67, 71], [45, 61, 64, 67]]

    def bar(buf, t0, b, c, i):
        walk = [c[0], c[0] + 4, c[0] + 7, c[0] + 9]
        for k in range(4):
            place(buf, pluck(mtof(walk[k] - 12), b * .95, .3), t0 + k * b, .6)
            place(buf, hat(.6, .09), t0 + k * b + b * .66, .18)
        for n in c[1:]:
            place(buf, bell(mtof(n), b * 2, 1.0), t0 + b * .66, .07)
            place(buf, bell(mtof(n), b * 1.5, 1.0), t0 + b * 2.66, .05)
    return seq(d, 84, 4, ch, bar)


def cue_serious(d):
    x = pad([38, 45, 50, 53], d + .5, a=.3, cut=900)[:int(d * SR)] * .9
    t = T(d); x += .25 * np.sin(2 * np.pi * mtof(26) * t)
    for k in range(int(d / 1.2) + 1): place(x, taiko(), .05 + k * 1.2, .7)
    return x


def cue_think(d):
    ch = [[53, 57, 60, 64], [55, 59, 62, 67], [52, 55, 59, 64], [57, 60, 64, 69]]

    def bar(buf, t0, b, c, i):
        arp = c + [c[1] + 12, c[2] + 12, c[3] + 12, c[2] + 12]
        for j, n in enumerate(arp): place(buf, bell(mtof(n + 12), b, 1.2), t0 + j * b / 2, .09)
        place(buf, pad([c[0] - 12, c[0]], b * 4, a=.5, cut=1200), t0, .35)
    return seq(d, 100, 4, ch, bar)


def cue_versus(d):
    ch = [[40], [40], [43], [38]]

    def bar(buf, t0, b, c, i):
        for k in range(4):
            place(buf, kick(), t0 + k * b, .8)
            if k % 2: place(buf, snare(), t0 + k * b, .45)
            for h in range(2):
                place(buf, bass(mtof(c[0]), b * .45), t0 + k * b + h * b / 2, .5)
                place(buf, hat(), t0 + k * b + h * b / 2, .2)
        place(buf, brass([mtof(c[0] + 24), mtof(c[0] + 31), mtof(c[0] + 36)], b * 1.2), t0, .35)
    return seq(d, 150, 4, ch, bar)


def cue_dora(d):
    # 哆啦A梦：F 大调钟琴 + 圆号式 oom-pah，120bpm
    ch = [[41, 57, 60, 65], [46, 58, 62, 65], [48, 58, 60, 64], [41, 57, 60, 65]]
    mel = [[77, 81, 84, None, 81, None, 77, None], [82, None, 81, 79, 77, None, 74, None],
           [76, 79, 84, None, 82, 79, 76, None], [77, None, 72, None, 77, None, None, None]]

    def bar(buf, t0, b, c, i):
        for k in range(4):
            place(buf, bass(mtof(c[0] if k % 2 == 0 else c[0] + 7), b * .9), t0 + k * b, .5)
            if k % 2:
                for n in c[1:]: place(buf, pluck(mtof(n), b * .4, .6), t0 + k * b, .13)
        for j, n in enumerate(mel[i % 4]):
            if n: place(buf, bell(mtof(n), b * 1.2, 1.5), t0 + j * b / 2, .18)
    return seq(d, 120, 4, ch, bar)


def cue_soft(d):
    x = pad([53, 57, 60, 64], d + .5, a=.6, cut=1400)[:int(d * SR)] * .6
    for k, n in enumerate([72, 76, 79, 77, 74, 72, 76, 79]):
        if .4 + k * .9 < d: place(x, bell(mtof(n), 2.0, .8), .4 + k * .9, .1)
    return x


def cue_sneak(d):
    # 蹑手蹑脚拨弦：A 小调半音下行，100bpm
    line = [57, None, 60, None, 59, None, 58, None, 57, None, 64, None, 63, 62, 61, None]

    def bar(buf, t0, b, c, i):
        for k in range(2): place(buf, pluck(mtof(33 if k == 0 else 40), b * .5, .4), t0 + k * 2 * b, .6)
        seg = line[(i % 2) * 8:(i % 2) * 8 + 8]
        for j, n in enumerate(seg):
            if n: place(buf, pluck(mtof(n + 12), b * .35, .9), t0 + j * b / 2, .3)
        for k in range(4): place(buf, hat(.5, .03), t0 + k * b + b / 2, .15)
    return seq(d, 100, 4, [[0]], bar)


def cue_epic(d):
    x = np.zeros(int(d * SR))
    place(x, brass([mtof(48), mtof(55), mtof(60), mtof(64), mtof(67)], d, a=.25), 0, .55)
    place(x, pad([48, 55, 60, 64, 72], d, a=.5, cut=3000), 0, .5)
    t = 0.0
    while t < d:  # 定音鼓滚奏渐强
        place(x, taiko(.4 + .6 * t / d), t, .5)
        t += max(.07, .25 - .2 * t / d)
    return x


def cue_intro(d):
    x = pad([45, 52, 57, 60], d, a=d * .8, cut=1200) * .6
    return x


def cue_drone(d):
    t = T(d)
    return (pad([33, 40], d, a=.3, cut=500) * .8 + .2 * np.sin(2 * np.pi * 55 * t)) * (1 + .3 * np.sin(2 * np.pi * 3 * t))


def cue_trailer(d):
    t = T(d)
    x = pad([38, 45, 49, 53], d, a=.2, cut=700) * .7 + .25 * np.sin(2 * np.pi * 36.7 * t)
    for k in range(int(d / .5)): place(x, kick(.6), .5 + k * .5, .4)
    place(x, taiko(1.0), d - .9, .9)
    place(x, brass([mtof(38), mtof(45), mtof(50)], .9, a=.01), d - .9, .5)
    return x


CUES = dict(comedy=(cue_comedy, .30), lazy=(cue_lazy, .34), serious=(cue_serious, .35), think=(cue_think, .38),
            versus=(cue_versus, .30), dora=(cue_dora, .30), soft=(cue_soft, .40), sneak=(cue_sneak, .38),
            epic=(cue_epic, .50), intro=(cue_intro, .45), drone=(cue_drone, .45), trailer=(cue_trailer, .48))


# ───────────────────────── 音效 ─────────────────────────
def sweep(f0, f1, d, kind='sin'):
    t = T(d); f = f0 * (f1 / f0) ** (t / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) if kind == 'sin' else np.sign(np.sin(ph))


def fx(name):
    t1 = lambda d: T(d)
    if name == 'boom_low':
        return kick(1) * .9 + lp(noise(.35), 200) * np.exp(-t1(.35) * 10) * .3
    if name == 'page_flip':
        x = np.zeros(int(.9 * SR))
        for k in range(14): place(x, bp(noise(.05), 2000, 8000) * np.exp(-t1(.05) * 50), k * .06, .35 * (1 - k / 16))
        return x
    if name == 'page_turn':
        return bp(noise(.4), 1500, 6000) * np.sin(np.pi * t1(.4) / .4) * .35
    if name == 'slap':
        return bp(noise(.12), 400, 4000) * np.exp(-t1(.12) * 40) * .9
    if name == 'sting':
        return brass([mtof(60), mtof(64), mtof(67), mtof(72)], 1.4, a=.01) * .6 + hp(noise(1.4), 6000) * np.exp(-t1(1.4) * 3) * .12
    if name == 'hum':
        t = t1(1.8); return lp(np.sign(np.sin(2 * np.pi * 55 * t)), 300) * adsr(len(t), .4, .4) * .25
    if name == 'pew':
        return sweep(1800, 500, .16, 'sq') * np.exp(-t1(.16) * 10) * .18
    if name == 'flash_boom':
        return (lp(noise(.9), 1500) * .5 + sweep(80, 35, .9)) * np.exp(-t1(.9) * 5) * .8
    if name in ('psy_hum', 'psy_soft'):
        d = 1.4 if name == 'psy_hum' else 1.0; t = t1(d)
        x = (np.sin(2 * np.pi * 110 * t) + .5 * np.sin(2 * np.pi * 220.7 * t)) * (1 + .5 * np.sin(2 * np.pi * 6 * t))
        return x * adsr(len(t), .2, .4) * (.22 if name == 'psy_hum' else .15)
    if name == 'charge':
        return (sweep(150, 900, 1.4) * .5 + bp(noise(1.4), 300, 3000) * .2) * np.linspace(.1, 1, int(1.4 * SR)) * adsr(int(1.4 * SR), .01, .05) * .45
    if name in ('whoosh', 'whoosh_short'):
        d = .7 if name == 'whoosh' else .35; t = t1(d)
        x = np.zeros_like(t); n = noise(d)
        for a, b in ((300, 1200), (1200, 4000)): x += bp(n, a, b)
        return x * np.sin(np.pi * t / d) ** 2 * .5
    if name == 'crash_far':
        return lp(noise(1.0), 900) * np.exp(-t1(1.0) * 4) * .5
    if name == 'clang':
        t = t1(1.2); x = np.zeros_like(t)
        for f, a in ((310, 1), (742, .7), (1187, .5), (1630, .35), (2350, .2)): x += a * np.sin(2 * np.pi * f * t)
        return (x * np.exp(-t * 5) * .35 + np.pad(kick(1), (0, len(t) - int(.35 * SR))) * .8)
    if name == 'boing':
        t = t1(.9); f = 220 + 140 * np.exp(-t * 4) * np.sin(2 * np.pi * 9 * t)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.5) * .35
    if name == 'blank_ding':
        return bell(mtof(93), 1.5, .3) * .25
    if name == 'crickets':
        x = np.zeros(int(1.3 * SR))
        for k in range(5):
            c = np.sin(2 * np.pi * 4300 * t1(.12)) * (np.sin(2 * np.pi * 45 * t1(.12)) > 0) * .07
            place(x, c, k * .26)
        return x
    if name == 'step':
        return lp(noise(.09), 700) * np.exp(-t1(.09) * 45) * .55 + bp(noise(.09), 2000, 5000) * np.exp(-t1(.09) * 70) * .12
    if name == 'anger':
        return (sweep(90, 70, .6, 'sq') * .2 + lp(noise(.6), 2000) * .1) * adsr(int(.6 * SR), .02, .2)
    if name == 'transition_low':
        return (sweep(70, 40, 1.8) + .3 * lp(noise(1.8), 300)) * np.exp(-t1(1.8) * 1.8) * .7
    if name in ('card_ding', 'card_ding2', 'tiny_ding'):
        f = {'card_ding': 88, 'card_ding2': 95, 'tiny_ding': 100}[name]
        return bell(mtof(f), 1.0, 1.0) * .22
    if name == 'thud_comic':
        return (kick(1)[:int(.35 * SR)] * .7 + sweep(300, 120, .35) * np.exp(-t1(.35) * 10) * .2)
    if name == 'psy_sweep':
        d = 2.2; t = t1(d); n = noise(d)
        x = bp(n, 400, 2500) * (1 + np.sin(2 * np.pi * 1.4 * t)) * .3 + np.sin(2 * np.pi * (180 + 60 * np.sin(2 * np.pi * .7 * t)) * t) * .12
        return x * adsr(len(t), .15, .4)
    if name == 'punch':
        return kick(1.1)[:int(.3 * SR)] + bp(noise(.3), 200, 2500) * np.exp(-t1(.3) * 25) * .6
    if name == 'door':
        x = np.zeros(int(.4 * SR)); c = bp(noise(.03), 1500, 6000) * np.exp(-t1(.03) * 120)
        place(x, c, 0, .7); place(x, c, .09, .5); return x
    if name == 'gadget':
        x = np.zeros(int(1.2 * SR)); place(x, bell(mtof(84), .8, 1.0), 0, .25); place(x, bell(mtof(79), .9, 1.0), .2, .25)
        return x
    if name == 'notice':
        x = np.zeros(int(.8 * SR)); place(x, bell(mtof(81), .6, .5), 0, .2); place(x, bell(mtof(76), .6, .5), .18, .2)
        return x
    if name == 'crack':
        return hp(noise(.08), 1500) * np.exp(-t1(.08) * 50) * .7 + sweep(900, 300, .08) * np.exp(-t1(.08) * 40) * .2
    if name == 'rummage':
        x = np.zeros(int(1.2 * SR))
        for k in range(9): place(x, bp(noise(.06), 300, 3000) * np.exp(-t1(.06) * 40), k * .12 + rng.random() * .04, .3)
        return x
    if name == 'squish':
        return sweep(500, 250, .25) * np.exp(-t1(.25) * 8) * (1 + .5 * np.sin(2 * np.pi * 30 * t1(.25))) * .15
    if name == 'explosion':
        d = 2.4; t = t1(d)
        return (lp(noise(d), 1200) * .7 + sweep(90, 30, d) * .6) * np.minimum(1, t * 30) * np.exp(-t * 1.6) * .9
    if name == 'scratch':
        d = .5; t = t1(d); f = 300 + 900 * np.abs(np.sin(2 * np.pi * 2 * t))
        return (bp(noise(d), 800, 5000) * .5 + .2 * np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR))) * adsr(len(t), .005, .05) * .55
    if name == 'freeze':
        return bell(mtof(98), .8, .2) * .1
    if name == 'drop':
        return bp(noise(.12), 300, 2000) * np.exp(-t1(.12) * 30) * .5
    if name == 'clash':
        t = t1(2.0); x = np.zeros_like(t)
        for f, a in ((523, 1), (1270, .6), (2210, .4), (3570, .25)): x += a * np.sin(2 * np.pi * f * t)
        return x * np.exp(-t * 2.2) * .25 + hp(noise(2.0), 3000) * np.exp(-t * 6) * .25 + np.pad(kick(1), (0, len(t) - int(.35 * SR))) * .7
    raise KeyError(name)


# ───────────────────────── 混音 ─────────────────────────
def load_wav(p):
    sr, x = wavfile.read(p)
    x = x.astype(np.float32) / 32768
    return x if x.ndim == 1 else x.mean(1)


def smooth_env(x, att=.03, rel=.35):
    env = np.abs(x)
    # 下采样到 1ms 求包络再插值，避免逐采样循环
    hop = SR // 1000
    e = env[:len(env) // hop * hop].reshape(-1, hop).max(1)
    out = np.zeros_like(e); a, r = np.exp(-1 / (att * 1000)), np.exp(-1 / (rel * 1000)); v = 0.0
    for i, s in enumerate(e):
        v = a * v + (1 - a) * s if s > v else r * v + (1 - r) * s
        out[i] = v
    return np.interp(np.arange(len(x)), np.arange(len(out)) * hop, out)


def main():
    shots, total = plan()
    n = int(total * SR) + SR
    voice, sfx, music = np.zeros(n), np.zeros(n), np.zeros(n)

    for s in shots:
        for l in s['lines']:
            v = load_wav(l['wav'])
            # 各句响度对齐：RMS 统一到约 -17 dBFS，峰值不超过 0.95
            v = v * min(.14 / (np.sqrt(np.mean(v ** 2)) + 1e-9), .95 / (np.abs(v).max() + 1e-9))
            place(voice, v, s['start'] + l['start'])
        for name, at in s.get('sfx', []):
            at = s['len'] - .25 if at is None else at
            place(sfx, fx(name), s['start'] + at)

    # 配乐段落
    segs, cur = [], None
    for s in shots:
        m = s.get('music')
        if m and m != cur:
            segs.append((s['start'], m)); cur = m
    segs.append((total, None))
    for (t0, m), (t1, _) in zip(segs, segs[1:]):
        if m == 'stop': continue
        fn, g = CUES[m]
        x = fn(t1 - t0 + .15)
        x = x / (np.abs(x).max() + 1e-9) * g
        fade = int(.15 * SR); x[-fade:] *= np.linspace(1, 0, fade)
        x[:int(.01 * SR)] *= np.linspace(0, 1, int(.01 * SR))
        place(music, x, t0)

    duck = 1 - .6 * np.clip(smooth_env(voice) / .15, 0, 1)
    music *= duck
    sfx *= 1 - .3 * np.clip(smooth_env(voice) / .15, 0, 1)

    mix = voice + .8 * sfx + music
    # 轻微立体声：配乐左右微延迟加宽
    d = int(.012 * SR)
    L = mix + .15 * np.roll(music, d)
    R = mix + .15 * np.roll(music, -d)
    st = np.stack([L, R], 1)
    st = np.tanh(st / (np.abs(st).max() + 1e-9) * 1.4) * .9
    wavfile.write('build/mix.wav', SR, (st * 32767).astype(np.int16))
    json.dump([dict(id=s['id'], start=s['start'], len=s['len']) for s in shots], open('build/plan.json', 'w'), indent=1)
    print(f'mix {total:.2f}s')


if __name__ == '__main__':
    main()

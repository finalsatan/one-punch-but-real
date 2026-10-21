"""EP1 动态漫画时间线：每镜的图、最短时长、镜头运动、台词、音效、字卡、配乐段落。

时长规则：镜头实际时长 = max(分镜表时长, 台词前置 + 配音总长 + 收尾留白)。
台词、字卡全部由 subs.py 生成 ASS 后烧录；配音见 tts.py；音效/配乐见 audio.py。
"""

IMG = '分镜/EP1/单镜图片/场景{s}/镜头{k}.png'

# 角色配音（edge-tts）：voice, rate, pitch；color 为字幕描边色（ASS &HBBGGRR）
VOICES = {
    '小新':   dict(voice='zh-CN-YunxiaNeural',   rate='-6%',  pitch='-4Hz',  color='&H1E2AD8'),  # 红
    '龙卷':   dict(voice='zh-CN-XiaoyiNeural',   rate='+4%',  pitch='+6Hz',  color='&H3C9A1E'),  # 绿
    '埼玉':   dict(voice='zh-CN-YunyangNeural',  rate='-12%', pitch='-6Hz',  color='&H10A8D8'),  # 黄
    '哆啦A梦': dict(voice='zh-CN-XiaoxiaoNeural', rate='+6%',  pitch='-12Hz', color='&HD8901E'),  # 蓝
    '旁白':   dict(voice='zh-CN-YunjianNeural',  rate='+0%',  pitch='+0Hz',  color='&H202020'),
}

LEAD, TAIL = 0.20, 0.40   # 台词前置 / 收尾留白（秒）

# motion: push / pushfast / pull / panup / pandown / panleft / panright / hold
#   可选 cx, cy（推近焦点，0–1）；shake=[(t0, t1, 像素)]；flash_in / flash_out（白闪秒数）；wobble（歪斜晃动）
# lines: [(角色, 台词, 相对镜头开头的起始秒 或 None=顺接[, 'nosub' 表示语气声不上字幕])]
# sfx:   [(音效名, 相对镜头开头的秒)]
# cards: [(字卡样式, 文本, 起, 止)]  止=None 表示到镜头结束
# music: 本镜开头切换的配乐段落（None 表示沿用上一段）
SHOTS = [
    # ── 场景1 片头 ──
    dict(id='1-01', img=(1, '01'), dur=1.2, motion='push', cx=.5, cy=.55, music='intro',
         sfx=[('boom_low', 0.0)]),
    dict(id='1-02', img=(1, '02'), dur=1.0, motion='pushfast', shake=[(0, .35, 10)],
         sfx=[('page_flip', 0.0)]),
    dict(id='1-03', img=(1, '03'), dur=2.6, motion='hold', flash_in=.12,
         lines=[('旁白', '一拳，但是真的！', .25, 'nosub')],
         sfx=[('slap', 0.0), ('sting', 0.05)],
         cards=[('Title', '一拳，但是真的', .1, None), ('Sub', '本集：打击力量的定义', .55, None)]),

    # ── 场景2 前3秒钩子 ──
    dict(id='2-01', img=None, dur=1.6, motion='hold', music='drone',
         sfx=[('hum', 0.0)],
         cards=[('Hook', '本系列改编自真实拳击专著', .05, None)]),
    dict(id='2-02', img=(2, '02'), dur=2.0, motion='push', cx=.4, cy=.4, flash_out=.18,
         shake=[(.55, .7, 6), (1.05, 1.2, 6)],
         lines=[('小新', '这不可能是真的吧？', .15)],
         sfx=[('pew', .55), ('pew', 1.05), ('flash_boom', None)]),   # None = 镜头末尾
    dict(id='2-03', img=(2, '03'), dur=2.0, motion='panup', music='comedy',
         lines=[('龙卷', '看好了，弱小的地球人。', .25)],
         sfx=[('psy_hum', .1)]),
    dict(id='2-04', img=(2, '04'), dur=1.5, motion='push', cx=.7, cy=.45,
         sfx=[('charge', 0.0)]),
    dict(id='2-05', img=(2, '05'), dur=1.1, motion='pushfast', cx=.5, cy=.3, shake=[(0, 1.1, 14)],
         sfx=[('whoosh', 0.0), ('crash_far', .6)]),
    dict(id='2-06', img=(2, '06'), dur=2.0, motion='hold',
         lines=[('龙卷', '这才叫实力。', .2), ('龙卷', '哼～', 1.3, 'nosub')]),
    dict(id='2-07', img=(2, '07'), dur=1.2, motion='hold', shake=[(0, .45, 18)], flash_in=.06,
         sfx=[('clang', 0.0), ('boing', .08)]),
    dict(id='2-08', img=(2, '08'), dur=1.6, motion='push', cx=.5, cy=.4, music='stop',
         lines=[('龙卷', '……啊？', .45)],
         sfx=[('blank_ding', 0.0)]),
    dict(id='2-09', img=(2, '09'), dur=1.4, motion='hold',
         sfx=[('crickets', 0.1)]),

    # ── 场景3 埼玉登场 ──
    dict(id='3-01', img=(3, '01'), dur=1.6, motion='panright', music='lazy',
         sfx=[('step', .1), ('step', .65), ('step', 1.2)]),
    dict(id='3-02', img=(3, '02'), dur=2.5, motion='panleft',
         lines=[('埼玉', '这在拳击场上，连边都摸不到。', .2)],
         sfx=[('step', .3), ('step', 1.0), ('step', 1.7)]),
    dict(id='3-03', img=(3, '03'), dur=1.5, motion='push', cx=.5, cy=.3, shake=[(.05, .35, 5)],
         sfx=[('anger', 0.0)]),
    dict(id='3-04', img=(3, '04'), dur=2.5, motion='push', cx=.5, cy=.3, music='serious',
         lines=[('埼玉', '没有让对手倒下的招数，都是在放烟花。', .35)],
         sfx=[('transition_low', 0.0)]),
    dict(id='3-05', img=(3, '05'), dur=4.0, motion='push', cx=.4, cy=.75, music='think',
         lines=[('旁白', '十秒法则：抢在对手防守之前，用足够的力量、在对的时机命中他，让他十秒内站不起来。', .5, 'nosub')],
         sfx=[('card_ding', .25)],
         cards=[('KTitle', '10秒法则', .25, None),
                ('KBody', '真正致命的一拳，不是“看起来猛”\\N而是在对手做出防守反应之前\\N用足够的力量、在对的时机命中他\\N——让他在10秒读秒结束前站不起来', .45, None)]),
    dict(id='3-06', img=(3, '06'), dur=2.0, motion='hold', music='comedy',
         shake=[(0, 2.0, 2)],
         lines=[('小新', '嘿嘿～', .05, 'nosub'), ('小新', '那念力波纹呢？那个不是很猛吗？', None)]),
    dict(id='3-07', img=(3, '07'), dur=2.5, motion='push', cx=.4, cy=.35,
         lines=[('埼玉', '猛，但打不中人的猛，等于零。', .2)],
         sfx=[('thud_comic', None)]),

    # ── 场景4 正误对照 ──
    dict(id='4-01', img=(4, '01'), dur=2.2, motion='pull', music='versus', shake=[(0, 2.2, 4)],
         sfx=[('psy_sweep', 0.0)]),
    dict(id='4-02', img=(4, '02'), dur=1.6, motion='pushfast', cx=.55, cy=.4, shake=[(.25, .55, 16)],
         sfx=[('whoosh_short', .05), ('punch', .25)]),
    dict(id='4-03', img=(4, '03'), dur=3.0, motion='push', cx=.5, cy=.5,
         sfx=[('card_ding', .3), ('card_ding2', 1.3)],
         cards=[('VsTop', '看起来猛', .3, None), ('VsMid', 'VS', .9, None), ('VsBot', '真的重', 1.3, None)]),

    # ── 场景5 道具与规则 ──
    dict(id='5-01', img=(5, '01'), dur=1.5, motion='push', cx=.25, cy=.4, music='dora',
         sfx=[('door', .15)]),
    dict(id='5-02', img=(5, '02'), dur=2.5, motion='push', cx=.4, cy=.45,
         lines=[('哆啦A梦', '这扇门连通好多个世界的拳馆哦。', .2)]),
    dict(id='5-03', img=(5, '03'), dur=3.0, motion='push', cx=.5, cy=.35,
         lines=[('哆啦A梦', '今天大家都是来打真拳击赛的，别的招数，留着以后再用。', .45)],
         sfx=[('gadget', .05)]),
    dict(id='5-04', img=(5, '03'), dur=3.6, motion='hold', dim=True, music='soft',
         sfx=[('notice', .1)],
         cards=[('SafeTitle', '⚠ 安全提示', .1, None),
                ('SafeBody', '真人拳击训练涉及手腕、肩、颈受伤风险\\N本系列所有招式仅供科普参考\\N实际训练请在专业教练指导下进行\\N务必佩戴护具', .2, None)]),
    dict(id='5-05', img=(5, '05'), dur=2.0, motion='panright', music='sneak'),
    dict(id='5-06', img=(5, '06'), dur=1.1, motion='push', cx=.5, cy=.4, shake=[(.35, .55, 6)],
         sfx=[('crack', .35)]),
    dict(id='5-07', img=(5, '07'), dur=1.6, motion='panleft',
         sfx=[('tiny_ding', .7), ('whoosh_short', 1.25)]),

    # ── 场景6 小新实践 ──
    dict(id='6-01', img=(6, '01'), dur=1.6, motion='push', cx=.6, cy=.6, music='comedy',
         sfx=[('rummage', .1)]),
    dict(id='6-02', img=(6, '02'), dur=1.6, motion='hold', shake=[(0, 1.6, 2)],
         sfx=[('squish', .2), ('squish', .8)]),
    dict(id='6-03', img=(6, '03'), dur=2.6, motion='pushfast', cx=.4, cy=.35, music='epic',
         shake=[(.2, 2.6, 12)], flash_in=.15,
         sfx=[('explosion', .15)]),
    dict(id='6-04', img=(6, '04'), dur=1.6, motion='hold', wobble=True, music='stop',
         sfx=[('scratch', 0.0)]),
    dict(id='6-05', img=(6, '05'), dur=1.6, motion='hold', music='lazy',
         lines=[('埼玉', '先站稳吧。', .25)]),
    dict(id='6-06', img=(6, '06'), dur=2.0, motion='push', cx=.5, cy=.3,
         lines=[('龙卷', '……我明明很强的。', .3)]),

    # ── 场景7 收尾 ──
    dict(id='7-01', img=(7, '01'), dur=3.0, motion='push', cx=.5, cy=.45, music='soft',
         lines=[('旁白', '没有让对手倒下的爆炸，只是在放烟花。', .5, 'nosub')],
         sfx=[('page_turn', 0.0)],
         cards=[('Quote', '“没有让对手倒下的爆炸，\\N只是在放烟花。”', .35, None),
                ('QuoteBy', '—— 野木笔记', 1.0, None)]),
    dict(id='7-02', img=(7, '02'), dur=1.6, motion='push', cx=.7, cy=.6, music='sneak',
         sfx=[('psy_soft', .2)]),
    dict(id='7-03', img=(7, '03'), dur=1.6, motion='push', cx=.5, cy=.35),
    dict(id='7-04', img=(7, '04'), dur=1.5, motion='hold', music='stop',
         sfx=[('freeze', 0.0)]),
    dict(id='7-05', img=(7, '05'), dur=2.2, motion='panleft', music='sneak',
         lines=[('龙卷', '嘿咻～', 1.1, 'nosub')],
         sfx=[('drop', .25)]),
    dict(id='7-06', img=(7, '06'), dur=3.4, motion='pull', music='trailer', flash_in=.1,
         shake=[(0, .25, 10)],
         lines=[('旁白', '下集，连拳头都不会包，你打个屁。', .6)],
         sfx=[('clash', 0.0)],
         cards=[('Next', '下集预告', .1, None)]),
]

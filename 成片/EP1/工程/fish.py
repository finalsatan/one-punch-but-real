"""Fish Audio 语音接口（api.fish.audio）。key 读取顺序：环境变量 FISH_API_KEY → ~/.config/fish/api_key。

与 minimax.py 同构：外部只需 tts(text, 音色ID, speed) -> mp3 字节。
区别是这里不打「音色设计」，直接用 Fish 公共音色模型（community model）的 reference_id
出声——模型本身就是对某角色原声训练的克隆，所以音色天然贴合原作。
默认模型 s2.1-pro-free：能力同 s2.1-pro，按公平使用免费（$0）。
"""
import json, os, urllib.request

BASE = 'https://api.fish.audio/v1'
MODEL = os.environ.get('FISH_MODEL', 's2.1-pro-free')

# MiniMax 的 emotion 枚举 → Fish 的自然语言风格指令（写在台词前的方括号里，S2 系列支持任意描述）
STYLE = {
    'happy': '开心地', 'sad': '低声失落', 'angry': '生气地吼', 'fearful': '害怕地',
    'disgusted': '嫌弃地', 'surprised': '惊讶地', 'calm': '平静地',
    'tired': '有气无力地', 'smug': '得意地', 'panic': '慌张地',
}


def key():
    k = os.environ.get('FISH_API_KEY')
    p = os.path.expanduser('~/.config/fish/api_key')
    if not k and os.path.exists(p):
        k = open(p).read().strip()
    return k


def styled(text, emotion=None):
    s = STYLE.get(emotion or '')
    return f'[{s}] {text}' if s else text


def tts(text, reference_id, speed=1.0):
    """用指定音色模型合成，返回 mp3 字节。"""
    body = dict(text=text, reference_id=reference_id, format='mp3', mp3_bitrate=128,
                sample_rate=44100, chunk_length=300, normalize=True, latency='normal',
                prosody=dict(speed=round(float(speed), 2), volume=0, normalize_loudness=True))
    req = urllib.request.Request(f'{BASE}/tts', data=json.dumps(body).encode(),
                                 headers={'Authorization': f'Bearer {key()}',
                                          'Content-Type': 'application/json', 'model': MODEL})
    with urllib.request.urlopen(req, timeout=180) as r:
        raw, ctype = r.read(), r.headers.get('Content-Type', '')
    if 'json' in ctype:  # 出错时返回 JSON，不出音频
        raise RuntimeError(f'Fish tts: {raw[:300]}')
    return raw


def model_info(reference_id):
    """查音色模型元信息（标题/语种/点赞/试听音频地址），用于选音色。"""
    with urllib.request.urlopen(f'https://api.fish.audio/model/{reference_id}', timeout=60) as r:
        return json.load(r)

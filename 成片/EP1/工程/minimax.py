"""MiniMax 语音接口（api.minimaxi.com）。key 读取顺序：环境变量 MINIMAX_API_KEY → ~/.config/minimax/api_key。"""
import json, os, urllib.request

BASE = 'https://api.minimaxi.com/v1'
MODEL = 'speech-02-hd'


def key():
    k = os.environ.get('MINIMAX_API_KEY')
    p = os.path.expanduser('~/.config/minimax/api_key')
    if not k and os.path.exists(p): k = open(p).read().strip()
    return k


def _post(path, body):
    req = urllib.request.Request(f'{BASE}/{path}', data=json.dumps(body).encode(),
                                 headers={'Authorization': f'Bearer {key()}', 'Content-Type': 'application/json'})
    d = json.load(urllib.request.urlopen(req, timeout=180))
    if d.get('base_resp', {}).get('status_code') != 0:
        raise RuntimeError(f"MiniMax {path}: {d.get('base_resp')}")
    return d


def design(prompt, preview_text):
    """按描述生成音色，返回 (voice_id, 试听 mp3 字节)。"""
    d = _post('voice_design', dict(prompt=prompt, preview_text=preview_text))
    return d['voice_id'], bytes.fromhex(d['trial_audio'])


def tts(text, voice_id, speed=1.0, emotion=None):
    vs = dict(voice_id=voice_id, speed=speed, vol=1, pitch=0)
    if emotion: vs['emotion'] = emotion
    d = _post('t2a_v2', dict(model=MODEL, text=text, stream=False, voice_setting=vs,
                             audio_setting=dict(sample_rate=32000, bitrate=128000, format='mp3', channel=1)))
    return bytes.fromhex(d['data']['audio'])

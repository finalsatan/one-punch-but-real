"""用 Fish 音色逐角色试听，不改动正式配音：python3 fish_try.py [角色名 ...]
每个角色取本集第一句正式台词，输出 build/voice_trial_fish/<角色>.mp3。
不给角色名就试听 voices_fish.json 里 EP1 有的全部角色。"""
import json, os, sys
import fish
from timeline import SHOTS, VOICES, EMOTION

DB = json.load(open('voices_fish.json'))
OUT = 'build/voice_trial_fish'
os.makedirs(OUT, exist_ok=True)

if not fish.key():
    sys.exit('缺 FISH_API_KEY（或 ~/.config/fish/api_key），无法试听')

targets = sys.argv[1:] or [w for w in VOICES if w in DB]
for who in targets:
    if who not in DB:
        print(who, '未在 voices_fish.json 登记，跳过')
        continue
    shot, text = next(((s['id'], t) for s in SHOTS for (w, t, *_) in s.get('lines', []) if w == who), (None, None))
    if not text:
        print(who, '本集无台词，跳过')
        continue
    audio = fish.tts(fish.styled(text, EMOTION.get(f'{shot}_0')), DB[who], VOICES[who]['speed'])
    p = f'{OUT}/{who}.mp3'
    open(p, 'wb').write(audio)
    print(f'{who}\t{len(audio)//1024}KB\t{p}\t「{text}」')

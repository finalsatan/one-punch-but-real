"""为每个角色生成 MiniMax 设计音色，voice_id 写入 voices_minimax.json，试听音频存 build/voice_trial/。
已有 voice_id 的角色跳过；要重新设计某个角色：design_voices.py 角色名 ..."""
import json, os, sys
import minimax
from timeline import VOICES, SHOTS

DB = 'voices_minimax.json'
db = json.load(open(DB)) if os.path.exists(DB) else {}
redo = sys.argv[1:]
os.makedirs('build/voice_trial', exist_ok=True)

for who, v in VOICES.items():
    if who in db and who not in redo: continue
    # 试听句取该角色本集第一句正式台词
    sample = next(t for s in SHOTS for (w, t, *rest) in s.get('lines', []) if w == who and not rest[1:])
    vid, audio = minimax.design(v['design'], sample)
    db[who] = vid
    open(f'build/voice_trial/{who}.mp3', 'wb').write(audio)
    json.dump(db, open(DB, 'w'), ensure_ascii=False, indent=1)
    print(who, vid)

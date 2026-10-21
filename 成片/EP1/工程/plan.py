"""把 timeline + 配音时长排成绝对时间轴（帧精确，30fps）。"""
import json
from timeline import SHOTS, LEAD, TAIL

FPS = 30


def plan():
    vd = json.load(open('build/voice.json'))
    t, out = 0.0, []
    for s in SHOTS:
        s = dict(s)
        lines, cur = [], LEAD
        for i, (who, text, st, *flag) in enumerate(s.get('lines', [])):
            st = cur if st is None else st
            d = vd[f"{s['id']}_{i}"]
            lines.append(dict(who=who, text=text, start=st, dur=d, sub=not flag, wav=f"build/voice/{s['id']}_{i}.wav"))
            cur = st + d + 0.15
        need = max([l['start'] + l['dur'] + TAIL for l in lines] or [0])
        frames = round(max(s['dur'], need) * FPS)
        s['frames'], s['start'], s['len'] = frames, t, frames / FPS
        s['lines'] = lines
        out.append(s)
        t += frames / FPS
    return out, t


if __name__ == '__main__':
    shots, total = plan()
    for s in shots:
        print(f"{s['id']}\t{s['start']:6.2f}\t{s['len']:.2f}s")
    print(f'total {total:.2f}s')

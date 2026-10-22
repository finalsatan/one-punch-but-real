"""生成全部台词配音：build/voice/<镜号>_<序号>.wav（48k 单声道），时长写入 build/voice.json。
有 MiniMax key 与 voices_minimax.json 时用 MiniMax 设计音色 + 逐句情绪，否则回退 edge-tts。
台词或音色变了要重配：删掉 build/voice/ 下对应 wav（或整个目录）再运行。"""
import asyncio, json, os, subprocess
import minimax
from timeline import SHOTS, VOICES, EMOTION

OUT = 'build/voice'
os.makedirs(OUT, exist_ok=True)
MM = json.load(open('voices_minimax.json')) if minimax.key() and os.path.exists('voices_minimax.json') else None


def to_wav(src, wav):
    # 去掉首尾静音，便于精确对位
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', src, '-af',
                    'silenceremove=start_periods=1:start_threshold=-45dB,areverse,'
                    'silenceremove=start_periods=1:start_threshold=-45dB,areverse',
                    '-ar', '48000', '-ac', '1', wav], check=True)


async def one(name, who, text):
    v = VOICES[who]
    mp3, wav = f'{OUT}/{name}.mp3', f'{OUT}/{name}.wav'
    if not os.path.exists(wav):
        if MM:
            audio = await asyncio.to_thread(minimax.tts, text, MM[who], v['speed'], EMOTION.get(name))
            open(mp3, 'wb').write(audio)
        else:
            import edge_tts
            await edge_tts.Communicate(text, v['voice'], rate=v['rate'], pitch=v['pitch']).save(mp3)
        to_wav(mp3, wav)
    d = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                       '-of', 'csv=p=0', wav]))
    return name, d


async def main():
    sem = asyncio.Semaphore(4)

    async def lim(*a):
        async with sem: return await one(*a)
    jobs = [lim(f"{s['id']}_{i}", who, text)
            for s in SHOTS for i, (who, text, *_) in enumerate(s.get('lines', []))]
    res = dict(await asyncio.gather(*jobs))
    json.dump(res, open('build/voice.json', 'w'), ensure_ascii=False, indent=1)
    print('provider:', 'minimax' if MM else 'edge-tts')
    for k, d in res.items():
        print(f'{k}\t{d:.2f}s')

asyncio.run(main())

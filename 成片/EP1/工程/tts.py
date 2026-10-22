"""生成全部台词配音：build/voice/<镜号>_<序号>.wav（48k 单声道），时长写入 build/voice.json。
音色优先级：TTS_PROVIDER=indextts（免费，HF Space 零样本克隆，voices_hf.json 里的参考音频）
        → Fish Audio 公共音色模型（FISH_API_KEY + voices_fish.json，音色=原角色克隆，s2.1-pro-free 为 $0）
        → MiniMax 设计音色 + 逐句情绪（MINIMAX_API_KEY + voices_minimax.json）
        → edge-tts（免费兜底）。
台词或音色变了要重配：删掉 build/voice/ 下对应 wav（或整个目录）再运行。"""
import asyncio, json, os, subprocess
import fish, minimax
from timeline import SHOTS, VOICES, EMOTION

OUT = 'build/voice'
os.makedirs(OUT, exist_ok=True)
MM = json.load(open('voices_minimax.json')) if minimax.key() and os.path.exists('voices_minimax.json') else None
FA = json.load(open('voices_fish.json')) if fish.key() and os.path.exists('voices_fish.json') else None
HF = json.load(open('voices_hf.json')) if os.environ.get('TTS_PROVIDER', '').lower() == 'indextts' else None
if HF:
    import indextts
    if not indextts.available():
        raise SystemExit('缺 gradio_client：pip install gradio_client（或 .venv/bin/pip install gradio_client）')


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
        if HF and who in HF:
            src = await asyncio.to_thread(indextts.clone, text, HF[who], EMOTION.get(name, ''))
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', src, mp3], check=True)
        elif FA and who in FA:
            audio = await asyncio.to_thread(fish.tts, fish.styled(text, EMOTION.get(name)),
                                            FA[who], v['speed'])
            open(mp3, 'wb').write(audio)
        elif MM:
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
    sem = asyncio.Semaphore(1 if HF else 4)

    async def lim(*a):
        async with sem: return await one(*a)
    jobs = [lim(f"{s['id']}_{i}", who, text)
            for s in SHOTS for i, (who, text, *_) in enumerate(s.get('lines', []))]
    res = dict(await asyncio.gather(*jobs))
    json.dump(res, open('build/voice.json', 'w'), ensure_ascii=False, indent=1)
    print('provider:', 'indextts(hf space)' if HF else 'fish' if FA else 'minimax' if MM else 'edge-tts')
    for k, d in res.items():
        print(f'{k}\t{d:.2f}s')

asyncio.run(main())

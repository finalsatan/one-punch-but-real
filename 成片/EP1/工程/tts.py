"""生成全部台词配音：build/voice/<镜号>_<序号>.wav（48k 单声道），时长写入 build/voice.json。"""
import asyncio, json, os, subprocess
import edge_tts
from timeline import SHOTS, VOICES

OUT = 'build/voice'
os.makedirs(OUT, exist_ok=True)


async def one(name, who, text):
    v = VOICES[who]
    mp3, wav = f'{OUT}/{name}.mp3', f'{OUT}/{name}.wav'
    if not os.path.exists(wav):
        await edge_tts.Communicate(text, v['voice'], rate=v['rate'], pitch=v['pitch']).save(mp3)
        # 去掉首尾静音，便于精确对位
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', mp3, '-af',
                        'silenceremove=start_periods=1:start_threshold=-45dB,areverse,'
                        'silenceremove=start_periods=1:start_threshold=-45dB,areverse',
                        '-ar', '48000', '-ac', '1', wav], check=True)
    d = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                       '-of', 'csv=p=0', wav]))
    return name, d


async def main():
    jobs = [one(f"{s['id']}_{i}", who, text)
            for s in SHOTS for i, (who, text, *_) in enumerate(s.get('lines', []))]
    res = dict(await asyncio.gather(*jobs))
    json.dump(res, open('build/voice.json', 'w'), ensure_ascii=False, indent=1)
    for k, d in res.items():
        print(f'{k}\t{d:.2f}s')

asyncio.run(main())

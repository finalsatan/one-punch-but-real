"""逐镜渲染动态画面 build/shots/<镜号>.mp4（1080×1920 30fps，无声无字），再按顺序拼接为 build/video.mp4。
单图先放大到 2160×3840 再做推拉摇移，避免 zoompan 低分辨率抖动；震屏在 1152×2048 中间画布上裁切实现。"""
import os, subprocess, sys
from timeline import IMG
from plan import plan, FPS

ROOT = '../../..'
os.makedirs('build/img', exist_ok=True)
os.makedirs('build/shots', exist_ok=True)
W, H = 2160, 3840           # 放大底图
MW, MH = 1152, 2048         # 中间画布（留震屏余量）
OX, OY = (MW - 1080) // 2, (MH - 1920) // 2


def run(cmd):
    subprocess.run(cmd, check=True)


def base_image(s):
    out = f"build/img/{s['id']}.png"
    if os.path.exists(out): return out
    if s['img'] is None:
        run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', f'color=black:s={W}x{H}', '-frames:v', '1', out])
        return out
    src = f"{ROOT}/" + IMG.format(s=s['img'][0], k=s['img'][1])
    vf = f'scale={W}:{H}:flags=lanczos'
    if s.get('dim'): vf += ',boxblur=24:2,eq=brightness=-0.28:saturation=0.7'
    run(['ffmpeg', '-loglevel', 'error', '-y', '-i', src, '-vf', vf, out])
    return out


def motion(s):
    """返回 zoompan 的 z/x/y 表达式。P 为 0→1 进度，E 为缓动。"""
    N = max(s['frames'] - 1, 1)
    P = f'(on/{N})'
    E = f'({P}*{P}*(3-2*{P}))'           # smoothstep
    EO = f'(1-(1-{P})*(1-{P}))'          # ease-out
    cx, cy = s.get('cx', .5), s.get('cy', .5)
    m = s['motion']
    xc = f"min(max({cx}*iw-iw/zoom/2,0),iw-iw/zoom)"
    yc = f"min(max({cy}*ih-ih/zoom/2,0),ih-ih/zoom)"
    if m == 'push':      return f'1+0.10*{E}', xc, yc
    if m == 'pushfast':  return f'1+0.22*{EO}', xc, yc
    if m == 'pull':      return f'1.16-0.16*{EO}', xc, yc
    if m == 'hold':      return f'1+0.035*{P}', xc, yc
    pz = '1.16'
    if m == 'panup':     return pz, '(iw-iw/zoom)/2', f'(ih-ih/zoom)*(1-{E})'
    if m == 'pandown':   return pz, '(iw-iw/zoom)/2', f'(ih-ih/zoom)*{E}'
    if m == 'panright':  return pz, f'(iw-iw/zoom)*{E}', '(ih-ih/zoom)/2'
    if m == 'panleft':   return pz, f'(iw-iw/zoom)*(1-{E})', '(ih-ih/zoom)/2'
    raise KeyError(m)


def shake_expr(s, axis):
    terms = []
    for t0, t1, a in s.get('shake', []):
        a = min(a, OX - 2)
        f1, f2 = (1.7, 2.9) if axis == 'x' else (2.3, 1.3)
        # 振幅随窗口内时间衰减
        terms.append(f"{a}*between(t,{t0},{t1})*(1-(t-{t0})/({t1}-{t0}+0.001))*(sin(n*{f1})+sin(n*{f2}))/2")
    return '+'.join(terms) or '0'


def render(s):
    out = f"build/shots/{s['id']}.mp4"
    img = base_image(s)
    z, x, y = motion(s)
    vf = [f"zoompan=z='{z}':x='{x}':y='{y}':d=1:s={MW}x{MH}:fps={FPS}"]
    if s.get('wobble'):
        vf.append("rotate='0.025*sin(2*PI*t*2.2)':fillcolor=white")
    vf.append(f"crop=1080:1920:'{OX}+{shake_expr(s, 'x')}':'{OY}+{shake_expr(s, 'y')}'")
    if s.get('flash_in'): vf.append(f"fade=t=in:st=0:d={s['flash_in']}:color=white")
    if s.get('flash_out'): vf.append(f"fade=t=out:st={s['len'] - s['flash_out']:.3f}:d={s['flash_out']}:color=white")
    vf.append('format=yuv420p')
    run(['ffmpeg', '-loglevel', 'error', '-y', '-loop', '1', '-framerate', str(FPS), '-i', img,
         '-vf', ','.join(vf), '-frames:v', str(s['frames']),
         '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-r', str(FPS), out])
    return out


def main():
    shots, total = plan()
    args = sys.argv[1:]
    concat_only = '--concat-only' in args
    only = [a for a in args if not a.startswith('--')]
    for s in shots:
        clip = f"build/shots/{s['id']}.mp4"
        # 镜头时长变了（帧数不符）或缺失时也要重渲
        stale = not os.path.exists(clip) or int(subprocess.check_output(
            ['ffprobe', '-v', 'error', '-count_packets', '-select_streams', 'v:0', '-show_entries',
             'stream=nb_read_packets', '-of', 'csv=p=0', clip])) != s['frames']
        if (only and s['id'] in only) or (not only and (stale or not concat_only)):
            render(s); print('ok', s['id'], f"{s['len']:.2f}s", flush=True)
    if only: return
    with open('build/concat.txt', 'w') as f:
        for s in shots: f.write(f"file 'shots/{s['id']}.mp4'\n")
    run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', 'build/concat.txt',
         '-c', 'copy', 'build/video.mp4'])
    print(f'video {total:.2f}s')


if __name__ == '__main__':
    main()

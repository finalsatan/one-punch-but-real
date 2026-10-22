"""零成本路线：Hugging Face Space「IndexTeam/IndexTTS-2-Demo」零样本克隆。

不注册任何付费服务也能出角色音：拿一段 8–15 秒该角色的参考音频（Fish 那个音色模型的试听 mp3 就能当参考），
IndexTTS-2 会照着这段音色说中文台词。

限制（实测 2026-10-22）：
- 匿名每 IP 只能跑 3 次，之后报 "You have exceeded your ZeroGPU runs limit"；
- 填一个免费 HF token（https://huggingface.co/settings/tokens）走每日免费 ZeroGPU 额度，够跑几十句；
- 只能串行（Space 单实例），别并发。
用法：pip install gradio_client（或 python3 -m venv .venv && .venv/bin/pip install gradio_client）
"""
import json, os

SPACE = 'IndexTeam/IndexTTS-2-Demo'
_client = None


def available():
    try:
        import gradio_client  # noqa: F401
        return True
    except ImportError:
        return False


def key():
    return os.environ.get('HF_TOKEN') or os.environ.get('HUGGINGFACE_TOKEN') or ''


def client():
    global _client
    if _client is None:
        from gradio_client import Client
        _client = Client(SPACE, token=key() or None, verbose=False)
    return _client


def clone(text, ref_audio, emotion=''):
    """用 ref_audio 的音色说 text，返回生成的 wav 临时文件路径。
    emotion 目前传了也不生效（Space 的情绪描述走另一个 tab），留参数位方便以后接。"""
    from gradio_client import handle_file
    kwargs = dict(emo_control_method='Same as the voice reference',
                  prompt=handle_file(ref_audio), text=text,
                  emo_ref_path=None, emo_weight=0.8,
                  vec1=0.0, vec2=0.0, vec3=0.0, vec4=0.0, vec5=0.0, vec6=0.0, vec7=0.0, vec8=0.0,
                  emo_text='', emo_random=False, max_text_tokens_per_segment=120,
                  param_16=True, param_17=0.8, param_18=30, param_19=0.8, param_20=0.0,
                  param_21=3, param_22=10.0, param_23=1500, api_name='/gen_single')
    r = client().predict(**kwargs)
    return r['value'] if isinstance(r, dict) else r

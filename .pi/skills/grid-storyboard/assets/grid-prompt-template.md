# 九宫格英文 Prompt 模板

> `<<...>>` 运行时替换。整段放进交付文件的 ```text 代码块，使用者可整段全选复制粘贴到生图工具。
> **不要**在此 prompt 内写「图1是什么角色」之类的参考图说明——参考图登记只出现在交付文件元信息段。
> **全项目只有一个风格串**：`Style:` 只写一行，取 `素材/画风/画风档位串.md` 唯一风格串原文，禁止拆成九行 `Style — Panel N:`。

---

## 骨架

```text
A single 3x3 grid storyboard, 9 equal panels, symmetrical hard-bordered grid, uniform thin gutters.
Aspect ratio: overall canvas <<9:16>>; the grid is evenly split 3x3, so each panel is also <<9:16>>. No inset hero panel, no irregular manga cut, no merged or skipped cells.
Through-line: <<场景2 前3秒钩子 — 龙卷用念力掀飞训练假人，假人却弹回原位站好，她当场愣住. Single scene, single moment in time inside a crossover boxing gym.>>
Location: <<场地锤定串，逐字取自 素材/场地/场地锚点表.md；一场跨两个空间则分格列出，如「Panel 1: <片头黑舞台串> | Panel 3-9: <拳馆串>」. This location is authoritative - do not add any furniture, equipment, matting or architectural feature that is not listed here.>>
Light: <<ceiling light from upper-left-front with a soft fill from the back-right, identical in all 9 panels>>

Consistency: identical face shape, hairstyle, hair color, eye color, outfit and body proportion for every character in all 9 panels; every character keeps exactly its own anchor body proportion and head-to-body ratio, nobody is re-proportioned towards a standard anime build and nobody is turned chibi; identical scene layout, identical color base, identical light direction across all 9 panels.

Characters:
<<Tatsumaki (One Punch Man): long curly green hair with two large ringlet curls, green eyes, dark green high-collar long dress with side slit, black gloves, black thigh-high boots, petite adult female build>>
<<gym training dummy: padded dark maroon leather humanoid torso on a metal base with a visible spring mount, no face>>

Style: <<唯一风格串，取 素材/画风/画风档位串.md 原文，逐字照抄>>

Panel 1: <<wide shot, front view — full gym interior, Tatsumaki standing before the training dummy, hands on hips>>
Panel 2: <<medium shot, side view — she raises one hand, telekinetic ripple spreading outward>>
Panel 3: <<medium shot over-the-shoulder — the dummy launched airborne past frame>>
Panel 4: <<close-up, front view — smug satisfied expression>>
Panel 5: <<wide shot, from behind — the dummy snapped back upright onto its base, perfectly still>>
Panel 6: <<extreme close-up, front view — pupils contracting, stunned>>
Panel 7: <<medium close-up, side view — a small girl wrapping her hands at the corner, unnoticed>>
Panel 8: <<medium shot, slight high angle — the little boy holding a toy gun, skeptical>>
Panel 9: <<medium shot, front view — the two of them locking eyes in awkward silence>>

No text, no speech bubbles, no captions, no panel numbers, no watermark, no signature. High detail.
Negative: no text, no letters, no captions, no subtitles, no speech bubbles, no panel numbering, no watermark, no signature, no irregular or unequal panels, no hero inset panel, no merged cells, no thick variant borders, no character redesign, no outfit change, no hairstyle change, no color shift between panels, no extra or missing limbs, no deformed hands, no duplicated characters, no inconsistent light direction, no scene change, no time-of-day change, no photorealistic or live-action rendering, no 3D render, no oversaturated colors, no CGI, no computer-generated look, no videogame cutscene look, no clay or plastic render, no ray-traced lighting, no global illumination, no ambient occlusion, no volumetric light shafts, no lens flare, no depth of field, no bokeh, no photographic blur, no specular PBR highlights, no metallic PBR shading, no subsurface scattering, no soft airbrush rendering on skin, no airbrushed gradient replacing line art, no missing or faded outlines, no 3D-looking background, no photoreal materials
```

---

## 填写规则

| 占位符 | 规则 |
|---|---|
| `<<比例>>` | 默认 `9:16`；**总图与单格必须写同一个值** |
| `Through-line` | 一句话，且**必须点名"单一场景 / 单一时间点"**，防止模型拼贴无关画面 |
| `Location` | **逐字**取 `素材/场地/场地锚点表.md` 对应场地的英文锚定串；**必填**。结尾一律附上 `This location is authoritative - do not add any furniture, equipment, matting or architectural feature that is not listed here.`。一场跨两个空间 → 按格区间分别列出（如 `Panel 1: <A> | Panel 3-9: <B>`）。**为什么必填**：场地参考图已撤离出图链路，空间锚点全靠这一行；漏写会让模型退回「拳击馆」先验（木地板 + 擂台 + 沙袋），与锚点表的蓝灰拼缝地垫冲突 |
| `Light` | 全局光位，9 格共用，不得出现第二种光位描述 |
| `Consistency:` | 逐项列出锁定属性，原文照抄；**必须含体型比例锁定语**（各角色保留自身原体型比例，禁止归一化 / chibi） |
| `Characters:` | 只列**出镜角色**的英文锚定串，一个角色一行 |
| `Style:` | **只写一行**，取 `素材/画风/画风档位串.md` 唯一风格串原文，逐字照抄；**禁止**拆成九行 `Style — Panel N:`、禁止自创/改写 |
| `Panel N:` | `<景别>, <角度> — <主体 + 动作 + 构图>`；禁止在 Panel 描述里写景别绑定词（如 "Panel 4 must be close-up"） |
| Negative | 原文照抄（含反 3D 负向词表），不增不删 |

## Negative 完整原文（照抄）

```
no text, no letters, no captions, no subtitles, no speech bubbles, no panel numbering, no watermark, no signature,
no irregular or unequal panels, no hero inset panel, no merged cells, no thick variant borders,
no character redesign, no outfit change, no hairstyle change, no color shift between panels,
no extra or missing limbs, no deformed hands, no duplicated characters,
no inconsistent light direction, no scene change, no time-of-day change,
no photorealistic or live-action rendering, no 3D render, no oversaturated colors,
no CGI, no computer-generated look, no videogame cutscene look, no clay or plastic render,
no ray-traced lighting, no global illumination, no ambient occlusion, no volumetric light shafts,
no lens flare, no depth of field, no bokeh, no photographic blur,
no specular PBR highlights, no metallic PBR shading, no subsurface scattering,
no soft airbrush rendering on skin, no airbrushed gradient replacing line art,
no missing or faded outlines, no 3D-looking background, no photoreal materials
```

> 反 3D 负向词表原文见 `素材/画风/画风档位串.md`「反 3D 负向词表」。三份模板共用同一段，逐字照抄。

## 禁止项

- ❌ **正向描述**里出现 `photorealistic` / `live-action` / `sequence photography` / `CGI` / `3D render` / `cel-shaded 3D`
  （例外：Negative 段中作为否定词的 `no photorealistic or live-action rendering`、反 3D 负向词表各项必须保留，不算违规）
- ❌ `8K`（改写 `High detail`）
- ❌ **第二个风格串** / 九行 `Style — Panel N:`（全项目只有一个风格档，只写一行 `Style:`）
- ❌ `Panel 4: close-up` 这类把景别绑死到镜号的写法
- ❌ prompt 内出现「图1是什么角色,图2是…」等参考图说明
- ❌ **漏写 `Location:` 行**，或只写「拳馆」之类泛称（模型会退回木地板 + 擂台 + 沙袋的通用健身房先验）
- ❌ 在 `Location:` 里自创锚定串（必须逐字取 `素材/场地/场地锚点表.md`）
- ❌ 中间大图 / 不规则分镜相关描述出现在正面段（只能在 Negative 里出现）

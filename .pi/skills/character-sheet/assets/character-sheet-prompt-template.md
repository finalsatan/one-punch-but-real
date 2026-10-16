# 角色三视图英文 Prompt 模板

> `<<...>>` 运行时替换。整段放进交付文件的 ```text 代码块，使用者可整段全选复制粘贴到生图工具（即梦 / Midjourney `--cref` / GPT / Nano Banana）。
> **不要**在此 prompt 内写参考图说明或文件路径——路径只出现在交付文件元信息段。
> **全项目只有一个风格串**：`Style:` 只写一行，取 `素材/画风/画风档位串.md` 唯一风格串原文，禁止拆成多段。

---

## 骨架

```text
A single character model sheet / turnaround reference sheet for exactly ONE character, <<角色中文名>> (<<IP>>), on a plain flat uniform light neutral gray background.

Layout: one landscape sheet, two rows of the same single character.
Top row: three full-body standing views of the same character, evenly spaced and drawn at the same scale — front view, side profile view facing left, and back view — all in the same relaxed neutral standing pose with arms slightly away from the body.
Bottom row: <<三种表情小样 / 或 无脸道具型角色的三格细节小样>>, evenly spaced at the same scale.
Generous even blank spacing between all figures. No drawn divider lines, no frames, no borders, no grid lines, no arrows, no labels.

Aspect ratio: overall sheet <<16:9>> landscape.

Consistency: identical face shape, hairstyle, hair color, eye color, outfit design, color scheme and body proportion across all figures; identical line weight and rendering across the whole sheet.

Character: <<英文锚定串>>
Expressions: <<中性 / 表情A / 表情B>>
Back-view design: <<背面视角的发型形状与服装设计显式声明>>
Prop: <<标志性道具；可选>>

Style: <<唯一风格串，取 素材/画风/画风档位串.md 原文，逐字照抄>>

Background: flat uniform light neutral gray, no scene, no environment, no floor line, no cast shadow gradient, no other characters, no animals, no furniture.

No text, no letters, no numbers, no labels, no annotations, no captions, no watermark, no signature. High detail.
Negative: no text, no letters, no numbers, no labels, no annotations, no arrows, no measurement lines, no color swatches, no captions, no watermark, no signature, no panel borders, no frames, no grid lines, no dividing lines, no manga panel layout, no storyboard, no second character, no extra or different characters, no character redesign, no outfit change between views, no hairstyle change between views, no color shift between views, no extra or missing limbs, no deformed hands, no cropped limbs in the full-body views, no scene background, no props besides the listed signature prop, no photorealistic or live-action rendering, no 3D render, no oversaturated colors, no CGI, no computer-generated look, no videogame cutscene look, no clay or plastic render, no ray-traced lighting, no global illumination, no ambient occlusion, no volumetric light shafts, no lens flare, no depth of field, no bokeh, no photographic blur, no specular PBR highlights, no metallic PBR shading, no subsurface scattering, no soft airbrush rendering on skin, no airbrushed gradient replacing line art, no missing or faded outlines, no 3D-looking background, no photoreal materials
```

### 无脸 / 道具型角色例外（如训练假人）

把 `Bottom row` 一行替换为：

```text
Bottom row: three detail studies of the same object — the torso front detail, the spring-mount base detail, and the same object tilted backward with the spring visibly compressed — evenly spaced at the same scale.
```

并**删掉** `Expressions:` 行。

---

## 填写规则

| 占位符 | 规则 |
|---|---|
| `<<角色中文名>>` `<<IP>>` | 中文名 + IP；与锚点表一致 |
| `<<比例>>` | 默认 `16:9` 横版；**只声明一次**，不与九宫格 9:16 混写 |
| `Top row` | 固定正 / 侧 / 背三视角全身，同比例同站姿；**不得改写视角数量或方向** |
| `Bottom row` | 默认 3 个表情小样；无脸 / 道具型角色换成 3 个细节小样 |
| `Consistency:` | 逐项列出锁定属性，原文照抄；**必须含体型比例锁定语** |
| `Character:` | 锚点表英文锚定串，逐字相同 |
| `Expressions:` | 3 个标志性表情；无脸角色删掉此行 |
| `Back-view design:` | 必须写；显式声明背面发型形状 + 服装设计 |
| `Prop:` | 只取锚点表登记的标志性道具；没有则写 `none beyond the character's own outfit` |
| `Style:` | 取 `素材/画风/画风档位串.md` **唯一风格串**原文，只写一行，逐字照抄 |
| `Negative` | 原文照抄（含反 3D 负向词表），不增不删 |
| `8K` | 禁止，只写 `high detail` |

## 禁止项

- ❌ **正向描述**里出现 `photorealistic` / `live-action` / `sequence photography` / `CGI` / `3D render` / `cel-shaded 3D`
  （例外：Negative 段中作为否定词的 `no photorealistic or live-action rendering`、反 3D 负向词表各项必须保留，不算违规）
- ❌ **第二段 prompt / 第二个风格串**（全项目只有一个风格档）
- ❌ `8K`
- ❌ 视角标签 `front view: ...` 之类画进画面的写法（只在 prompt 指令里描述视角即可）
- ❌ 多角色同图
- ❌ 场景背景 / 地面线 / 投影渐变
- ❌ 分格线 / 边框 / grid / storyboard 相关正面描述
- ❌ 参考图文件路径出现在 prompt 正文

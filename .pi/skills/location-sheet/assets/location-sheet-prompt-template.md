# 场地参考图英文 Prompt 模板

> `<<...>>` 运行时替换。每段单独放进交付文件的 ```text 代码块，使用者可整段全选复制粘贴到生图工具（即梦 / Midjourney / GPT / Nano Banana）。
> **不要**在此 prompt 内写参考图说明或文件路径——路径只出现在交付文件元信息段。

---

## 骨架 · 实景空间型（4 视图）

```text
A single location model sheet / environment reference sheet for exactly ONE empty location, <<场地中文名>> (<<英文名>>), with no characters anywhere.

Sheet background: flat uniform light neutral gray, visible only in the blank spacing between the views; the location itself keeps its own real materials, colors and lighting.

Layout: one landscape sheet, four views of the same single location.
Top row: three wide establishing views of the same space, evenly spaced and drawn at the same scale — main camera view, reverse 180-degree view, and side 90-degree view.
Bottom row: one top-down floor plan of the same space, centred, drawn at the same scale, showing the fixed layout and the light direction as a soft cast shadow.
Generous even blank spacing between all views. No drawn divider lines, no frames, no borders, no grid lines, no arrows, no labels, no dimension lines.

Aspect ratio: overall sheet <<16:9>> landscape.

Space: <<space + material 字段合成一句>>
Spatial lock: <<layout 字段：固定陈设位置关系，四视图逐件吻合>>
Fixed furnishings: <<props 字段>>
Light: <<light 字段；俯视图以阴影方向表达同一光位>>
Camera axis: <<轴线约定，如 the main view looks from the entrance side toward the far corner; the reverse view looks back from the far corner toward the entrance; the side view looks across the axis; the same axis is never crossed>>

Style: <<唯一风格串，取 素材/画风/画风档位串.md 原文，逐字照抄>>

No characters, no people, no human silhouettes, no crowd, no animals anywhere in any view.
No text, no letters, no numbers, no labels, no annotations, no captions, no watermark, no signature. High detail.
Negative: no text, no letters, no numbers, no labels, no annotations, no arrows, no dimension lines, no measurement lines, no captions, no watermark, no signature, no panel borders, no frames, no grid lines, no dividing lines, no manga panel layout, no storyboard, no characters, no people, no human silhouettes, no crowd, no animals, no layout change between views, no prop position change between views, no furniture moving between views, no color shift between views, no scene change, no time-of-day change, no interior redesign, no photorealistic or live-action rendering, no 3D render, no oversaturated colors, no CGI, no computer-generated look, no videogame cutscene look, no clay or plastic render, no ray-traced lighting, no global illumination, no ambient occlusion, no volumetric light shafts, no lens flare, no depth of field, no bokeh, no photographic blur, no specular PBR highlights, no metallic PBR shading, no subsurface scattering, no soft airbrush rendering, no airbrushed gradient replacing line art, no missing or faded outlines, no 3D-looking background, no photoreal materials
```

---

## 骨架 · 抽象舞台型（2 视图 · 例外）

与上面**仅两处不同**，其余逐字相同：

1. `four views` → `two views`
2. **整行删除** `Bottom row: one top-down floor plan ...` 那一行

```text
Layout: one landscape sheet, two views of the same single location.
Top row: two wide establishing views of the same space, evenly spaced and drawn at the same scale — main camera view and reverse 180-degree view.
Generous even blank spacing between all views. No drawn divider lines, no frames, no borders, no grid lines, no arrows, no labels, no dimension lines.
```

> 抽象舞台型**不出俯视布局图**：纯黑虚空没有地面也没有陈设，俯视图无信息量，且会诱导模型虚构出地面与墙体。

---

## 填写规则

| 占位符 | 规则 |
|---|---|
| `<<场地中文名>>` `<<英文名>>` | 中文名 + 英文名；与锚点表一致 |
| `<<比例>>` | 默认 `16:9` 横版；**只声明一次**，不与九宫格 9:16 混写 |
| `Layout` | 按 `type:` 取值；实景空间型 4 视图、抽象舞台型 2 视图；**不得改写机位数量或方向** |
| `Space:` | `space` + `material` 字段合成一句；`抽象舞台型` 只写 `space` |
| `Spatial lock:` | `layout` 字段展开；**四视图逐件吻合的关键抓手**；每一版都必须写 |
| `Fixed furnishings:` | `props` 字段；只列锚点表登记的陈设 |
| `Light:` | `light` 字段；必须注明俯视图以阴影方向表达同一光位 |
| `Camera axis:` | 轴线约定；`抽象舞台型` 写 `the main view and the reverse view look in opposite directions along the same axis; the axis is never crossed` |
| `Style:` | 取 `素材/画风/画风档位串.md` **唯一风格串**原文，只写一行，逐字照抄 |
| `Negative` | 原文照抄（含反 3D 负向词表），不增不删 |
| `8K` | 禁止，只写 `high detail` |

## 禁止项

- ❌ 画面内出现任何角色 / 人形剪影 / 群众 / 宠物
  - 例外：锚点表登记的**固定陈设**（训练假人、装备箱、书本等）可以出现
- ❌ **正向描述**里出现 `photorealistic` / `live-action` / `sequence photography`
  （例外：Negative 段中作为否定词的 `no photorealistic or live-action rendering`、反 3D 负向词表各项必须保留，不算违规）
- ❌ **第二段 prompt / 第二个风格串**（全项目只有一个风格档）
- ❌ `8K`
- ❌ 机位标签 `main view: ...` 之类画进画面的写法（只在 prompt 指令里描述机位即可）
- ❌ 分格线 / 边框 / grid / storyboard 相关正面描述
- ❌ 参考图文件路径出现在 prompt 正文
- ❌ 抽象舞台型写 `top-down floor plan`

# 切分算法与 PNG 约束（grid-split 参考）

> 本文件解释 `split_grid.mjs` 的**实现约束**与**白缝检测算法**，供排错与调参使用。
> 本技能**零 npm 依赖**，仅用 Node 内置 `fs` / `path` / `zlib`。

---

## 1 为什么自己写 PNG 编解码

项目 `image-gen` 明确「零 npm 依赖」，且当前环境无 `node_modules` / `package.json`。切分只需「解码 → 裁剪 → 编码」，PNG 的这一子集用 `zlib` + 手写滤波/CRC 即可覆盖，不引入 `sharp` 等原生依赖（还免去 Windows 编译）。

---

## 2 支持的 PNG 子集

| 维度 | 支持 | 不支持（明确 exit 3） |
|---|---|---|
| 格式 | PNG（magic `89 50 4E 47 0D 0A 1A 0A`） | JPEG / WebP / GIF / BMP 等 |
| bit depth | `8` | 16、1、2、4 |
| color type | `0` 灰度、`2` RGB、`3` 调色板、`4` 灰度+α、`6` RGBA | — |
| interlace | `0` 非隔行 | `1` Adam7 隔行 |
| 未知块 | 忽略（如 Chrome 写入的 `caBX` 私有块） | — |
| `tRNS` | 仅调色板 best-effort | 灰度/RGB 的 `tRNS` 透明键忽略 |

**实测**：本项目 `image-gen` 产出的九宫格为 `941x1672` / `1008x1792`，**colorType 2、bitDepth 8、interlace 0**，并带一个可忽略的 `caBX` 块 —— 落在支持范围内。

**归一化**：解码后统一为 RGB（无 α）或 RGBA（有 α）。输出 colorType 2（RGB）或 6（RGBA），bitDepth 8。裁剪不改颜色空间。

### 解码步骤

1. 遍历 chunk：读 `IHDR`、`PLTE`、`tRNS`，拼接所有 `IDAT`，忽略其余；`IEND` 结束
2. `zlib.inflateSync(IDAT)` 得到滤波后的扫描线流
3. 逐扫描线反滤波（Filter 0 None / 1 Sub / 2 Up / 3 Average / 4 Paeth），`bpp` = 每像素字节数
4. 按 colorType 展开为 RGB / RGBA 像素缓冲

### 编码步骤

1. 按裁切矩形逐行 `Buffer.copy` 抽取像素
2. 每条扫描线前置 filter 字节 `0`（None），拼接后 `zlib.deflateSync(level 9)`
3. 写 `IHDR` + `IDAT` + `IEND`（自实现 CRC32 与长度前缀）

**无损**：filter 0 不改变像素值，deflate 无损。输出逐字节可还原源图对应区域。

---

## 3 白缝 / 外描边检测（`auto-trim`）

### 3.1 判「缝」的准则

对某一**列**（统计其所有行的像素）或某一**行**（统计其所有列的像素）：

1. 每个 RGB 通道建 256 桶直方图，取 2% / 98% 分位
2. `spread_ch = p98_ch − p2_ch`（该通道的值域）
3. 判缝条件：

   - **近单色**：`max(spread_R, spread_G, spread_B) ≤ tolerance`（默认 12）
   - **近白**：`(mean_R + mean_G + mean_B) / 3 ≥ threshold`（默认 235）

用分位而非 min/max，是为了**抗噪**（单个亮点不会毁掉整列判定）。

### 3.2 只在期望边界附近找缝

内部竖线期望位置 `ex_k = round(W · k / cols)`，`k = 1..cols-1`。搜索窗口半宽 `win = max(8, round(W · 0.03))`（横向同理用 `H`）。

在 `[ex_k − win, ex_k + win]` 内找**连续缝列 run**：

- run 长度必须 `≤ maxGutter = max(6, round(W · 0.04))` —— 防止把面板内**大片白墙 / 白色背景格**误判为缝
- 取「中心离 `ex_k` 最近」的 run

命中 → 缝带 `[a, b]`，则左面板内容右边缘 = `a`（开区间）、右面板内容左边缘 = `b + 1`。
未命中任何合格 run → **回退** `leftEnd = rightStart = ex_k`（精确三等分），并记 warning。

### 3.3 外描边

左/上/右/下四条外边的**前缀 run**：从边缘起连续缝列/行的长度，要求 `≤ maxGutter`。
命中 → `leftTrim = run长度`（余同）；未命中 → `0`。

### 3.4 裁切矩形

面板 `(r, c)`（0-based），`colBands[i]` 对应边界 `k=i+1`（即 `c` 与 `c+1` 之间）：

```
x0 = c == 0        ? leftTrim            : colBands[c-1].rightStart
x1 = c == cols-1   ? W - rightTrim       : colBands[c].leftEnd
y0 = r == 0        ? topTrim             : rowBands[r-1].bottomStart
y1 = r == rows-1   ? H - bottomTrim      : rowBands[r].topEnd
```

任一 `w = x1 - x0 ≤ 0` 或 `h = y1 - y0 ≤ 0` → exit 3，提示改用 `--fixed` / `--trim-px`。

### 3.5 尺寸一致性告警

9 格尺寸互差超容差（`max(4, round(期望格尺寸 · 1%) )`）→ 记 warning「可能存在误检」，但仍产出。
**说明**：源图若本身就宽窄不均（实测 `EP1-场景1` 中间列比两侧宽 ~34px），检测是**正确**的，warning 只是提示；要等分请用 `--fixed`。

---

## 4 其他模式

| 模式 | 边界 | 外描边 |
|---|---|---|
| `--fixed` | `x0 = ex(c)`，`x1 = ex(c+1)`，`y` 同理 | 0 |
| `--trim-px N` | `x0 = ex(c) + N`，`x1 = ex(c+1) − N`，`y` 同理 | 每格四边均内缩 N |

其中 `ex(k) = round(W · k / cols)`，`ey(k) = round(H · k / rows)`。

仅 `--fixed` / `--trim-px` 会额外检查「源图是否为 `cols×rows` 整数倍」并 warning（因为这两种模式确实按 round 均分）；`auto-trim` 由检测结果决定，不做该检查。

---

## 5 性能

单张 ~1000×1800 的九宫格：解码 + 直方图统计 + 9 次裁剪编码，通常在**数秒内**完成（纯 Node 单线程）。无网络、无外部进程。

---

## 6 常见现象与处置

| 现象 | 原因 | 处置 |
|---|---|---|
| 某边界「未检出白缝，按精确三等分」 | 该处缝隙偏灰/带噪/不在窗口内 | 调 `--gutter-threshold`（降）/ `--gutter-tolerance`（升），或改 `--fixed` |
| 「9 格尺寸偏差较大」 | 源图格子本身宽窄不均，或误检 | 目视 dry-run 缝带；确认不均就用 `--fixed` |
| 「非整数倍，按 round 均分」 | 仅 `--fixed`/`--trim-px`；尺寸不能被行/列整除 | 正常，round 均分；要严格等分原始设计即如此 |
| exit 3「不是 PNG」 | 源图是 JPEG 等 | 用 image-gen 重出为 PNG，或先转码 |
| exit 3「不支持隔行 / bit depth 16」 | PNG 变体超出子集 | 另存为非隔行 8-bit PNG |
| exit 4「无法从 .md 定位源 PNG」 | 交付文件还没出图，或「出图状态」行缺失 | 先跑 image-gen；或直接传入 `.png` |

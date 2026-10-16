#!/usr/bin/env node
/**
 * grid-split :: split_grid.mjs
 *
 * 把 3×3 九宫格合成图切成 9 张等大单格图。
 * 自动识别并裁掉格间白缝 / 外描边；给 .md 交付文件时按 ② 分镜表镜号命名，
 * 并把「切分状态」回写到该交付文件。
 *
 * 零 npm 依赖，仅用 Node >= 18 内置能力（fs / path / zlib）。
 * 只处理 PNG；非 PNG / 隔行 / 16-bit 一律明确报错。
 *
 * 用法：
 *   node split_grid.mjs <交付文件.md | 九宫格.png> [选项]
 *
 * 完整参数见 `--help`。
 */

import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';

// ---------------------------------------------------------------- 常量

const EXIT_OK = 0;
const EXIT_USAGE = 2;
const EXIT_IMAGE = 3;
const EXIT_INPUT = 4;

const PNG_SIG = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

const CHANNELS_OF_COLOR_TYPE = { 0: 1, 2: 3, 3: 1, 4: 2, 6: 4 };

const HELP = `
grid-split :: 把 3×3 九宫格切成 9 张单格图

用法
  node split_grid.mjs <交付文件.md | 九宫格.png> [选项]

输入
  <.md 交付文件>       从「出图状态」行反查源 .png；读 ② 分镜表镜号做命名；可回写「切分状态」
  <.png 九宫格图>       直接切分；命名回退 panel-1.png … panel-9.png

输出
  --out-dir <dir>           输出目录（默认 <源图目录>/<源图去扩展名>/）
  --force                   允许覆盖已存在的输出（默认拒绝）
  --no-manifest             不写 index.json
  --no-writeback            不向 .md 回写「切分状态」

切分
  --fixed                   关闭自动裁缝，精确按 1/3 切（round(W·k/3)）
  --trim-px <n>             固定从每格四边内缩 n 像素（覆盖自动检测）
  --rows <n> --cols <n>     网格行列，默认 3 / 3

白缝检测
  --gutter-threshold <n>    「近白」亮度下限 0-255，默认 235
  --gutter-tolerance <n>    「近单色」通道极差上限，默认 12

诊断
  --dry-run                 只报告检测到的边界 / 9 个矩形 / 输出路径，不落盘
  --json                    机器可读输出
  -h, --help                显示本帮助

退出码
  0 成功 · 2 参数/解析错误 · 3 图像编解码错误（非 PNG / 隔行 / 16-bit）· 4 输入缺失或无法定位源图
`;

const OUT_DIR_NOTE = '默认 <源图目录>/<源图去扩展名>/';

// ---------------------------------------------------------------- 错误

class UsageError extends Error {
  constructor(message, { hint, exitCode = EXIT_USAGE } = {}) {
    super(message);
    this.name = 'UsageError';
    this.hint = hint;
    this.exitCode = exitCode;
  }
}

class ImageError extends Error {
  constructor(message, { hint, exitCode = EXIT_IMAGE } = {}) {
    super(message);
    this.name = 'ImageError';
    this.hint = hint;
    this.exitCode = exitCode;
  }
}

class InputError extends Error {
  constructor(message, { hint, exitCode = EXIT_INPUT } = {}) {
    super(message);
    this.name = 'InputError';
    this.hint = hint;
    this.exitCode = exitCode;
  }
}

const c = {
  dim: (s) => `\x1b[2m${s}\x1b[0m`,
  bold: (s) => `\x1b[1m${s}\x1b[0m`,
  red: (s) => `\x1b[31m${s}\x1b[0m`,
  yellow: (s) => `\x1b[33m${s}\x1b[0m`,
  green: (s) => `\x1b[32m${s}\x1b[0m`,
  cyan: (s) => `\x1b[36m${s}\x1b[0m`,
};

function fail(err) {
  const name = err?.constructor?.name;
  const prefix =
    name === 'UsageError'
      ? '参数错误'
      : name === 'InputError'
        ? '输入错误'
        : name === 'ImageError'
          ? '图像错误'
          : '错误';
  const exitCode =
    err?.exitCode ??
    (name === 'UsageError' ? EXIT_USAGE : name === 'InputError' ? EXIT_INPUT : EXIT_IMAGE);
  process.stderr.write(`${c.red('✗ ' + prefix + '：')}${err.message}\n`);
  if (err?.hint) process.stderr.write(`${c.dim('  提示：' + err.hint)}\n`);
  process.exitCode = exitCode;
  setTimeout(() => process.exit(exitCode), 150);
}

// ---------------------------------------------------------------- 小工具

function rel(p) {
  const r = path.relative(process.cwd(), p);
  return r && !r.startsWith('..') ? r.split(path.sep).join('/') : p;
}

function humanSize(bytes) {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)}MB`;
}

function timestamp() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

function pad2(n) {
  return String(n).padStart(2, '0');
}

// ---------------------------------------------------------------- 参数解析

const BOOL_FLAGS = new Set([
  '--help',
  '-h',
  '--force',
  '--fixed',
  '--no-manifest',
  '--no-writeback',
  '--dry-run',
  '--json',
]);
const VALUE_FLAGS = new Set([
  '--out-dir',
  '--trim-px',
  '--rows',
  '--cols',
  '--gutter-threshold',
  '--gutter-tolerance',
]);

function parseArgs(argv) {
  const opts = { positional: [] };
  for (let i = 0; i < argv.length; i++) {
    let arg = argv[i];
    let inlineValue = null;
    if (arg.startsWith('--') && arg.includes('=')) {
      const eq = arg.indexOf('=');
      inlineValue = arg.slice(eq + 1);
      arg = arg.slice(0, eq);
    }
    if (BOOL_FLAGS.has(arg)) {
      if (inlineValue !== null) throw new UsageError(`${arg} 不接受值`);
      opts[arg.replace(/^--?/, '').replace(/-/g, '_')] = true;
      continue;
    }
    if (VALUE_FLAGS.has(arg)) {
      let value = inlineValue;
      if (value === null) value = argv[++i];
      if (value === undefined) throw new UsageError(`${arg} 缺少值`);
      opts[arg.replace(/^--?/, '').replace(/-/g, '_')] = value;
      continue;
    }
    if (arg.startsWith('-')) throw new UsageError(`未知参数 ${arg}（用 --help 查看可用参数）`);
    opts.positional.push(arg);
  }
  return opts;
}

function parseIntOpt(raw, name, { min = 0, max = Infinity } = {}) {
  const n = Number(raw);
  if (!Number.isInteger(n) || n < min || n > max) {
    throw new UsageError(`${name} 只接受 ${min}..${max === Infinity ? '∞' : max} 的整数，收到 "${raw}"`);
  }
  return n;
}

// ---------------------------------------------------------------- markdown 解析

function stripMd(line) {
  return line.replace(/[`*_#>]/g, '');
}

function splitRow(line) {
  return line
    .trim()
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map((s) => s.trim());
}

function isSeparatorRow(line) {
  return /^\s*\|[\s:|-]+\|\s*$/.test(line);
}

function readLinesWithMeta(docPath) {
  const raw = fs.readFileSync(docPath, 'utf8');
  const bom = raw.charCodeAt(0) === 0xfeff;
  const body = bom ? raw.slice(1) : raw;
  const eol = /\r\n/.test(body) ? '\r\n' : '\n';
  return { lines: body.split(/\r?\n/), eol, bom };
}

/** 从「出图状态 / 生成状态」行反查源 .png 相对路径。 */
function extractSourceFromMd(lines) {
  for (const line of lines) {
    const m = /^\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$/.exec(line);
    if (!m) continue;
    if (!/^(出图状态|生成状态|图片路径)$/.test(stripMd(m[1]).trim())) continue;
    const value = m[2];
    const cands = [...value.matchAll(/([^\s`，,；;（）()【】\[\]|]+\.png)/gi)].map((x) => x[1].trim());
    const withDir = cands.find((p) => p.includes('/') || p.includes('\\'));
    if (withDir || cands[0]) return withDir || cands[0];
  }
  return null;
}

/** 抽取 ② 分镜表「镜号」列的标签序列。 */
function extractPanelLabels(lines) {
  let headerIdx = -1;
  let col = -1;
  for (let i = 0; i < lines.length; i++) {
    if (!/^\s*\|/.test(lines[i])) continue;
    if (!isSeparatorRow(lines[i + 1] || '')) continue;
    const cells = splitRow(lines[i]);
    const ci = cells.findIndex((x) => /镜号/.test(stripMd(x)));
    if (ci !== -1) {
      headerIdx = i;
      col = ci;
      break;
    }
  }
  if (headerIdx === -1) return [];
  const labels = [];
  for (let i = headerIdx + 2; i < lines.length; i++) {
    if (!/^\s*\|/.test(lines[i])) break;
    if (isSeparatorRow(lines[i])) continue;
    const cells = splitRow(lines[i]);
    const lab = stripMd(cells[col] ?? '').trim();
    if (lab) labels.push(lab);
  }
  return labels;
}

/**
 * 定位源 PNG：优先用 .md 里的声明路径，依次尝试
 * cwd 相对 / md 所在目录相对 / md 同目录同名 .png。
 */
function resolveSourcePng(declared, docPath) {
  const docDir = path.dirname(path.resolve(docPath));
  const tries = [];
  if (declared) {
    const norm = declared.split('\\').join('/');
    tries.push(path.resolve(process.cwd(), norm));
    tries.push(path.resolve(docDir, norm));
    tries.push(path.resolve(docDir, path.basename(norm)));
  }
  tries.push(path.resolve(docPath).replace(/\.md$/i, '.png'));
  for (const t of tries) {
    if (fs.existsSync(t) && fs.statSync(t).isFile()) return t;
  }
  return null;
}

// ---------------------------------------------------------------- PNG 解码

function readChunks(buf) {
  if (!buf.subarray(0, 8).equals(PNG_SIG)) {
    throw new ImageError('输入不是 PNG（文件头不匹配）', {
      hint: '本技能只处理 PNG。image-gen 默认输出 PNG；若是 JPEG，请先用 image-gen 重出为 png，或转码后重试。',
    });
  }
  const chunks = {};
  const idat = [];
  let off = 8;
  while (off + 8 <= buf.length) {
    const len = buf.readUInt32BE(off);
    const type = buf.toString('latin1', off + 4, off + 8);
    const dataStart = off + 8;
    const dataEnd = dataStart + len;
    if (dataEnd > buf.length) throw new ImageError(`PNG 块 ${type} 长度越界（文件损坏）`);
    if (type === 'IDAT') idat.push(buf.subarray(dataStart, dataEnd));
    else if (chunks[type] === undefined) chunks[type] = buf.subarray(dataStart, dataEnd);
    if (type === 'IEND') break;
    off = dataEnd + 4; // 跳过 CRC
  }
  return { chunks, idat: Buffer.concat(idat) };
}

function paeth(a, b, c) {
  const p = a + b - c;
  const pa = Math.abs(p - a);
  const pb = Math.abs(p - b);
  const pc = Math.abs(p - c);
  if (pa <= pb && pa <= pc) return a;
  if (pb <= pc) return b;
  return c;
}

function unfilter(raw, width, height, bpp) {
  const stride = width * bpp;
  const out = Buffer.alloc(height * stride);
  let pos = 0;
  for (let y = 0; y < height; y++) {
    if (pos >= raw.length) throw new ImageError('PNG 数据不足（解压结果与尺寸不符）');
    const ft = raw[pos++];
    const line = raw.subarray(pos, pos + stride);
    pos += stride;
    const cur = out.subarray(y * stride, (y + 1) * stride);
    const prev = y === 0 ? null : out.subarray((y - 1) * stride, y * stride);
    for (let i = 0; i < stride; i++) {
      const a = i >= bpp ? cur[i - bpp] : 0;
      const b = prev ? prev[i] : 0;
      const cUp = i >= bpp && prev ? prev[i - bpp] : 0;
      let v = line[i];
      switch (ft) {
        case 0:
          break;
        case 1:
          v = (v + a) & 0xff;
          break;
        case 2:
          v = (v + b) & 0xff;
          break;
        case 3:
          v = (v + ((a + b) >> 1)) & 0xff;
          break;
        case 4:
          v = (v + paeth(a, b, cUp)) & 0xff;
          break;
        default:
          throw new ImageError(`未知 PNG 滤波类型 ${ft}`);
      }
      cur[i] = v;
    }
  }
  return out;
}

/**
 * 解码 PNG 为归一化像素缓冲。
 * @returns {{width:number,height:number,channels:3|4,pixels:Buffer,colorType:number,bitDepth:number}}
 */
function decodePng(buf) {
  const { chunks, idat } = readChunks(buf);
  const ihdr = chunks.IHDR;
  if (!ihdr || ihdr.length < 13) throw new ImageError('PNG 缺少 IHDR');

  const width = ihdr.readUInt32BE(0);
  const height = ihdr.readUInt32BE(4);
  const bitDepth = ihdr[8];
  const colorType = ihdr[9];
  const interlace = ihdr[12];

  if (interlace !== 0) {
    throw new ImageError('不支持隔行扫描（Adam7）的 PNG', {
      hint: '用 image-gen 重出（非隔行）或先用图像工具另存为非隔行 PNG。',
    });
  }
  if (bitDepth !== 8) {
    throw new ImageError(`不支持 bit depth = ${bitDepth} 的 PNG（仅支持 8）`, {
      hint: '用 image-gen 重出（8-bit）或先转码为 8-bit PNG。',
    });
  }
  const bpp = CHANNELS_OF_COLOR_TYPE[colorType];
  if (bpp === undefined) throw new ImageError(`不支持的颜色类型 ${colorType}`);

  let raw;
  try {
    raw = zlib.inflateSync(idat);
  } catch (e) {
    throw new ImageError(`PNG IDAT 解压失败：${e.message}`);
  }

  const src = unfilter(raw, width, height, bpp);

  // 归一化：有 α → RGBA(4)，否则 RGB(3)
  const hasAlpha = colorType === 4 || colorType === 6;
  const channels = hasAlpha ? 4 : 3;
  const pixels = Buffer.alloc(width * height * channels);

  const palette = chunks.PLTE;
  for (let i = 0, p = 0; i < width * height; i++, p += channels) {
    const s = i * bpp;
    if (colorType === 2 || colorType === 6) {
      pixels[p] = src[s];
      pixels[p + 1] = src[s + 1];
      pixels[p + 2] = src[s + 2];
      if (hasAlpha) pixels[p + 3] = src[s + 3];
    } else if (colorType === 0 || colorType === 4) {
      pixels[p] = pixels[p + 1] = pixels[p + 2] = src[s];
      if (hasAlpha) pixels[p + 3] = src[s + 1];
    } else if (colorType === 3) {
      const idx = src[s];
      if (!palette || idx * 3 + 2 >= palette.length) throw new ImageError('调色板 PNG 的 PLTE 缺失或越界');
      pixels[p] = palette[idx * 3];
      pixels[p + 1] = palette[idx * 3 + 1];
      pixels[p + 2] = palette[idx * 3 + 2];
    }
  }

  return { width, height, channels, pixels, colorType, bitDepth };
}

// ---------------------------------------------------------------- PNG 编码

const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let ch = n;
    for (let k = 0; k < 8; k++) ch = ch & 1 ? 0xedb88320 ^ (ch >>> 1) : ch >>> 1;
    t[n] = ch >>> 0;
  }
  return t;
})();

function crc32(buf) {
  let ch = 0xffffffff;
  for (let i = 0; i < buf.length; i++) ch = CRC_TABLE[(ch ^ buf[i]) & 0xff] ^ (ch >>> 8);
  return (ch ^ 0xffffffff) >>> 0;
}

function pngChunk(type, data) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length, 0);
  const typeBuf = Buffer.from(type, 'latin1');
  const crcBuf = Buffer.alloc(4);
  crcBuf.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])), 0);
  return Buffer.concat([len, typeBuf, data, crcBuf]);
}

function encodePng(width, height, channels, pixels) {
  const stride = width * channels;
  const raw = Buffer.alloc((stride + 1) * height);
  for (let y = 0; y < height; y++) {
    raw[y * (stride + 1)] = 0; // filter 0 (None)
    pixels.copy(raw, y * (stride + 1) + 1, y * stride, y * stride + stride);
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8;
  ihdr[9] = channels === 4 ? 6 : 2;
  const idat = zlib.deflateSync(raw, { level: 9 });
  return Buffer.concat([
    PNG_SIG,
    pngChunk('IHDR', ihdr),
    pngChunk('IDAT', idat),
    pngChunk('IEND', Buffer.alloc(0)),
  ]);
}

function cropPixels(src, srcWidth, srcChannels, rect) {
  const { x, y, w, h } = rect;
  const out = Buffer.alloc(w * h * srcChannels);
  const rowBytes = w * srcChannels;
  for (let yy = 0; yy < h; yy++) {
    const srcStart = ((y + yy) * srcWidth + x) * srcChannels;
    src.pixels.copy(out, yy * rowBytes, srcStart, srcStart + rowBytes);
  }
  return out;
}

// ---------------------------------------------------------------- 白缝检测

/** 单通道 2% / 98% 分位与均值（基于 256 桶直方图）。 */
function columnStats(hist, total) {
  const p2 = Math.floor(total * 0.02);
  const p98 = Math.floor(total * 0.98);
  const out = [];
  for (let ch = 0; ch < 3; ch++) {
    const h = hist[ch];
    let acc = 0;
    let lo = 0;
    let hi = 255;
    let foundLo = false;
    for (let v = 0; v < 256; v++) {
      acc += h[v];
      if (!foundLo && acc > p2) {
        lo = v;
        foundLo = true;
      }
      if (acc > p98) {
        hi = v;
        break;
      }
    }
    let meanNum = 0;
    for (let v = 0; v < 256; v++) meanNum += v * h[v];
    out.push({ lo, hi, mean: total ? meanNum / total : 0 });
  }
  return out;
}

/**
 * 检测「缝」带（近白且近单色）。
 * @returns {{gutter: boolean[], stats: Array}}
 */
function detectGutters(pixels, width, height, channels, { threshold, tolerance }) {
  const perPixel = channels;
  // 列统计
  const colHist = Array.from({ length: width }, () => [new Uint32Array(256), new Uint32Array(256), new Uint32Array(256)]);
  const rowHist = Array.from({ length: height }, () => [new Uint32Array(256), new Uint32Array(256), new Uint32Array(256)]);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const p = (y * width + x) * perPixel;
      for (let ch = 0; ch < 3; ch++) {
        const v = pixels[p + ch];
        colHist[x][ch][v]++;
        rowHist[y][ch][v]++;
      }
    }
  }

  const judge = (stats) => {
    const spread = Math.max(...stats.map((s) => s.hi - s.lo));
    const brightness = (stats[0].mean + stats[1].mean + stats[2].mean) / 3;
    return spread <= tolerance && brightness >= threshold;
  };

  const gutterCols = new Uint8Array(width);
  for (let x = 0; x < width; x++) if (judge(columnStats(colHist[x], height))) gutterCols[x] = 1;
  const gutterRows = new Uint8Array(height);
  for (let y = 0; y < height; y++) if (judge(columnStats(rowHist[y], width))) gutterRows[y] = 1;

  return { gutterCols, gutterRows };
}

/** 在 [lo,hi] 内找连续 gutter run，取长度 <= maxLen 且中心离 expected 最近者。 */
function pickGutterRun(flags, expected, win, maxLen) {
  const lo = Math.max(0, expected - win);
  const hi = Math.min(flags.length - 1, expected + win);
  let best = null;
  let i = lo;
  while (i <= hi) {
    if (!flags[i]) {
      i++;
      continue;
    }
    const a = i;
    while (i + 1 <= hi && flags[i + 1]) i++;
    const b = i;
    const len = b - a + 1;
    i++;
    if (len > maxLen) continue; // 疑似面板内大片白区，不当作缝
    const center = (a + b) / 2;
    const dist = Math.abs(center - expected);
    if (!best || dist < best.dist || (dist === best.dist && len > best.len)) {
      best = { a, b, len, dist };
    }
  }
  return best;
}

/** 从 0 起的 gutter 前缀长度（用于外描边），超长则视为无。 */
function leadingGutterLen(flags, win, maxLen) {
  let len = 0;
  for (let i = 0; i < Math.min(flags.length, win + 1); i++) {
    if (!flags[i]) break;
    len++;
  }
  return len > 0 && len <= maxLen ? len : 0;
}

/**
 * 计算所有切分边界。
 * @returns {{colBands:Array|null,rowBands:Array|null,leftTrim,topTrim,rightTrim,bottomTrim,warnings:Array}}
 */
function computeBands(img, rows, cols, opts) {
  const { width: W, height: H } = img;
  const warnings = [];
  const mode = opts.fixed ? 'fixed' : opts.trim_px !== undefined ? 'trim-px' : 'auto-trim';

  const colExpected = (k) => Math.round((W * k) / cols);
  const rowExpected = (k) => Math.round((H * k) / rows);

  if (mode === 'fixed') {
    return { colBands: null, rowBands: null, leftTrim: 0, topTrim: 0, rightTrim: 0, bottomTrim: 0, warnings, mode };
  }
  if (mode === 'trim-px') {
    const n = opts.trim_px;
    return { colBands: null, rowBands: null, leftTrim: n, topTrim: n, rightTrim: n, bottomTrim: n, warnings, mode };
  }

  const winX = Math.max(8, Math.round(W * 0.03));
  const winY = Math.max(8, Math.round(H * 0.03));
  const maxGutterX = Math.max(6, Math.round(W * 0.04));
  const maxGutterY = Math.max(6, Math.round(H * 0.04));

  const { gutterCols, gutterRows } = detectGutters(img.pixels, W, H, img.channels, {
    threshold: opts.gutter_threshold,
    tolerance: opts.gutter_tolerance,
  });

  const colBands = [];
  for (let k = 1; k < cols; k++) {
    const run = pickGutterRun(gutterCols, colExpected(k), winX, maxGutterX);
    if (run) {
      colBands.push({ k, leftEnd: run.a, rightStart: run.b + 1, a: run.a, b: run.b, found: true });
    } else {
      const ex = colExpected(k);
      colBands.push({ k, leftEnd: ex, rightStart: ex, a: null, b: null, found: false });
      warnings.push(`竖边界 ${k} 未检出白缝，已按精确三等分（x=${ex}）`);
    }
  }
  const rowBands = [];
  for (let k = 1; k < rows; k++) {
    const run = pickGutterRun(gutterRows, rowExpected(k), winY, maxGutterY);
    if (run) {
      rowBands.push({ k, topEnd: run.a, bottomStart: run.b + 1, a: run.a, b: run.b, found: true });
    } else {
      const ey = rowExpected(k);
      rowBands.push({ k, topEnd: ey, bottomStart: ey, a: null, b: null, found: false });
      warnings.push(`横边界 ${k} 未检出白缝，已按精确三等分（y=${ey}）`);
    }
  }

  const leftTrim = leadingGutterLen(gutterCols, winX, maxGutterX);
  const topTrim = leadingGutterLen(gutterRows, winY, maxGutterY);
  const rightTrim = leadingGutterLen([...gutterCols].reverse(), winX, maxGutterX);
  const bottomTrim = leadingGutterLen([...gutterRows].reverse(), winY, maxGutterY);

  return { colBands, rowBands, leftTrim, topTrim, rightTrim, bottomTrim, warnings, mode };
}

function rectsFor(img, rows, cols, bands) {
  const { width: W, height: H } = img;
  const ex = (k) => Math.round((W * k) / cols);
  const ey = (k) => Math.round((H * k) / rows);
  const rects = [];
  for (let r = 0; r < rows; r++) {
    for (let col = 0; col < cols; col++) {
      let x0;
      let x1;
      let y0;
      let y1;
      if (bands.mode === 'fixed') {
        x0 = ex(col);
        x1 = ex(col + 1);
        y0 = ey(r);
        y1 = ey(r + 1);
      } else if (bands.mode === 'trim-px') {
        const n = bands.leftTrim; // 每格四边内缩 n
        x0 = ex(col) + n;
        x1 = ex(col + 1) - n;
        y0 = ey(r) + n;
        y1 = ey(r + 1) - n;
      } else {
        // colBands[i] 对应边界 k=i+1（i 为 0..cols-2），即 col 与 col+1 之间
        x0 = col === 0 ? bands.leftTrim : bands.colBands[col - 1].rightStart;
        x1 = col === cols - 1 ? W - bands.rightTrim : bands.colBands[col].leftEnd;
        y0 = r === 0 ? bands.topTrim : bands.rowBands[r - 1].bottomStart;
        y1 = r === rows - 1 ? H - bands.bottomTrim : bands.rowBands[r].topEnd;
      }
      const w = x1 - x0;
      const h = y1 - y0;
      if (w <= 0 || h <= 0) {
        throw new ImageError(`第 ${r * cols + col + 1} 格裁切矩形非法（w=${w}, h=${h}）`, {
          hint: '可能是白缝检测误判；用 --fixed 或 --trim-px <n> 强制切分再核对。',
        });
      }
      rects.push({ index: r * cols + col + 1, row: r, col, x: x0, y: y0, w, h });
    }
  }
  return rects;
}

// ---------------------------------------------------------------- 输出

function atomicWrite(target, buf) {
  fs.mkdirSync(path.dirname(target), { recursive: true });
  const tmp = `${target}.part`;
  fs.writeFileSync(tmp, buf);
  fs.renameSync(tmp, target);
}

function assertNotExists(targets, force) {
  if (force) return;
  const existing = targets.filter((t) => fs.existsSync(t));
  if (existing.length) {
    throw new UsageError(`输出已存在，拒绝覆盖：\n    ${existing.map(rel).join('\n    ')}`, {
      hint: '确认要重切就加 --force，或先移走旧产物。',
    });
  }
}

// ---------------------------------------------------------------- 回写

function updateTableRow(lines, keyRe, newValue) {
  for (let i = 0; i < lines.length; i++) {
    const m = /^\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$/.exec(lines[i]);
    if (!m) continue;
    if (!keyRe.test(stripMd(m[1]).trim())) continue;
    lines[i] = `| ${m[1].trim()} | ${newValue} |`;
    return { line: i + 1, inserted: false };
  }
  return null;
}

function insertTableRow(lines, afterRe, newLine) {
  let last = -1;
  for (let i = 0; i < lines.length; i++) {
    const m = /^\s*\|\s*(.*?)\s*\|/.exec(lines[i]);
    if (m && afterRe.test(stripMd(m[1]).trim())) last = i;
  }
  if (last === -1) return null;
  lines.splice(last + 1, 0, newLine);
  return { line: last + 2, inserted: true };
}

function writeBack(ctx, result, opts) {
  if (!ctx || opts.no_writeback || opts.dry_run) return null;
  const value = `已切分 · ${rel(result.outDir)}/ · ${result.panels.length} 张 · ${timestamp()}`;
  const lines = [...ctx.lines];
  let applied = updateTableRow(lines, /^(切分状态)$/, value);
  if (!applied) {
    applied = insertTableRow(lines, /^(出图状态|生成状态|需同批上传的参考图|参考图)/, `| 切分状态 | ${value} |`);
  }
  if (!applied) return null;
  const text = (ctx.bom ? '\ufeff' : '') + lines.join(ctx.eol);
  fs.writeFileSync(ctx.docPath, text, 'utf8');
  return { line: applied.line, inserted: applied.inserted, value };
}

// ---------------------------------------------------------------- 主流程

function fileType(buf) {
  if (buf.subarray(0, 8).equals(PNG_SIG)) return 'png';
  if (buf.length >= 3 && buf[0] === 0xff && buf[1] === 0xd8) return 'jpeg';
  if (buf.length >= 12 && buf.toString('latin1', 0, 4) === 'RIFF' && buf.toString('latin1', 8, 12) === 'WEBP') return 'webp';
  if (buf.length >= 6 && /^GIF8[79]a$/.test(buf.toString('latin1', 0, 6))) return 'gif';
  return 'unknown';
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) {
    process.stdout.write(HELP);
    return;
  }

  // --- 参数
  if (opts.fixed && opts.trim_px !== undefined) {
    throw new UsageError('--fixed 与 --trim-px 互斥');
  }
  const rows = opts.rows === undefined ? 3 : parseIntOpt(opts.rows, '--rows', { min: 1, max: 20 });
  const cols = opts.cols === undefined ? 3 : parseIntOpt(opts.cols, '--cols', { min: 1, max: 20 });
  const trimPx = opts.trim_px === undefined ? undefined : parseIntOpt(opts.trim_px, '--trim-px', { min: 1, max: 500 });
  const threshold = opts.gutter_threshold === undefined ? 235 : parseIntOpt(opts.gutter_threshold, '--gutter-threshold', { min: 0, max: 255 });
  const tolerance = opts.gutter_tolerance === undefined ? 12 : parseIntOpt(opts.gutter_tolerance, '--gutter-tolerance', { min: 0, max: 255 });

  const positional = opts.positional;
  if (positional.length !== 1) {
    process.stdout.write(HELP);
    throw new UsageError(`需要且仅需 1 个输入（.md 交付文件或 .png 九宫格图），收到 ${positional.length} 个`);
  }

  // --- 输入解析
  const inputPath = path.resolve(positional[0]);
  if (!fs.existsSync(inputPath)) throw new InputError(`输入不存在：${positional[0]}`);

  let sourcePng;
  let ctx = null;
  let docPath = null;
  if (/\.md$/i.test(inputPath)) {
    docPath = inputPath;
    const { lines, eol, bom } = readLinesWithMeta(docPath);
    ctx = { docPath, lines, eol, bom };
    const declared = extractSourceFromMd(lines);
    sourcePng = resolveSourcePng(declared, docPath);
    if (!sourcePng) {
      throw new InputError(`无法从 ${path.basename(docPath)} 定位源 PNG`, {
        hint: `先跑 image-gen 出图（出图状态行会写回实际 .png 路径），或直接传入 .png。声明值：${declared ?? '(无)'}`,
      });
    }
  } else {
    sourcePng = inputPath;
  }

  // --- 读图 + 校验格式
  const buf = fs.readFileSync(sourcePng);
  const ft = fileType(buf);
  if (ft !== 'png') {
    throw new ImageError(`输入不是 PNG（检测为 ${ft}）`, {
      hint: '本技能只处理 PNG。用 image-gen 重出（默认 PNG）或先转码为 PNG。',
    });
  }

  const img = decodePng(buf);

  // --- 计算切分
  const bands = computeBands(img, rows, cols, { fixed: opts.fixed, trim_px: trimPx, gutter_threshold: threshold, gutter_tolerance: tolerance });
  const rects = rectsFor(img, rows, cols, bands);
  const warnings = [...bands.warnings];

  // 仅在按 round 均分的模式（fixed / trim-px）下才关心整除性；auto-trim 由检测结果决定
  if (bands.mode !== 'auto-trim') {
    const remX = Math.abs((img.width / cols) - Math.round(img.width / cols));
    const remY = Math.abs((img.height / rows) - Math.round(img.height / rows));
    if (remX > 0.01 || remY > 0.01) {
      warnings.push(`源图 ${img.width}x${img.height} 非 ${cols}×${rows} 的整数倍，按 round 均分`);
    }
  }

  // 尺寸一致性：与预期格尺寸的偏差超阈值才算疑似误检（容忍真实白缝粗细不均造成的差异）
  const ws = rects.map((r) => r.w);
  const hs = rects.map((r) => r.h);
  const tolW = Math.max(4, Math.round(img.width / cols / 100));
  const tolH = Math.max(4, Math.round(img.height / rows / 100));
  const spreadW = Math.max(...ws) - Math.min(...ws);
  const spreadH = Math.max(...hs) - Math.min(...hs);
  if (spreadW > tolW || spreadH > tolH) {
    warnings.push(`9 格尺寸偏差较大（w ${Math.min(...ws)}..${Math.max(...ws)}，h ${Math.min(...hs)}..${Math.max(...hs)}；容差 w≤${tolW}/h≤${tolH}），可能存在误检`);
  }

  // --- 标签
  let labels = [];
  if (ctx) labels = extractPanelLabels(ctx.lines);
  if (labels.length && labels.length < rects.length) {
    warnings.push(`② 表镜号只有 ${labels.length} 个，不足的格回退 panel-N`);
  }

  // --- 输出路径
  const srcDir = path.dirname(sourcePng);
  const srcBase = path.basename(sourcePng).replace(/\.png$/i, '');
  const outDir = opts.out_dir ? path.resolve(opts.out_dir) : path.join(srcDir, srcBase);

  const panels = rects.map((rect) => {
    const label = labels[rect.index - 1] || `panel-${rect.index}`;
    const file = `${label}.png`;
    return { ...rect, label, file, outPath: path.join(outDir, file) };
  });

  const manifestPath = path.join(outDir, 'index.json');
  const plannedTargets = panels.map((p) => p.outPath);
  if (!opts.no_manifest) plannedTargets.push(manifestPath);

  // --- dry-run
  if (opts.dry_run) {
    const report = {
      mode: 'dry-run',
      input: rel(inputPath),
      source: rel(sourcePng),
      sourceInfo: { format: 'png', width: img.width, height: img.height, colorType: img.colorType, bitDepth: img.bitDepth },
      grid: { rows, cols },
      cutMode: bands.mode,
      trim: { left: bands.leftTrim, top: bands.topTrim, right: bands.rightTrim, bottom: bands.bottomTrim },
      cutLines: {
        x: bands.colBands ? bands.colBands.map((b) => (b.found ? `${b.a}..${b.b}` : `${b.leftEnd}`)) : [],
        y: bands.rowBands ? bands.rowBands.map((b) => (b.found ? `${b.a}..${b.b}` : `${b.topEnd}`)) : [],
      },
      outDir: rel(outDir),
      writeback: !!ctx && !opts.no_writeback,
      outputs: panels.map((p) => ({ index: p.index, label: p.label, file: p.file, rect: { x: p.x, y: p.y, w: p.w, h: p.h } })),
      wouldOverwrite: plannedTargets.filter((t) => fs.existsSync(t)).map(rel),
      warnings,
    };
    if (opts.json) process.stdout.write(JSON.stringify(report, null, 2) + '\n');
    else printDryRun(report);
    return;
  }

  // --- 防覆盖
  assertNotExists(plannedTargets, opts.force);

  // --- 切分 + 落盘
  const results = [];
  for (const p of panels) {
    const pixels = cropPixels(img, img.width, img.channels, { x: p.x, y: p.y, w: p.w, h: p.h });
    const out = encodePng(p.w, p.h, img.channels, pixels);
    atomicWrite(p.outPath, out);
    results.push({ ...p, bytes: out.length });
  }

  // --- manifest
  let manifestWritten = null;
  if (!opts.no_manifest) {
    const manifest = {
      source: rel(sourcePng),
      sourceInfo: { format: 'png', width: img.width, height: img.height, colorType: img.colorType, bitDepth: img.bitDepth },
      grid: { rows, cols },
      mode: bands.mode,
      trim: { left: bands.leftTrim, top: bands.topTrim, right: bands.rightTrim, bottom: bands.bottomTrim },
      cutLines: {
        x: bands.colBands ? bands.colBands.map((b) => (b.found ? [b.a, b.b] : [b.leftEnd, b.leftEnd])) : [],
        y: bands.rowBands ? bands.rowBands.map((b) => (b.found ? [b.a, b.b] : [b.topEnd, b.topEnd])) : [],
      },
      warnings,
      panels: results.map((r) => ({
        index: r.index,
        row: r.row,
        col: r.col,
        label: r.label,
        file: r.file,
        rect: { x: r.x, y: r.y, w: r.w, h: r.h },
      })),
    };
    atomicWrite(manifestPath, Buffer.from(JSON.stringify(manifest, null, 2) + '\n', 'utf8'));
    manifestWritten = manifestPath;
  }

  // --- 回写
  const result = { outDir, panels: results };
  let writeback = null;
  try {
    writeback = writeBack(ctx, result, opts);
  } catch (e) {
    warnings.push(`回写失败（图片已保存）：${e.message}`);
  }

  // --- 报告
  const report = {
    mode: 'split',
    status: 'ok',
    input: rel(inputPath),
    source: rel(sourcePng),
    sourceInfo: { format: 'png', width: img.width, height: img.height, colorType: img.colorType, bitDepth: img.bitDepth },
    grid: { rows, cols },
    cutMode: bands.mode,
    trim: { left: bands.leftTrim, top: bands.topTrim, right: bands.rightTrim, bottom: bands.bottomTrim },
    outDir: rel(outDir),
    manifest: manifestWritten ? rel(manifestWritten) : null,
    writeback: writeback ? { doc: rel(docPath), line: writeback.line, inserted: writeback.inserted } : null,
    outputs: results.map((r) => ({ index: r.index, label: r.label, path: rel(r.outPath), bytes: r.bytes, dimensions: `${r.w}x${r.h}` })),
    warnings,
  };

  if (opts.json) process.stdout.write(JSON.stringify(report, null, 2) + '\n');
  else printReport(report, results);
}

function printDryRun(r) {
  const w = (k, v) => process.stdout.write(`  ${c.dim(k.padEnd(14))}${v}\n`);
  process.stdout.write(`${c.bold('DRY RUN')} ${c.dim('（未写入任何文件）')}\n`);
  w('输入', r.input);
  w('源图', `${r.source} ${c.dim(`${r.sourceInfo.width}x${r.sourceInfo.height} colorType=${r.sourceInfo.colorType}`)}`);
  w('网格', `${r.grid.rows}×${r.grid.cols}`);
  w('切分模式', r.cutMode);
  w('外描边裁切', `left ${r.trim.left} · top ${r.trim.top} · right ${r.trim.right} · bottom ${r.trim.bottom}`);
  if (r.cutLines.x.length) w('竖缝带', r.cutLines.x.map((s) => `x=${s}`).join('  '));
  if (r.cutLines.y.length) w('横缝带', r.cutLines.y.map((s) => `y=${s}`).join('  '));
  w('输出目录', r.outDir + '/');
  for (const o of r.outputs) {
    process.stdout.write(
      `      ${c.cyan(pad2(o.index))} ${o.label.padEnd(10)} ${c.dim(`${o.rect.w}x${o.rect.h} @(${o.rect.x},${o.rect.y})`)} → ${o.file}\n`,
    );
  }
  w('回写', r.writeback ? '是' : '否');
  if (r.wouldOverwrite.length) w('会覆盖', c.yellow(r.wouldOverwrite.join(', ') + '（正式运行时默认拒绝，需 --force）'));
  for (const warn of r.warnings) process.stderr.write(`${c.yellow('⚠')} ${warn}\n`);
}

function printReport(r, results) {
  process.stdout.write(`${c.green('✓ 切分成功')}\n`);
  const w = (k, v) => process.stdout.write(`  ${c.dim(k.padEnd(12))}${v}\n`);
  w('源图', `${r.source} ${c.dim(`${r.sourceInfo.width}x${r.sourceInfo.height}`)}`);
  w('网格', `${r.grid.rows}×${r.grid.cols} · ${r.cutMode}`);
  w('外描边', `left ${r.trim.left} · top ${r.trim.top} · right ${r.trim.right} · bottom ${r.trim.bottom}`);
  for (const o of results) {
    process.stdout.write(`  ${c.green('→')} ${rel(o.outPath)} ${c.dim(`${o.w}x${o.h} ${humanSize(o.bytes)}`)}\n`);
  }
  if (r.manifest) w('清单', r.manifest);
  if (r.writeback) w('回写', `${r.writeback.doc} 第 ${r.writeback.line} 行${r.writeback.inserted ? '（新增）' : ''}`);
  else w('回写', '未执行');
  for (const warn of r.warnings) process.stderr.write(`${c.yellow('⚠')} ${warn}\n`);
}

main().catch(fail);

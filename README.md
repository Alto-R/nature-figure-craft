<div align="center">

# nature-figure-craft 📐

**把科研配图拆成两件事：该画哪种图，和怎么把它画成能过投稿的图。**

两个可直接安装的 Claude Code skill，外加三个能独立使用的绘图模块。

![Skills](https://img.shields.io/badge/skills-2-4C72B0)
![Python](https://img.shields.io/badge/python-3.9%2B-3C5488)
![matplotlib](https://img.shields.io/badge/matplotlib-%E2%89%A53.5-0B75B3)
![R](https://img.shields.io/badge/R-circlize-982B2D)
![License](https://img.shields.io/badge/license-CC--BY--4.0-00A087)
![Status](https://img.shields.io/badge/status-v0.1%20初版-DDAA33)

**[中文](README.md)** | **[English](README-EN.md)**

</div>

---

## 🙋 关于

我是 [Churui Huang](https://alto-r.github.io/)，北京大学在读研究生，我的研究兴趣位于能源与交通系统 · 能源地理 · 城市计算 · 优化 · 人工智能的交叉领域。

这个库是我自己投稿过程中反复踩坑之后攒出来的：里面的配色、版式规则、地图图层顺序、象限图分界线的定法、面板分开画再拼版的流程，基本都来自实际写论文时画过的图。

**会持续更新。** 每写一篇新论文、画一批新图，就会把新踩到的坑和新总结出来的规则补进去——尤其是 `palettes.md` 这类示例库，会随着后面的图慢慢变厚。

目前是 **v0.1 初版**，欢迎提 issue 指出不对的地方。

---

<div align="center">

| | | |
|:--:|:--:|:--:|
| [🧭 这是什么](#-这是什么) | [⚖️ 两个 skill 的分工](#-两个-skill-的分工) | [🚀 安装](#-安装) |
| [🗂️ 目录结构](#-目录结构) | [🎨 配色示例库](#-配色示例库) | [🧩 直接用样式模块](#-直接用样式模块) |
| [💡 核心观点](#-核心观点) | [📄 License](#-license) | |

</div>

---

## 🧭 这是什么

大多数不好的图，问题不在**画得糙**，而在**选错了图**——一张排版精美的分组柱状图，如果数据本来是时间序列，那它依然是错的。所以这里把配图拆成前后两步，各做成一个 skill：

- **`chart-type-chooser`** —— 写任何绘图代码之前用。先给数据做画像，再问"这张图要让读者记住哪一句话"，然后回 2–3 个候选图型、被否掉的方案和理由、编码方案，以及一遍反模式检查。覆盖九类表达意图下约 70 种图型。
- **`nature-figure-production`** —— 图型定了之后用。按 Nature 系期刊的终稿规格（88/180 mm 栏宽、落版字号、可编辑矢量、RGB、50 MB 上限）和 house style 出图，含地图、象限图、弦图三类"自带几何"的图族配方，以及面板分开画、图例单独导出、最后矢量拼版的生产流程。

两者都不替你做学术判断：它们负责的是**把判断稳定地落到纸面上**这一段。

## ⚖️ 两个 skill 的分工

| | `chart-type-chooser` | `nature-figure-production` |
|---|---|---|
| **回答** | 画哪种图 | 怎么画成发表水平 |
| **输入** | 一句想让读者记住的话 + 数据结构 | 已确定的图型 + 数据 |
| **输出** | 2–3 个候选图型 + 理由 + 被否方案 + 编码方案 | 尺寸、样式代码、导出产物、投稿审查报告 |
| **何时用** | 写任何绘图代码**之前** | 确定图型**之后** |

> 标准顺序：`chart-type-chooser` → `nature-figure-production`。

## 🚀 安装

复制到 Claude Code 的 skills 目录：

```bash
git clone https://github.com/Alto-R/nature-figure-craft.git
cd nature-figure-craft
cp -r chart-type-chooser        ~/.claude/skills/
cp -r nature-figure-production  ~/.claude/skills/
```

Windows：

```bat
xcopy /E /I chart-type-chooser        %USERPROFILE%\.claude\skills\chart-type-chooser
xcopy /E /I nature-figure-production  %USERPROFILE%\.claude\skills\nature-figure-production
```

装好之后正常提需求即可，比如"帮我画一下这组数据"或"这张图看着不像论文里的图"，skill 会自己被触发。

## 🗂️ 目录结构

```
nature-figure-craft/
│
├── chart-type-chooser/                 # skill 1：选图
│   ├── SKILL.md
│   ├── references/
│   │   ├── catalog.md                  # 九大意图 × ~70 种图型
│   │   ├── decision-rules.md           # 数据结构门控、编码通道排序、平局裁决
│   │   └── antipatterns.md             # 症状 → 病因 → 处方
│   └── assets/
│       └── profile_data.py             # 数据画像：列类型、分组规模、构成集、开放/已定决策点
│
└── nature-figure-production/           # skill 2：画图
    ├── SKILL.md
    ├── references/
    │   ├── spec.md                     # 终稿硬规格（88/180 mm、落版字号、矢量、50 MB）
    │   ├── style.md                    # 版式、单位写法、配色规则、colormap 选择
    │   ├── palettes.md                 # 配色示例库（见下）
    │   ├── composition.md              # 十个多面板构图模板
    │   ├── quadrant.md                 # 象限图：分界线怎么定、命名、图层、边际、图例
    │   ├── maps.md                     # 地图面板：图层栈、basemap 预设、点 vs 多边形
    │   └── workflow.md                 # 面板分离生产流程 + 投稿前审查清单
    └── assets/
        ├── nature_style.py             # panel() / apply_style() / landed_report() / save_all()
        │                               #   + 全部配色常量、diverging_cmap()、palette_report()
        ├── nature_map.py               # 地图五层：basemap / 多边形 / 密度场 / 值点 / 边际剖面
        ├── nature_quadrant.py          # 象限图：阈值推导 / 分区背景 / 气泡 / inset / 示意图图例
        └── nature_chord.R              # 弦图（circlize）：透明度编码流量、矢量导出、可选分组
```

三个 asset 自带 self-test（合成数据），直接跑就出 demo 图：

```bash
python nature_style.py      # demo 样式图 + 配色体检报告
python nature_quadrant.py   # demo_quadrant.png / _legend.png / _2x2.png
Rscript nature_chord.R      # demo_chord_ungrouped.* / _grouped.* / _legend.pdf
```

> `nature_map.py` 没有 self-test —— 它需要 cartopy 和真实经纬度，造不出有意义的合成样例。

## 🎨 配色示例库

`references/palettes.md` 是一份**可以直接抄**的配色方案集，每一条都写清楚它干什么用、为什么成立，并且全部作为常量从 `nature_style.py` 导出：

| 类型 | 常量 | 用在哪 |
|---|---|---|
| 发散 | `DIVERGING`（13 级）、`DIVERGING_WARM`、`DIVERGING_GAP` | 有符号量、异常值、残差、与基准的差 |
| 顺序 | `SEQ_BLUE` / `SEQ_GREEN` / `SEQ_RED` / `SEQ_TEAL` | 一个物理量一个色相；teal 专门留给"第二个配色图层" |
| 有序分类 | `CLASSES6`、`SCENARIO` | 排了序的类别，让颜色本身编码等级 |
| 定性 | `NPG` / `AAAS` / `NEJM` / `JAMA` | 无序类别，一篇论文只用一套 |
| 语义 | 成本、技术、车型等示例字典 | 一个物理量一个颜色，全文固定 |
| 2×2 | `TWO_FACTOR` | 两个二值因子相交：色相编码一个，明度编码另一个 |
| 分区 | `REGION_FILL` / `REGION_MARK` | 象限图的背景填充与其上的点，成对给出 |

配的每一组都带 CIE L\* 实测值，不是"看着还行"：

```python
from nature_style import DIVERGING, diverging_cmap, CLASSES6, palette_report

cmap = diverging_cmap()                          # 中性色钉在 0.5，而不是默认的 0.583
palette_report(CLASSES6, ordered=True)           # 灰度下哪两级会撞在一起，直接报出来
```

## 🧩 直接用样式模块

不装 skill 也能用，把 `nature_style.py` 拷进项目即可：

```bash
cp nature-figure-production/assets/nature_style.py  your_project/figures/
cd your_project/figures && python nature_style.py     # self-test，生成 demo 图
```

```python
from nature_style import panel, apply_style, landed_report, save_all, clean_axes, panel_letter

p = panel(placed_mm=60, aspect=0.8)      # 这个面板最终占 60 mm，而不是"画多大"
apply_style(p)
fig, ax = plt.subplots(figsize=p.figsize)
...
clean_axes(ax)
panel_letter(ax, 'a')
landed_report(fig, p)                    # 导出前先量一遍落版字号
save_all('fig1_a_timeseries', fig)       # 同时写出 pdf/ svg/ png/
```

这里最要紧的一条：**字号要按"落到版面上是多大"来定，而不是按脚本里画多大来定**。真实主图是十几到二十几个面板拼出来的，每个面板落版宽度都不一样，所以没有一个统一的 `figsize` 可用；不变的是那条算式——`landed_pt = drawn_pt × (placed_mm / drawn_mm)`。`panel()` 负责算，`landed_report()` 负责验。

## 💡 核心观点

**外观**
> 硬规格先钉死 → 把不重要的东西压成灰 → 主角只留 1–2 个饱和色 → 敢删（标题 / 边框 / 网格 / 图例框 / 重复轴标签）→ 但删完要回头补一遍：参考线、单位、n、色带、地图图层 —— 图有两种死法，"太乱"和"太空"，后者过得了检查表，过不了读者。

**选图**
> 先写下"这张图要让读者记住的那一句话"。写不出来，就别画这张图。

## 📄 License

[CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

---

<div align="center">
<sub>规范来自各期刊公开的 artwork guideline；具体取舍是一家之言，不代表任何期刊的官方立场。</sub>
</div>

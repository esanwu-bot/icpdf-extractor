# Phase 1.1 诊断报告：真实 Datasheet 验收与坐标链审计

**日期:** 2026-11-05
**结论:** Phase 1 **未通过最终验收**；Phase 2（LLM/DashScope）继续冻结。
本轮只做诊断，没有再改检测算法（除进入诊断前已加的硬门槛）。不通过的原因不是“样例少”，而是真实 PDF 上 **Table Detector 过检严重、header/table_type 识别近乎失效**。

---

## 1. 坐标链审计（实测，不靠文档推断）

### 1.1 实测结论（PyMuPDF 2.0）

对同一段 `MARKER` 文本（写入坐标 `(100,100)`）在 4 个 `/Rotate` 下实测：

| rotation | `page.rect` | `get_text` span bbox |
|---|---|---|
| 0 | `(0,0,612,792)` | `(100.0, 87.1, 151.34, 103.59)` |
| 90 | `(0,0,792,612)` | 同上（**未旋转**） |
| 180 | `(0,0,612,792)` | 同上（**未旋转**） |
| 270 | `(0,0,792,612)` | 同上（**未旋转**） |

结论：`Page.get_text()` 返回的是**未旋转 PDF 用户坐标**，`page.rect` 是裁剪+旋转后的显示坐标。CropBox 偏移也不会自动扣除：

```text
CropBox=(50,50,562,742), page.rect=(0,0,512,692)
span bbox=(100.0, 87.1, 134.67, 103.59)   # 仍是未旋转绝对坐标
```

### 1.2 代码修复位置

| 文件 | 处理 |
|---|---|
| `src/icpdf/parser/coords.py` | `to_display_bbox()`：先减 CropBox 原点，再按 rotation 旋转进 `page.rect`，最后 clamp；0/90/180/270 全覆盖 |
| `src/icpdf/parser/text_blocks.py` | 每个 span/word 先 `geometry.to_display_bbox(raw_bbox)`，再进入 table/candidate 链 |
| `src/icpdf/parser/page_renderer.py` | PyMuPDF 2.0 的 `get_pixmap(dpi=...)` 只接受整数；统一 `int(round(dpi))`，几何仍记录 float dpi |
| `table_detector.py` / `table_rebuilder.py` / `candidate_registry.py` | 全部消费 `page.rect` 显示坐标，无第二套坐标空间 |

### 1.3 新增测试与结果

`tests/integration/test_coordinate_chain.py`：

- rotation=0/90/180/270 的 bbox 期望值逐项断言（误差 ≤1 pt）；
- CropBox 非零偏移；
- CropBox + 90° 旋转；
- MediaBox/CropBox 不同的几何记录；
- 原生文本 bbox → PNG 像素位置 → 反向 bbox（≤0.5 pt）；
- 渲染图裁剪：候选 bbox 像素区域必须含墨水（`getextrema()[0] < 200`）；
- effective config + `parser_config_sha256` 写入 manifest。

```text
python -m pytest -q
48 passed
```

---

## 2. Table 全量统计

| 型号 | 页数 | Table 总数 | 每页最多/中位 | reconstructed | partial | unresolved | unknown type | Candidate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LM358 | 68 | 412 | 26 / 5 | 73 | 107 | 232 | 410 / 412 | 6,510 |
| ADS1299 | 84 | 391 | 16 / 5 | 105 | 90 | 196 | 389 / 391 | 4,050 |
| ADC12DJ5200 | 180 | 891 | 17 / 6 | 232 | 265 | 394 | 889 / 891 | 10,386 |

表规模：

| 型号 | 行数中位/最大 | 列数中位/最大 |
|---|---|---|
| LM358 | 1 / 43 | 4 / 22 |
| ADS1299 | 1 / 23 | 5 / 22 |
| ADC12DJ5200 | 1 / 47 | 5 / 22 |

**“行数中位=1”是过检的直接信号**：大量单行文本片段被当成独立 Table。

明细：`docs/phase1_1/<型号>/table_stats.csv`、`page_stats.csv`。

---

## 3. unknown/unresolved 细分原因（诊断分类）

分类函数在 `tools/phase11_audit.py::_diagnose`，只做诊断、不改解析判定：

| 型号 | not_a_table | row_structure_uncertain | merged_cell_uncertain | column_structure_uncertain | table_boundary_uncertain | 干净 |
|---|---:|---:|---:|---:|---:|---:|
| LM358 | 236 | 50 | 52 | 0 | 1 | 73 |
| ADS1299 | 199 | 54 | 32 | 1 | 0 | 105 |
| ADC12DJ5200 | 413 | 175 | 71 | 0 | 0 | 232 |

`not_a_table` 判定依据：`unresolved` + 行数<2 或存在 >80 字符的长文本单元格。它不代表所有 `unresolved` 都无价值，但**绝大多数是正文、修订记录、引脚片段或目录行**。

---

## 4. 人工审计：每型号 20 个 Candidate

抽样规则：reconstructed 6 + partial 6 + unresolved 8（不只看成功案例）。
每个候选均记录 page / table_id / row_id / cell_id / candidate_id / raw_text /
column_role / bbox / 状态 / 诊断原因 / 定位判定。

| 型号 | 抽样 | bbox 在页内 | bbox 覆盖墨水 | 非 unknown 列角色 | 人工可确认角色正确 |
|---|---:|---:|---:|---:|---:|
| LM358 | 20 | 20/20 | 20/20 | 2/20 | 0/2 |
| ADS1299 | 20 | 20/20 | 20/20 | 0/20 | 0/0 |
| ADC12DJ5200 | 20 | 20/20 | 20/20 | 4/20 | 1/4 |

**定位准确率：60/60（100%）** —— 前提是“bbox 覆盖正确墨水区域”。
**行/列归属准确率：无法确认 54/60；6/60 有非 unknown 角色，其中仅 1/6 可确认正确**（ADC 的 `28` 判为 `value`）。列角色识别依赖 header，而 header 在真实 PDF 上基本没识别出来。

典型失败样例：

| 型号 | 位置 | 内容 | 问题 |
|---|---|---|---|
| LM358 | p001-t14 | `Gain bandwidth product` | 单行特性条目被当成 Table |
| LM358 | p035-t03 | `Yes` | 表格单元格被拆成独立 Table |
| LM358 | p038-t03 | `Production` | 同左，状态列碎片 |
| LM358 | p001-t02 | `brushless DC, high-voltage, lo…` | 正文被当成 Table（not_a_table） |
| ADS1299 | p001-t03 | `PART NUMBER` | 表头/正文碎片，merged_cell_uncertain |
| ADS1299 | p001-t01 | `Multiple` | 正文，not_a_table |
| ADC12DJ5200 | p002-t01 | `5.4 Thermal Information.......` | 目录行（点引导线）被当成 Table |
| ADC12DJ5200 | p001-t01 | `1 Features` | 章节标题被当成 Table |
| ADC12DJ5200 | p004-t01 | `DA0+` | 引脚列表碎片，not_a_table |
| ADC12DJ5200 | p016-t08 | `A IN = –9 dBFS per tone` | 测试条件正文，partial |

证据文件：

- `docs/phase1_1/<型号>/audit_candidates.csv`（含 `verdict` / `note`）
- `docs/phase1_1/<型号>/contact_sheet.png`（20 个裁剪 + 状态 + 诊断原因）
- `docs/phase1_1/<型号>/pages/page-XXXX-annotated.png`（蓝=Table、绿=Row、红=Candidate、标签含 Table/Candidate/role/reason）

---

## 5. 指标

> 下表中的 precision 为**抽样/启发式估计**，不是逐表人工真值；报告明确标注，避免把估计当事实。

| 指标 | LM358 | ADS1299 | ADC12DJ5200 | 说明 |
|---|---:|---:|---:|---|
| Table Detection Precision（严格：仅 reconstructed） | 17.7% | 26.9% | 26.0% | 73/412、105/391、232/891 |
| Precision 上限（排除 not_a_table） | 42.7% | 49.1% | 53.6% | 仍含 partial 误检 |
| Candidate 定位准确率（抽样 20） | 100% | 100% | 100% | bbox 在页内且覆盖墨水 |
| 行/列归属可确认率（抽样 20） | 2/20 | 0/20 | 4/20 | 依赖 header 识别 |
| 行/列归属准确率（可确认样本） | 0/2 | — | 1/4 | 样本极小，不可外推 |
| table_type 覆盖率 | 2/412 (0.5%) | 2/391 (0.5%) | 2/891 (0.2%) | unknown 占绝对多数 |
| table_type 准确率 | 不可测 | 不可测 | 不可测 | 已知类型仅 2 个/型号，未逐个人工确认 |
| unresolved 占比 | 56.3% | 50.1% | 44.2% | — |
| partial 占比 | 26.0% | 23.0% | 29.7% | — |

---

## 6. 误检归因与优化优先级

### P0 — Table Detector（必须优先）

1. **边界/起止判定失效**：正文、目录、章节标题、修订记录被当成 Table；大量单行 Table。
   - 证据：行数中位=1；`not_a_table` 236/199/413。
2. **header 识别失效**：真实表格多为多行表头（单位、条件、MIN/TYP/MAX 跨行），当前只认首行关键词，导致 `column_role` 大面积 unknown。
3. **目录行/点引导线**：`5.4 Thermal Information.......` 这类行必须排除。
4. **同页多表与相邻片段**：状态列 `Yes` / `Production` 被拆成独立 Table，需合并/拒绝。

### P1 — Layout 特征

- 两栏正文、图注（`Figure 5-41 ...`）、引脚列表、Revision History 需要显式排除或单独类型。
- 点引导线、章节编号、TOC 行需要专门规则。

### P2 — Table Rebuilder

- 多行表头、合并单元格、跨页续表；当前把跨页拆成独立 Table（页绑定正确但逻辑连续未做）。
- Row 没有独立 bbox 字段（当前由 cells 求并集），后续考虑显式 row bbox。

### P3 — 检测阈值

- 8pt 列间隙、2.5× 行距、±2 列容差不是主因；`cell_gap_pt=8` 在双栏正文仍会切开。**先把边界/标题/表头判对，再调阈值**。

---

## 7. 已知限制（本轮明确不解决）

1. 没有 OCR；无文本层页面候选为 0。
2. 没有 vector-line 表格重建（仅文本对齐）。
3. 没有跨页续表合并。
4. table_type 仍是启发式；真实 PDF 上覆盖率 <1%。
5. 未接 LLM/DashScope，未新增自动参数生成能力。

---

## 8. 实际执行命令与产物

```bash
python -m pytest -q                       # 48 passed
python tools/phase11_audit.py --pdf <real.pdf> --mpn <MPN> \
       --out docs/phase1_1/<MPN> --sample 20
```

产物：

- `docs/PHASE1_1_DIAGNOSIS.md`（本报告）
- `docs/phase1_1/LM358/`：`table_stats.csv`、`page_stats.csv`、`audit_candidates.csv`、`contact_sheet.png`、`pages/*-annotated.png`
- `docs/phase1_1/ADS1299/`：同上
- `docs/phase1_1/ADC12DJ5200/`：同上
- 原始运行工件：`runs/phase11_audit/<run_id>/`（document/tables/candidates/pages/run_manifest）

---

## 9. 评审建议

**不建议进入 Phase 2。** 先解决 Table Detector 的边界与 header 问题：

1. 单行/正文/目录/图注/引脚列表显式排除；
2. 多行 header 识别 + 列角色映射；
3. 同页多表的合并与边界置信；
4. 用 3 个真实型号逐表人工标注 30–50 张表作为 gold table set，再谈 precision/recall。

在这些完成前接入 LLM，只会把“错误表格 + 错误列角色”放大成“错误参数”。

# paper-methods-writer

**methods-experiments-writer**：来源可追溯的论文「方法与实验」章节写作 Skill。

本仓库是玻尔产品赛「写作09｜方法与实验章节写作」（challenge `product-arena-05-64faa4a2`）的参赛 Skill。Skill 可被 Agent 加载调用，把散落的实验材料（论文、代码、配置、日志、数据说明）整理成**写得全、写得准、做得着、说得住**的方法与实验章节，并同步交付证据映射与缺口清单。

## 核心思路

从材料抽取要素 → 构建证据映射 → 对齐正文 → 发现缺口并显式追问：

1. **证据映射驱动**：先按六类要素清单（方法步骤、实验设置、参数与来源、数据集与划分、对照实验、可复现性与限制）从材料中抽取事实并登记来源，正文只能引用已登记的事实；
2. **可追溯性校验**：脚本反向扫描正文数值，凡找不到来源且未标注 `〔待确认〕` 的数值即判失败，封闭"先写后凑"的漏洞；
3. **四态标注**：每条要素分为 confirmed / inferred / conflict / missing，冲突与缺失一律显式化并列入追问清单，不沉默取舍、不补造数据；
4. **诚实降级**：任何一步失败时保存当前产物并将运行状态记为 `partial`，说明卡点，不伪造完成。

## 目录结构

```
SKILL.md                     # Skill 本体（name/description frontmatter + 工作流）
docs/USAGE.md                # 使用与方法说明（依赖、调用步骤、限制、失败处理）
references/                  # 六类要素抽取清单、写作规范（含负面失败模式）
templates/                   # 章节骨架、证据映射 JSON 模板、缺口报告模板
scripts/                     # 三个仅依赖标准库的 Python 脚本（Python >= 3.8）
  collect_inputs.py          #   盘点输入材料，生成带 SHA-256 的 inventory.json
  check_traceability.py      #   校验正文数值均可追溯到证据映射
  make_result.py             #   按案例 output_contract 组装并校验 result.json
examples/minimal-example.md  # 最小调用示例（虚构输入，示意输出已标注为示例）
```

## 快速开始

```bash
# 1. 盘点材料
python scripts/collect_inputs.py --input /input --work /app/work

# 2. 阅读材料，按 references/extraction-checklist.md 填写
#    /app/work/evidence_map.json 与 /app/work/draft.md（人工或 Agent）

# 3. 可追溯性校验，迭代至退出码 0
python scripts/check_traceability.py --draft /app/work/draft.md \
    --evidence /app/work/evidence_map.json

# 4. 组装最终输出（result.json 必含 case_id 与 output_contract 全部字段）
python scripts/make_result.py --case /input/case.json --output-dir /app/output \
    --draft /app/output/methods_experiments_section.md \
    --evidence /app/output/evidence_map.json \
    --gaps /app/output/gap_report.md --status success
```

完整说明见 [docs/USAGE.md](docs/USAGE.md)。

## 依赖与边界

- Python ≥ 3.8，仅标准库；可选 pandoc / LaTeX 用于导出草稿 PDF 预览；
- 数值追溯校验基于字面与数值等价匹配，不识别"数值正确但语义错位"，该核对依赖阅读环节（详见 USAGE.md 的限制一节）；
- 资源约束：全部为 UTF-8 文本文件，无符号链接，符合赛题 Skill 资源限制（≤50 文件、单文件 ≤500KB、总量 ≤2MB）。

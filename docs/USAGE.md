# 使用与方法说明：methods-experiments-writer

## 用途与适用场景

依据论文、代码、配置、日志、数据说明等材料，生成或核对**来源可追溯**的方法与实验章节。适用：竞赛案例的章节撰写 / 补全 / 修改任务；日常科研写作中把实验记录整理成论文方法节。

不适用：结果与讨论章节撰写、纯文献综述、无材料依据的自由写作——这些场景不会触发本 Skill。

## 依赖

- Python ≥ 3.8（仅标准库，无需安装第三方包）；
- 可选：pandoc / LaTeX / office-renderer（仅用于导出草稿 PDF 预览，缺失时跳过并说明）。

## 输入与输出

| 项 | 路径 | 说明 |
|-|-|-|
| 案例输入 | `/input/case.json`、`/input/task.md` | 含 `case_id`、任务要求、材料路径、`output_contract` |
| 中间产物 | `/app/work/` | `inventory.json`、`evidence_map.json`、`draft.md`、校验报告 |
| 最终产物 | `/app/output/` | 章节草稿（.md）、`evidence_map.json`、`gap_report.md`、`result.json`（必含 `case_id` 与 `output_contract` 全部字段） |

## 调用步骤（Agent 或人工均可照做）

1. 读取 `/input/case.json` 与 `/input/task.md`；
2. `python scripts/collect_inputs.py --input /input --work /app/work` 盘点材料；
3. 按 `references/extraction-checklist.md` 抽取六类要素，填 `evidence_map.json`（结构见 `templates/evidence-map.schema.json`）；
4. 按 `templates/section-skeleton.md` 与 `references/writing-conventions.md` 起草 `draft.md`，数值带 `〔来源: …〕`，缺失写 `〔待确认: …〕`；
5. `python scripts/check_traceability.py --draft … --evidence …` 迭代至退出码 0；
6. 填 `templates/gap-report.md` 生成 `gap_report.md`；
7. `python scripts/make_result.py --case /input/case.json --output-dir /app/output --draft … --evidence … --gaps … --status success|partial|failed`。

脚本路径以 Skill 安装目录（评测时为 `/skills/weekly-skill`）为基准解析，不依赖进程工作目录。

## 关键方法

- **证据映射驱动**：先抽取后写作，正文只能引用已登记的事实；校验脚本反向扫描正文数值，封闭"先写后凑"的漏洞；
- **状态机标注**：每条要素四态（confirmed / inferred / conflict / missing），冲突与缺失一律显式化，不沉默取舍；
- **诚实降级**：任何一步失败时保存当前产物并将状态记为 `partial`，说明卡点，不伪造完成。

## 限制

- 数值追溯校验基于字面与数值等价匹配，不能识别"数值正确但语义错位"（如把验证集比例安到测试集上），该核对依赖第 1 步的人工/模型阅读；
- 不做 PDF 语义解析，PDF 内容的读取质量取决于环境提供的 pdf-text / render / OCR 工具；
- `output_contract` 形态未知时 `make_result.py` 采用字段名启发式填充，无法推断的字段以占位符标出，需人工确认。

## 失败处理与自查

- 脚本均返回非零退出码表示失败：`collect_inputs.py`=2（输入目录缺失）；`check_traceability.py`=1（有无来源数值）/2（文件错误）；`make_result.py`=1（产物缺失或 case 无效）/2（参数错误）；
- 提交前对照 `SKILL.md` 末尾"完成前自查"清单逐项确认。

## 维护信息

- 版本：1.0.0（2026-11）；资源清单见 `SKILL.md` 与各子目录，全部为 UTF-8 文本，无符号链接；
- 需人工确认项：正文中全部 `〔待确认〕` 标注与 `gap_report.md` 的 A/B/C/D 四节。

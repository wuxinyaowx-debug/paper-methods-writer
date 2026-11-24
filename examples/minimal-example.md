# 最小调用示例（示例，非正式案例结果）

> 本文件仅说明接口与流程，输入为虚构的微型材料，输出为示意，**不是**平台正式案例的运行结果。

## 示例输入（虚构）

`/input/case.json`（节选）：

```json
{
  "case_id": "demo-001",
  "output_contract": {"fields": ["case_id", "status", "draft", "evidence_map", "gap_report"]}
}
```

`/input/materials/config.yaml`（虚构）：

```yaml
optimizer: {name: adamw, lr: 0.0003, weight_decay: 0.01}
training: {batch_size: 32, epochs: 50, seed: 42}
```

`/input/materials/train.log`（虚构）首行：`[2025-03-01] seed=42 lr=3e-4 batch_size=32 epochs=50 gpu=A100x1 torch=2.1.0`

## 调用方式

```bash
python scripts/collect_inputs.py --input /input --work /app/work
# → 人工/模型阅读材料，填写 /app/work/evidence_map.json 与 /app/work/draft.md
python scripts/check_traceability.py --draft /app/work/draft.md --evidence /app/work/evidence_map.json
python scripts/make_result.py --case /input/case.json --output-dir /app/output \
    --draft /app/output/methods_experiments_section.md \
    --evidence /app/output/evidence_map.json \
    --gaps /app/output/gap_report.md --status partial \
    --notes "数据集版本未在材料中给出，已标注待确认"
```

## 示意输出（示例）

草稿片段（`/app/output/methods_experiments_section.md`）：

```markdown
**训练**：实验在 1 张 NVIDIA A100 上进行〔来源: train.log, 第 1 行〕，框架为
PyTorch 2.1.0〔来源: train.log, 第 1 行〕。采用 AdamW 优化器，学习率 3e-4、
权重衰减 0.01〔来源: config.yaml, optimizer 节〕，batch size 为 32，训练 50
个 epoch，随机种子固定为 42〔来源: config.yaml, training 节；train.log, 第 1 行〕。
数据集版本〔待确认: 材料未给出数据集版本，影响结果可比性〕。
```

校验脚本输出：

```text
可追溯数值: 7
已标注待确认/来源但无映射（警告）: 0
无来源且未标注（失败）: 0
```

`result.json`（节选）：

```json
{
  "case_id": "demo-001",
  "status": "partial",
  "draft": "/app/output/methods_experiments_section.md",
  "evidence_map": "/app/output/evidence_map.json",
  "gap_report": "/app/output/gap_report.md",
  "summary": "数据集版本未在材料中给出，已标注待确认"
}
```

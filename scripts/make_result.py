#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按案例 output_contract 组装并校验 /app/output/result.json。

用法:
    python scripts/make_result.py --case /input/case.json --output-dir /app/output \
        --draft /app/output/methods_experiments_section.md \
        --evidence /app/output/evidence_map.json \
        --gaps /app/output/gap_report.md \
        --status success [--notes "说明文字"] [--extra key=value]

行为:
- 从 case.json 读取 case_id 与 output_contract；契约形态未知时做宽容处理
  （dict 取键、list 取元素、嵌套 dict 递归取叶子字段名）；
- result.json 必含 case_id、status、artifacts、sources、uncertainty、change_record；
- 契约声明的每个字段都必须出现：能用参数填充的填充，无法填充的写入占位符
  "<未提供: 原因>" 并打印警告（此时建议把 --status 降为 partial 并在 --notes 说明）；
- 引用的产物文件必须真实存在，不存在则以 1 退出。

退出码: 0 成功（允许带警告）；1 产物缺失或 case.json 无效；2 参数 / 文件错误。
仅依赖标准库，Python >= 3.8。
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_FIELDS = ("case_id", "status", "summary", "artifacts", "sources", "uncertainty", "change_record")


def contract_fields(contract):
    """从 output_contract 提取字段名集合，兼容 dict / list / 嵌套结构。"""
    fields = []

    def walk(node):
        if isinstance(node, dict):
            if "fields" in node and isinstance(node["fields"], (dict, list)):
                walk(node["fields"])
            else:
                for key, value in node.items():
                    if isinstance(value, (dict, list)):
                        walk(value)
                    else:
                        fields.append(str(key))
        elif isinstance(node, list):
            for item in node:
                if isinstance(item, str):
                    fields.append(item)
                else:
                    walk(item)

    walk(contract)
    seen, ordered = set(), []
    for name in fields:
        if name not in seen:
            seen.add(name)
            ordered.append(name)
    return ordered


def main() -> int:
    parser = argparse.ArgumentParser(description="组装并校验 result.json")
    parser.add_argument("--case", default="/input/case.json", help="案例 JSON（默认 /input/case.json）")
    parser.add_argument("--output-dir", default="/app/output", help="输出目录（默认 /app/output）")
    parser.add_argument("--draft", required=True, help="章节草稿路径")
    parser.add_argument("--evidence", required=True, help="证据映射 JSON 路径")
    parser.add_argument("--gaps", required=True, help="缺口报告路径")
    parser.add_argument("--status", required=True, choices=["success", "partial", "failed"], help="运行状态")
    parser.add_argument("--notes", action="append", default=[], help="附加说明，可重复")
    parser.add_argument("--extra", action="append", default=[], help="额外字段 key=value，可重复")
    args = parser.parse_args()

    case_path = Path(args.case)
    if not case_path.is_file():
        print(f"[make_result] 错误：案例文件不存在: {case_path}", file=sys.stderr)
        return 2
    try:
        case = json.loads(case_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        print(f"[make_result] 错误：case.json 不是合法 JSON: {exc}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = {
        "draft": args.draft,
        "evidence_map": args.evidence,
        "gap_report": args.gaps,
    }
    for label, path_text in artifacts.items():
        if not Path(path_text).is_file():
            print(f"[make_result] 错误：产物 {label} 不存在: {path_text}", file=sys.stderr)
            return 1

    case_id = case.get("case_id") or case.get("id") or "unknown"
    warnings = []

    result = {
        "case_id": case_id,
        "status": args.status,
        "summary": "；".join(args.notes) if args.notes else "",
        "artifacts": artifacts,
        "sources": "见 evidence_map.json：每条要素含文件路径与定位（配置键 / 行号 / 页码）",
        "uncertainty": "见 gap_report.md：材料缺失、冲突与无法判断项逐条登记",
        "change_record": "见 gap_report.md 与（如为修改任务）change_record.md",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    for pair in args.extra:
        if "=" not in pair:
            print(f"[make_result] 警告：忽略无法解析的 --extra 项: {pair!r}（应为 key=value）", file=sys.stderr)
            continue
        key, value = pair.split("=", 1)
        result[key] = value

    contract = case.get("output_contract")
    required = contract_fields(contract) if contract else []
    if not contract:
        warnings.append("case.json 未声明 output_contract，仅写入基础字段")

    for field in required:
        if field in result:
            continue
        lowered = field.lower()
        if any(word in lowered for word in ("draft", "section", "manuscript", "document", "text")):
            result[field] = args.draft
        elif any(word in lowered for word in ("evidence", "source", "map", "trace")):
            result[field] = args.evidence
        elif any(word in lowered for word in ("gap", "issue", "question", "confirm")):
            result[field] = args.gaps
        elif "status" in lowered:
            result[field] = args.status
        else:
            result[field] = f"<未提供: 契约字段 {field!r} 无法从当前产物推断>"
            warnings.append(f"契约字段 {field!r} 以占位符填充，需人工补充")

    out_path = output_dir / "result.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[make_result] case_id={case_id} status={args.status}")
    print(f"[make_result] 契约字段 {len(required)} 个，全部已覆盖: "
          + ("是" if all(f in result for f in required) else "否（异常）"))
    for message in warnings:
        print(f"[make_result] 警告：{message}", file=sys.stderr)
    print(f"[make_result] -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

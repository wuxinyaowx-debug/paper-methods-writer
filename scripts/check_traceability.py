#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""可追溯性校验：检查章节草稿中的数值是否都能追溯到证据映射。

用法:
    python scripts/check_traceability.py --draft /app/work/draft.md \
        --evidence /app/work/evidence_map.json [--report /app/work/trace_report.txt] [--no-fail]

规则:
- 提取草稿中的数值字面量（整数、小数、百分数、科学计数法）；
- 含 "待确认" 或 "来源" 标注的行内的数值若在证据映射中找不到，只警告、不计失败——
  但鼓励把一切数值登记进证据映射；
- 行首的章节编号（如 "3.2"、"1."）不视为数值；
- 与证据映射中任一 value / raw_value 数值相等（相对误差 <= 1e-6）即视为可追溯。

退出码: 0 全部可追溯；1 存在无来源数值；2 输入文件错误。
仅依赖标准库，Python >= 3.8。
"""
import argparse
import json
import re
import sys
from pathlib import Path

NUMBER_RE = re.compile(
    r"(?<![\w.])-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?%?(?![\w.])"
)
SECTION_RE = re.compile(r"^\s*(?:#+\s*)?\d+(?:\.\d+)*[.、]?\s")


def collect_evidence_values(node, out):
    """递归收集证据映射中的全部标量取值。"""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in ("value", "raw_value") and isinstance(value, (int, float, str)):
                out.append(str(value))
            else:
                collect_evidence_values(value, out)
    elif isinstance(node, list):
        for item in node:
            collect_evidence_values(item, out)


def to_float(text):
    try:
        return float(text.rstrip("%"))
    except (ValueError, AttributeError):
        return None


def matches(token: str, evidence_values) -> bool:
    if token in evidence_values:
        return True
    number = to_float(token)
    if number is None:
        return False
    for raw in evidence_values:
        other = to_float(raw)
        if other is None:
            continue
        if other == number or (other != 0 and abs(number - other) / abs(other) <= 1e-6):
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="校验草稿数值是否均可追溯到证据映射")
    parser.add_argument("--draft", required=True, help="章节草稿（Markdown）")
    parser.add_argument("--evidence", required=True, help="证据映射 evidence_map.json")
    parser.add_argument("--report", default=None, help="可选：报告输出路径")
    parser.add_argument("--no-fail", action="store_true", help="发现无来源数值时仍以 0 退出")
    args = parser.parse_args()

    draft_path, evidence_path = Path(args.draft), Path(args.evidence)
    for path in (draft_path, evidence_path):
        if not path.is_file():
            print(f"[check_traceability] 错误：文件不存在: {path}", file=sys.stderr)
            return 2

    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        print(f"[check_traceability] 错误：证据映射不是合法 JSON: {exc}", file=sys.stderr)
        return 2

    evidence_values = []
    collect_evidence_values(evidence, evidence_values)

    untraced, warned, traced_count = [], [], 0
    for lineno, line in enumerate(draft_path.read_text(encoding="utf-8").splitlines(), 1):
        if SECTION_RE.match(line):
            line = SECTION_RE.sub("", line, count=1)
        marked = ("待确认" in line) or ("来源" in line)
        for token in NUMBER_RE.findall(line):
            if matches(token, evidence_values):
                traced_count += 1
            elif marked:
                warned.append((lineno, token))
            else:
                untraced.append((lineno, token))

    lines = [
        f"可追溯数值: {traced_count}",
        f"已标注待确认/来源但无映射（警告）: {len(warned)}",
        f"无来源且未标注（失败）: {len(untraced)}",
    ]
    for lineno, token in warned:
        lines.append(f"  [警告] 第 {lineno} 行: {token}")
    for lineno, token in untraced:
        lines.append(f"  [失败] 第 {lineno} 行: {token}")
    report = "\n".join(lines)
    print(report)

    if args.report:
        Path(args.report).write_text(report + "\n", encoding="utf-8")

    if untraced and not args.no_fail:
        print("[check_traceability] 存在无来源数值：请补入证据映射，或改为 〔待确认〕 标注。", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

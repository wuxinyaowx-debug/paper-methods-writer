#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盘点输入材料，生成 inventory.json。

用法:
    python scripts/collect_inputs.py --input /input --work /app/work

退出码: 0 正常（含零文件警告）；2 输入目录不存在或不可读。
仅依赖标准库，Python >= 3.8。
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

TYPE_BY_EXT = {
    ".pdf": "paper-pdf",
    ".md": "document", ".txt": "document", ".tex": "document",
    ".yaml": "config", ".yml": "config", ".json": "config",
    ".toml": "config", ".ini": "config", ".cfg": "config",
    ".log": "log", ".out": "log",
    ".py": "code", ".sh": "code", ".ipynb": "code",
    ".csv": "data", ".tsv": "data", ".parquet": "data",
    ".jsonl": "data", ".npy": "data", ".npz": "data",
    ".png": "figure", ".jpg": "figure", ".jpeg": "figure", ".svg": "figure",
}


def sha256_of(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="盘点输入材料并生成 inventory.json")
    parser.add_argument("--input", default="/input", help="输入目录（默认 /input）")
    parser.add_argument("--work", default="/app/work", help="中间产物目录（默认 /app/work）")
    parser.add_argument("--out", default=None, help="输出路径（默认 <work>/inventory.json）")
    args = parser.parse_args()

    input_dir = Path(args.input)
    if not input_dir.is_dir():
        print(f"[collect_inputs] 错误：输入目录不存在或不可读: {input_dir}", file=sys.stderr)
        return 2

    work_dir = Path(args.work)
    work_dir.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out) if args.out else work_dir / "inventory.json"

    files = []
    for path in sorted(input_dir.rglob("*")):
        if not path.is_file():
            continue
        stat = path.stat()
        files.append({
            "path": str(path),
            "relative_path": str(path.relative_to(input_dir)),
            "guessed_type": TYPE_BY_EXT.get(path.suffix.lower(), "unknown"),
            "size_bytes": stat.st_size,
            "sha256": sha256_of(path),
        })

    inventory = {
        "input_dir": str(input_dir),
        "file_count": len(files),
        "files": files,
        "note": "guessed_type 仅按扩展名猜测，使用前必须打开文件确认实际内容",
    }
    out_path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[collect_inputs] 共 {len(files)} 个文件 -> {out_path}")
    if not files:
        print("[collect_inputs] 警告：输入目录为空，材料缺失，应在 result.json 中将状态记为 partial", file=sys.stderr)
    for item in files:
        print(f"  {item['guessed_type']:<12} {item['size_bytes']:>10} B  {item['relative_path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

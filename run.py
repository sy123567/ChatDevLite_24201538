#!/usr/bin/env python3
"""ChatDevLite 主入口 (实验单 1.1).

用法:
    python run.py --task "开发一个待办事项命令行工具"
    python run.py --task "做一个命令行计算器" --out outputs/calculator
    python run.py --demo          # 不传需求时, 用待办示例跑一遍

只用标准库, 不联网, 不启动服务. 跑完后在输出目录里看:
    requirements.md / design.md / main.py / check.md / conversation.md
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chatdevlite.agents import slugify  # noqa: E402
from chatdevlite.pipeline import run_pipeline  # noqa: E402

DEMO_TASK = "开发一个待办事项命令行工具"


def main() -> int:
    parser = argparse.ArgumentParser(description="ChatDevLite: 一句话需求 -> 可运行代码")
    parser.add_argument("--task", default="", help="用户需求, 例如: 开发一个待办事项命令行工具")
    parser.add_argument("--out", default="", help="输出目录, 默认 outputs/<需求简写>")
    parser.add_argument("--demo", action="store_true", help="用待办示例跑一遍")
    args = parser.parse_args()

    task = DEMO_TASK if args.demo or not args.task else args.task
    out_dir = Path(args.out) if args.out else Path("outputs") / slugify(task)
    print(f"[主入口] 需求: {task}")
    print(f"[主入口] 输出目录: {out_dir}")
    meta = run_pipeline(task, out_dir)
    print("[CPO+CEO] 需求文档 -> requirements.md")
    print("[CTO+CEO] 系统设计 -> design.md")
    print("[Programmer] 代码 -> main.py")
    print(f"[检查] {'通过' if meta['check_passed'] else '未通过, 请看 check.md'}")
    print(f"完成: {out_dir} / main.py 可以直接运行, 示例命令见 design.md")
    return 0 if meta["check_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

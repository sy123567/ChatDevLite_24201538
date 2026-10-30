"""待办事项命令行工具 (由 ChatDevLite 生成).

用法:
    python main.py add "买牛奶"
    python main.py list
    python main.py done 1
    python main.py delete 1
数据存在同目录下的 tasks.json.
"""

import argparse
import json
import os
import sys

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")


def load():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def save(tasks):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def cmd_add(title):
    tasks = load()
    new_id = max([t["id"] for t in tasks], default=0) + 1
    tasks.append({"id": new_id, "title": title, "done": False})
    save(tasks)
    print(f"已添加 [{new_id}] {title}")


def cmd_list():
    tasks = load()
    if not tasks:
        print("还没有待办, 先用 add 添加一条吧.")
        return
    for t in tasks:
        mark = "✓" if t["done"] else "□"
        print(f"{t['id']}. {mark} {t['title']}")


def cmd_done(task_id):
    tasks = load()
    for t in tasks:
        if t["id"] == task_id:
            t["done"] = True
            save(tasks)
            print(f"已完成 [{task_id}] {t['title']}")
            return
    print(f"找不到编号为 {task_id} 的待办.")
    sys.exit(1)


def cmd_delete(task_id):
    tasks = load()
    rest = [t for t in tasks if t["id"] != task_id]
    if len(rest) == len(tasks):
        print(f"找不到编号为 {task_id} 的待办.")
        sys.exit(1)
    save(rest)
    print(f"已删除 [{task_id}]")


def main():
    parser = argparse.ArgumentParser(description="待办事项命令行工具")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add"); p.add_argument("title")
    sub.add_parser("list")
    p = sub.add_parser("done"); p.add_argument("id", type=int)
    p = sub.add_parser("delete"); p.add_argument("id", type=int)
    args = parser.parse_args()
    if args.cmd == "add":
        cmd_add(args.title)
    elif args.cmd == "list":
        cmd_list()
    elif args.cmd == "done":
        cmd_done(args.id)
    elif args.cmd == "delete":
        cmd_delete(args.id)


if __name__ == "__main__":
    main()

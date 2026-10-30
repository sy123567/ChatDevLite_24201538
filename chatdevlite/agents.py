"""四个轻量角色.

实验单对应的分工:
    1.1 主入口: 用户一句话需求, ``python run.py --task "..."``
    1.2 需求分析: CPO + CEO, 输出需求文档
    1.3 系统设计: CTO + CEO, 输出设计文档
    1.4 编码: Programmer, 输出可运行的源代码

原版 ChatDev 用大模型多轮对话完成上面几步, 轻量版把"对话"
收敛成确定性的三步模板: 这样不用 API Key、不用联网、
不用等模型, 老师和同学在本地就能完整跑通、复现结果.
如果以后要接真实大模型, 只需要在本文件里把
``_mock_*`` 换成一次模型调用, 流水线接口不用变.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Agent:
    """一个角色: 名字、职位、负责的事."""

    name: str
    role: str
    job: str

    def say(self, text: str) -> str:
        return f"[{self.name} / {self.role}] {text}"


CPO = Agent("CPO", "首席产品官", "把用户一句话变成可验收的需求")
CEO = Agent("CEO", "首席执行官", "拍板范围: 做什么、不做什么")
CTO = Agent("CTO", "首席技术官", "定技术方案、数据模型和接口")
PROGRAMMER = Agent("Programmer", "程序员", "按设计文档写出可运行代码")


def detect_app_type(task: str) -> str:
    """从任务关键词判断应用类型, 决定生成哪一份模板代码."""
    text = task.lower()
    if any(k in task for k in ("待办", "任务清单", "todo", "todolist")):
        return "todo"
    if any(k in task for k in ("计算", "calculator", "算术")):
        return "calculator"
    if any(k in task for k in ("猜数字", "猜数", "guessing")):
        return "guessing"
    if any(k in task for k in ("记账", "账本", "收支")):
        return "ledger"
    return "generic"


APP_NAMES = {
    "todo": "待办事项命令行工具",
    "calculator": "命令行计算器",
    "guessing": "猜数字小游戏",
    "ledger": "简易记账工具",
    "generic": "通用条目管理命令行工具",
}


def analyse_requirements(task: str) -> dict:
    """1.2 需求分析: CPO 提需求, CEO 定范围."""
    app_type = detect_app_type(task)
    common_non_functional = [
        "只用 Python 标准库, 不装第三方包, 不联网",
        "命令行运行, 不启动 Web 服务, 不做图形界面",
        "数据存在本地 JSON 文件, 关掉程序也不丢",
        "所有命令都有 --help, 出错时给出一句人话提示",
    ]
    functional = {
        "todo": ["添加一条待办", "列出全部待办", "把一条标记为已完成", "删除一条待办"],
        "calculator": ["输入一个算术表达式并输出结果", "支持加减乘除和括号", "表达式非法时报错, 不崩溃"],
        "guessing": ["随机生成 1 到 100 的目标数字", "玩家输入猜测, 提示偏大或偏小", "猜中后报告用了几次"],
        "ledger": ["记一笔收入或支出", "列出全部账目", "按类型汇总收入、支出和结余"],
        "generic": ["添加一条记录", "列出全部记录", "按关键词搜索记录", "删除一条记录"],
    }[app_type]
    return {
        "task": task,
        "app_type": app_type,
        "app_name": APP_NAMES[app_type],
        "user_story": f"作为用户, 我想用一句话「{task}」得到一个能直接跑的工具, 而不是只拿到一份文档.",
        "functional": functional,
        "non_functional": common_non_functional,
        "acceptance": [
            "生成的 main.py 能通过 py_compile 语法检查",
            "按设计文档里的示例命令跑一遍, 结果和文档一致",
            "不做范围外的事: 无界面、无账号登录、无联网同步、无数据库服务",
        ],
        "out_of_scope": ["图形界面 / Web 界面", "账号登录", "联网同步", "数据库服务", "多用户权限"],
        "log": [
            CPO.say(f"收到需求: {task}, 先拆成可验收的功能点."),
            CEO.say(f"范围定下来: 只做「{APP_NAMES[app_type]}」, 其余一律不做, 保证轻量."),
        ],
    }


def design_system(req: dict) -> dict:
    """1.3 系统设计: CTO 定方案, CEO 确认不超范围."""
    app_type = req["app_type"]
    models = {
        "todo": "Task(id: int, title: str, done: bool, created: str), 存在 tasks.json",
        "calculator": "无持久化数据, 输入是表达式字符串, 输出是数字或错误提示",
        "guessing": "Game(target: int, tries: int), 目标在 1 到 100 之间随机生成",
        "ledger": "Record(id: int, kind: 收入/支出, amount: float, note: str), 存在 records.json",
        "generic": "Item(id: int, title: str, created: str), 存在 items.json",
    }[app_type]
    commands = {
        "todo": "python main.py add \"买牛奶\" / list / done 1 / delete 1",
        "calculator": "python main.py \"2 + 3 * 4\"",
        "guessing": "python main.py (按提示输入数字, 直到猜中)",
        "ledger": "python main.py add 支出 12.5 午饭 / list / summary",
        "generic": "python main.py add \"第一条\" / list / search 关键词 / delete 1",
    }[app_type]
    return {
        "modules": [
            ("main.py", "唯一入口: 解析命令行参数, 调用业务逻辑, 打印结果"),
            ("数据文件 (JSON)", "本地持久化, 结构见下方数据模型, 人可以直接打开检查"),
            ("检查脚本 (流水线自带)", "py_compile + 示例命令冒烟测试, 结果写进 check.md"),
        ],
        "data_model": models,
        "commands": commands,
        "test_plan": ["py_compile 通过", "示例命令跑通, 结果符合需求文档", "--help 能正常打印"],
        "log": [
            CTO.say(f"方案: 单文件 main.py + 一个 JSON 数据文件, 标准库足够, 不引入框架."),
            CEO.say("确认: 这个方案没有超出需求范围, 可以交给 Programmer."),
        ],
    }


# ---------------------------------------------------------------------------
# 1.4 编码: 按应用类型生成一份真正能跑的代码, 不是占位符.
# 每份模板都刻意保持短小: 一个文件、一个主函数、异常只报人话.
# ---------------------------------------------------------------------------

_TODO_CODE = '''"""待办事项命令行工具 (由 ChatDevLite 生成).

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
'''

_CALCULATOR_CODE = '''"""命令行计算器 (由 ChatDevLite 生成).

用法: python main.py "2 + 3 * 4"   # 输出 14
只允许数字、四则运算和括号, 其他字符一律拒绝, 避免执行任意代码.
"""

import ast
import operator
import sys

OPS = {ast.Add: operator.add, ast.Sub: operator.sub,
       ast.Mult: operator.mul, ast.Div: operator.truediv,
       ast.USub: operator.neg}


def calc(node):
    if isinstance(node, ast.Expression):
        return calc(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        return OPS[type(node.op)](calc(node.left), calc(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
        return OPS[type(node.op)](calc(node.operand))
    raise ValueError("不支持的表达式, 只支持数字、四则运算和括号.")


def main():
    if len(sys.argv) != 2:
        print('用法: python main.py "2 + 3 * 4"')
        sys.exit(1)
    try:
        tree = ast.parse(sys.argv[1], mode="eval")
        print(calc(tree))
    except Exception as e:
        print(f"算不出来: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

_GUESSING_CODE = '''"""猜数字小游戏 (由 ChatDevLite 生成).

用法: python main.py
程序随机想一个 1 到 100 的数字, 你输入猜测, 它会提示偏大或偏小,
猜中后告诉你用了几次.
"""

import random


def play():
    target = random.randint(1, 100)
    tries = 0
    print("我想了一个 1 到 100 的数字, 猜猜看:")
    while True:
        try:
            guess = int(input("你的猜测: "))
        except ValueError:
            print("请输入一个整数.")
            continue
        tries += 1
        if guess < target:
            print("偏小了, 再大一点.")
        elif guess > target:
            print("偏大了, 再小一点.")
        else:
            print(f"猜中了! 一共用了 {tries} 次.")
            break


if __name__ == "__main__":
    play()
'''

_LEDGER_CODE = '''"""简易记账工具 (由 ChatDevLite 生成).

用法:
    python main.py add 支出 12.5 午饭
    python main.py list
    python main.py summary
数据存在同目录下的 records.json.
"""

import argparse
import json
import os
import sys

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "records.json")


def load():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def save(records):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="简易记账工具")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add")
    p.add_argument("kind", choices=["收入", "支出"])
    p.add_argument("amount", type=float)
    p.add_argument("note", nargs="?", default="")
    sub.add_parser("list")
    sub.add_parser("summary")
    args = parser.parse_args()
    if args.cmd == "add":
        records = load()
        new_id = max([r["id"] for r in records], default=0) + 1
        records.append({"id": new_id, "kind": args.kind,
                        "amount": args.amount, "note": args.note})
        save(records)
        print(f"已记 [{new_id}] {args.kind} {args.amount} {args.note}")
    elif args.cmd == "list":
        for r in load():
            print(f"{r['id']}. {r['kind']} {r['amount']} {r['note']}")
    elif args.cmd == "summary":
        records = load()
        income = sum(r["amount"] for r in records if r["kind"] == "收入")
        expense = sum(r["amount"] for r in records if r["kind"] == "支出")
        print(f"收入 {income}  支出 {expense}  结余 {income - expense}")


if __name__ == "__main__":
    main()
'''

_GENERIC_CODE = _TODO_CODE.replace("待办事项命令行工具", "通用条目管理命令行工具").replace(
    "待办", "条目").replace("tasks.json", "items.json")


def generate_code(req: dict) -> tuple[str, list[str]]:
    """1.4 编码: Programmer 按设计文档出代码."""
    code = {
        "todo": _TODO_CODE,
        "calculator": _CALCULATOR_CODE,
        "guessing": _GUESSING_CODE,
        "ledger": _LEDGER_CODE,
        "generic": _GENERIC_CODE,
    }[req["app_type"]]
    log = [
        PROGRAMMER.say("按设计文档写完了 main.py, 单文件, 只用标准库."),
        PROGRAMMER.say("下一步交给流水线做语法检查和冒烟测试, 通过才算交付."),
    ]
    return code, log


def slugify(task: str) -> str:
    """给输出目录起一个安全的名字."""
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "_", task.strip())[:20].strip("_")
    return text or "app"

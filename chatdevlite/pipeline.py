"""流水线: 把四个角色串成一步到位的端到端流程.

    输入一句话 -> 需求文档 -> 设计文档 -> 代码 -> 语法检查+冒烟测试

每一步的结果都落盘, 而不是只打印在终端里:
    requirements.md  需求分析 (CPO + CEO)
    design.md        系统设计 (CTO + CEO)
    main.py          生成的代码 (Programmer)
    check.md         审查与测试结果 (py_compile + 示例命令)
    conversation.md  四个角色的对话记录
    pipeline.json    本次运行的元数据, 方便复现
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from . import agents


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _requirements_md(req: dict) -> str:
    lines = [f"# 需求文档: {req['app_name']}", "",
             f"原始需求: {req['task']}", "",
             f"用户故事: {req['user_story']}", "",
             "## 功能需求"]
    lines += [f"- {f}" for f in req["functional"]]
    lines += ["", "## 非功能需求"]
    lines += [f"- {f}" for f in req["non_functional"]]
    lines += ["", "## 验收标准"]
    lines += [f"- {f}" for f in req["acceptance"]]
    lines += ["", "## 不做 (范围外)"]
    lines += [f"- {f}" for f in req["out_of_scope"]]
    return "\n".join(lines) + "\n"


def _design_md(req: dict, design: dict) -> str:
    lines = [f"# 系统设计: {req['app_name']}", "",
             "## 模块", "",
             "| 模块 | 说明 |",
             "|---|---|"]
    lines += [f"| {m} | {d} |" for m, d in design["modules"]]
    lines += ["", f"## 数据模型", "", design["data_model"], "",
              "## 示例命令", "", "```", design["commands"], "```", "",
              "## 测试计划"]
    lines += [f"- {t}" for t in design["test_plan"]]
    return "\n".join(lines) + "\n"


def _run(cmd: list[str], cwd: Path) -> tuple[bool, str]:
    """跑一条命令, 返回 (是否成功, 合并后的输出, 截断到 500 字)."""
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True,
                              text=True, timeout=30)
        out = (proc.stdout + proc.stderr).strip()
        return proc.returncode == 0, out[:500]
    except Exception as e:  # 超时、找不到解释器等都算测试失败, 要写进报告
        return False, str(e)


def _smoke_commands(app_type: str, out_dir: Path) -> list[list[str]]:
    """每种应用一条确定性的冒烟命令 (猜数字是交互游戏, 只测 --help 兜底除外)."""
    py = sys.executable
    if app_type == "todo":
        return [[py, "main.py", "add", "冒烟测试任务"],
                [py, "main.py", "list"]]
    if app_type == "calculator":
        return [[py, "main.py", "2 + 3 * 4"]]
    if app_type == "ledger":
        return [[py, "main.py", "add", "支出", "12.5", "午饭"],
                [py, "main.py", "summary"]]
    if app_type == "generic":
        return [[py, "main.py", "add", "冒烟测试条目"],
                [py, "main.py", "list"]]
    return [[py, "main.py", "--help"]]


def run_pipeline(task: str, out_dir: Path) -> dict:
    """跑完整条流水线, 返回元数据 (同时落盘 6 个文件)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    req = agents.analyse_requirements(task)
    design = agents.design_system(req)
    code, code_log = agents.generate_code(req)

    log_lines = req["log"] + design["log"] + code_log
    _write(out_dir / "requirements.md", _requirements_md(req))
    _write(out_dir / "design.md", _design_md(req, design))
    _write(out_dir / "main.py", code)

    # 审查与测试: 先语法检查, 再跑冒烟命令. 猜数字类不跑交互命令,
    # 只做语法检查, 避免流水线在等待输入时卡住.
    checks: list[str] = []
    ok, out = _run([sys.executable, "-m", "py_compile", "main.py"], out_dir)
    checks.append(f"- py_compile: {'通过' if ok else '失败'} {out}")
    all_ok = ok
    if req["app_type"] != "guessing":
        for cmd in _smoke_commands(req["app_type"], out_dir):
            ok, out = _run(cmd, out_dir)
            all_ok = all_ok and ok
            checks.append(f"- {' '.join(cmd[2:])}: {'通过' if ok else '失败'} {out}")
    else:
        checks.append("- 冒烟测试: 跳过交互输入, 只做语法检查 (猜数字需人工试玩)")
    check_md = "# 审查与测试\n\n" + "\n".join(checks) + \
        f"\n\n结论: {'通过' if all_ok else '未通过, 请看上面失败项'}\n"
    _write(out_dir / "check.md", check_md)
    _write(out_dir / "conversation.md",
           "# 对话记录\n\n" + "\n".join(log_lines) + "\n")
    meta = {"task": task, "app_type": req["app_type"],
            "app_name": req["app_name"],
            "files": ["requirements.md", "design.md", "main.py",
                      "check.md", "conversation.md", "pipeline.json"],
            "check_passed": all_ok}
    _write(out_dir / "pipeline.json", json.dumps(meta, ensure_ascii=False, indent=2))
    return meta

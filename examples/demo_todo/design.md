# 系统设计: 待办事项命令行工具

## 模块

| 模块 | 说明 |
|---|---|
| main.py | 唯一入口: 解析命令行参数, 调用业务逻辑, 打印结果 |
| 数据文件 (JSON) | 本地持久化, 结构见下方数据模型, 人可以直接打开检查 |
| 检查脚本 (流水线自带) | py_compile + 示例命令冒烟测试, 结果写进 check.md |

## 数据模型

Task(id: int, title: str, done: bool, created: str), 存在 tasks.json

## 示例命令

```
python main.py add "买牛奶" / list / done 1 / delete 1
```

## 测试计划
- py_compile 通过
- 示例命令跑通, 结果符合需求文档
- --help 能正常打印

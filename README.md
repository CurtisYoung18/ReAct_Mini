# ReAct Mini

基于 **Reasoning + Acting** 循环的轻量级 AI Agent 实现。

## 核心架构

```
用户输入 → LLM思考 → 需要工具? → 执行工具 → 更新上下文 → 循环直到完成
                         ↓
                    直接返回答案
```

## 快速开始

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## 文件结构

| 文件 | 说明 |
|------|------|
| `agent.py` | ReAct Agent 核心 + Multi-Agent 路由器 |
| `tools.py` | 工具注册与实现 (bash/文件操作/搜索/计算器) |
| `main.py` | 入口 (演示模式 + 交互式对话) |

## 工作原理

1. LLM 接收用户请求 + 可用工具列表
2. LLM 决定是否调用工具（通过 Function Calling）
3. 执行工具，将结果加入对话上下文
4. LLM 继续推理，直到任务完成

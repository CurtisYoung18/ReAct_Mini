"""
工具模块 - 定义 ReAct Agent 可用的工具
"""
import subprocess
import os
import json
from typing import Callable, Any

# 工具注册表
TOOLS: dict[str, dict] = {}


def register_tool(name: str, description: str, parameters: dict):
    """工具注册装饰器"""
    def decorator(func: Callable):
        TOOLS[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": func
        }
        return func
    return decorator


@register_tool(
    name="bash",
    description="执行 shell 命令并返回结果。用于运行系统命令、安装依赖、执行脚本等。",
    parameters={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "要执行的 shell 命令"
            }
        },
        "required": ["command"]
    }
)
def bash_tool(command: str) -> str:
    """执行 shell 命令"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"
        if result.returncode != 0:
            output += f"\n[exit code]: {result.returncode}"
        return output if output.strip() else "[命令执行成功，无输出]"
    except subprocess.TimeoutExpired:
        return "[错误]: 命令执行超时（60秒）"
    except Exception as e:
        return f"[错误]: {str(e)}"


@register_tool(
    name="read_file",
    description="读取文件内容。用于查看代码、配置文件等。",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "文件路径"
            }
        },
        "required": ["path"]
    }
)
def read_file_tool(path: str) -> str:
    """读取文件"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content if content else "[文件为空]"
    except FileNotFoundError:
        return f"[错误]: 文件不存在: {path}"
    except Exception as e:
        return f"[错误]: {str(e)}"


@register_tool(
    name="write_file",
    description="写入内容到文件。用于创建或修改文件。",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "文件路径"
            },
            "content": {
                "type": "string",
                "description": "要写入的内容"
            }
        },
        "required": ["path", "content"]
    }
)
def write_file_tool(path: str, content: str) -> str:
    """写入文件"""
    try:
        # 确保目录存在
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"[成功]: 已写入 {len(content)} 字符到 {path}"
    except Exception as e:
        return f"[错误]: {str(e)}"


@register_tool(
    name="list_dir",
    description="列出目录内容。用于探索文件结构。",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "目录路径，默认为当前目录"
            }
        },
        "required": []
    }
)
def list_dir_tool(path: str = ".") -> str:
    """列出目录"""
    try:
        entries = os.listdir(path)
        if not entries:
            return "[目录为空]"
        result = []
        for entry in sorted(entries):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                result.append(f"📁 {entry}/")
            else:
                size = os.path.getsize(full_path)
                result.append(f"📄 {entry} ({size} bytes)")
        return "\n".join(result)
    except FileNotFoundError:
        return f"[错误]: 目录不存在: {path}"
    except Exception as e:
        return f"[错误]: {str(e)}"


@register_tool(
    name="search_files",
    description="在目录中搜索文件。用于查找特定文件。",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "搜索模式（支持 * 通配符）"
            },
            "path": {
                "type": "string",
                "description": "搜索目录，默认为当前目录"
            }
        },
        "required": ["pattern"]
    }
)
def search_files_tool(pattern: str, path: str = ".") -> str:
    """搜索文件"""
    import fnmatch
    try:
        matches = []
        for root, dirs, files in os.walk(path):
            # 跳过隐藏目录和常见的忽略目录
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv']]
            for filename in files:
                if fnmatch.fnmatch(filename, pattern):
                    matches.append(os.path.join(root, filename))
        if not matches:
            return f"[未找到匹配 '{pattern}' 的文件]"
        return "\n".join(matches[:50])  # 限制结果数量
    except Exception as e:
        return f"[错误]: {str(e)}"


@register_tool(
    name="calculator",
    description="执行数学计算。用于数值计算。",
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "数学表达式，如 '2 + 3 * 4'"
            }
        },
        "required": ["expression"]
    }
)
def calculator_tool(expression: str) -> str:
    """计算器"""
    try:
        # 安全地执行数学表达式
        allowed_names = {"abs": abs, "round": round, "min": min, "max": max, "sum": sum, "pow": pow}
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return str(result)
    except Exception as e:
        return f"[错误]: 无法计算 '{expression}': {str(e)}"


def get_tools_for_llm() -> list[dict]:
    """获取 LLM 格式的工具定义"""
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            }
        }
        for tool in TOOLS.values()
    ]


def execute_tool(name: str, arguments: dict) -> str:
    """执行工具"""
    if name not in TOOLS:
        return f"[错误]: 未知工具 '{name}'"
    
    tool = TOOLS[name]
    try:
        return tool["handler"](**arguments)
    except TypeError as e:
        return f"[错误]: 工具参数错误: {str(e)}"
    except Exception as e:
        return f"[错误]: 工具执行失败: {str(e)}"

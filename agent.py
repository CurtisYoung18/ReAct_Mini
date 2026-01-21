"""
ReAct Agent 核心实现
基于 Reasoning + Acting 循环的 Agent 架构
"""
import json
from typing import Optional
from openai import OpenAI
from tools import get_tools_for_llm, execute_tool, TOOLS


class ReActAgent:
    """
    ReAct Agent - 推理与行动循环
    
    核心流程：
    1. 接收用户输入
    2. LLM 思考并决定是否需要工具
    3. 如果需要工具 -> 执行工具 -> 将结果加入上下文 -> 回到步骤2
    4. 如果不需要工具 -> 返回最终回答
    """
    
    SYSTEM_PROMPT = """你是一个智能助手，可以使用工具来帮助用户完成任务。

## 工作模式
你采用 ReAct（Reasoning + Acting）模式工作：
1. **思考**：分析用户的需求，决定下一步行动
2. **行动**：如果需要，调用合适的工具获取信息或执行操作
3. **观察**：查看工具返回的结果
4. **循环**：根据结果继续思考，直到任务完成

## 可用工具
{tools_description}

## 重要规则
1. 需要执行操作时必须使用工具，不要模拟或假设结果
2. 一步一步思考，确保每个行动都有明确目的
3. 工具调用失败时，分析原因并尝试其他方法
4. 任务完成后给出清晰的总结

## 输出格式
思考时请先说明你的推理过程，然后决定是否调用工具。"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.moonshot.cn/v1",
        model: str = "moonshot-v1-8k",
        max_iterations: int = 10,
        verbose: bool = True
    ):
        """
        初始化 ReAct Agent
        
        Args:
            api_key: Kimi API Key
            base_url: API 基础 URL
            model: 模型名称
            max_iterations: 最大循环次数，防止无限循环
            verbose: 是否打印详细日志
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.messages: list[dict] = []
        
    def _get_system_prompt(self) -> str:
        """生成系统提示，包含工具描述"""
        tools_desc = "\n".join([
            f"- **{name}**: {tool['description']}"
            for name, tool in TOOLS.items()
        ])
        return self.SYSTEM_PROMPT.format(tools_description=tools_desc)
    
    def _log(self, message: str, prefix: str = ""):
        """打印日志"""
        if self.verbose:
            if prefix:
                print(f"\n{'='*60}")
                print(f"[{prefix}]")
                print('='*60)
            print(message)
    
    def _call_llm(self) -> dict:
        """调用 LLM"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=get_tools_for_llm(),
            tool_choice="auto"
        )
        return response.choices[0].message
    
    def _handle_tool_calls(self, tool_calls: list) -> list[dict]:
        """处理工具调用"""
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                arguments = {}
            
            self._log(f"工具: {tool_name}\n参数: {json.dumps(arguments, ensure_ascii=False, indent=2)}", "工具调用")
            
            # 执行工具
            result = execute_tool(tool_name, arguments)
            
            self._log(f"{result[:500]}{'...(截断)' if len(result) > 500 else ''}", "工具结果")
            
            results.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })
        
        return results
    
    def run(self, user_input: str) -> str:
        """
        运行 ReAct 循环
        
        Args:
            user_input: 用户输入
            
        Returns:
            最终回答
        """
        # 初始化消息
        self.messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": user_input}
        ]
        
        self._log(f"用户输入: {user_input}", "开始任务")
        
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            self._log(f"", f"迭代 {iteration}/{self.max_iterations}")
            
            # 调用 LLM
            response = self._call_llm()
            
            # 检查是否有工具调用
            if response.tool_calls:
                # 添加 assistant 消息（包含工具调用）
                self.messages.append({
                    "role": "assistant",
                    "content": response.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in response.tool_calls
                    ]
                })
                
                # 执行工具并添加结果
                tool_results = self._handle_tool_calls(response.tool_calls)
                self.messages.extend(tool_results)
                
            else:
                # 没有工具调用，返回最终回答
                final_answer = response.content or "[无回答]"
                self._log(final_answer, "最终回答")
                return final_answer
        
        # 超过最大迭代次数
        return "[警告]: 达到最大迭代次数，任务可能未完成"
    
    def chat(self, user_input: str) -> str:
        """
        对话模式 - 保持上下文
        
        Args:
            user_input: 用户输入
            
        Returns:
            回答
        """
        # 如果是新对话，初始化系统提示
        if not self.messages:
            self.messages = [
                {"role": "system", "content": self._get_system_prompt()}
            ]
        
        # 添加用户消息
        self.messages.append({"role": "user", "content": user_input})
        
        self._log(f"用户: {user_input}", "对话")
        
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            
            # 调用 LLM
            response = self._call_llm()
            
            if response.tool_calls:
                # 处理工具调用
                self.messages.append({
                    "role": "assistant",
                    "content": response.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in response.tool_calls
                    ]
                })
                
                tool_results = self._handle_tool_calls(response.tool_calls)
                self.messages.extend(tool_results)
            else:
                # 最终回答
                final_answer = response.content or "[无回答]"
                self.messages.append({"role": "assistant", "content": final_answer})
                self._log(f"助手: {final_answer}", "回答")
                return final_answer
        
        return "[警告]: 达到最大迭代次数"
    
    def reset(self):
        """重置对话历史"""
        self.messages = []


class MultiAgentRouter:
    """
    多 Agent 路由器
    根据用户意图选择合适的专门化 Agent
    """
    
    ROUTER_PROMPT = """你是一个任务分类专家。分析用户请求，返回最合适的 agent 类型。

可选类型：
- explore: 搜索文件、理解代码结构、查找内容
- code: 编写代码、创建文件、实现功能
- bash: 执行命令、系统操作、安装依赖
- general: 通用对话、简单查询

只返回一个单词：explore/code/bash/general"""

    def __init__(self, api_key: str, base_url: str = "https://api.moonshot.cn/v1"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.api_key = api_key
        self.base_url = base_url
        
        # 专门化 Agent 的系统提示
        self.agent_prompts = {
            "explore": """你是代码探索专家。擅长搜索文件、理解代码结构。
主要使用: list_dir, read_file, search_files 工具。
风格: 直接给出发现，提供清晰的文件路径。""",
            
            "code": """你是代码编写专家。擅长创建和修改代码。
主要使用: read_file, write_file 工具。
风格: 先理解需求，再编写高质量代码。""",
            
            "bash": """你是命令行专家。擅长执行系统命令。
主要使用: bash 工具。
风格: 谨慎执行，先确认命令安全性。""",
            
            "general": """你是通用助手。可以使用所有工具完成各种任务。
根据需要灵活选择合适的工具。"""
        }
    
    def classify(self, user_input: str) -> str:
        """分类用户请求"""
        response = self.client.chat.completions.create(
            model="moonshot-v1-8k",
            messages=[
                {"role": "system", "content": self.ROUTER_PROMPT},
                {"role": "user", "content": user_input}
            ],
            temperature=0.1,
            max_tokens=10
        )
        
        agent_type = response.choices[0].message.content.strip().lower()
        if agent_type not in self.agent_prompts:
            agent_type = "general"
        
        return agent_type
    
    def route(self, user_input: str) -> str:
        """
        路由并执行任务
        
        Args:
            user_input: 用户输入
            
        Returns:
            执行结果
        """
        # 分类
        agent_type = self.classify(user_input)
        print(f"\n[路由器] 选择 Agent: {agent_type}")
        
        # 创建专门化 Agent
        agent = ReActAgent(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        # 修改系统提示
        original_prompt = agent._get_system_prompt()
        specialized_prompt = self.agent_prompts[agent_type]
        agent.SYSTEM_PROMPT = f"{specialized_prompt}\n\n{original_prompt}"
        
        # 执行
        return agent.run(user_input)

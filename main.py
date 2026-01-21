#!/usr/bin/env python3
"""
ReAct Agent 入口文件
演示 ReAct 架构的工作流程
"""
from agent import ReActAgent, MultiAgentRouter

# Kimi API 配置
API_KEY = "sk-p5lZ0EOImGmlUDFz7LQLnYWwewgvZqFWM4JWCMQ7Z7wZiHPe"
BASE_URL = "https://api.moonshot.cn/v1"
MODEL = "moonshot-v1-8k"


def demo_single_agent():
    """演示单 Agent 模式"""
    print("\n" + "="*70)
    print("🤖 ReAct Agent 演示 - 单 Agent 模式")
    print("="*70)
    
    agent = ReActAgent(
        api_key=API_KEY,
        base_url=BASE_URL,
        model=MODEL,
        verbose=True
    )
    
    # 示例任务
    tasks = [
        "列出当前目录下的所有文件",
        "计算 (15 + 27) * 3 - 18 / 2 的结果",
    ]
    
    for task in tasks:
        print("\n" + "-"*70)
        result = agent.run(task)
        print("-"*70)


def demo_multi_agent():
    """演示多 Agent 路由模式"""
    print("\n" + "="*70)
    print("🤖 ReAct Agent 演示 - 多 Agent 路由模式")
    print("="*70)
    
    router = MultiAgentRouter(
        api_key=API_KEY,
        base_url=BASE_URL
    )
    
    tasks = [
        "搜索当前目录下所有的 Python 文件",
        "执行 echo 'Hello ReAct!' 命令",
    ]
    
    for task in tasks:
        print("\n" + "-"*70)
        result = router.route(task)
        print("-"*70)


def interactive_mode():
    """交互式对话模式"""
    print("\n" + "="*70)
    print("🤖 ReAct Agent - 交互式对话模式")
    print("="*70)
    print("输入 'quit' 或 'exit' 退出")
    print("输入 'reset' 重置对话历史")
    print("-"*70)
    
    agent = ReActAgent(
        api_key=API_KEY,
        base_url=BASE_URL,
        model=MODEL,
        verbose=True
    )
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit']:
                print("再见! 👋")
                break
            
            if user_input.lower() == 'reset':
                agent.reset()
                print("[对话已重置]")
                continue
            
            response = agent.chat(user_input)
            
        except KeyboardInterrupt:
            print("\n再见! 👋")
            break
        except Exception as e:
            print(f"[错误]: {e}")


def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                    ReAct Agent - 推理与行动循环                        ║
╠══════════════════════════════════════════════════════════════════════╣
║  基于 Reasoning + Acting 架构的智能助手                                ║
║  支持工具调用、多轮对话、多 Agent 路由                                  ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    print("请选择运行模式:")
    print("1. 单 Agent 演示")
    print("2. 多 Agent 路由演示")
    print("3. 交互式对话")
    print("4. 退出")
    
    while True:
        try:
            choice = input("\n请输入选项 (1-4): ").strip()
            
            if choice == '1':
                demo_single_agent()
            elif choice == '2':
                demo_multi_agent()
            elif choice == '3':
                interactive_mode()
            elif choice == '4':
                print("再见! 👋")
                break
            else:
                print("无效选项，请输入 1-4")
                
        except KeyboardInterrupt:
            print("\n再见! 👋")
            break
        except Exception as e:
            print(f"[错误]: {e}")


if __name__ == "__main__":
    main()

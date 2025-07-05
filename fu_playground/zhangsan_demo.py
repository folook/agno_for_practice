#!/usr/bin/env python3
"""
简化版Agentic RAG Demo - 验证多轮推理能力
"""

from typing import Optional
from agno.agent import Agent
from agno.models.openai import OpenAIChat


# Mock数据存储
mock_db = {
    "张三": {
        "爱好": "张三喜欢的爱好和李四相似"
    },
    "李四": {
        "爱好": "李四的爱好是吃苹果"
    }
}

# 记录召回历史
recall_history = []


def recall(agent: Agent, round_num: int) -> str:
    """
    Mock召回工具
    Args:
        round_num: 召回轮次，1=第一轮，2=第二轮
    """
    print(f"🔍 执行第{round_num}轮召回...")
    
    if round_num == 1:
        result = mock_db["张三"]["爱好"]
    elif round_num == 2:
        result = mock_db["李四"]["爱好"]
    else:
        result = "没有更多信息"
    
    recall_history.append({
        "round": round_num,
        "result": result
    })
    
    print(f"📝 召回结果: {result}")
    return result


def analyze(agent: Agent, question: str, current_info: str) -> str:
    """
    分析工具：判断当前信息是否足够，如果不够，返回下一步需要查询什么
    """
    print(f"🧠 执行信息分析...")
    print(f"   原始问题: {question}")
    print(f"   当前信息: {current_info}")
    
    if "张三的爱好" in question:
        if "张三喜欢的爱好和李四相似" in current_info and "李四的爱好是" not in current_info:
            analysis = "信息不足，需要查询：李四的爱好是什么"
        elif "李四的爱好是吃苹果" in current_info:
            analysis = "信息充足，可以推理出答案：张三的爱好也是吃苹果"
        else:
            analysis = "需要先查询张三的信息"
    else:
        analysis = "当前信息状态未知"
    
    print(f"📊 分析结果: {analysis}")
    return analysis


def get_simple_rag_agent() -> Agent:
    """创建简化版的Agentic RAG Agent"""
    
    instructions = """
    你是一个智能RAG系统。处理用户问题时，请按以下步骤：
    
    1. 第一轮召回：使用recall工具(round_num=1)获取初始信息
    2. 分析：使用analyze工具判断信息是否充足，传入原始问题和当前获得的信息
    3. 如果信息不足：
       - 识别需要查询的内容（如"李四的爱好"）
       - 使用recall工具(round_num=2)进行第二轮召回
    4. 再次分析，得出最终答案
    
    重要：
    - 展示完整的推理过程，让用户看到多轮召回的效果
    - analyze工具需要两个参数：question（原始问题）和current_info（当前收集到的所有信息）
    """
    
    return Agent(
        name="Simple Agentic RAG",
        agent_id="simple-rag",
        model=OpenAIChat(id="gpt-4"),
        instructions=instructions,
        tools=[recall, analyze],
        markdown=True,
        show_tool_calls=True,  # 显示工具调用过程
        debug_mode=True
    )


def main():
    """运行演示"""
    print("🚀 简化版 Agentic RAG Demo")
    print("=" * 60)
    print("📋 测试场景：问'张三的爱好是什么'")
    print("   预期流程：")
    print("   1. 第一轮召回 → '张三喜欢的爱好和李四相似'")
    print("   2. 分析发现信息不足 → 需要查询李四的爱好")
    print("   3. 第二轮召回 → '李四的爱好是吃苹果'")
    print("   4. 推理得出 → 张三的爱好是吃苹果")
    print("=" * 60)
    
    # 清空历史记录
    global recall_history
    recall_history = []
    
    # 创建agent
    agent = get_simple_rag_agent()
    
    # 测试问题
    question = "张三的爱好是什么？"
    
    print(f"\n💬 用户问题: {question}")
    print("\n🤖 AI处理中...\n")
    print("-" * 60)
    
    try:
        # 运行agent
        response = agent.run(question, stream=False)
        
        print("-" * 60)
        print(f"\n✅ 最终回答: {response.content}")
        
        # 显示召回历史
        print("\n📚 召回历史:")
        for i, record in enumerate(recall_history, 1):
            print(f"   第{record['round']}轮: {record['result']}")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 演示完成！")


if __name__ == "__main__":
    main()
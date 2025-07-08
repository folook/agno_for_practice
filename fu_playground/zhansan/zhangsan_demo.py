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
        "爱好": "李四的爱好和王五一样"
    },
    "王五": {
        "爱好": "王五喜欢打篮球"
    }
}

# 记录召回历史
recall_history = []


def recall(agent: Agent, query: str) -> str:
    """
    智能召回工具：根据查询内容返回相关信息
    Args:
        query: 查询内容，如"张三的爱好"、"李四的爱好"等
    """
    print(f"🔍 执行召回: {query}")

    # 智能匹配查询内容
    if "张三" in query and "爱好" in query:
        result = mock_db["张三"]["爱好"]
    elif "李四" in query and "爱好" in query:
        result = mock_db["李四"]["爱好"]
    elif "王五" in query and "爱好" in query:
        result = mock_db["王五"]["爱好"]
    else:
        result = "未找到相关信息"

    recall_history.append({
        "query": query,
        "result": result
    })

    print(f"📝 召回结果: {result}")
    return result


def analyze(agent: Agent, question: str, current_info: str) -> str:
    """
    智能分析工具：使用Agent进行智能分析，判断当前信息是否足够
    """
    print(f"🧠 执行信息分析...")
    print(f"   原始问题: {question}")
    print(f"   当前信息: {current_info}")

    # 构造分析提示
    analysis_prompt = f"""
    请分析以下信息是否足够回答用户的问题：

    用户问题：{question}
    当前获得的信息：{current_info}

    请仔细分析：
    1. 当前信息是否足够直接回答问题？
    2. 如果不够，具体缺少什么关键信息？
    3. 如果需要更多信息，应该查询什么内容？

    请按以下格式返回：
    状态：[充足/不足]
    分析：[详细分析当前信息的完整性]
    建议：[如果不足，建议下一步查询什么具体内容]
    """

    try:
        # 使用传入的Agent进行分析
        from agno.agent import Agent
        from agno.models.openai import OpenAIChat

        # 创建临时的分析Agent
        analyzer = Agent(
            model=OpenAIChat(id="gpt-4"),
            name="Analyzer",
            instructions="你是一个信息分析专家，负责判断信息的完整性。"
        )

        # 运行分析
        analysis_response = analyzer.run(analysis_prompt, stream=False)
        analysis = analysis_response.content

        print(f"📊 分析结果: {analysis}")
        return analysis
    except Exception as e:
        print(f"❌ 分析过程中出错: {e}")
        return "无法进行分析"


def get_simple_rag_agent() -> Agent:
    """创建简化版的Agentic RAG Agent"""

    instructions = """
    你是一个智能RAG系统，具备多轮推理能力。处理用户问题时，请按以下步骤：

    1. 首先使用recall工具获取初始信息，传入用户的原始问题作为查询
    2. 使用analyze工具分析当前信息是否充足，传入原始问题和当前获得的信息
    3. 根据analyze工具的分析结果决定下一步：
       - 如果信息充足：直接回答问题
       - 如果信息不足：
         a. 使用recall工具搜索缺失的信息，传入具体的查询内容
         b. 获得新信息后，再次识别analyze工具建议查询的具体内容
         c. 如果不充足，循环执行步骤2和3，直到信息充足为止
    4. 最终基于所有收集到的信息给出完整答案

    重要原则：
    - 展示完整的推理过程，让用户看到多轮召回的效果
    - 不要预设答案，要基于实际召回的信息进行推理
    - 如果信息提到需要参考其他人或事物，主动识别并查询相关信息
    - 每次分析后要明确说明下一步行动
    - 每次 recall 之后需要调用 analyze 工具进行信息完整性分析，不可连续多次调用 recall
    """

    return Agent(
        name="Smart Agentic RAG",
        agent_id="smart-rag",
        model=OpenAIChat(id="gpt-4"),
        instructions=instructions,
        tools=[recall, analyze],
        markdown=True,
        show_tool_calls=True,  # 显示工具调用过程
        debug_mode=True
    )


def main():
    """运行演示"""
    print("🚀 智能版 Agentic RAG Demo")
    print("=" * 60)
    print("📋 测试场景：问'张三的爱好是什么'")
    print("   期望流程：")
    print("   1. Agent自动进行第一轮召回")
    print("   2. Agent智能分析信息完整性")
    print("   3. Agent自动识别需要查询李四的信息")
    print("   4. Agent自动进行第二轮召回或搜索")
    print("   5. Agent基于完整信息进行推理回答")
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
            print(f"   第{i}轮: {record['query']} -> {record['result']}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

    print("\n🎉 演示完成！")


if __name__ == "__main__":
    main()

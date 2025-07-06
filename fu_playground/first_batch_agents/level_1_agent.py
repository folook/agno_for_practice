# pip install -U agno anthropic yfinance
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.yfinance import YFinanceTools

from agno.models.openai import OpenAIChat

agent = Agent(
    # model=OpenAIChat(id="gpt-4"),
    model=Claude(id="claude-sonnet-4-20250514"),
    tools=[YFinanceTools(stock_price=True)],
    instructions="使用表格展示数据。不包含任何其他文本。",
    markdown=True,
)
agent.print_response("苹果的股价是多少？", stream=False)

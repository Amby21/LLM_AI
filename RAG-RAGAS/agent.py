from typing import TypedDict, Annotated , List
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_ollama import ChatOllama
from tools import tools
import operator

llm = ChatOllama(model="llama3", temperature=0)
llm_with_tools = llm.bind_tools(tools)

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage],operator.add]

def agent_node(state: AgentState) -> dict:
    response = llm_with_tools.invoke(state["messages"])
    return {"messages:" [response]}

tool_node = ToolNode(tools)

def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return "end"

workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent",should_continue,{"tools","tools","end": END})
workflow.add_edge("tools","agent")
app = workflow.compile()

last_run = {"question":"", "contexts":[], "answer":""}

def run_agent(question: str) -> str:
    last_run["question"] = question
    last_run["contexts"] = []
    last_run["answer"] = ""

    result = app.invoke({"messages":[HumanMessage(content=question)]})
    for msg in result["messages"]:
        if hasattr (msg,"content") and msg.__class__.__name__ =="ToolMessage":
            last_run["contexts"].append(msg.content)
    
    answer = result["messages"][-1].content
    last_run["answer"] = answer

    return answer
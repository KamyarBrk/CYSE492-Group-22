from typing import TypedDict, List, Union, Annotated, Sequence
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END
import subprocess




class AgentState(TypedDict):
    messages : Annotated[Sequence[BaseMessage], add_messages]


@tool
def add(a: int, b: int):
    """This is an addition function that adds two files together"""
    
    return a + b

@tool
def sub(a: int, b: int):
    """Subtraction Function"""
    return a - b

@tool
def mult(a: int, b: int):
    """Multiplication Function"""
    return a * b

@tool
def commands(command: str):
    """Allows the AI commands to run commands"""
    result = subprocess.run(
            command,
            shell=isinstance(command, str),
            capture_output=True,
            text=True
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode



tools = [add, sub, mult, commands]

llm = ChatOllama(model="llama3.1:8b").bind_tools(tools)


def recon_call(state:AgentState) -> AgentState:
    system_prompt = SystemMessage(content=
                "You are an AI assistant that is designed to autonimously carry out the recon phase of a cybersecurity penetration test for a windows computer with a user named Paul Dean"
                )
    response = llm.invoke([system_prompt] + state["messages"])
    return {"messages": [response]}


def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls:

        return "end"
    else:
        return "continue"

graph = StateGraph(AgentState)
graph.add_node("recon_agent", recon_call)

tool_node = ToolNode(tools=tools)
graph.add_node("tools", tool_node)

graph.set_entry_point("recon_agent")

graph.add_conditional_edges(
    "recon_agent",
    should_continue,
    {
        "continue": "tools",
        "end": END,
    },
)

graph.add_edge("tools", "recon_agent")

recon = graph.compile()

#conversation_history = []

def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()

user_input = input("Enter: ")
while user_input != 'exit':
    #conversation_history.append(HumanMessage(content=user_input))
    result = print_stream(recon.stream({"messages": user_input}, stream_mode="values"))
    #conversation_history = result["messages"]
    user_input = input("Enter: ")
    

'''with open("logging.txt", "w") as file:
    #file.write("Your Converstion Log:\n")

    for message in conversation_history:
        if isinstance(message, HumanMessage):
            file.write(f"You: {message.content}\n")
        elif isinstance(message, AIMessage):
            file.write(f"AI {message.content}\n\n")
    file.write('End of Converstion')

print("Converstation saved to logging.txt")'''

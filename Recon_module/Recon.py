from typing import TypedDict, List, Union, Annotated, Sequence  #defines dictionaries
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage  #defines messages by LANGCHAIN
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool #Decorator to define tools into the LLM
from langchain_ollama import ChatOllama  #Ollama LLM integration for LangChain
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode 
from langgraph.graph import StateGraph, START, END
import subprocess #runs shell commands


# Create the agent state as a dictionary

class AgentState(TypedDict): #this is the "memory state" of the agent
    #
    messages : Annotated[Sequence[BaseMessage], add_messages] # List of messages exchanged so far
#when new message is added, add_messages function is called to add it to the list
# Definition of tools such add, sub, mult, commands
@tool
def add(a: int, b: int):
    """This is an addition function that adds two files together"""
    #adds two integers a n b
    return a + b #returns the sum of a a n b

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



tools = [add, sub, mult, commands] #using these tools when needed

llm = ChatOllama(model="gpt-oss:20b").bind_tools(tools)

#AI is supposed to run recon commands on a windows machine using powershell
def recon_call(state:AgentState) -> AgentState: #this is the main function of the agent
    system_prompt = SystemMessage(content=
                "You are an AI assistant that is designed to autonimously carry out the recon phase of a cybersecurity penetration test for a windows computer using powershell commands"
                )
    response = llm.invoke([system_prompt] + state["messages"]) #feed the system prompt and the messages to the LLM then gets the response back
    return {"messages": [response]} #returns the agent state with the new message added.


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



def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()

user_input = input("Enter: ")
while user_input != 'exit':

    result = print_stream(recon.stream({"messages": user_input}, stream_mode="values"))
    user_input = input("Enter: ")


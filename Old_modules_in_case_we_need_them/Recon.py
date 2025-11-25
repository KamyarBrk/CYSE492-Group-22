from typing import TypedDict, List, Union, Annotated, Sequence  #defines dictionaries
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage  #defines messages by LANGCHAIN
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool #Decorator to define tools into the LLM
from langchain_ollama import ChatOllama  #Ollama LLM integration for LangChain
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode 
from langgraph.graph import StateGraph, START, END
import subprocess #runs shell commands
import nmap3  #nmap library for python

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

#new tool
@tool
def nmap_tool(target_domain: str): 
    '''Allows the AI to use nmap processes'''
    nmap = nmap3.Nmap()
    return (nmap.nmap_version_detection(target_domain))
            
@tool
def dnsenum_tool(target_domain: str):       
    '''Allows the AI to use dnsenum processes'''
    result = subprocess.run(     
        ["dnsenum", target_domain],
        capture_output=True,
        text=True
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


tools = [add, sub, mult, commands] #using these tools when needed

llm = ChatOllama(model="gpt-oss:20b").bind_tools(tools) #binding the tools to the LLM

#AI is supposed to run recon commands on a windows machine using powershell
def recon_call(state:AgentState) -> AgentState: #this is the main function of the agent
    system_prompt = SystemMessage(content=
                "You are an AI assistant that is designed to autonimously carry out the recon phase of a cybersecurity penetration test for a windows computer using powershell commands"
                )
    response = llm.invoke([system_prompt] + state["messages"]) #feed the system prompt and the messages to the LLM then gets the response back
    return {"messages": [response]} #returns the agent state with the new message added.


def should_continue(state: AgentState): #decides whether to continue or end the recon phase
    messages = state["messages"] #get the messages from the state
    last_message = messages[-1] #get the last message
    if not last_message.tool_calls: #if there are no tool calls in the last message, end the recon phase

        return "end"
    else: #if there are tool calls, continue the recon phase
        return "continue"

graph = StateGraph(AgentState) #creates a state graph using the AgentState dictionary
graph.add_node("recon_agent", recon_call) #adds the recon_call function as a node in the graph

tool_node = ToolNode(tools=tools) #adds the tools as a node in the graph
graph.add_node("tools", tool_node) #adds the tool node to the graph

graph.set_entry_point("recon_agent") #sets the entry point of the graph to the recon_agent node
#adds conditional edges to the graph based on the should_continue function
graph.add_conditional_edges(
    "recon_agent",
    should_continue,
    {
        "continue": "tools", #if continue, go to tools node
        "end": END, #if end, go to end node
    },
)
#adds edge from tools node back to recon_agent nodes
graph.add_edge("tools", "recon_agent")

recon = graph.compile() #compiles the graph into an executable form



def print_stream(stream): #prints the stream of messages from the LLM
    for s in stream: 
        message = s["messages"][-1] #get the last message
        if isinstance(message, tuple): #if the message is a tuple, print it
            print(message)
        else: 
            message.pretty_print()#pretty print the message

user_input = input("Enter: ") 
while user_input != 'exit':
    #Start the recon graph with the user's input as the initial message list
    result = print_stream(recon.stream({"messages": user_input}, stream_mode="values"))
    ## Ask for the next user input, or 'exit' to stop
    user_input = input("Enter: ")
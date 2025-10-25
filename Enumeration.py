
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import START, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict


class State(TypedDict):
    foo: str

# Subgraph

def subgraph_node_1(state: State):
    return {"foo": state["foo"] + "bar"}

prompt = ChatPromptTemplate.from_template(
    "You are an AI model that performs the enumeration phase of a penetration test."
    "\nQuestion: {question}\nAnswer:"
)

# The LLM model chosen 
enum = OllamaLLM(model="gemma3:4b")

llm_chain = prompt | enum | StrOutputParser()

def query_llm(question): 
    print(llm_chain.invoke({'question': question})) 

# --- ENUMERATION START ---

print("Welcome to the Enumeration Phase")

subgraph_builder = StateGraph(State)
subgraph_builder.add_node(subgraph_node_1)
subgraph_builder.add_edge(START, "subgraph_node_1")
subgraph = subgraph_builder.compile()  

# Parent graph

builder = StateGraph(State)
builder.add_node("node_1", subgraph)  
builder.add_edge(START, "node_1")

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)  

while True:
# Gets user input
    user = input("Enter-> ")
# If user enters 'exit' then the model is not queried and the program terminates. 
    if user.lower() == "exit":
        print('Goodbye!')
        break
# Queries the LLM with user input
    query_llm(user)



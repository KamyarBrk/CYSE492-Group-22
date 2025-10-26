from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import TypedDict, List, Union
from langchain_core.messages import HumanMessage, AIMessage
from langchain_ollama import OllamaLLM
from langgraph.graph import StateGraph, START, END


class AgentState(TypedDict):
    messages : List[Union[HumanMessage, AIMessage]]


Reco = OllamaLLM(model="gemma3:1b")

def process(state: AgentState) -> AgentState:
    response = Reco.invoke(state["messages"])

    state["messages"].append(AIMessage(content=response))
    print(f"\n {response}")
    return state

graph = StateGraph(AgentState)
graph.add_node("process", process)
graph.add_edge(START, "process")
graph.add_edge("process", END)
agent = graph.compile()

conversation_history = []



#Creates the question to be asked to the model
def query_recon_llm(question): 
    agent.invoke({'question': question})

user_input = input("Welcome to the reconnisance phase"
"\nEnter: ")
while user_input != 'exit':
    conversation_history.append(HumanMessage(content=user_input))
    result = agent.invoke({"messages": conversation_history})
    conversation_history = result["messages"]
    user_input = input("Enter: ")

with open("logging.txt", "w") as file:
    file.write("Your Converstion Log:\n")

    for message in conversation_history:
        if isinstance(message, HumanMessage):
            file.write(f"You: {message.content}\n")
        elif isinstance(message, AIMessage):
            file.write(f"AI {message.content}\n\n")
    file.write('End of Converstion')

print("Conversation saved to logging.txt")





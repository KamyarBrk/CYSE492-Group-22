from typing import TypedDict, List
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import START, StateGraph
from langgraph.checkpoint.memory import MemorySaver  # <- use MemorySaver
# pip install -U langgraph if needed

# ----- State -----
class State(TypedDict, total=False):
    question: str
    history: List[str]   # simple running log
    answer: str

# ----- LLM chain -----
prompt = ChatPromptTemplate.from_template(
    "You are an AI model that performs the enumeration phase of a penetration test.\n"
    "Conversation so far:\n{history}\n"
    "Question: {question}\nAnswer:"
)
enum = OllamaLLM(model="gemma3:1b")
llm_chain = prompt | enum | StrOutputParser()

# ----- Node(s) -----
def enum_node(state: State) -> State:
    hist_str = "\n".join(state.get("history", []))
    ans = llm_chain.invoke({"question": state["question"], "history": hist_str})
    new_hist = state.get("history", []) + [f"Q: {state['question']}", f"A: {ans}"]
    return {"answer": ans, "history": new_hist}

# ----- Graph -----
builder = StateGraph(State)
builder.add_node("enumerate", enum_node)
builder.add_edge(START, "enumerate")

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

print("Welcome to the Enumeration Phase")
THREAD_ID = "enum-session-1"  # anything stable per session

while True:
    user = input("Enter-> ")
    if user.lower() == "exit":
        print("Goodbye!")
        break

    # Each turn we pass the new question; prior state is restored via thread_id.
    result = graph.invoke(
        {"question": user}, 
        config={"configurable": {"thread_id": THREAD_ID}}
    )
    print(result["answer"])

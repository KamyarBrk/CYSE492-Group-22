from typing import TypedDict, List
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import START, StateGraph
from langgraph.checkpoint.memory import MemorySaver  # <- use MemorySaver
# pip install -U langgraph if needed
import subprocess
import sys

# ----- State -----

# This is a dictionary that contains everything that is passed to the AI
class State(TypedDict, total=False): 
# The user's question
    question: str
# The conversation history so far (simple running log)
    history: List[str]
# The AI's latest answer
    answer: str

# ----- LLM chain -----

# Prompt given to AI every time it is queried (asked a question)
prompt = ChatPromptTemplate.from_template(
    "You are an AI model that performs the enumeration phase of a penetration test.\n"
    "Conversation so far:\n{history}\n"
    "Question: {question}\nAnswer:"
)


def select_model_func():
    proc = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True)

    # Extract model names
    installed_models = []
    for line in proc.stdout.splitlines():
        if line.strip():
            # Get model name before ':' (e.g., "gamma:latest" -> "gamma")
            model_name = line.split()[0]
            installed_models.append(model_name)
    
    print("Select a model for enumeration phase:")
    print("1: gemma3:1b\n2: gemma3:4b\n3: gemma3:12b\n4: gemma3:27b\n5: gpt-oss:20b")
    model_dict = {
        1: "gemma3:1b",
        2: "gemma3:4b",
        3: "gemma3:12b",
        4: "gemma3:27b",
        5: "gpt-oss:20b"
    }
    model_option = int(input("Enter model option->  "))
    while model_dict[model_option] not in installed_models:
        print("The selected model is not available. Please choose from the list above.")
        print(f"Installed Models:{installed_models[1:]}")
        model_option = int(input("Enter model option->  "))
    selected_model=None
    for k,v in model_dict.items():
        if model_option==k:
            selected_model=v
            break

    print(f"Selected model: {selected_model}")
    return selected_model

selected_model=select_model_func()
enum = OllamaLLM(model=selected_model, temperature=0.3)
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


# ----- SESSION START -----

print("Welcome to the Enumeration Phase")
THREAD_ID = "enum-session-1"  # anything stable per session

while True:
    user = input("Enter-> ")
    if user.lower() == "exit":
        print("Goodbye!")
        break

    # Each turn we pass the new question; prior state is restored via thread_id.
    try:
        result = graph.invoke(
            {"question": user}, 
            config={"configurable": {"thread_id": THREAD_ID}}
        )
        print(result["answer"])
    except Exception as e:
        print(f"Error during invocation: {e}")
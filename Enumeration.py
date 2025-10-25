from typing import TypedDict, List
from langchain_ollama import OllamaLLM  # LLM interface for Ollama models
from langchain_core.prompts import ChatPromptTemplate  # Template for AI prompts
from langchain_core.output_parsers import StrOutputParser  # Parse AI output as string
from langgraph.graph import START, StateGraph  # State graph for workflow nodes
from langgraph.checkpoint.memory import MemorySaver  # Memory checkpointing
# pip install -U langgraph if needed
import subprocess
import sys

# ----- State -----
# State is a dictionary representing the current context of the conversation
class State(TypedDict, total=False): 
    # The user's current question
    question: str
    # The history of previous exchanges (list of Q&A strings)
    history: List[str]
    # The AI's last answer
    answer: str

# ----- LLM chain -----
# Define the prompt template used for the AI
prompt = ChatPromptTemplate.from_template(
    "You are an AI model that performs the enumeration phase of a penetration test.\n"
    "Conversation so far:\n{history}\n"
    "Question: {question}\nAnswer:"
)
# The {history} and {question} placeholders will be filled dynamically at runtime

# Function to select which Ollama model to use
def select_model_func():
    # Get the list of installed Ollama models via CLI
    proc = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True)

    # Extract model names from the CLI output
    installed_models = []
    for line in proc.stdout.splitlines():
        if line.strip():
            # Assume model name comes before the first space
            model_name = line.split()[0]
            installed_models.append(model_name)
    
    # Display available options to the user
    print("Select a model for enumeration phase:")
    print("1: gemma3:1b\n2: gemma3:4b\n3: gemma3:12b\n4: gemma3:27b\n5: gpt-oss:20b")
    model_dict = {
        1: "gemma3:1b",
        2: "gemma3:4b",
        3: "gemma3:12b",
        4: "gemma3:27b",
        5: "gpt-oss:20b"
    }
    
    # Ask user to select a model option
    model_option = int(input("Enter model option->  "))
    # Ensure selected model is actually installed
    while model_dict[model_option] not in installed_models:
        print("The selected model is not available. Please choose from the list above.")
        print(f"Installed Models:{installed_models[1:]}")
        model_option = int(input("Enter model option->  "))
    
    # Determine the selected model string
    selected_model = None
    for k, v in model_dict.items():
        if model_option == k:
            selected_model = v
            break

    print(f"Selected model: {selected_model}")
    return selected_model

# Prompt user to select a model
selected_model = select_model_func()

# Initialize the Ollama LLM with the chosen model and a low temperature for deterministic output
enum = OllamaLLM(model=selected_model, temperature=0.3)

# Create a chain: prompt -> model -> string parser
llm_chain = prompt | enum | StrOutputParser()

# ----- Node(s) -----
# Node function representing the "enumerate" step in the workflow
def enum_node(state: State) -> State:
    # Convert the list of previous Q&A into a single string for context
    hist_str = "\n".join(state.get("history", []))
    # Invoke the LLM chain with the current question and history
    ans = llm_chain.invoke({"question": state["question"], "history": hist_str})
    # Update history with the new Q&A
    new_hist = state.get("history", []) + [f"Q: {state['question']}", f"A: {ans}"]
    # Return updated state including answer and history
    return {"answer": ans, "history": new_hist}

# ----- Graph -----
# Build a state graph to manage workflow nodes
builder = StateGraph(State)
builder.add_node("enumerate", enum_node)  # Add "enumerate" node
builder.add_edge(START, "enumerate")  # Connect the start to "enumerate"

# Use memory checkpointing to save/reload session state
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# ----- SESSION START -----
print("Welcome to the Enumeration Phase")
THREAD_ID = "enum-session-1"  # Unique identifier for this session

# Main loop: accept user input and process via graph
while True:
    user = input("Enter-> ")
    if user.lower() == "exit":
        print("Goodbye!")
        break

    # Each turn we pass the new question; prior state is restored via thread_id
    try:
        result = graph.invoke(
            {"question": user}, 
            config={"configurable": {"thread_id": THREAD_ID}}
        )
        # Print the AI's answer
        print(result["answer"])
    
    except Exception as e:
        # Catch and display any errors in invocation
        print(f"Error during invocation: {e}")
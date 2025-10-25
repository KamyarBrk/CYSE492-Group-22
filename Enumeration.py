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

# Define a dictionary structure for storing AI interaction state
class State(TypedDict, total=False):
    # The user's current question
    question: str
    # Conversation history, stored as a list of strings
    history: List[str]
    # The AI's most recent answer
    answer: str

# ----- LLM chain -----

# Define the prompt template given to the AI each time it is queried
prompt = ChatPromptTemplate.from_template(
    "You are an AI model that performs the enumeration phase of a penetration test.\n"
    "Conversation so far:\n{history}\n"
    "Question: {question}\nAnswer:"
)

# ----- Model selection -----
def select_model_func():
    # Run 'ollama list' to get all installed Ollama models
    proc = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True)

    # Extract model names from command output
    installed_models = []
    for line in proc.stdout.splitlines():
        if line.strip():  # skip empty lines
            # Get the model name (e.g., "gamma:latest" -> "gamma")
            model_name = line.split()[0]
            installed_models.append(model_name)
    
    # Show user a predefined list of models to choose from
    print("Select a model for enumeration phase:")
    print("1: gemma3:1b\n2: gemma3:4b\n3: gemma3:12b\n4: gemma3:27b\n5: gpt-oss:20b")
    
    # Map user input number to actual model names
    model_dict = {
        1: "gemma3:1b",
        2: "gemma3:4b",
        3: "gemma3:12b",
        4: "gemma3:27b",
        5: "gpt-oss:20b"
    }
    
    # Ask the user for their selection
    model_option = int(input("Enter model option->  "))
    
    # Check if selected model is installed
    while model_dict[model_option] not in installed_models:
        print("The selected model is not available. Please choose from the list above.")
        print(f"Installed Models:{installed_models[1:]}")
        model_option = int(input("Enter model option->  "))
    
    # Assign selected model
    selected_model = None
    for k, v in model_dict.items():
        if model_option == k:
            selected_model = v
            break

    print(f"Selected model: {selected_model}")
    return selected_model

# Get the selected model
selected_model = select_model_func()

# Create an Ollama LLM instance with a moderate temperature
enum = OllamaLLM(model=selected_model, temperature=0.3)

# Define the LLM chain: prompt -> LLM -> output parser
llm_chain = prompt | enum | StrOutputParser()

# ----- Node(s) -----

# Define the node function for enumeration
def enum_node(state: State) -> State:
    # Convert the history list to a single string for prompt
    hist_str = "\n".join(state.get("history", []))
    # Invoke the LLM chain with the question and conversation history
    ans = llm_chain.invoke({"question": state["question"], "history": hist_str})
    # Update history with the new Q&A
    new_hist = state.get("history", []) + [f"Q: {state['question']}", f"A: {ans}"]
    # Return updated state with answer and history
    return {"answer": ans, "history": new_hist}

# ----- Graph -----

# Initialize a state graph for managing nodes and transitions
builder = StateGraph(State)
# Add enumeration node
builder.add_node("enumerate", enum_node)
# Connect start node to enumeration node
builder.add_edge(START, "enumerate")

# Initialize memory saver for checkpointing conversation state
checkpointer = MemorySaver()
# Compile the graph with the checkpointer
graph = builder.compile(checkpointer=checkpointer)

# ----- SESSION START -----

print("Welcome to the Enumeration Phase")
THREAD_ID = "enum-session-1"  # stable identifier for session/thread

# Main interactive loop
while True:
    user = input("Enter-> ")
    if user.lower() == "exit":
        print("Goodbye!")
        break

    # Pass the new question to the graph; prior state restored via thread_id
    try:
        result = graph.invoke(
            {"question": user}, 
            config={"configurable": {"thread_id": THREAD_ID}}
        )
        # Print the AI's answer
        print(result["answer"])
    
    except Exception as e:
        # Catch any errors during invocation
        print(f"Error during invocation: {e}")
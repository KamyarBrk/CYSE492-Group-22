from typing import TypedDict, List, Iterable, Annotated, Sequence
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END
import subprocess
import json
from pathlib import Path


# --- Simple file-backed conversation memory settings ---
MEMORY_FILE = Path("enumeration_memory.json")
MAX_MEMORY_MESSAGES = 200  # keep only the last N messages to avoid unbounded growth

def _msg_role(m: BaseMessage) -> str:
    if isinstance(m, SystemMessage):
        return "system"
    if isinstance(m, HumanMessage):
        return "human"
    if isinstance(m, AIMessage):
        return "ai"
    # fallback for unknown BaseMessage subclasses (e.g., ToolMessage)
    return m.__class__.__name__.lower()

def save_memory(messages: Iterable[BaseMessage], memory_file: Path = MEMORY_FILE):
    """Serialize messages to disk as a list of {role, content} dicts."""
    out = []
    for m in messages:
        # BaseMessage subclasses should have .content
        try:
            content = m.content
        except Exception:
            # Fallback: string-ify if message doesn't expose .content
            content = str(m)
        out.append({"role": _msg_role(m), "content": content})
    # Trim to last MAX_MEMORY_MESSAGES to keep the file small
    out = out[-MAX_MEMORY_MESSAGES:]
    memory_file.write_text(json.dumps(out, indent=2), encoding="utf-8")

def load_memory(memory_file: Path = MEMORY_FILE, max_messages: int = MAX_MEMORY_MESSAGES) -> List[BaseMessage]:
    """Load messages from disk and return them as BaseMessage objects (most recent last)."""
    if not memory_file.exists():
        return []
    try:
        data = json.loads(memory_file.read_text(encoding="utf-8"))
    except Exception:
        return []
    msgs: List[BaseMessage] = []
    for item in data[-max_messages:]:
        role = item.get("role", "human")
        content = item.get("content", "") or ""
        if role == "system":
            msgs.append(SystemMessage(content=content))
        elif role == "human":
            msgs.append(HumanMessage(content=content))
        elif role == "ai":
            msgs.append(AIMessage(content=content))
        else:
            # Unknown roles map to HumanMessage so the model can see them
            msgs.append(HumanMessage(content=content))
    return msgs

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
    
    # Map user input number to actual model names
    model_dict = {
        1: "llama3.2:latest",
        2: "gpt-oss:20b"
    }
    
    while True:
        # Show user a predefined list of models to choose from
        print("\nSelect a model for enumeration phase:")
        print("1: llama3.2:latest (less powerful)\n2: gpt-oss:20b (most powerful)")
        print('')
        try:
            # Ask the user for their selection
            model_option = input("Enter model option (number) -> ")
            if model_option.lower() == "exit":
                print("Goodbye!")
                exit()
            model_option = int(model_option)

            if not model_option in model_dict:
                raise
            else:
                # Check if selected model is installed
                while model_dict[model_option] not in installed_models:
                    print("The selected model is not available. Please choose from the list above.")
                    print(f"Installed Models: {installed_models[1:]}")
                    model_option = int(input("Enter model option-> "))
                break
        except Exception:
            print("What you entered was invalid. Please enter a valid number.")
    
    # Assign selected model
    selected_model = None
    for k, v in model_dict.items():
        if model_option == k:
            selected_model = v
            break

    print(f"Selected model: {selected_model}")
    return selected_model

# ---------------------------------------------------------------------
# Your original tool + LLM setup
# ---------------------------------------------------------------------
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

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


tools = [commands]


# ---------------------------------------------------------------------
# enum_call now uses file-backed memory (this is the enum_call that will be
# registered in the graph below, BEFORE compilation)
# ---------------------------------------------------------------------
def enum_call(state: AgentState) -> AgentState:
    # Load persisted memory (chronological, oldest first)
    mem_msgs = load_memory()

    # Normalize incoming state["messages"] into a list of BaseMessage objects
    incoming: List[BaseMessage] = []
    for m in state["messages"]:
        # If the graph/system already gave BaseMessage subclasses, keep them.
        if isinstance(m, BaseMessage):
            incoming.append(m)
        else:
            # If raw string was passed (or other), coerce into HumanMessage
            incoming.append(HumanMessage(content=str(m)))

    system_prompt = SystemMessage(
        content="You are an AI model that performs the enumeration phase of a penetration test."
    )

    # Compose final prompt: system -> memory -> incoming conversation
    full_prompt = [system_prompt] + mem_msgs + incoming

    response = llm.invoke(full_prompt)

    # Update stored memory: append the incoming messages + the assistant response
    updated_memory = mem_msgs + incoming + [response]
    save_memory(updated_memory)

    return {"messages": [response]}


# ---------------------------------------------------------------------
# Graph creation (this will pick up the enum_call defined above)
# ---------------------------------------------------------------------
def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    # Tool-calls are only present when the model returned them; check attribute presence
    if not getattr(last_message, "tool_calls", None):
        return "end"
    else:
        return "continue"


graph = StateGraph(AgentState)
graph.add_node("enum_agent", enum_call)

tool_node = ToolNode(tools=tools)
graph.add_node("tools", tool_node)

graph.set_entry_point("enum_agent")

graph.add_conditional_edges(
    "enum_agent",
    should_continue,
    {
        "continue": "tools",
        "end": END,
    },
)

graph.add_edge("tools", "enum_agent")

enum = graph.compile()


# ---------------------------------------------------------------------
# Stream printing + interactive loop (single loop; passes HumanMessage)
# ---------------------------------------------------------------------
def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            try:
                message.pretty_print()
            except Exception:
                # Fallback: print raw
                print(message)


if __name__ == "__main__":
    # Open the file in write mode ('w') and delete its contents
    open("enumeration_memory.json", 'w').close()
    llm = ChatOllama(model=select_model_func()).bind_tools(tools)
    user_input = input("\nEnter: ")
    while user_input != 'exit':
        # convert raw string input to a HumanMessage and pass as a single-item list
        human_msg = HumanMessage(content=user_input)
        _ = print_stream(enum.stream({"messages": [human_msg]}, stream_mode="values"))
        user_input = input("\nEnter: ")
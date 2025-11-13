This is CYSE 492 Group 22's repo for their agentic penetration testing AI. It is written entirely in Python, and uses existing AI models to carry out its tasks. Retrevial Augmented Generation (RAG) is used to provide additional information to the models without the need to retrain them. 

The overal system is built out of several different modules to carry out the steps of penetration testing:

-Recon
-Enumeration
-Exploitation
-Post-Exploitation

These modules are designed to run sequentially, and pass information to each other. They are centered around two open-source tools: Langgraph and Ollama. Langgraph allows for the easy construction of stateful, multi-agent programs by creating workflows as graphs. Ollama allows us to interact with different AI models using the same API (Application programming interface). This means we can easily switch bewtween AI models without rewriting code.


Some Python packages 

**Local Python Environment Setup Instructions**

1. Clone the repo locally in VS code
2. Open the folder in VS Code
3. Run `.\setup.ps1` (Windows) or `./setup.sh` (macOS/Linux) in the terminal. Note you need Python 3.11 or 3.12. 

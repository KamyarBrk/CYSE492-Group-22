This is CYSE 492 Group 22's repo for their agentic penetration testing AI. 

It uses several different modules to carry out the steps of penetration testing:

-Recon
-Enumeration
-Exploitation
-Post-Exploitation

These modules are designed to run sequentially, and pass information to each other. They are centered around two open-source tools: Langgraph and Ollama. Langgraph allows for the easy construction of stateful, multi-agent programs by creating workflows as graphs. 


**Local Python Environment Setup Instructions**

1. Clone the repo locally in VS code
2. Open the folder in VS Code
3. Run `.\setup.ps1` (Windows) or `./setup.sh` (macOS/Linux) in the terminal. Note you need Python 3.11 or 3.12. 

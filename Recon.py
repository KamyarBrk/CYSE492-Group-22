
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os


#Initializes the prompt for the chatbot, establishing it is a recon module and sets place for user input
init = ChatPromptTemplate.from_template("You are an AI model that performs the reconnaissance phase of a penetration test."
    "\nQuestion: {question}\nAnswer:")

Reco = OllamaLLM(model="gemma3:1b")

#Chains the prompt with the initialized prompt, ai, and an output parser for formatting
recon_chain = init | Reco | StrOutputParser()

#Creates the question to be asked to the model
def query_recon_llm(question): 
    print(recon_chain.invoke({'question': question})) 

#Initial user prompt which will query the chatbot with the response
print("Welcome to the Reconnaissance Phase")
while True:
    user = input("Enter-> ")
    query_recon_llm(user)
'''
Theoretical connection to Enumeration Module:

import Enumeration.py

Enum_user = query_recon_llm(question)
query_llm(Enum_user)

Then the output could either be printed as it goes or have the enumeration handle the printing
'''
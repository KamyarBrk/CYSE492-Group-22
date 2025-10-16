
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser



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
while True:
# Gets user input
    user = input("Enter-> ")
# If user enters 'exit' then the model is not queried and the program terminates. 
    if user.lower() == "exit":
        print('Goodbye!')
        break
# Queries the LLM with user input
    query_llm(user)

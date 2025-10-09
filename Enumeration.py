
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser



prompt = ChatPromptTemplate.from_template(
    "You are an AI model that performs the enumeration phase of a penetration test."
    "\nQuestion: {question}\nAnswer:"
)


enum = OllamaLLM(model="gemma3:1b")

llm_chain = prompt | enum | StrOutputParser()

def query_llm(question): 
    print(llm_chain.invoke({'question': question})) 

print("Welcome to the Enumeration Phase")
while True:
    user = input("Enter-> ")
    query_llm(user)


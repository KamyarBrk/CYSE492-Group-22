from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
load_dotenv()



prompt = ChatPromptTemplate.from_template(
    "You are an AI model that performs the enumeration phase of a penetration test."
    "\nQuestion: {question}\nAnswer:"
)


llm = ChatOpenAI(model="gpt-5-nano",temperature=0)

llm_chain = prompt | llm | StrOutputParser()

def query_llm(question): 
    print(llm_chain.invoke({'question': question})) 

print("Welcome to the Enumeration Phase")
while True:
    user = input("Enter-> ")
    query_llm(user)

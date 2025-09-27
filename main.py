from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model="gpt-5-nano", temperature=0)
resp = llm.invoke("Hello from inside the Dev Container!")
print(resp.content)

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

llm = ChatOpenAI(
    model="openrouter/free",
    api_key=os.getenv("API_TOKEN"),
    base_url="https://openrouter.ai/api/v1"
)

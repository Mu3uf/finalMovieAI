
import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from app.tools.recommend_unwatched_movies import recommend_unwatched_movies
from app.agent.prompts import system_prompt
from app.tools.search_movie import search_movie
from app.tools.trending_movies import trending_movies

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is missing from .env")

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    google_api_key=GOOGLE_API_KEY,
    temperature=0,
    max_retries=2,
)

tools = [
    search_movie,
    trending_movies,
    recommend_unwatched_movies
]

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt,
)
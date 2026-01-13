from graphiti_core import Graphiti
from openai import AsyncOpenAI
from graphiti_core.embedder.azure_openai import AzureOpenAIEmbedderClient
from graphiti_core.llm_client.azure_openai_client import AzureOpenAILLMClient
from graphiti_core.llm_client.config import LLMConfig
import os

neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')

open_ai_base_url = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1/')
open_ai_api_key = os.environ.get('OPENAI_API_KEY', None)

azure_client = AsyncOpenAI(
    base_url=open_ai_base_url,
    api_key=open_ai_api_key,
)

llm_client = AzureOpenAILLMClient(
    azure_client=azure_client,
    config=LLMConfig(model="gpt-5-mini", small_model="gpt-5-mini")  # Your Azure deployment name
)

embedder_client = AzureOpenAIEmbedderClient(
    azure_client=azure_client,
    model="text-embedding-3-large"  # Your Azure embedding deployment name
)

async def initialize_db(graphiti: Graphiti):
    await graphiti.build_indices_and_constraints()
    print("Graphiti schema initialized")

_graphiti: Graphiti | None = None

 # Initialize Graphiti with Neo4j connection
async def get_graphiti() -> Graphiti:
    global _graphiti
    if _graphiti is None:
        _graphiti = Graphiti(
            neo4j_uri,
            neo4j_user,
            neo4j_password,
            llm_client,
            embedder_client
        )

        await initialize_db(_graphiti)

    return _graphiti

async def close_graphiti():
    global _graphiti
    if _graphiti is not None:
        await _graphiti.close() 
        _graphiti = None
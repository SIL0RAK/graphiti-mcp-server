import json
from graphiti_core import Graphiti
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF
from openai import AsyncOpenAI
from graphiti_core.embedder.azure_openai import AzureOpenAIEmbedderClient
from graphiti_core.llm_client.azure_openai_client import AzureOpenAILLMClient
from graphiti_core.llm_client.config import LLMConfig
import os
from pydantic import BaseModel, Field
from typing import Union
from datetime import datetime, timezone
from graphiti_core.nodes import EpisodeType

def register_tools(mcp):
    """
        Define a function that takes mcp and registers tools by using FastMCP decorator
    """

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

    # Initialize Graphiti with Neo4j connection
    graphiti = Graphiti(
        neo4j_uri,
        neo4j_user,
        neo4j_password,
        llm_client,
        embedder_client
    )

    @mcp.tool(
        name="search",
        description="Allows user to search trough reference DB to find knowledge about existing company projects"
    )
    async def get_data_value(query: str) -> str:
        node_search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        node_search_config.limit = 5
    
        results = await graphiti.search(query)

        data = ""

        for result in results:
                data += f'UUID: {result.uuid}'
                data += f'Fact: {result.fact}'
                if hasattr(result, 'valid_at') and result.valid_at:
                    data += f'Valid from: {result.valid_at}'
                if hasattr(result, 'invalid_at') and result.invalid_at:
                     data += f'Valid until: {result.invalid_at}'
                data += '---'

        return data
    
    class Episode(BaseModel):
        name: str = Field(..., description="The name of the episode")
        content: Union[str, dict] = Field(..., description="The body/content of the episode")
        type: str = Field(..., description="The type of the episode", enum=["text", "json"])
        description: str = Field(..., description="A brief description of the episode")

    @mcp.tool(
        name="set_data",
        description="Uploads data to database"
    )
    async def set_data(episode: Episode) -> str:
        print("setdata called")
        try:
            if (episode.type == "json"):
                type = EpisodeType.text
            else:
                type = EpisodeType.text

            await graphiti.add_episode(
                name=episode.name,
                episode_body=episode.content
                if isinstance(episode.content, str)
                else json.dumps(episode.content),
                source=type,
                source_description=episode.description,
                reference_time=datetime.now(timezone.utc)
            )

            print("OK")

            return "OK"
        except Exception as e:
            print("Error: " + str(e))
            return f"Error: {str(e)}"
    
    return [
        get_data_value,
        set_data,
    ]

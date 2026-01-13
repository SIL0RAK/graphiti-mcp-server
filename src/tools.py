from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF
from pydantic import BaseModel, Field
from typing import Union
from datetime import datetime, timezone
from graphiti_core.nodes import EpisodeType
import traceback

from graphiti import get_graphiti

def register_tools(mcp):
    """
        Define a function that takes mcp and registers tools by using FastMCP decorator
    """

    @mcp.tool(
        name="search",
        description="Allows user to search trough reference DB to find knowledge about existing company projects"
    )
    async def get_data_value(query: str) -> str:
        node_search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        node_search_config.limit = 5
        graphiti = await get_graphiti()
    
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
        content: str = Field(..., description="The body/content of the episode")
        description: str = Field(..., description="A brief description of the episode")

    @mcp.tool(
        name="set_data",
        description="Uploads data to database"
    )
    async def set_data(episode: Episode) -> str:
        print("setdata called")
        try:
            graphiti = await get_graphiti()

            await graphiti.add_episode(
                name=episode.name,
                episode_body=episode.content,
                source=EpisodeType.text,
                source_description=episode.description,
                reference_time=datetime.now(timezone.utc)
            )

            return "OK"

        except Exception as e:

            print("Error: " + str(e))
            print(traceback.format_exc())
            return f"Error: {str(e)}"

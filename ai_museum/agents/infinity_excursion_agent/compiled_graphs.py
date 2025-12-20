from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph.state import CompiledStateGraph
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from ai_museum.agents.infinity_excursion_agent.expert import (
    ExpertState,
    InitExpertState,
    expert_graph,
)
from ai_museum.agents.infinity_excursion_agent.guide import (
    GuideState,
    InitGuideState,
    guide_graph,
)
from ai_museum.db.init import psycopg_connection_uri

guide_app: CompiledStateGraph[GuideState, None, InitGuideState, GuideState] = None  # pyright: ignore[reportAssignmentType]
expert_app: CompiledStateGraph[ExpertState, None, InitExpertState, ExpertState] = None  # pyright: ignore[reportAssignmentType]


async def init_graphs():
    checkpointer = AsyncPostgresSaver(
        await AsyncConnection.connect(
            psycopg_connection_uri,
            autocommit=True,
            row_factory=dict_row,  # pyright: ignore[reportArgumentType]
        ),
    )

    global guide_app, expert_app

    guide_app = guide_graph.compile(checkpointer=checkpointer)
    expert_app = expert_graph.compile(checkpointer=checkpointer)

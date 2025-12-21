from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph.state import CompiledStateGraph
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

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
from ai_museum.db.init import psycopg_conninfo

guide_app: CompiledStateGraph[GuideState, None, InitGuideState, GuideState] = None  # pyright: ignore[reportAssignmentType]
expert_app: CompiledStateGraph[ExpertState, None, InitExpertState, ExpertState] = None  # pyright: ignore[reportAssignmentType]


async def init_graphs():
    checkpointer = AsyncPostgresSaver(
        AsyncConnectionPool(
            psycopg_conninfo,
            kwargs={
                "autocommit": True,
                "row_factory": dict_row,
            },
            min_size=2,
        )
    )

    global guide_app, expert_app

    guide_app = guide_graph.compile(checkpointer=checkpointer)
    expert_app = expert_graph.compile(checkpointer=checkpointer)

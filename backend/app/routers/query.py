"""Q&A query router — POST /query"""
from fastapi import APIRouter, Request

from app.models import AnswerResponse, QueryRequest
from app.utils.logger import get_logger

log = get_logger(__name__)
router = APIRouter()


@router.post("/query")
async def post_query(request: Request, body: QueryRequest) -> AnswerResponse:
    graph = request.app.state.qa_graph
    settings = request.app.state.settings

    as_of_date = body.as_of_date or settings.simulated_today

    log.info(f"Query received: '{body.question}' as_of_date={as_of_date}")

    initial_state = {
        "question": body.question,
        "as_of_date": as_of_date,
        "error": None,
    }

    final_state = await graph.ainvoke(initial_state)
    return final_state["response"]

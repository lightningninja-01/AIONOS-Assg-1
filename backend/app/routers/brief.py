"""Brief generation router — GET /brief"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.engine.status_resolver import resolve_category, resolve_status
from app.models import CommitmentCategory, CommitmentStatus, DailyBrief
from app.utils.logger import get_logger

log = get_logger(__name__)
router = APIRouter()


@router.get("/brief")
async def get_brief(request: Request, as_of_date: str | None = None) -> DailyBrief:
    store = request.app.state.commitment_store
    settings = request.app.state.settings

    if as_of_date is None:
        as_of_date = settings.simulated_today

    all_commitments = store.all()

    my_actions = []
    waiting_on_others = []
    ownership_unclear = []

    for c in all_commitments:
        # Recalculate status against the requested date
        status = resolve_status(c.deadline_latest, c.evidence, as_of_date)
        c = c.model_copy(update={"status": status})

        # Recalculate category against requested date + updated status
        cat_str = resolve_category(c.owner, c.ownership_status.value, as_of_date, status)
        c = c.model_copy(update={"category": CommitmentCategory(cat_str)})

        if c.category == CommitmentCategory.ownership_unclear:
            ownership_unclear.append(c)
        elif c.category == CommitmentCategory.my_action:
            my_actions.append(c)
        else:
            waiting_on_others.append(c)

    # Sort: overdue > due_today > outstanding > completed
    _urgency = {
        CommitmentStatus.overdue: 0,
        CommitmentStatus.due_today: 1,
        CommitmentStatus.outstanding: 2,
        CommitmentStatus.unclear: 3,
        CommitmentStatus.completed: 4,
    }
    my_actions.sort(key=lambda c: _urgency.get(c.status, 5))
    waiting_on_others.sort(key=lambda c: _urgency.get(c.status, 5))
    ownership_unclear.sort(key=lambda c: c.deadline_latest or "9999")

    log.info(f"Brief for {as_of_date}: {len(my_actions)} actions, {len(waiting_on_others)} waiting, {len(ownership_unclear)} unclear")

    return DailyBrief(
        as_of_date=as_of_date,
        my_actions=my_actions,
        waiting_on_others=waiting_on_others,
        ownership_unclear=ownership_unclear,
    )

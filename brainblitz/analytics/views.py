from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from .mongo_aggregation import average_score_per_category
from .mongo_client import get_user_attempts
from .mongodb_config import mongo_enabled


@staff_member_required
def demo(request):
    recent: list = []
    aggregate_rows: list = []
    if mongo_enabled():
        recent = get_user_attempts(request.user.id, limit=15)
        aggregate_rows = average_score_per_category()
    return render(
        request,
        "analytics/demo.html",
        {
            "mongo_enabled": mongo_enabled(),
            "recent": recent,
            "aggregate_rows": aggregate_rows,
        },
    )

from fastapi import APIRouter, Depends
from app.core.metrics import metrics
from app.services.auth_service import require_admin

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/")
def get_metrics(current_user=Depends(require_admin)):
    return metrics.snapshot()

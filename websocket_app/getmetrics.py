import psutil
from fastapi import APIRouter

router = APIRouter()

@router.get("/metrics")
def get_metrics():
    memory = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.5)
    return {
        "memory_used_mb": round(memory.used / (1024 ** 2), 2),
        "memory_percent": memory.percent,
        "cpu_percent": cpu
    }
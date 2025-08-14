from fastapi import APIRouter, HTTPException
from app.plugins.manager import plugin_manager

router = APIRouter(prefix="/plugins", tags=["plugins"])

@router.get("/")
def list_plugins():
    return {"plugins": list(plugin_manager.plugins.keys())}

@router.post("/{plugin_name}")
def call_plugin(plugin_name: str, args: dict = {}):
    try:
        result = plugin_manager.call(plugin_name, **args)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

from typing import Any

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel
from pydantic import Field

from app.plugins.manager import plugin_manager

router = APIRouter(prefix="/plugins", tags=["plugins"])


class PluginCallRequest(BaseModel):
    args: dict[str, Any] = Field(default_factory=dict)


@router.get("/")
def list_plugins():
    return {"plugins": list(plugin_manager.plugins.keys())}


@router.post("/{plugin_name}")
def call_plugin(plugin_name: str, req: PluginCallRequest):
    try:
        result = plugin_manager.call(plugin_name, **req.args)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from None

"""REST 路由（架构文档 §6.1）。

支持主机动态增删改：
- POST /api/hosts — 添加主机
- PUT /api/hosts/{host_id} — 更新主机
- DELETE /api/hosts/{host_id} — 删除主机
- 修改会持久化到 hosts.yaml 并热更新监控
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request

from .config import HostConfig, _build_host, merge_thresholds, save_config, load_config
from .monitor import MonitorRegistry
import os

log = __import__("logging").getLogger("llamalens.api")

router = APIRouter(prefix="/api")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VALID_WINDOWS = (300, 900, 3600)


def _registry(request: Request) -> MonitorRegistry:
    return request.app.state.registry


def _monitor(request: Request, host_id: str):
    m = _registry(request).get(host_id)
    if m is None:
        raise HTTPException(status_code=404, detail="unknown host: %s" % host_id)
    return m


@router.get("/health")
async def panel_health(request: Request):
    reg = _registry(request)
    hosts = {}
    for mid, m in reg.monitors.items():
        snap = m.snapshot()
        hosts[mid] = {
            "llama_online": snap["llama"]["online"],
            "ssh_ok": snap["host_metrics"].get("reachable", False),
        }
    return {"status": "ok", "hosts": hosts}


@router.get("/hosts")
async def list_hosts(request: Request):
    return _registry(request).list()


@router.get("/hosts/{host_id}/overview")
async def host_overview(request: Request, host_id: str):
    return _monitor(request, host_id).snapshot()


@router.get("/hosts/{host_id}/history")
async def host_history(request: Request, host_id: str,
                       window: int = Query(default=300)):
    if window not in VALID_WINDOWS:
        window = 300
    return _monitor(request, host_id).history(window)


@router.get("/hosts/{host_id}/events")
async def host_events(request: Request, host_id: str,
                      limit: int = Query(default=50, ge=1, le=200)):
    return _monitor(request, host_id).events_list(limit)


@router.post("/hosts")
async def add_host(request: Request):
    """添加主机并持久化到 hosts.yaml。"""
    body = await request.json()
    global_cfg = request.app.state.registry.app_cfg.global_cfg
    
    # 构建主机配置
    try:
        host = _build_host(body, global_cfg.thresholds)
    except Exception as e:
        raise HTTPException(status_code=400, detail="配置错误: %s" % str(e))
    
    # 添加到运行时
    try:
        await request.app.state.registry.add_host(host)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    
    # 持久化到 hosts.yaml
    try:
        save_config(BASE_DIR, request.app.state.registry.app_cfg)
    except Exception as e:
        # 持久化失败不影响添加，只记录日志
        log.warning("保存 hosts.yaml 失败: %s", e)
    
    return {"status": "ok", "id": host.id}


@router.put("/hosts/{host_id}")
async def update_host(request: Request, host_id: str):
    """更新主机配置并持久化到 hosts.yaml。"""
    body = await request.json()
    global_cfg = request.app.state.registry.app_cfg.global_cfg
    
    # 构建新配置
    try:
        new_host = _build_host(body, global_cfg.thresholds)
    except Exception as e:
        raise HTTPException(status_code=400, detail="配置错误: %s" % str(e))
    
    if new_host.id != host_id:
        raise HTTPException(status_code=400, detail="host id 不匹配")
    
    # 删除旧主机
    old_monitor = _monitor(request, host_id)
    await request.app.state.registry.remove_host(host_id)
    
    # 添加新主机
    try:
        await request.app.state.registry.add_host(new_host)
    except Exception:
        # 回滚：重新添加旧主机
        await request.app.state.registry.add_host(old_monitor.cfg)
        raise HTTPException(status_code=500, detail="更新失败，已回滚")
    
    # 持久化
    try:
        save_config(BASE_DIR, request.app.state.registry.app_cfg)
    except Exception as e:
        log.warning("保存 hosts.yaml 失败: %s", e)
    
    return {"status": "ok", "id": new_host.id}


@router.delete("/hosts/{host_id}")
async def delete_host(request: Request, host_id: str):
    """删除主机并持久化到 hosts.yaml。"""
    monitor = _monitor(request, host_id)
    
    # 删除运行时监控
    await request.app.state.registry.remove_host(host_id)
    
    # 持久化
    try:
        save_config(BASE_DIR, request.app.state.registry.app_cfg)
    except Exception as e:
        log.warning("保存 hosts.yaml 失败: %s", e)
    
    return {"status": "ok", "id": host_id}

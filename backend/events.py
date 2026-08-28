"""事件检测器（EventDetector）。

每主机一个状态机，检测状态迁移并产生事件：
- llama: online ⇄ offline
- ssh:   connected ⇄ disconnected
- task:  idle → running (task_start) → idle (task_end, 带统计)
- model: model_path 变化 → model_change
- boot:  日志 "listening"/"model loaded" → llama_boot

事件环形缓冲 200 条，字段 {ts, level, type, msg}。兼容 Python 3.9。
"""
import asyncio
import time
from collections import deque
from typing import List, Optional


class EventDetector:
    # API 源任务结束事件的宽限期：等日志源补全完整统计（MTP/上下文）
    TASK_END_GRACE_S = 2.0

    def __init__(self, maxlen: int = 200):
        self.events: deque = deque(maxlen=maxlen)
        self._llama_online: Optional[bool] = None
        self._ssh_connected: Optional[bool] = None
        self._task_running: bool = False
        self._running_task_id: Optional[int] = None
        self._model_path: Optional[str] = None
        self._pending_task_end: Optional[tuple] = None
        self._pending_task_end_timer = None
        self._ended_task_ids: deque = deque(maxlen=200)

    # ------------------------------------------------------------------
    def emit(self, ts: Optional[float], level: str, type_: str, msg: str) -> None:
        self.events.append({
            "ts": ts if ts is not None else time.time(),
            "level": level,
            "type": type_,
            "msg": msg,
        })

    def set_llama_online(self, ts: float, online: bool, model_name: str = "") -> None:
        if self._llama_online is None:
            self._llama_online = online
            if online:
                self.emit(ts, "info", "llama_up", "llama 上线" + (" · 模型 %s" % model_name if model_name else ""))
            return
        if online != self._llama_online:
            self._llama_online = online
            if online:
                self.emit(ts, "info", "llama_up", "llama 恢复在线" + (" · 模型 %s" % model_name if model_name else ""))
            else:
                self.reset_task_state()
                self.emit(ts, "error", "llama_down", "llama 离线")

    def set_ssh_connected(self, ts: float, connected: bool) -> None:
        if self._ssh_connected is None:
            self._ssh_connected = connected
            return
        if connected != self._ssh_connected:
            self._ssh_connected = connected
            if connected:
                self.emit(ts, "info", "ssh_up", "SSH 重连成功")
            else:
                self.emit(ts, "warn", "ssh_down", "SSH 断开")

    def reset_task_state(self) -> None:
        """重置任务相关状态。llama 重启后任务 ID 从 0 重新计数，
        旧的去重记录会把新任务的结束事件误判为重复而吞掉。"""
        self._task_running = False
        self._running_task_id = None
        self._ended_task_ids.clear()
        self._cancel_pending_task_end()

    def set_task_running(self, ts: float, running: bool, task_id: Optional[int] = None,
                         prompt_tokens: Optional[int] = None) -> None:
        if running and not self._task_running:
            self._task_running = True
            self._running_task_id = task_id
            msg = "任务 #%s 开始" % task_id if task_id is not None else "任务开始"
            if prompt_tokens is not None:
                msg += " (prompt %d tokens)" % prompt_tokens
            self.emit(ts, "info", "task_start", msg)
        elif (running and self._task_running and task_id is not None
              and task_id != self._running_task_id):
            # 旧任务的结束事件还在宽限期内，新任务已开始：先落盘旧结束事件再开始
            self._fire_pending_task_end()
            self._task_running = True
            self._running_task_id = task_id
            msg = "任务 #%s 开始" % task_id
            if prompt_tokens is not None:
                msg += " (prompt %d tokens)" % prompt_tokens
            self.emit(ts, "info", "task_start", msg)
        elif not running and self._task_running:
            self._task_running = False
            self._running_task_id = None
            self._cancel_pending_task_end()
            self.emit(ts, "info", "task_end", "任务 #%s 结束" % task_id if task_id is not None else "任务结束")

    def task_end_with_stats(self, ts: float, task_id: Optional[int], total_tokens: Optional[int],
                            duration_s: Optional[float], avg_tps: Optional[float],
                            mtp_acceptance: Optional[float] = None,
                            ctx_used: Optional[int] = None,
                            note: Optional[str] = None) -> None:
        # 日志源与 API 源都会调用本方法。日志源统计完整（MTP/上下文），
        # API 源只有 tokens/时长/均速。完整统计立即发；不完整（API 源先到）
        # 延迟 TASK_END_GRACE_S 给日志源补全的机会，超时用部分统计兜底。
        complete = (mtp_acceptance is not None or ctx_used is not None)
        if complete:
            self._cancel_pending_task_end()
            self._emit_task_end(ts, task_id, total_tokens, duration_s, avg_tps,
                                mtp_acceptance, ctx_used, note)
        else:
            if not self._task_running:
                return
            if self._pending_task_end is None:
                self._pending_task_end = (ts, task_id, total_tokens, duration_s,
                                          avg_tps, mtp_acceptance, ctx_used, note)
                try:
                    self._pending_task_end_timer = asyncio.get_running_loop().call_later(
                        self.TASK_END_GRACE_S, self._fire_pending_task_end)
                except RuntimeError:
                    self._fire_pending_task_end()

    def _emit_task_end(self, ts: float, task_id: Optional[int], total_tokens: Optional[int],
                       duration_s: Optional[float], avg_tps: Optional[float],
                       mtp_acceptance: Optional[float], ctx_used: Optional[int],
                       note: Optional[str]) -> None:
        if task_id is not None:
            if task_id in self._ended_task_ids:
                return  # 该任务的结束事件已发过（双源去重）
            self._ended_task_ids.append(task_id)
        if self._running_task_id in (None, task_id):
            self._task_running = False
            self._running_task_id = None
        parts = []
        if task_id is not None:
            parts.append("任务 #%s 结束" % task_id)
        else:
            parts.append("任务结束")
        if note:
            parts.append("(%s)" % note)
        stats = []
        if total_tokens is not None:
            stats.append("%d tokens" % total_tokens)
        if duration_s is not None:
            stats.append(_fmt_duration(duration_s))
        if avg_tps is not None:
            stats.append("平均 %.1f tok/s" % avg_tps)
        if mtp_acceptance is not None:
            stats.append("MTP 接受率 %.1f%%" % (mtp_acceptance * 100))
        if ctx_used is not None:
            stats.append("上下文 %d" % ctx_used)
        msg = " ".join(parts)
        if stats:
            msg += ": " + " · ".join(stats)
        self.emit(ts, "info", "task_end", msg)

    def _fire_pending_task_end(self) -> None:
        args = self._pending_task_end
        self._pending_task_end = None
        if self._pending_task_end_timer is not None:
            self._pending_task_end_timer.cancel()
            self._pending_task_end_timer = None
        if args is None:
            return
        self._emit_task_end(*args)

    def _cancel_pending_task_end(self) -> None:
        self._pending_task_end = None
        if self._pending_task_end_timer is not None:
            self._pending_task_end_timer.cancel()
            self._pending_task_end_timer = None

    def set_model(self, ts: float, model_path: str) -> None:
        if not model_path:
            return
        if self._model_path is None:
            self._model_path = model_path
            return
        if model_path != self._model_path:
            old = self._model_path
            self._model_path = model_path
            self.emit(ts, "warn", "model_change", "模型变更: %s → %s" % (_short(old), _short(model_path)))

    def llama_boot(self, ts: float, info: str) -> None:
        self.emit(ts, "info", "llama_boot", "llama 启动: " + info)

    # ------------------------------------------------------------------
    def list(self, limit: int = 50) -> List[dict]:
        items = list(self.events)
        return items[-limit:] if limit > 0 else items

    @property
    def llama_online(self) -> Optional[bool]:
        return self._llama_online

    @property
    def ssh_connected(self) -> Optional[bool]:
        return self._ssh_connected


def _short(path: str) -> str:
    return path.rsplit("/", 1)[-1] if path else path


def _fmt_duration(seconds: float) -> str:
    if seconds < 60:
        return "%.0fs" % seconds
    m = int(seconds // 60)
    s = int(seconds % 60)
    if m < 60:
        return "%dm%02ds" % (m, s)
    h = m // 60
    return "%dh%02dm" % (h, m % 60)

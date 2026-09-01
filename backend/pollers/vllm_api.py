"""vLLM HTTP 采集器（VllmPoller）。

- 每 interval（默认 2s）轮询 vLLM 的 Prometheus 兼容 /metrics 端点。
- 解析 Prometheus text 格式 → {metric_name, labels} → value 字典。
- 提取关键指标（GPU 缓存使用率、KV 缓存、请求队列、token 吞吐）。
- 3 次连续请求失败 → online=False + vllm_down 事件；恢复 → vllm_up。
- 状态存入 self.state，HostMonitor.snapshot() 读取后合并到快照。
- 兼容 Python 3.9（不使用 3.10+ 语法）。
"""
import asyncio
import logging
import time
from typing import Any, Dict, Optional

import httpx

from ..config import HostConfig
from ..events import EventDetector

log = logging.getLogger("llamalens.vllm")

FAIL_OFFLINE = 3  # 连续失败 count → mark vLLM offline


class VllmPoller:
    """vLLM /metrics HTTP poller. Reads Prometheus text, extracts key indicators into self.state.

    state keys (source Prometheus metric in parentheses):
      - online: bool (True when /metrics returned HTTP 200)
      - gpu_cache_pct: float 0-100 (vllm:gpu_cache_usage_perc, 0-1)
      - cpu_cache_pct: float 0-100 (vllm:cpu_cache_usage_perc, 0-1)
      - running_requests: int (vllm:num_requests_running)
      - waiting_requests: int (vllm:num_requests_waiting)
      - prompt_tokens_total: int (vllm:prompt_tokens_total)
      - generation_tokens_total: int (vllm:generation_tokens_total)
      - last_poll_ts: float (time.time() of last successful poll)
      - raw: dict (full {(name, labels)} → value, for debugging)
    """

    def __init__(self, cfg: HostConfig, events: EventDetector):
        self.cfg = cfg
        self.events = events
        self.vllm_cfg = cfg.vllm  # VllmCfg (already parsed from hosts.yaml)
        self.state: Dict[str, Any] = {
            "online": False,
            "gpu_cache_pct": 0.0,
            "cpu_cache_pct": 0.0,
            "running_requests": 0,
            "waiting_requests": 0,
            "prompt_tokens_total": 0,
            "generation_tokens_total": 0,
            "preemptions_total": 0,
            "last_poll_ts": 0.0,
            "raw": {},
        }
        self._fail_count = 0
        self._client: Optional[httpx.AsyncClient] = None
        self._stopped = False

    # ------------------------------------------------------------------
    async def start(self) -> None:
        if not self.vllm_cfg:
            log.warning("[%s] vLLM 未配置，VllmPoller 跳过", self.cfg.id)
            return
        log.info("[%s] VllmPoller 启动 %s:%s（每 %.1fs 采集一次）",
                   self.cfg.id, self.vllm_cfg.host, self.vllm_cfg.port,
                   self.vllm_cfg.interval)
        base_url = "http://%s:%d" % (self.vllm_cfg.host, self.vllm_cfg.port)
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=self.vllm_cfg.timeout,
        )
        try:
            while not self._stopped:
                await self._poll_once()
                await asyncio.sleep(self.vllm_cfg.interval)
        finally:
            if self._client:
                await self._client.aclose()

    def stop(self) -> None:
        self._stopped = True

    # ------------------------------------------------------------------
    async def _poll_once(self) -> None:
        if self._client is None:
            return
        try:
            resp = await self._client.get("/metrics")
            resp.raise_for_status()
            text = resp.text
            raw = self._parse_prometheus(text)
            self.state["raw"] = raw
            self._update_state(raw)
            self.state["online"] = True
            self.state["last_poll_ts"] = time.time()
            self._fail_count = 0
            if not getattr(self, "_ever_online", False):
                self._ever_online = True
                self.events.emit(
                    time.time(), "info", "vllm_up",
                    "vLLM 上线: %s:%d" % (self.vllm_cfg.host, self.vllm_cfg.port),
                )
        except Exception as e:
            self._fail_count += 1
            if self._fail_count == 1 or self._fail_count % 15 == 0:
                log.warning("[%s] vLLM 请求失败(%d): %s", self.cfg.id, self._fail_count, e)
            if self._fail_count >= FAIL_OFFLINE and self.state["online"]:
                self.state["online"] = False
                self.events.emit(time.time(), "error", "vllm_down", "vLLM 离线")

    def _update_state(self, raw: Dict[str, float]) -> None:
        """从 metric_name → total_value 中提取 vLLM 核心指标。

        raw 由 _parse_prometheus 产出，每条 key 为指标名（如
        "vllm:num_requests_running"），value 为该指标所有标签序列
        的值之和（单模型部署下每个指标仅一条序列，即其原值）。
        """
        st = self.state
        # KV 缓存占用（Prometheus 值为 0-1，转为 0-100 百分比）。
        # 新版 vLLM 使用 vllm:kv_cache_usage_perc；旧版拆分为
        # vllm:gpu_cache_usage_perc / vllm:cpu_cache_usage_perc，故依次回退。
        kv = raw.get("vllm:kv_cache_usage_perc")
        if kv is None:
            kv = raw.get("vllm:gpu_cache_usage_perc")
        st["gpu_cache_pct"] = _to_pct(kv)
        st["cpu_cache_pct"] = _to_pct(raw.get("vllm:cpu_cache_usage_perc"))
        # 调度器状态：运行中 / 等待中请求数
        st["running_requests"] = _to_int(raw.get("vllm:num_requests_running"))
        st["waiting_requests"] = _to_int(raw.get("vllm:num_requests_waiting"))
        # 累计计数
        st["prompt_tokens_total"] = _to_int(raw.get("vllm:prompt_tokens_total"))
        st["generation_tokens_total"] = _to_int(raw.get("vllm:generation_tokens_total"))
        st["preemptions_total"] = _to_int(raw.get("vllm:num_preemptions_total"))

    @staticmethod
    def _parse_prometheus(text: str) -> Dict[str, float]:
        """Parse Prometheus text format → {metric_name: total_value}.

        Line format (one metric sample per line):
          <name>{label="val",...} <value>
          <name> <value>       (no labels)
          # HELP <name> ...     (comment – skipped)
          # TYPE <name> gauge    (comment – skipped)

        Multiple lines can share the same metric name when they carry
        different label sets (e.g. one per engine, model, or finished_reason).
        vLLM does not publish the same metric with both labelled and
        unlabelled samples, so for each name we simply sum the values:
        for a single-label-set deployment the sum is the raw gauge/counter
        value; for multi-engine it is the aggregate across engines.
        """
        out: Dict[str, float] = {}
        for line in text.splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            # 值始终是行内最后一个空白分隔 token
            tokens = s.split()
            if len(tokens) < 1:
                continue
            try:
                val = float(tokens[-1])
            except ValueError:
                continue  # 末尾不是数字 → 非指标行（如 TYPE 注释）
            # 指标名 = 去掉末尾数值 token 及标签串后的前缀
            prefix = s[: s.rfind(tokens[-1])].rstrip()
            brace = prefix.find("{")
            name = (prefix[:brace].strip() if brace > 0 else prefix.strip())
            if not name:
                continue
            out[name] = out.get(name, 0.0) + val
        return out


def _to_pct(v: Optional[float]) -> float:
    """Prometheus 浮点 → 0-100 百分比。缺失（None）→ 0。

    多数 vLLM 版本的 *_usage_perc 指标按 0-1 比例上报（1.0 = 100%）；若个别版本
    直接上报 0-100 数值，则 v > 1.0，此时不再乘以 100，仅做上限截断。
    """
    if v is None:
        return 0.0
    v = float(v)
    if v > 1.0:
        v = min(v, 100.0)  # 已是百分比数值
    else:
        v = v * 100.0     # 0-1 比例，换算为百分比
    return round(max(0.0, v), 2)


def _to_int(v: Optional[float]) -> int:
    """计数 / 数值 → 非负整数。缺失（None）→ 0。"""
    if v is None:
        return 0
    return int(max(0.0, float(v)))




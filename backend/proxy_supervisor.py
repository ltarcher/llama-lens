"""Codex CLI 规范化代理（devtools/codex_llama_proxy.py）的可选守护。

背景：code-server 容器部署中 systemd 无法创建新 unit（cgroup 只读），
后台进程会随会话结束被杀；后端是容器内最长寿的自研进程，启用后由它托管代理：

- 启动时若监听端口未被占用则拉起代理（已占用视为已手动启动，不重复拉起）
- 代理退出后自动重启（指数退避，防止崩溃热循环）
- 后端停止时终止代理

启用：.env 中设置 LLAMALENS_CODEX_PROXY=1（见 .env.example）
可选：LLAMALENS_PROXY_LISTEN（默认 127.0.0.1:8901）、
      LLAMALENS_PROXY_UPSTREAM（默认 http://ai.lan:8080）
"""
import asyncio
import logging
import os
import socket
import subprocess
import sys
import time

log = logging.getLogger("llamalens.proxy_supervisor")

DEFAULT_LISTEN = "127.0.0.1:8901"
DEFAULT_UPSTREAM = "http://ai.lan:8080"
ENABLED_VALUES = ("1", "true", "yes", "on")
RESTART_BASE_DELAY = 2.0
RESTART_MAX_DELAY = 60.0
QUICK_DEATH_WINDOW = 5.0  # 启动后短时间内退出视为启动失败，持续退避


def _port_in_use(host: str, port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1.0)
            return sock.connect_ex((host, port)) == 0
    except OSError:
        return False


class ProxySupervisor:
    """拉起并看护 codex_llama_proxy.py 子进程（asyncio 任务，异常不外抛）。"""

    def __init__(self, base_dir: str, listen: str = DEFAULT_LISTEN,
                 upstream: str = DEFAULT_UPSTREAM):
        self.base_dir = base_dir
        self.listen = listen
        self.upstream = upstream
        self._proc = None
        self._task = None
        self._stopping = False

    @property
    def enabled(self) -> bool:
        return os.environ.get("LLAMALENS_CODEX_PROXY", "").strip().lower() in ENABLED_VALUES

    async def start(self) -> None:
        if not self.enabled:
            return
        self._task = asyncio.get_running_loop().create_task(
            self._run(), name="codex-proxy-supervisor")
        log.info("Codex 代理守护已启动（listen=%s upstream=%s）", self.listen, self.upstream)

    async def stop(self) -> None:
        self._stopping = True
        proc, self._proc = self._proc, None
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except BaseException:
                pass
            self._task = None

    def _spawn(self) -> subprocess.Popen:
        log_dir = os.path.join(self.base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        logf = open(os.path.join(log_dir, "codex_llama_proxy.log"), "a", encoding="utf-8")
        cmd = [sys.executable, os.path.join(self.base_dir, "devtools", "codex_llama_proxy.py"),
               "--listen", self.listen, "--upstream", self.upstream]
        log.info("拉起 Codex 代理：%s", " ".join(cmd))
        return subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL, start_new_session=True,
                                cwd=self.base_dir)

    async def _run(self) -> None:
        host, _, port = self.listen.rpartition(":")
        host = host or "127.0.0.1"
        port = int(port or 8901)
        loop = asyncio.get_running_loop()
        delay = RESTART_BASE_DELAY
        while not self._stopping:
            if _port_in_use(host, port):
                log.info("端口 %s:%d 已被占用，视为 Codex 代理已启动，不再拉起", host, port)
                return
            try:
                proc = self._spawn()
            except Exception:
                log.exception("Codex 代理拉起失败，%.0fs 后重试", delay)
                await asyncio.sleep(delay)
                delay = min(delay * 2, RESTART_MAX_DELAY)
                continue
            self._proc = proc
            started = time.monotonic()
            try:
                rc = await loop.run_in_executor(None, proc.wait)
            except Exception:
                log.exception("等待 Codex 代理进程异常")
                rc = -1
            self._proc = None
            if self._stopping:
                return
            ran = time.monotonic() - started
            if ran < QUICK_DEATH_WINDOW:
                log.warning("Codex 代理 %.0fs 内退出（rc=%s），%.0fs 后重启", ran, rc, delay)
                await asyncio.sleep(delay)
                delay = min(delay * 2, RESTART_MAX_DELAY)
            else:
                log.info("Codex 代理退出（rc=%s，运行 %.0fs），%.0fs 后重启", rc, ran, RESTART_BASE_DELAY)
                delay = RESTART_BASE_DELAY
                await asyncio.sleep(delay)

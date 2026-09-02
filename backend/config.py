"""配置加载：hosts.yaml + .env。

- 凭证：SSH 支持密钥认证（key_path）与密码认证（password / ${ENV} 引用）两种方式。
- 阈值：全局默认 + 每主机覆盖，加载时合并为每主机一份完整阈值表。
- 兼容 Python 3.9（不使用 3.10+ 语法）。
"""
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

import yaml

log = logging.getLogger("llamalens.config")

# ---------------------------------------------------------------------------
# .env 加载（不引入外部依赖，简单 KEY=VALUE 解析）
# ---------------------------------------------------------------------------

def load_dotenv(path: str) -> None:
    """把 .env 中的 KEY=VALUE 载入 os.environ（已存在的环境变量不覆盖）。"""
    if not path or not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v


_ENV_RE = re.compile(r"\$\{(\w+)\}")
_WIN_ENV_RE = re.compile(r"%(\w+)%")


def resolve_env(value: Any) -> Any:
    """解析字符串中的 ${VAR} 和 %VAR% 环境变量引用。"""
    if isinstance(value, str):
        # 先解析 ${VAR} 格式
        value = _ENV_RE.sub(lambda m: os.environ.get(m.group(1), m.group(0)), value)
        # 再解析 %VAR% 格式（Windows 环境变量）
        value = _WIN_ENV_RE.sub(lambda m: os.environ.get(m.group(1), m.group(0)), value)
    return value


# ---------------------------------------------------------------------------
# 阈值
# ---------------------------------------------------------------------------

# 默认阈值表（与需求文档 §8 一致）。
# 注意：mtp 为“低于阈值告警”（inverted），其余为“高于阈值告警”。
DEFAULT_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "gpu_util": {"warn": 80, "danger": 90},
    "gpu_mem": {"warn": 85, "danger": 95},
    "gpu_temp": {"warn": 75, "danger": 85},
    "gpu_power": {"warn": 85, "danger": 95},
    "cpu": {"warn": 80, "danger": 90},
    "mem": {"warn": 85, "danger": 95},
    "disk": {"warn": 80, "danger": 90},
    "ctx": {"warn": 80, "danger": 90},
    "mtp": {"warn": 80, "danger": 65},
}

# 低于阈值才告警的指标（其余为高于阈值告警）
INVERTED_METRICS = {"mtp"}


def merge_thresholds(global_t: Optional[dict], host_t: Optional[dict]) -> Dict[str, Dict[str, float]]:
    """全局默认 → 全局覆盖 → 主机覆盖，逐字段合并。"""
    merged = {k: dict(v) for k, v in DEFAULT_THRESHOLDS.items()}
    for src in (global_t or {}, host_t or {}):
        for k, v in src.items():
            if k in merged and isinstance(v, dict):
                merged[k].update({kk: float(vv) for kk, vv in v.items() if kk in merged[k]})
    return merged


# ---------------------------------------------------------------------------
# 配置数据结构
# ---------------------------------------------------------------------------

@dataclass
class LlamaCfg:
    host: str
    port: int = 8080
    interval: float = 1.0        # /health + /slots 轮询间隔（秒）
    slow_interval: float = 30.0  # /props + /v1/models 轮询间隔（秒）
    timeout: float = 3.0         # 单次请求超时


@dataclass
class VllmCfg:
    host: str
    port: int = 8000
    interval: float = 2.0        # /metrics 轮询间隔（秒）
    timeout: float = 3.0


@dataclass
class SshCfg:
    host: str
    port: int = 22
    user: str = "root"
    password: Optional[str] = None
    key_path: Optional[str] = None
    interval: float = 2.0        # 批量采集间隔（秒）
    keepalive: int = 15          # SSH keepalive（秒）
    timeout: float = 15.0        # 单条命令超时


@dataclass
class LogCfg:
    source: str = "journal"      # journal（systemd unit）| file（日志文件）| windows_eventlog
    unit: str = "llama-server"   # systemd unit 名（source=journal）
    path: Optional[str] = None   # 日志文件路径（source=file）
    follow: bool = True
    catchup_sec: int = 30


@dataclass
class HostConfig:
    id: str
    name: str
    llama: List[LlamaCfg]  # 支持多端口
    ssh: SshCfg
    process_name: str = "llama-server"
    log: LogCfg = field(default_factory=LogCfg)
    disk_mounts: List[str] = field(default_factory=lambda: ["/"])
    systemd_unit: str = "llama-server.service"
    os_type: Optional[str] = None  # 手动指定 OS 类型（linux/windows），自动检测时忽略
    thresholds: Dict[str, Dict[str, float]] = field(default_factory=dict)
    vllm: Optional[VllmCfg] = None  # vLLM /metrics 监控（可选）


@dataclass
class GlobalConfig:
    push_interval: float = 1.0
    llama_points: int = 3600     # llama 指标环形缓冲点数 @1s（1h）
    host_points: int = 1800      # host 指标环形缓冲点数 @2s（1h）
    thresholds: Dict[str, Dict[str, float]] = field(default_factory=dict)


@dataclass
class AppConfig:
    global_cfg: GlobalConfig
    hosts: List[HostConfig]
    port: int = 8000


# ---------------------------------------------------------------------------
# 解析
# ---------------------------------------------------------------------------

def _build_llama(d: dict) -> LlamaCfg:
    d = d or {}
    return LlamaCfg(
        host=d.get("host", ""),
        port=int(d.get("port", 8080)),
        interval=float(d.get("interval", 1.0)),
        slow_interval=float(d.get("slow_interval", 30.0)),
        timeout=float(d.get("timeout", 3.0)),
    )


def _build_vllm(d: Optional[dict]) -> Optional[VllmCfg]:
    """解析 vLLM 监控配置。返回 None 表示未配置（不启用）。"""
    if d is None:
        return None
    d = d or {}
    host = d.get("host", "")
    if not host:
        return None  # 无 host 字段视为未配置
    return VllmCfg(
        host=host,
        port=int(d.get("port", 8000)),
        interval=float(d.get("interval", 2.0)),
        timeout=float(d.get("timeout", 3.0)),
    )


def _build_ssh(d: dict) -> SshCfg:
    d = d or {}
    password = resolve_env(d.get("password"))
    if password and _ENV_RE.search(password):
        log.warning("SSH 密码含未解析的环境变量引用 %s（检查 .env 是否已填写）", password)
    return SshCfg(
        host=d.get("host", ""),
        port=int(d.get("port", 22)),
        user=d.get("user", "root"),
        password=password,
        key_path=resolve_env(d.get("key_path")),
        interval=float(d.get("interval", 2.0)),
        keepalive=int(d.get("keepalive", 15)),
        timeout=float(d.get("timeout", 15.0)),
    )


def _build_log(d: dict) -> LogCfg:
    d = d or {}
    source = str(d.get("source", "journal")).lower()
    if source not in ("journal", "file", "windows_eventlog"):
        raise ValueError("log.source 仅支持 journal | file | windows_eventlog，当前: %s" % source)
    return LogCfg(
        source=source,
        unit=d.get("unit", "llama-server"),
        path=resolve_env(d.get("path")),
        follow=bool(d.get("follow", True)),
        catchup_sec=int(d.get("catchup_sec", 30)),
    )


def _build_host(d: dict, global_t: dict) -> HostConfig:
    d = d or {}
    host_id = d.get("id")
    if not host_id:
        raise ValueError("hosts 条目缺少 id 字段")
    proc = d.get("process")
    if isinstance(proc, dict):
        process_name = proc.get("name", "llama-server")
    else:
        process_name = d.get("process_name", "llama-server")
    
    # 解析 disk_mounts：Windows 使用盘符（如 C:\），Linux 使用路径（如 /）
    raw_mounts = d.get("disk_mounts")
    if raw_mounts is None:
        raw_mounts = ["/"]
    
    # 解析 llama 配置：支持单个或多个端口
    llama_raw = d.get("llama")
    if isinstance(llama_raw, list):
        llama_list = [_build_llama(l) for l in llama_raw]
    elif isinstance(llama_raw, dict):
        llama_list = [_build_llama(llama_raw)]
    else:
        llama_list = []
    
    return HostConfig(
        id=str(host_id),
        name=d.get("name", host_id),
        llama=llama_list,
        ssh=_build_ssh(d.get("ssh")),
        process_name=process_name,
        log=_build_log(d.get("log")),
        disk_mounts=[str(x) for x in raw_mounts],
        systemd_unit=d.get("systemd_unit", "llama-server.service"),
        os_type=d.get("os_type"),  # 手动指定 OS 类型
        thresholds=merge_thresholds(global_t, d.get("thresholds") or {}),
        vllm=_build_vllm(d.get("vllm")),
    )


def load_config(base_dir: str, env_file: Optional[str] = None,
                hosts_file: Optional[str] = None) -> AppConfig:
    """加载完整应用配置。base_dir 为项目根目录。"""
    env_file = env_file or os.path.join(base_dir, ".env")
    hosts_file = hosts_file or os.path.join(base_dir, "config", "hosts.yaml")
    load_dotenv(env_file)

    with open(hosts_file, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    g_raw = raw.get("global") or {}
    global_cfg = GlobalConfig(
        push_interval=float(g_raw.get("push_interval", 1.0)),
        llama_points=int((g_raw.get("history") or {}).get("llama_points", 3600)),
        host_points=int((g_raw.get("history") or {}).get("host_points", 1800)),
        thresholds=g_raw.get("thresholds") or {},
    )

    hosts = [_build_host(h, global_cfg.thresholds) for h in (raw.get("hosts") or [])]

    seen = set()
    for h in hosts:
        if h.id in seen:
            raise ValueError("重复的 host id: %s" % h.id)
        seen.add(h.id)
        if not h.ssh.key_path and not h.ssh.password:
            raise ValueError("host %s 未配置 SSH 凭证（key_path 或 password）" % h.id)
        if h.ssh.key_path:
            h.ssh.key_path = os.path.expanduser(h.ssh.key_path)

    port = int(os.environ.get("PORT", 8000))
    return AppConfig(global_cfg=global_cfg, hosts=hosts, port=port)


def save_config(base_dir: str, app_cfg: AppConfig,
                env_file: Optional[str] = None,
                hosts_file: Optional[str] = None) -> None:
    """将 AppConfig 写回 hosts.yaml（保留注释和格式的最小改动）。"""
    env_file = env_file or os.path.join(base_dir, ".env")
    hosts_file = hosts_file or os.path.join(base_dir, "config", "hosts.yaml")
    
    # 构建 YAML 数据
    data: Dict[str, Any] = {}
    g = app_cfg.global_cfg
    data["global"] = {
        "push_interval": g.push_interval,
        "history": {
            "llama_points": g.llama_points,
            "host_points": g.host_points,
        },
    }
    if g.thresholds:
        data["global"]["thresholds"] = g.thresholds
    
    data["hosts"] = []
    for h in app_cfg.hosts:
        host_dict: Dict[str, Any] = {
            "id": h.id,
            "name": h.name,
        }
        # llama 配置（可选）
        if h.llama and len(h.llama) > 0:
            if len(h.llama) == 1:
                ll = h.llama[0]
                host_dict["llama"] = {
                    "host": ll.host,
                    "port": ll.port,
                    "interval": ll.interval,
                    "slow_interval": ll.slow_interval,
                    "timeout": ll.timeout,
                }
            else:
                host_dict["llama"] = [
                    {
                        "host": ll.host,
                        "port": ll.port,
                        "interval": ll.interval,
                        "slow_interval": ll.slow_interval,
                        "timeout": ll.timeout,
                    }
                    for ll in h.llama
                ]
        
        # vLLM 配置（可选）
        if h.vllm:
            host_dict["vllm"] = {
                "host": h.vllm.host,
                "port": h.vllm.port,
                "interval": h.vllm.interval,
                "timeout": h.vllm.timeout,
            }
        
        # SSH 配置
        ssh_dict: Dict[str, Any] = {
            "host": h.ssh.host,
            "port": h.ssh.port,
            "user": h.ssh.user,
        }
        if h.ssh.password:
            ssh_dict["password"] = h.ssh.password
        if h.ssh.key_path:
            ssh_dict["key_path"] = h.ssh.key_path
        host_dict["ssh"] = ssh_dict
        
        # 其他配置
        if h.process_name != "llama-server":
            host_dict["process"] = {"name": h.process_name}
        host_dict["systemd_unit"] = h.systemd_unit
        
        # OS 类型
        if h.os_type:
            host_dict["os_type"] = h.os_type
        
        # Log 配置
        log_dict: Dict[str, Any] = {
            "source": h.log.source,
            "follow": h.log.follow,
            "catchup_sec": h.log.catchup_sec,
        }
        if h.log.source == "journal" and h.log.unit:
            log_dict["unit"] = h.log.unit
        elif h.log.source == "file" and h.log.path:
            log_dict["path"] = h.log.path
        host_dict["log"] = log_dict
        
        # disk_mounts
        if h.disk_mounts != ["/"]:
            host_dict["disk_mounts"] = h.disk_mounts
        
        # thresholds（如果有自定义覆盖）
        if h.thresholds:
            host_dict["thresholds"] = h.thresholds
        
        data["hosts"].append(host_dict)
    
    # 写入文件
    with open(hosts_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


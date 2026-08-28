"""llama-server 命令行参数解析（进程卡参数表 + MTP 静态配置）。

输入为 /proc/<pid>/cmdline 得到的完整命令行，输出 {key: value}。
只解析已知参数表，未知参数忽略。兼容 Python 3.9。
"""
from typing import Any, Dict, List, Optional, Tuple

# (短选项, 长选项, 输出键)
FLAG_MAP: List[Tuple[Optional[str], Optional[str], str]] = [
    ("-m", "--model", "model"),
    (None, "--mmproj", "mmproj"),
    ("-ngl", "--n-gpu-layers", "n_gpu_layers"),
    (None, "--flash-attn", "flash_attn"),
    ("-ts", "--tensor-split", "tensor_split"),
    ("-b", "--batch", "batch"),
    ("-ub", "--ubatch", "ubatch"),
    ("-np", "--parallel", "np"),
    ("-c", "--ctx-size", "ctx_size"),
    (None, "--kv-offload", "kv_offload"),
    (None, "--cache-type-k", "cache_type_k"),
    (None, "--cache-type-v", "cache_type_v"),
    (None, "--fit", "fit"),
    ("-t", "--threads", "threads"),
    (None, "--threads-batch", "threads_batch"),
    (None, "--threads-http", "threads_http"),
    (None, "--temperature", "temperature"),
    (None, "--top-p", "top_p"),
    ("-tk", "--top-k", "top_k"),
    (None, "--spec-type", "spec_type"),
    (None, "--spec-draft-n-max", "spec_draft_n_max"),
    (None, "--port", "port"),
    (None, "--host", "host"),
]

# 无取值的布尔开关
BOOL_FLAGS = {"--kv-offload"}

_LOOKUP = {}
for _short, _long, _key in FLAG_MAP:
    if _short:
        _LOOKUP[_short] = (_key, _short in BOOL_FLAGS)
    if _long:
        _LOOKUP[_long] = (_key, _long in BOOL_FLAGS)


def parse_cmdline(cmdline: str) -> Dict[str, Any]:
    """把 llama-server 命令行解析为参数表。"""
    if not cmdline:
        return {}
    tokens = cmdline.split()
    flags: Dict[str, Any] = {}
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        hit = _LOOKUP.get(tok)
        if hit is None:
            i += 1
            continue
        key, is_bool = hit
        if is_bool:
            flags[key] = True
            i += 1
        else:
            if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                flags[key] = tokens[i + 1]
                i += 2
            else:
                flags[key] = True
                i += 1
    return flags

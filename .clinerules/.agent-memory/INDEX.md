# Agent Memory Index

## 当前状态

最后更新：2026-08-30

当前工作：LlamaLens（llama-server 多主机监控面板）—— CLI 已整体删除（2026-08-30：先重设计为后端终端客户端并实测通过，但用户实际终端中 TUI 排版混乱（疑似 CJK 双宽未计入列宽 / 备用屏处理差异，根因未确认），用户决定不做 CLI；cli/ 目录、README/docs/02 相关章节、旧采集器备份全部移除，旧 CLI 从未入 git 无历史可恢复）；此前：前端总览区第 8 轮迭代（2026-08-29，2 项：GPU 卡 3×4 紧凑网格 + CUDA 版本/驱动版本（后端 nvidia-smi +cuda_version 22 列、gauge 88px、整卡高度降低）、LlamaStateCard 动态数据丰富化（解码加 MTP 接受率/Graphs 复用、预填充加上下文占用/KV 缓存命中、任务 ID 行加 slot id/总数）；dist index-DWrWtmiU.js，CUDA 字段需重启后端生效）；此前：前端总览区第 7 轮 Bug 修复（2026-08-29，2 项：预填充速度卡停止后归 0（promptVal 不再回退 last_prefill.speed，sub/foot 保留上次预填充信息）、事件流撑高修复（删 .feed.fill height:100%，高度唯一来源 .task-row > * 320px，自动滚底显示最新事件）；dist index-D_xwIVzL.js，纯前端无需重启后端）；此前：前端总览区第 6 轮迭代落地（2026-08-29，6 项：GPU 区上移至实时生成任务区之上、任务区两卡固定高 320px（.task-row > * 父级规则唯一高度源，左卡卡内滚动、事件流 min-height:0 出滚动条）、预填充速度卡条位复用为进度条（BarCard progress prop，绿色 0/50/100% 刻度，卡高不变）、LlamaStateCard 丰富化（头部"已运行"每秒跳、三列 stat3 大数字、decoding 剩余tokens/生成进度/ETA、prefill 已处理Prompt/已耗时、idle 上一任务耗时明细、底部 cfg-strip 静态配置，新增 flags/now props + 后端 log.state.started_at）、GpuPanel 青色芯片图标 + 4 新指标（显存利用率/显存温度/ECC 纠错不可纠/降频状态位掩码→中文，后端 nvidia-smi +4 字段 21 列 + _parse_throttle）；dist 已重建 index-cXMsBnSt.js，待用户重启后端使 GPU 新字段/started_at 生效）；此前：前端总览区第 5 轮迭代落地（2026-08-29，3 问题：预填充速度卡改持久 last_prefill 数据源 + 进度 %/ETA、任务区左卡 align-items:start 修底部空白、状态卡丰富、事件流 +2 类事件（prefill_start、alert 阈值穿越 check_alerts 30s 冷却）；dist index-CSqJVaY2.js）；更早：前端总览区第 4 轮迭代落地（2026-08-29，7 条反馈：MTP 仪表值驱动颜色 zoneColors、任务区 2 卡=状态卡+事件流上移、Slot 卡 auto-fit 修自适应、趋势 12 图 3 组（llama/GPU/系统，系统组加负载均值 1/5/15）、Prompt 速度卡仅预填充期显示+上次预填充速度、上下文卡大数字改原始 token 数（百分比移右上角）、ctx_used 改 1s 采样修 60s 趋势缺失）+ 指标改名（Token 生成速度/预填充速度）+ 前端总览区重构方案一落地（2026-08-29，实时总览 4 卡 = 3 BarCard 条卡 + 1 GaugeCard 仪表，"AI 核心指标"改名"实时生成任务"只留 LlamaStateCard，删 KpiCard/ContextCard/MtpCard，dist 已重建，用户刷新浏览器验证）+ 前端 UI 自适应 + v1.0.0 发布前修复完成 + Codex CLI 规范化代理落地（2026-08-29）：`devtools/codex_llama_proxy.py`（Responses 报文规范化）+ `backend/proxy_supervisor.py`（后端守护，`.env` `LLAMALENS_CODEX_PROXY=1` 启用）+ Go CLI（`cli/`，TUI/JSON/单帧三模式，已对真实 ai.lan:8080 功能验证）；待用户重启后端（使代理守护 + Top CPU/ctx 修复生效）并改 Codex config 指向 127.0.0.1:8901；工程规则在根目录 AGENTS.md（Codex 自动加载），`.clinerules/` 保留供 Cline 使用

## 项目

- 路径：/data/case/LlamaLens
- 交付物：docs/01-需求文档.md（需求基线）、02-架构设计文档.md、03-UI与交互设计文档.md、README.md
- 用户明确：后续开发以 01-需求文档.md 为主依据

## 重要架构决策

- 本机单进程部署 :8000，FastAPI 托管前端 dist
- 多主机：hosts.yaml 注册 + 每主机独立 HostMonitor（采集/缓冲/事件隔离）
- Token 速度：日志 tg_3s 为主（3s 窗口，服务端计算），/slots 差分兜底；/metrics 未启用（501）不可用
- 日志解析：LogPoller 专用 SSH channel 跑 journalctl -f（重连后 --since 补拉 30s），解析 11 类行；提供 MTP 接受率/上下文 n_tokens/KV 保留 f_keep 等 API 拿不到的数据
- SSH：paramiko 持久连接 + keepalive + 指数退避重连，每 2s 一条批量只读命令
- 实时：WS 1s 推送为主，断线自动降级 HTTP 轮询；前端刷新控制 实时/1s/2s/5s/暂停
- 阈值飘红：后端评估 alerts[]（warn/danger），前端渲染；默认 GPU util 80/90、显存 85/95、温度 75/85、CPU 80/90、磁盘 80/90、上下文 80/90、MTP 接受率 <80/<65
- 凭证：.env + hosts.yaml 均 gitignore，只提交 example 模板
- Codex CLI 代理：Codex（wire_api=responses）直发 llama-server 会 500（Qwen3 内置模板要求 system/developer 在 input[0]，compaction 后必触发）+ web_search/namespace 工具告警刷屏。方案：`devtools/codex_llama_proxy.py` 只规范化 POST */responses（system/developer 合并至 input[0]、tools 只留 function、SSE 直通），由 `backend/proxy_supervisor.py` 守护（选 env 启用、崩溃指数退避重启、端口占用跳过）；Codex config base_url 指向 127.0.0.1:8901/v1
- Go CLI（cli/）：本机单主机监控（journalctl/tail//proc 本地读 + llama HTTP 可远端），TUI/NDJSON/--once 三模式，阈值与 Web 版同源；差分指标首帧为 null（基线）属设计
- 前端布局：内容全宽（无 max-width）；响应式断点 1500/1100/640px（总览 4→2→1、GPU/模型/进程 2→1、系统/趋势 2→1）；详情页顶部"实时总览"4 卡（Token/Prompt 速度 + 上下文占用 = BarCard 条卡：大数字+条+刻度+60s spark+峰谷均，速度卡满量程动态 niceMax(60s 峰值×1.1)、上下文固定 100%；MTP 接受率 = GaugeCard：ECharts 240° 弧 gauge 阈值色带+指针，颜色与 alerts 同源）；"实时生成任务"区单卡 LlamaStateCard（max-width 640px）；每指标 3 层展示（TopBar 芯片→总览→趋势）避免重复；sparkline 用 vector-effect:non-scaling-stroke 防拉伸变粗

## 环境限制（code-server 容器，勿重复调查）

- bwrap 沙箱 `--die-with-parent`：exec 会话结束后台进程即死；PID 命名空间 2 层（/proc 是宿主 pid、getpid() 是命名空间 pid）→ 测试用 Popen.pid
- /sys/fs/cgroup 只读 → systemd 无法 StartTransientUnit（ENXIO）；版本串 "247.3" 误导，实际 D-Bus 是 256+ 接口；systemctl --user 失败、busctl 可用
- 根文件系统只读（writable roots 外）→ 无 cron/unit 文件；pgrep/pkill 损坏（恒 exit 1）→ 扫 /proc/*/cmdline
- 长寿进程挂靠点：LlamaLens 后端 uvicorn（system-code-server.slice/code-server@root.service）会话死后仍存活 → 需要常驻的辅助进程由后端守护
- Codex 沙箱在嵌套 PID 命名空间（self pid=2）：读得到宿主 /proc 但 kill -0 宿主 PID 报 no such process → 无法重启后端；/root/.codex 在可写根外改不了；沙箱内 setsid nohup 拉起的进程随会话死 → 持久化代理/改 Codex config 须用户 code-server 终端执行

## 重要发现（ai.lan 实测 2026-08-28）

- llama-server 为定制构建 llama-cpp-turboquant，systemd unit llama-server.service
- /v1/models 提供 n_params/n_embd/n_vocab/文件体积（27.32B/5120/248320/22.87GB）
- systemd status 提供服务级 CPU 累计/内存（含 peak）/Tasks
- GPU1 PCIe 是 gen3 x4（GPU0 是 x16）
- 本机 Python 3.9.2（非 3.11），代码必须 3.9 兼容；fastapi/paramiko/uvicorn 均已预装
- ai.lan 为 IPv6（2408:8266:401:2eca::fa6），paramiko/requests 连接正常
- 日志（journalctl）：上下文跨任务持续增长（130453→201047，76.7% of 262144，长对话累积）；MTP 接受率随上下文下降（0.931→0.688）；prompt 冷启动 ~1100 t/s / 热 ~500 t/s；启动时 KV 缓存 K 自动升级 turbo3→q8_0

## 重要 Bug（已修复，待重启生效）

- Top CPU 列表"数据是假的"（与 Top MEM 相同、CPU% 全 0）：根因是 procps 的 stime 列是启动时间而非系统 CPU 时间、utime 列不可用（输出 -）。第一轮改用 ps time 列后又发现 **time 列仅 1s 粒度**，2s 窗口下 CPU% 被量化成 0/50/100/150 台阶（空闲全 0 看似静态）。最终方案：`==PSTICKS==` 段单条 awk 读全部 /proc/<pid>/stat 的 utime/stime（10ms 粒度）按 PID 关联（详见 2026-08-29.md）。**运行中后端需重启才生效**（Codex 沙箱无法 kill 沙箱外进程）
- 双主机"SSH 断开"（CPU —/MEM —，后端零日志）：根因是上一轮 PSTICKS 修复往 `BATCH_CMD`（str.format 模板）新增的 awk 行**未转义 `{`/`}`** → 首个采集周期 `ValueError: unexpected '{' in field name` → SshPoller asyncio 任务静默死亡（异常未被 retrieve，无任何日志）→ reachable 恒 False → ssh_ok=false。修复：转义花括号（`{{`/`}}`）+ SshPoller/LogPoller 循环体加 try/except（单周期异常只记 ERROR 不杀任务）。另修 tvai 专属问题：`log.source=file` 但 `log.path` 为空 → `tail` 无文件参数读 SSH channel stdin（paramiko 永不关闭）挂起 15s → 空消息 socket.timeout 拖垮共享连接反复重连；现配置守卫快速失败并明确报错。tvai 的"llama 离线"非 Bug（机器 09:37 重启，llama-server 10:00 启动后自恢复）。详见 2026-08-29.md

- ctx 告警不实时（长任务中 TopBar 芯片不飘色）：根因是 `monitor.py _build_snapshot()` 的 `evaluate_alerts` 传 LogPoller 活引用 `logst`（context 仅任务结束行更新）而非合并副本 `log_snap`（API 实时 ctx 优先）→ 长任务 API ctx ≥80% 时 ContextCard 变色但 TopBar 芯片不飘。修复：一行 `logst` → `log_snap`（详见 2026-08-29.md）
- KPI 卡阈值双轨：`HostDetailView` ctxLevel/mtpLevel 硬编码 80/90、65/80，与后端 alerts（每主机合并阈值）在用户覆盖 thresholds 时分歧。修复：改 `alertLevel(alerts, 'ctx'/'mtp')` 与 TopBar 同源
## 未完成

- **重启后端**（用户操作）：`pkill -f "uvicorn backend.main:app"` 后 `./run.sh` —— 一次使多处生效：Codex 代理守护（.env 已启用）、Top CPU 精度修复、"SSH 断开"修复、ctx 告警实时化、轮 4 ctx_used/load 序列、轮 5 last_prefill/prefill_start/alert 阈值穿越事件、轮 6 GPU 新 4 字段（显存温度/ECC/降频/显存利用率展示）+ log.state.started_at（状态卡"已运行"）；重启后 `logs/codex_llama_proxy.log` 应出现 "listening on http://127.0.0.1:8901"，两主机 ssh_ok=true，任务中 ctx ≥80% 时 TopBar 芯片应与 KPI 卡同步飘色，预填充速度卡非预填充期应显示"上次 HH:MM:SS"+上次预填充速度，GPU 卡出现 显存温度/ECC/降频状态 行（消费卡显存温度与 ECC 为 "—"）
- **启用 Codex 代理（一键）**（用户操作）：code-server 终端跑 `cd /data/case/LlamaLens && ./devtools/enable_codex_proxy.sh`（起持久代理 + base_url 改 http://127.0.0.1:8901/v1，幂等带备份），再重启 Codex CLI；验证 llama-server journal 不再出现 Jinja 500。注意：Codex 沙箱内拉起的代理不持久（会话结束即死），必须用户终端起
- Go CLI 未提交 git → 已解决（2026-08-30 用户决定不做 CLI，cli/ 整体删除）
- 用户刷新浏览器验证：模型与 Slot 区两卡 50/50（`.model-grid` `repeat(2,1fr)`），右缘与其他双列区对齐（dist 已重建，纯 CSS 无需重启后端）
- 用户刷新浏览器验证进程区排版（dist 已重建：进程卡 4 列指标网格 + 键值服务行，Top 表 PID 右对齐；见 2026-08-29.md）
- 用户刷新浏览器验证趋势区：上下文占用不再闪烁（animation:false + ctxTotal 原始值依赖）；新增 GPU 温度/功耗两图（后端 gpu_temp_N/gpu_power_N 自 init 已采集，无需重启后端）
- 用户刷新浏览器验证：模型与 Slot 区 Model 卡与 Slot 卡等高（.model-grid 删除 align-items:start，dist 已重建，纯 CSS 无需重启后端）
- 用户刷新浏览器验证总览区重构（方案一，dist 已重建，纯前端无需重启后端）：实时总览 4 卡（Token 速度/Prompt 速度/上下文占用条卡 + MTP 接受率仪表）、"实时生成任务"区单卡 LlamaStateCard；窄窗口 2 列/1 列自适应
- tvai 日志采集需用户决策：llama-server stdout 在终端（/dev/pts/0）无日志文件；要么重定向输出到文件并配置 hosts.yaml 的 log.path，要么改用 systemd + source: journal（当前代码对 source=file 无 path 快速失败并报错，不再挂起 SSH）
- 开发后按 AC-01~AC-13 逐项验收（含用运行中任务实测 token 速度）

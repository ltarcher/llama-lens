# Agent Memory Index

## 当前状态

最后更新：2026-08-29

当前工作：LlamaLens（llama-server 多主机监控面板）—— v1.0.0 发布前修复完成（2026-08-29）：ctx 告警实时化、KPI 卡阈值统一、模型区 50/50、README 版本化；dist 已重建，待重启后端 + 用户浏览器目测；工程规则在根目录 AGENTS.md（Codex 自动加载），`.clinerules/` 保留供 Cline 使用

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

- 重启后端使 Top CPU 精度修复 + "SSH 断开"修复 + ctx 告警实时化生效（用户操作：pkill -f "uvicorn backend.main:app" 后 ./run.sh；重启后两主机应显示 ssh_ok=true，任务中 ctx ≥80% 时 TopBar 芯片应与 KPI 卡同步飘色）
- 用户刷新浏览器验证：模型与 Slot 区两卡 50/50（`.model-grid` `repeat(2,1fr)`），右缘与其他双列区对齐（dist 已重建，纯 CSS 无需重启后端）
- 用户刷新浏览器验证进程区排版（dist 已重建：进程卡 4 列指标网格 + 键值服务行，Top 表 PID 右对齐；见 2026-08-29.md）
- 用户刷新浏览器验证趋势区：上下文占用不再闪烁（animation:false + ctxTotal 原始值依赖）；新增 GPU 温度/功耗两图（后端 gpu_temp_N/gpu_power_N 自 init 已采集，无需重启后端）
- 用户刷新浏览器验证：模型与 Slot 区 Model 卡与 Slot 卡等高（.model-grid 删除 align-items:start，dist 已重建，纯 CSS 无需重启后端）
- tvai 日志采集需用户决策：llama-server stdout 在终端（/dev/pts/0）无日志文件；要么重定向输出到文件并配置 hosts.yaml 的 log.path，要么改用 systemd + source: journal（当前代码对 source=file 无 path 快速失败并报错，不再挂起 SSH）
- 开发后按 AC-01~AC-13 逐项验收（含用运行中任务实测 token 速度）

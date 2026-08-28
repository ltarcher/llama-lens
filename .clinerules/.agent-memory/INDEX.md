# Agent Memory Index

## 当前状态

最后更新：2026-08-29

当前工作：LlamaLens（llama-server 多主机监控面板）—— 后端 + 前端已实现，frontend/dist 已构建，`./run.sh` 可启动；工程规则已迁移至根目录 AGENTS.md（Codex 自动加载），`.clinerules/` 保留供 Cline 使用

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

## 未完成

- 开发后按 AC-01~AC-13 逐项验收（含用运行中任务实测 token 速度）

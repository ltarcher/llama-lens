# LlamaLens

llama.cpp llama-server 多主机实时监控面板。

- **门户页**：所有主机状态一览（状态/模型/token 速度/GPU/CPU/内存）
- **单主机详情**：token 速度 / GPU 按卡聚合 / CPU（每核）/ 内存 / 磁盘 / 网络 / 进程 / 模型 / Slot / 事件流，80+ 数据项
- **实时**：WebSocket 1s 推送（可配置 1s/2s/5s/暂停），断线自动降级轮询
- **阈值飘红**：黄/红两级色阶，可按主机配置
- **高科技深色 UI**：霓虹青 + 荧光绿、玻璃拟态、发光动效

## 当前状态

✅ **已实现**（2026-08-28）—— 后端（FastAPI + SSH/HTTP 采集 + WS 推送）与前端（Vue 3 + ECharts）均已完成，
`frontend/dist` 已构建，`./run.sh` 可直接启动。

## 文档索引

| 文档 | 说明 |
|---|---|
| [docs/01-需求文档.md](docs/01-需求文档.md) | 需求基线（后续开发主依据） |
| [docs/02-架构设计文档.md](docs/02-架构设计文档.md) | 架构、采集、数据模型、API、部署 |
| [docs/03-UI与交互设计文档.md](docs/03-UI与交互设计文档.md) | 视觉规范、页面布局、组件、交互 |

## 技术栈（规划）

- 后端：Python 3.9 + FastAPI + uvicorn + paramiko（SSH 只读采集）
- 前端：Vue 3 + Vite + ECharts 5 + Vue Router
- 部署：单进程 :8000（FastAPI 托管前端构建产物）

## 监控对象（首台主机）

- ai.lan — Qwen3.8-27B-Q6_K（27.32B）· 双 RTX 3080 · llama-server :8080
- 详见 01-需求文档.md 附录 A

## 快速开始（实现后）

```bash
cp config/hosts.example.yaml config/hosts.yaml   # 填写主机信息
cp .env.example .env                              # 填写 SSH 密码
cd frontend && npm install && npm run build
./run.sh                                          # http://<本机>:8000
```

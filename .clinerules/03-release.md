# 发布、构建、交付与 Git 规则

# 1. 默认原则

代码完成后：

> 不要自作主张完整构建、重启、重新部署。

优先：

-   静态检查
-   targeted test
-   lint
-   类型检查
-   查看编译错误

完整构建只有在：

-   用户明确要求
-   修改必须通过构建验证
-   发布流程要求
-   需要确认编译结果

时执行。

# 2. 前端构建

前端构建较慢。

不要：

``` text
改一个小文件
↓
完整 build
↓
再改一个小文件
↓
再次完整 build
```

应该尽可能集中修改后，再在需要时构建。

# 3. 重启 / Reload

不要主动说：

> "你是不是没重启？"

除非有明确证据。

如果修改必须重启才能生效：

明确说明：

``` text
为什么需要重启
什么组件需要重启
重启什么
重启后验证什么
```

如果不需要：

> 明确告诉用户不需要。

# 4. Git 状态

开始任务前：

``` bash
git status
```

结束任务后：

``` bash
git status
git diff
```

如果涉及版本：

``` bash
git diff <previous-version>..<current-version>
```

# 5. 用户已有修改

如果 Git 中存在任务开始之前的修改：

-   不覆盖
-   不 reset
-   不 checkout 丢弃
-   不自动清理

必须区分：

``` text
已有用户修改
vs
本次任务修改
```

# 6. Diff Review

完成修改后必须检查：

``` bash
git diff
```

重点：

-   是否改到了正确文件
-   是否多改文件
-   是否出现无关格式变化
-   是否删除了用户内容
-   是否产生调试代码
-   是否产生临时文件
-   是否有意外配置变化

核心问题：

> "这个 diff 是否全部属于当前任务？"

# 7. 交付目录

每次发布版本：

``` text
output/v{版本号}/
```

默认交付物：

``` text
deploy-workbench-image.tar.gz
k8s-deploy.yaml
README.md
编排检查规则指导.md
介质对比使用手册.md
```

# 8. Docker 镜像

默认交付镜像：

``` text
deploy-workbench-image.tar.gz
```

构建思路：

``` text
docker build
    ↓
docker save
    ↓
gzip
```

技术栈：

``` text
Python 3.11
FastAPI
Node 20
Vue 3
```

默认端口：

``` text
8000
```

# 9. Kubernetes

交付：

``` text
k8s-deploy.yaml
```

包括：

``` text
ConfigMap
Deployment
Service
Ingress
```

编排参考：

``` text
/data/case/jbgs/case1/deploy-workbench/deploy
```

不要脱离现有编排结构重新设计。

# 10. README

每次发布版本都检查 README 是否需要更新。

至少同步：

-   安装
-   启动
-   部署
-   使用方式
-   配置
-   注意事项
-   版本变化

# 11. Check 规则指导文档

文件：

``` text
编排检查规则指导.md
```

必须与：

``` text
engine.py
ALL_RULES
```

保持同步。

如果新增、删除、修改检查规则：

检查文档是否需要同步。

# 12. 介质对比使用手册

文件：

``` text
介质对比使用手册.md
```

涉及介质对比功能变化时同步更新。

# 13. 版本生成流程

例如要生成：

``` text
v4
```

先检查：

``` text
output/v3/
```

理解上一版本：

-   文件结构
-   内容
-   配置
-   交付方式

然后再更新。

不要从零凭空生成。

# 14. 更新日志

生成新版本时：

1.  查看上一版本
2.  查看 Git diff
3.  总结新增
4.  总结修改
5.  总结修复
6.  总结重要架构变化
7.  更新合适的文档

Git 仓库：

``` text
/data/case/jbgs/case1/deploy-workbench
```

# 15. 发布前 Gate

发布前必须：

``` text
代码完成
   ↓
测试
   ↓
Git diff
   ↓
交付物检查
   ↓
文档同步
   ↓
版本号确认
   ↓
构建
   ↓
产物检查
   ↓
交付
```

# 16. Definition of Done

发布任务只有满足：

-   [ ] 代码完成
-   [ ] 测试完成
-   [ ] Git diff 已检查
-   [ ] 版本号正确
-   [ ] Docker 产物正确
-   [ ] K8s 文件同步
-   [ ] README 同步
-   [ ] Check 规则文档同步
-   [ ] 介质对比手册同步
-   [ ] 产物目录正确
-   [ ] 没有无关文件

才能宣布发布完成。

# 17. 最终发布报告

``` text
## 版本
vX.X.X

## 新增
- ...

## 修复
- ...

## 修改
- ...

## 测试
- ...

## 构建
- ...

## 交付物
- ...

## Git
- ...

## 风险
- ...

## 未完成
- ...
```

# 18. 凭证安全

禁止把：

-   账号
-   密码
-   Token
-   Cookie
-   API Key
-   内部认证信息

写入：

-   Cline Rules
-   README
-   Git
-   Dockerfile
-   交付文档

测试环境认证信息应使用：

``` text
环境变量
.env
Secret
外部凭证配置
```

并确保敏感文件被 Git 忽略。

如果项目已有凭证写在旧规则中：

> 不要继续扩散。

后续规则只描述：

> "从环境变量/Secret 获取测试凭证。"

# 19. 发布任务的最终原则

不要把：

> "代码能运行"

等同于：

> "可以发布"。

发布是：

``` text
代码
+
测试
+
配置
+
文档
+
版本
+
交付物
+
Git
```

全部一致之后才算完成。

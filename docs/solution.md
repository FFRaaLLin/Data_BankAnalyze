# 不明表单回传分类方案（MariaDB + FastAPI）

## 1. 目标
你当前已有：
- Python 运行环境
- MariaDB

本方案补齐：
1. 不明表单落库（你上游解析后直接调用接口入库）。
2. 生成对外处理批次（推送给线上 Excel 平台）。
3. 接收业务人员处理后的分类结果并回填。
4. 内置失败重试与错误日志，便于后续维护。

---

## 2. 数据流
1. 上游把不明表单写入 `/unknown-forms/batch`。
2. 系统调用 `/sync/tasks/export` 生成“待外发批次”，将数据送到 Excel 平台。
3. 业务在 Excel 平台确认类目后，平台回调 `/sync/tasks/{task_id}/callback`。
4. 系统写入 `classification_results`，并把 `unknown_forms.status` 改为 `resolved`。
5. 如果回调失败，任务进入 `callback_failed`，并记录到 `retry_logs`。
6. 运维可调用 `/sync/tasks/{task_id}/retry` 手工重试。

---

## 3. 表结构
- `unknown_forms`：不明表单主表。
- `sync_tasks`：外发与回调任务表（含状态、重试次数、下次重试时间）。
- `classification_results`：业务确认后的最终类目。
- `retry_logs`：失败明细日志。

初始化 SQL 见 `scripts/init_db.sql`。

---

## 4. 接口清单
### 4.1 批量落库
`POST /unknown-forms/batch`

### 4.2 创建外发任务
`POST /sync/tasks/export`
- 入参：`limit`，控制单批大小。
- 出参：`task_id + items`，其中 `items` 就是给 Excel 平台的数据。

### 4.3 回调处理
`POST /sync/tasks/{task_id}/callback`
- 每条需包含 `form_id + category_code + category_name + reviewer + reviewed_at`。

### 4.4 手工重试
`POST /sync/tasks/{task_id}/retry`

### 4.5 健康检查
`GET /healthz`

---

## 5. 部署步骤

## 5.1 安装依赖
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 5.2 准备环境变量
```bash
cp .env.example .env
# 按你的 MariaDB 实际账号密码修改
```

## 5.3 初始化数据库
```bash
mysql -u root -p < scripts/init_db.sql
```

## 5.4 启动服务
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 6. 错误重传机制（当前已具备）
1. 回调处理异常时，任务状态设为 `callback_failed`。
2. `retry_count` 自增，写入 `retry_logs`。
3. 自动计算 `next_retry_at = now + 5*retry_count 分钟`（指数阶梯近似）。
4. 超过 `RETRY_MAX_TIMES` 后停止自动建议重试（需要人工介入）。
5. 运维可调用手工重试接口恢复任务到 `pushed`。

> 后续可增加定时任务（cron/celery beat）按 `next_retry_at` 自动重放。

---

## 7. 你后续建议补全项
1. **幂等控制**：对 `source_order_id + source_system` 做唯一约束（按业务需要）。
2. **回调鉴权**：加签名（HMAC）+ 时间戳防重放。
3. **字段映射字典表**：避免 Excel 文本脏数据直接入主表。
4. **审计追踪**：记录“谁在什么时候把某单改成什么类目”。
5. **监控告警**：`callback_failed` 超阈值时钉钉/企业微信告警。
6. **归档策略**：超过 N 月数据转历史表，保证在线性能。


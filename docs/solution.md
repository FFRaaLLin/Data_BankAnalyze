# 不明表单回传分类方案（MariaDB + FastAPI）

## 1. 目标
你当前已有：
- Python 运行环境
- MariaDB

本方案补齐：
1. 不明表单落库（按你给的 Excel 表头字段）。
2. 生成对外处理批次（推送给线上 Excel/报表平台）。
3. 接收业务人员处理后的分类结果并回填。
4. 内置失败重试与错误日志，便于后续维护。

---

## 2. Excel 表头字段（已支持）
- `Transaction Date`
- `银行`
- `银行账户`
- `收支类型`
- `对方账户`
- `Transaction Details`
- `Withdrawals`
- `Lodgment`

> 入库后会存到 `unknown_forms` 表对应字段，并在导出时转换为同名 JSON 键。

---

## 3. 数据流
1. 上游把不明表单写入 `/unknown-forms/batch`。
2. 系统调用 `/sync/tasks/export` 生成“待外发批次”，将数据送到 Excel 平台。
3. 业务在 Excel 平台确认类目后，平台回调 `/sync/tasks/{task_id}/callback`。
4. 系统写入 `classification_results`，并把 `unknown_forms.status` 改为 `resolved`。
5. 如果回调失败，任务进入 `callback_failed`，并记录到 `retry_logs`。
6. 运维可调用 `/sync/tasks/{task_id}/retry` 手工重试。

---

## 4. 关键接口
### 4.1 批量落库
`POST /unknown-forms/batch`

请求示例：
```json
{
  "items": [
    {
      "Transaction Date": "2026-03-19",
      "银行": "ABC Bank",
      "银行账户": "6222xxxx",
      "收支类型": "支出",
      "对方账户": "9988xxxx",
      "Transaction Details": "供应商付款",
      "Withdrawals": 1200.5,
      "Lodgment": 0
    }
  ]
}
```

### 4.2 创建外发任务（生成 JSON 给线上报表平台）
`POST /sync/tasks/export`

返回 `items` 示例（可直接传前端平台）：
```json
{
  "task_id": 101,
  "items": [
    {
      "form_id": 1,
      "Transaction Date": "2026-03-19",
      "银行": "ABC Bank",
      "银行账户": "6222xxxx",
      "收支类型": "支出",
      "对方账户": "9988xxxx",
      "Transaction Details": "供应商付款",
      "Withdrawals": 1200.5,
      "Lodgment": 0
    }
  ]
}
```

### 4.3 回调处理
`POST /sync/tasks/{task_id}/callback`

### 4.4 手工重试
`POST /sync/tasks/{task_id}/retry`

---

## 5. 部署步骤

### 5.1 安装依赖
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 5.2 准备环境变量
```bash
cp .env.example .env
# 按你的 MariaDB 实际账号密码修改
```

### 5.3 初始化数据库
```bash
mysql -u root -p < scripts/init_db.sql
```

### 5.4 启动服务
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 6. 错误重传机制（当前已具备）
1. 回调处理异常时，任务状态设为 `callback_failed`。
2. `retry_count` 自增，写入 `retry_logs`。
3. 自动计算 `next_retry_at = now + 5*retry_count 分钟`。
4. 超过 `RETRY_MAX_TIMES` 后停止自动建议重试（需要人工介入）。
5. 运维可调用手工重试接口恢复任务到 `pushed`。

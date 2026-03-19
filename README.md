# Data_BankAnalyze

该仓库提供了一个“**不明账单表单人工分类回填**”的最小可运行实现：

- 支持按 Excel 表头落库（Transaction Date、银行、银行账户、收支类型、对方账户、Transaction Details、Withdrawals、Lodgment）
- FastAPI 接口服务（落库、导出 JSON 批次、回调、重试）
- MariaDB 数据模型
- 回调失败重试机制
- 部署说明

详细方案见：`docs/solution.md`

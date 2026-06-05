# 机房智能巡检与问题闭环管理系统 - 后端

## 快速启动

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # 或直接使用项目内已生成的 .env

python -m alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

数据库结构由 Alembic 负责；应用启动只检查表结构并执行幂等 seed，不再自动创建业务表。

启动后访问：

- Swagger 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

## 演示账号

首次启动会自动写入演示数据，初始密码统一为 `123456`：

| 账号 | 角色 |
|---|---|
| admin | 管理员 |
| inspector01 / inspector02 | 巡检员 |
| handler01 / handler02 | 处理员 |
| verifier01 | 核实员 |

## 目录速览

- `app/core/` — 配置、JWT、密码哈希、日志
- `app/db/` — SQLAlchemy session + 启动种子
- `app/models/` — ORM 模型
- `app/schemas/` — Pydantic 出入参
- `app/crud/` — 数据访问
- `app/services/` — 业务逻辑（状态机统一在这里）
- `app/api/v1/` — REST 接口
- `app/middleware/` — 异常 + 请求日志
- `uploads/` — 本地附件存储（运行后生成）
- `logs/` — 应用日志（运行后生成）

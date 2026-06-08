# 移动端扫码巡检 — 局域网测试说明

用于在开发环境验证「固定二维码 → 手机扫码 → 登录 → 选机房 → 巡检 → 提交」整条链路。

> 架构要点：前端接口一律走**相对地址**（开发用 Vite 代理、生产用 Nginx 转发到后端），
> 所以**手机端不要把后端地址写成 `localhost`**。手机能不能用，取决于
> `PUBLIC_WEB_BASE_URL`（二维码指向的前端地址）是否为手机可达的局域网 IP。

## 1. 取电脑局域网 IP

```bash
# Windows: ipconfig    Linux/Mac: ip addr / ifconfig
```

找到与手机同一 WiFi 的网卡 IPv4，例如当前固定使用的 `192.168.31.204`。手机与电脑必须在同一局域网。

## 2. 配置二维码指向地址

编辑 `backend/.env`（开发前端默认端口 **8001**）：

```text
PUBLIC_WEB_BASE_URL=http://192.168.31.204:8001
FRONTEND_ROUTER_MODE=hash
CORS_ORIGINS=["http://localhost:8001","http://192.168.31.204:8001"]
```

> 若仍是 `localhost` / `127.0.0.1`，二维码弹窗会提示「仅限本机预览」并禁用下载/打印。
> 前端 `frontend/.env.development` 不需要改（接口走相对地址 + 代理）。

## 3. 启动后端

```bash
cd backend
# Windows: .\.venv\Scripts\Activate.ps1   Linux/Mac: source .venv/bin/activate
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 4. 启动前端

```bash
cd frontend
npm run dev            # 默认 0.0.0.0:8001
```

## 5. 放行防火墙

确保电脑防火墙允许入站 **8001**（手机要访问的端口；后端 8000 只需本机，由前端代理转发）。

- Windows：`New-NetFirewallRule -DisplayName "inspection-8001" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8001 -Profile Any`（管理员）
- 第三方安全软件（如火绒/360）可能另需放行 `node.exe` 入站。

## 6. 手机测试步骤

1. 手机浏览器先直接访问 `http://192.168.31.204:8001/`，确认登录页能打开（排除网络/防火墙问题）。
2. 电脑端用管理员登录后台 → **系统管理 → 巡检入口二维码**，得到固定二维码。
3. 手机扫码（微信弹"继续访问"点继续）→ 登录页 → 用巡检员/管理员账号登录。
4. 登录后进入**「选择要巡检的机房」**，点机房 → 逐台设备巡检 → 提交。
5. 回电脑后台「巡检记录」即可看到该次数据与生成的报告。

## 7. 常见问题

- 手机浏览器都打不开 → 不在同一网段 / 防火墙未放行 / WiFi 开了 AP 隔离。
- 接口 Network Error 但页面能开 → 多为后端没起或前端把接口指到了绝对地址（本项目已用相对地址规避）。
- 二维码只包含巡检入口 URL，不含账号、密码、Token。
- 停用的机房不出现在可选列表中。

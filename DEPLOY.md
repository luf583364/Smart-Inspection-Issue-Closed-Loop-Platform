# 部署说明（Docker Compose）

目标：在服务器上以 `http://<服务器IP>:8001` 对外提供服务（下文 `<服务器IP>` 替换成你的实际地址，例如 `172.16.4.54`）。

## 一、前置条件

- 服务器已安装 **Docker** 与 **Docker Compose v2**（`docker compose version` 可用）。
- 服务器 `8001` 端口未被占用、且允许内网/手机访问。

## 一点五、镜像拉取（国内服务器重要）

国内服务器经常连不上 Docker Hub（`registry-1.docker.io` 超时）。构建本项目需要拉取
`python:3.12-slim`、`node:20-alpine`、`nginx:1.27-alpine` 三个基础镜像。若 `docker compose build`
卡在 `failed to do request ... registry-1.docker.io` 这类错误，配置**镜像加速器**即可：

编辑 `/etc/docker/daemon.json`（没有就新建）：

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live",
    "https://hub.rat.dev"
  ]
}
```

然后重启 Docker 并重试：

```bash
sudo systemctl restart docker
docker compose build
```

> 镜像加速器地址时效性较强，若上面的失效，换一个当前可用的公共加速器即可。
> 也可手动 `docker pull docker.m.daocloud.io/library/python:3.12-slim` 后
> `docker tag` 成 `python:3.12-slim`，对三个基础镜像各做一次，再 `docker compose build`（会用本地缓存）。

## 二、部署步骤

```bash
# 1. 把整个项目目录拷到服务器，例如 /opt/inspection
cd /opt/inspection

# 2. 准备环境变量
cp .env.example .env
vi .env            # 改 PUBLIC_WEB_BASE_URL 和 JWT_SECRET（见下）

# 3. 构建并后台启动
docker compose up -d --build

# 4. 查看状态 / 日志
docker compose ps
docker compose logs -f backend
```

启动后访问 **http://<服务器IP>:8001**，默认管理员 `admin / 123456`（请尽快在「用户管理」改密码）。

## ✅ 部署后必做清单

| # | 事项 | 操作 |
|---|---|---|
| 1 | **改入口地址** | `.env` 里 `PUBLIC_WEB_BASE_URL=http://<服务器IP>:8001`（必须手机能访问到，否则二维码扫不开），改完 `docker compose up -d` |
| 2 | **改密钥** | `.env` 里 `JWT_SECRET` 换成一段足够长的随机字符串，改完重启 |
| 3 | **改默认密码** | 登录 `admin/123456` 后，到「系统管理 → 用户管理」修改 **admin** 及所有演示账号的密码 |
| 4 | **放行端口** | 服务器防火墙/安全组放行 **8001** 入站 |
| 5 | **处理演示数据** | 首次启动会写入演示用户/机房/设备/巡检记录。正式使用前：在「用户管理 / 机房 / 设备」里改成真实数据，或**清空重来**（停服 → 删除 `./data/inspection.db` → `docker compose up -d`，空库会再次写入演示数据，请据此调整账号/机房） |
| 6 | **建好角色账号** | 闭环需要：至少 1 个**处理员**、1 个**核实员**（演示自带 `handler01/02`、`verifier01`，可改密保留或新建真实账号） |
| 7 | **备份** | 定期备份 `./data` 目录（数据库 + 照片 + 报告） |

> 二维码在「系统管理 → 巡检入口二维码」生成；若页面提示「仅限本机预览/不可打印」，说明 `PUBLIC_WEB_BASE_URL` 还是 localhost，按第 1 条改。

## 三、关键配置 `.env`

| 变量 | 说明 |
|---|---|
| `PUBLIC_WEB_BASE_URL` | 机房二维码里编码的地址。**必须是手机能访问到的地址**（如 `http://172.16.4.54:8001`）。若填 localhost，二维码会被标记为「不可打印」。 |
| `JWT_SECRET` | 登录令牌签名密钥，务必改成足够长的随机串。 |

改完 `.env` 后需 `docker compose up -d`（会重建受影响容器）使其生效。

## 四、数据存放位置（都在宿主机 `./data`）

| 路径 | 内容 |
|---|---|
| `./data/inspection.db` | **数据库**：用户/机房/设备/巡检记录/检查项结果/附件元数据 |
| `./data/uploads/` | 巡检上传的**现场照片**（原图按 `年/月` 归档） |
| `./data/reports/` | 每次提交自动生成的**巡检报告 HTML**，文件名即记录编号（如 `IR202606040002.html`） |

- 报告为**自包含 HTML**（照片以 base64 内嵌），可直接双击查看、随意拷贝分发。
- 系统内：巡检记录列表 / 详情页都有「查看报告」「下载报告」按钮。
- 想单独挂一块盘专门放报告，把 compose 里 `./data` 换成你的目录，或单独把 `./data/reports` 软链/挂载到目标盘即可。

**备份**：停服或热备直接拷贝整个 `./data` 目录即可，恢复同理。

## 五、常用运维命令

```bash
docker compose restart backend      # 重启后端
docker compose down                 # 停服（数据保留在 ./data）
docker compose up -d --build        # 改代码后重新构建发布
docker compose logs -f              # 跟踪日志
```

## 六、升级 / 迁移

- 代码更新后 `docker compose up -d --build`，后端容器启动时会自动执行 `alembic upgrade head` 应用数据库迁移，无需手动操作。
- 数据库 schema 变更通过 `backend/alembic/versions/` 管理，迁移含历史数据回填。

## 七、故障排查

| 现象 | 处理 |
|---|---|
| 8001 打不开 | `docker compose ps` 看 frontend 是否 Up；`docker compose logs frontend` |
| 接口 502 | 后端没起来：`docker compose logs backend`（多为迁移失败或端口冲突） |
| 二维码扫码打不开 | `.env` 的 `PUBLIC_WEB_BASE_URL` 不是手机可达地址，改成服务器内网 IP 后 `docker compose up -d` |
| 后端镜像构建时某依赖编译失败 | 极少见；给 `backend/Dockerfile` 的 pip 安装前加一层 `apt-get update && apt-get install -y build-essential libffi-dev` |
| 照片上传 413 | nginx 已设 `client_max_body_size 10m`，单图上限 5MB；如需更大同时改 nginx.conf 与后端 `file_storage.MAX_BYTES` |

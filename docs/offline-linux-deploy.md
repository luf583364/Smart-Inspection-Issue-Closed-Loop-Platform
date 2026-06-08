# 机房巡检系统离线 Linux 部署教程

适用场景：Linux 服务器不能连接外网，只能通过 XFTP/SFTP 上传文件。

## 1. 部署结构

- 前端容器：Nginx，对外端口 `8001`
- 后端容器：FastAPI，容器内部端口 `8000`，不直接暴露到宿主机
- 数据库：SQLite 文件，路径为服务器项目目录下的 `./data/inspection.db`
- 上传照片：`./data/uploads`
- 巡检报告：`./data/reports`

当前项目不需要额外安装 MySQL、PostgreSQL 等数据库。Docker Compose 只启动前端和后端两个容器，数据库是后端使用的 SQLite 单文件，并通过 `./data:/app/data` 挂载到宿主机，容器重建后数据仍在。

## 2. 先在有网且 Docker 可用的机器上打包

在 Windows 项目目录执行：

```powershell
cd E:\机房巡检系统
.\scripts\offline-deploy\build-and-save-images.ps1 -PackageAfterBuild
```

成功后会生成：

```text
offline-package\inspection-system-offline.zip
```

这个 zip 内包含项目代码、部署脚本、Compose 配置和 `docker-images/*.tar` 镜像包。

如果执行时报 Docker daemon 未运行，需要先启动 Docker Desktop，或换一台能运行 Docker 的电脑执行上面的命令。服务器离线时不能现场构建镜像，因为构建需要 Python、Node、Nginx 基础镜像和依赖包。

## 3. 如果服务器没有 Docker

可以把 Docker 安装包也一起通过 XFTP 上传，但安装包必须匹配服务器系统和 CPU 架构。

建议在一台相同 Linux 发行版和版本的有网机器上下载完整依赖包：

Ubuntu/Debian：

```bash
mkdir -p docker-install/deb
cd docker-install/deb
apt download containerd.io docker-ce docker-ce-cli docker-buildx-plugin docker-compose-plugin
```

CentOS/RHEL/Rocky/Anolis：

```bash
mkdir -p docker-install/rpm
cd docker-install/rpm
yumdownloader --resolve docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

把 `docker-install` 目录放到解压后的项目根目录，然后在服务器执行：

```bash
bash scripts/offline-deploy/install-docker-from-local-packages.sh
```

如果提示缺少系统依赖，说明离线包不完整，需要在同版本系统上把依赖一并下载后再上传。

## 4. 上传并解压项目

通过 XFTP 上传 `inspection-system-offline.zip` 到服务器，例如 `/opt/inspection`：

```bash
sudo mkdir -p /opt/inspection
sudo chown -R "$USER":"$USER" /opt/inspection
cd /opt/inspection
unzip inspection-system-offline.zip
cd inspection-system
```

## 5. 修改生产环境配置

复制环境变量文件：

```bash
cp .env.example .env
vi .env
```

至少修改：

```env
PUBLIC_WEB_BASE_URL=http://服务器IP:8001
JWT_SECRET=换成一串足够长的随机字符串
TZ=Asia/Shanghai
APP_TIMEZONE=Asia/Shanghai
SEED_DEMO_DATA=false
BOOTSTRAP_ADMIN_USERNAME=admin
BOOTSTRAP_ADMIN_PASSWORD=123456
```

`PUBLIC_WEB_BASE_URL` 必须是手机能访问到的地址，不能写 `localhost`。二维码扫码地址由这个变量生成。

`SEED_DEMO_DATA=false` 表示干净生产初始化：只创建管理员账号、两个基础机房、基础设备和巡检类目模板，不创建演示用户和演示巡检记录。

如果需要演示数据，再改成 `SEED_DEMO_DATA=true`。

巡检提交时间由后端写入。`APP_TIMEZONE=Asia/Shanghai` 用于固定业务时间，避免容器默认 UTC 导致提交时间偏差。

## 6. 启动系统

```bash
bash scripts/offline-deploy/load-and-start.sh
```

脚本会执行：

- 加载 `docker-images/*.tar`
- 创建 `data/uploads` 和 `data/reports`
- 使用 `docker compose up -d --no-build` 启动，避免离线服务器构建或拉镜像

查看状态：

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
```

检查容器时间：

```bash
docker compose exec backend date
docker compose exec backend python -c "from app.utils.time_utils import now_local; print(now_local())"
```

浏览器访问：

```text
http://服务器IP:8001
```

默认账号来自 `.env`：

```text
admin / 123456
```

上线后请在系统里尽快修改密码。

## 7. 防火墙

Ubuntu：

```bash
sudo ufw allow 8001/tcp
```

CentOS/RHEL/Rocky/Anolis：

```bash
sudo firewall-cmd --add-port=8001/tcp --permanent
sudo firewall-cmd --reload
```

## 8. 数据一致性说明

前端不保存业务数据。人员、机房、设备、巡检记录、照片、报告都通过后端 API 写入后端数据库或数据目录。

部署后真实数据位置：

```text
data/inspection.db
data/uploads/
data/reports/
```

只要使用系统页面进行新增、编辑、停用、删除和提交巡检，前后端会保持一致。不要手工改浏览器缓存或直接改数据库文件。

当前删除规则会避免破坏历史数据关联：例如已被巡检记录引用的人员、机房、设备，不应直接物理删除，应停用或按后端规则处理。

## 9. 备份与恢复

停止服务：

```bash
docker compose down
```

备份：

```bash
tar czf inspection-data-$(date +%F).tar.gz data
```

恢复：

```bash
docker compose down
rm -rf data
tar xzf inspection-data-YYYY-MM-DD.tar.gz
docker compose up -d --no-build
```

## 10. 更新版本

在有网且 Docker 可用的机器上重新执行：

```powershell
.\scripts\offline-deploy\build-and-save-images.ps1 -PackageAfterBuild
```

把新的 `inspection-system-offline.zip` 上传服务器，解压覆盖代码和镜像包，但不要删除服务器 `data` 目录。

然后执行：

```bash
bash scripts/offline-deploy/load-and-start.sh
```

后端启动时会自动执行数据库迁移，历史数据会保留在 `data/inspection.db`。

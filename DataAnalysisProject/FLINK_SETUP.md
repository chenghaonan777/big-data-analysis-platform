# Apache Flink 配置指南

## 配置说明

本配置基于 Docker Compose，创建了一个与截图中相同的 Flink 环境：
- Flink 版本：1.13.6
- 1 个 JobManager
- 3 个 TaskManager，共 3 个 Task Slots
- Web Dashboard 端口：8081

## 启动 Flink 服务

### 单独启动 Flink（推荐）

```bash
# 进入项目目录
cd DataAnalysisProject

# 启动 Flink 服务
docker-compose -f docker-compose-flink.yml up -d
```

### 同时启动所有服务（包括 Hadoop 和 Hive）

```bash
# 启动所有服务
docker-compose -f docker-compose.yml -f docker-compose-flink.yml up -d
```

## 访问 Flink Web Dashboard

启动后，打开浏览器访问：
```
http://localhost:8081
```

您将看到与截图中相同的 Flink Web Dashboard，显示：
- Available Task Slots: 3
- Total Task Slots: 3
- Task Managers: 3

## 验证服务状态

### 检查容器状态

```bash
docker ps
```

您应该看到以下容器正在运行：
- flink-jobmanager
- flink-taskmanager-1
- flink-taskmanager-2
- flink-taskmanager-3

### 查看服务日志

```bash
# 查看 JobManager 日志
docker logs flink-jobmanager

# 查看 TaskManager 日志
docker logs flink-taskmanager-1
```

## 提交 Flink 作业

1. 访问 Flink Web Dashboard: http://localhost:8081
2. 点击左侧菜单中的 "Submit New Job"
3. 上传您的 Flink 作业 JAR 文件
4. 配置作业参数并提交

## 停止服务

```bash
# 停止 Flink 服务
docker-compose -f docker-compose-flink.yml down

# 停止所有服务
docker-compose -f docker-compose.yml -f docker-compose-flink.yml down
```

## 配置调整

如果需要调整配置，可以修改 `docker-compose-flink.yml` 文件：

- **增加 Task Slots**：修改每个 TaskManager 的 `taskmanager.numberOfTaskSlots` 值
- **增加 TaskManager**：复制 TaskManager 服务配置并修改容器名称
- **修改端口**：调整 JobManager 的端口映射

## 版本说明

本配置使用的 Flink 版本为 1.13.6，与截图中显示的版本一致。如果需要使用其他版本，只需修改 `docker-compose-flink.yml` 文件中的镜像标签即可。
# FinalShell 中配置 Apache Flink 步骤指南

## 前提条件

- 已安装 FinalShell
- 已连接到 Linux 服务器
- 服务器已安装 Java 8 或更高版本

## 步骤 1：检查 Java 环境

在 FinalShell 中执行以下命令：

```bash
java -version
```

确保输出显示 Java 8 或更高版本。

## 步骤 2：下载 Flink

执行以下命令下载 Flink 1.13.6 版本（与截图中版本一致）：

```bash
wget https://archive.apache.org/dist/flink/flink-1.13.6/flink-1.13.6-bin-scala_2.12.tgz
```

## 步骤 3：解压 Flink

```bash
tar -xzf flink-1.13.6-bin-scala_2.12.tgz
mv flink-1.13.6-bin-scala_2.12 flink
```

## 步骤 4：配置 Flink

### 修改 flink/conf/flink-conf.yaml 文件

执行以下命令编辑配置文件：

```bash
vi flink/conf/flink-conf.yaml
```

按 `i` 进入编辑模式，修改以下配置：

```yaml
# JobManager 配置
jobmanager.rpc.address: localhost
jobmanager.rpc.port: 6123
jobmanager.heap.size: 1024m

# TaskManager 配置
taskmanager.heap.size: 1024m
taskmanager.numberOfTaskSlots: 1  # 每个 TaskManager 1 个 slot

# Web Dashboard 配置
rest.port: 8081
```

按 `Esc` 键退出编辑模式，输入 `:wq` 保存并退出。

### 修改 flink/conf/workers 文件

执行以下命令编辑 workers 文件：

```bash
vi flink/conf/workers
```

按 `i` 进入编辑模式，添加 3 个 TaskManager：

```
localhost
localhost
localhost
```

按 `Esc` 键退出编辑模式，输入 `:wq` 保存并退出。

## 步骤 5：启动 Flink 集群

执行以下命令启动 Flink 集群：

```bash
cd flink
./bin/start-cluster.sh
```

## 步骤 6：验证 Flink 服务

### 检查进程状态

```bash
jps
```

您应该看到以下进程：
- JobManager
- TaskManager (3个)

### 查看 Flink Web Dashboard

在浏览器中访问：
```
http://服务器IP:8081
```

您将看到与截图中相同的 Flink Web Dashboard，显示：
- Available Task Slots: 3
- Total Task Slots: 3
- Task Managers: 3

## 步骤 7：停止 Flink 集群

当您完成工作后，可以执行以下命令停止 Flink 集群：

```bash
cd flink
./bin/stop-cluster.sh
```

## 步骤 8：配置环境变量（可选）

为了方便使用 Flink 命令，可以将 Flink 添加到环境变量中：

```bash
vi ~/.bashrc
```

在文件末尾添加：

```bash
export FLINK_HOME=~/flink
export PATH=$PATH:$FLINK_HOME/bin
```

执行以下命令使配置生效：

```bash
source ~/.bashrc
```

## 验证配置

执行以下命令验证 Flink 配置：

```bash
flink --version
```

您应该看到 Flink 1.13.6 版本信息。

## 常见问题

### 端口冲突

如果 8081 端口已被占用，可以修改 `flink/conf/flink-conf.yaml` 文件中的 `rest.port` 配置。

### 内存不足

如果启动失败，可以修改 `flink/conf/flink-conf.yaml` 文件中的内存配置，减少 `jobmanager.heap.size` 和 `taskmanager.heap.size` 的值。

### Java 版本问题

确保使用 Java 8 或更高版本，Flink 1.13.6 不支持 Java 7 及以下版本。
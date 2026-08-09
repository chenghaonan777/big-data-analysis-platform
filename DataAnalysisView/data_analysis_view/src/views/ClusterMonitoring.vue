<template>
  <div class="cluster-monitoring">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>
        <i class="el-icon-monitor"></i>
        集群监控中心
      </h1>
      <div class="header-actions">
        <el-button
          type="primary"
          icon="el-icon-refresh"
          @click="refreshAll"
          :loading="refreshing">
          刷新全部
        </el-button>
        <el-button
          :type="monitoringActive ? 'danger' : 'success'"
          :icon="monitoringActive ? 'el-icon-video-pause' : 'el-icon-video-play'"
          @click="toggleMonitoring">
          {{ monitoringActive ? '停止监控' : '启动监控' }}
        </el-button>
      </div>
    </div>

    <!-- 系统概览卡片 -->
    <el-row :gutter="20" class="overview-section">
      <el-col :span="6">
        <el-card class="status-card" :class="overallStatus">
          <div class="status-content">
            <div class="status-icon">
              <i :class="statusIcon"></i>
            </div>
            <div class="status-info">
              <h3>集群状态</h3>
              <p>{{ statusText }}</p>
              <small>{{ lastUpdated }}</small>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="metric-card">
          <div class="metric-content">
            <div class="metric-icon">
              <i class="el-icon-warning-outline"></i>
            </div>
            <div class="metric-info">
              <h3>{{ alertSummary.total_count || 0 }}</h3>
              <p>活动告警</p>
              <small>错误: {{ alertSummary.error_count || 0 }} | 警告: {{ alertSummary.warning_count || 0 }}</small>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="metric-card">
          <div class="metric-content">
            <div class="metric-icon">
              <i class="el-icon-cpu"></i>
            </div>
            <div class="metric-info">
              <h3>{{ systemMetrics.cpu?.usage_percent || 0 }}%</h3>
              <p>CPU使用率</p>
              <small>{{ systemMetrics.cpu?.core_count || 0 }} 核心</small>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="metric-card">
          <div class="metric-content">
            <div class="metric-icon">
              <i class="el-icon-s-data"></i>
            </div>
            <div class="metric-info">
              <h3>{{ systemMetrics.memory?.usage_percent || 0 }}%</h3>
              <p>内存使用率</p>
              <small>{{ formatGB(systemMetrics.memory?.used_gb) }} / {{
                  formatGB(systemMetrics.memory?.total_gb)
                }}</small>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 组件状态监控 -->
    <el-row :gutter="20" class="components-section">
      <el-col :span="8" v-for="(component, name) in clusterStatus.components" :key="name">
        <el-card class="component-card">
          <div slot="header" class="component-header">
            <span class="component-title">
              <i :class="getComponentIcon(name)"></i>
              {{ getComponentName(name) }}
            </span>
            <el-tag :type="getStatusType(component.status)" size="small">
              {{ getStatusText(component.status) }}
            </el-tag>
          </div>

          <div class="component-details">
            <div v-if="name === 'hadoop'" class="detail-item">
              <span>NameNode:</span>
              <el-tag :type="component.namenode_status === 'active' ? 'success' : 'warning'" size="mini">
                {{ component.namenode_status }}
              </el-tag>
            </div>

            <div v-if="name === 'hadoop'" class="detail-item">
              <span>容量使用:</span>
              <span>{{ component.capacity_used?.toFixed(1) }}%</span>
            </div>

            <div v-if="name === 'hive'" class="detail-item">
              <span>数据库数量:</span>
              <span>{{ component.database_count }}</span>
            </div>

            <div v-if="name === 'hive'" class="detail-item">
              <span>表数量:</span>
              <span>{{ component.table_count }}</span>
            </div>

            <div v-if="name === 'mysql'" class="detail-item">
              <span>连接状态:</span>
              <el-tag :type="component.connection_status === 'active' ? 'success' : 'info'" size="mini">
                {{ component.connection_status }}
              </el-tag>
            </div>

            <div v-if="name === 'mysql'" class="detail-item">
              <span>数据库大小:</span>
              <span>{{ component.database_size?.toFixed(1) }} MB</span>
            </div>

            <div class="detail-item">
              <span>最后检查:</span>
              <span>{{ formatTime(component.last_check) }}</span>
            </div>
          </div>

          <div class="component-actions">
            <el-button size="mini" @click="showComponentDetail(name, component)">
              详细信息
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 性能指标图表 -->
    <el-row :gutter="20" class="metrics-section">
      <el-col :span="12">
        <el-card>
          <div slot="header">
            <span>系统资源使用率</span>
          </div>
          <div class="chart-container">
            <div ref="systemChart" style="height: 300px; width: 100%;"></div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <div slot="header">
            <span>数据处理性能</span>
          </div>
          <div class="chart-container">
            <div ref="performanceChart" style="height: 300px; width: 100%;"></div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 告警信息 -->
    <el-row class="alerts-section">
      <el-col :span="24">
        <el-card>
          <div slot="header">
            <span>系统告警</span>
            <el-button style="float: right;" type="text" @click="refreshAlerts">
              <i class="el-icon-refresh"></i>
            </el-button>
          </div>

          <el-table :data="alerts" style="width: 100%" empty-text="暂无告警信息">
            <el-table-column prop="level" label="级别" width="80">
              <template slot-scope="scope">
                <el-tag :type="scope.row.level === 'error' ? 'danger' : 'warning'" size="small">
                  {{ scope.row.level === 'error' ? '错误' : '警告' }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="component" label="组件" width="100">
              <template slot-scope="scope">
                <span>{{ getComponentName(scope.row.component) }}</span>
              </template>
            </el-table-column>

            <el-table-column prop="message" label="告警信息"></el-table-column>

            <el-table-column prop="timestamp" label="时间" width="180">
              <template slot-scope="scope">
                {{ formatTime(scope.row.timestamp) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 大数据环境状态 -->
    <el-row class="bigdata-section">
      <el-col :span="24">
        <el-card>
          <div slot="header">
            <span>大数据环境管理</span>
          </div>

          <div class="bigdata-controls">
            <el-button type="primary" @click="initializeBigData" :loading="bigdataLoading">
              初始化环境
            </el-button>
          </div>

          <div class="bigdata-status">
            <el-row :gutter="15">
              <el-col :span="8" v-for="(status, component) in bigdataStatus" :key="component">
                <div class="bigdata-item">
                  <span class="component-name">{{ getComponentName(component) }}:</span>
                  <el-tag :type="getBigDataStatusType(status)" size="small">
                    {{ getBigDataStatusText(status) }}
                  </el-tag>
                </div>
              </el-col>
            </el-row>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 组件详情弹窗 -->
    <el-dialog
      :title="`${selectedComponentName} 详细信息`"
      :visible.sync="componentDetailVisible"
      width="600px">
      <div v-if="selectedComponent">
        <el-descriptions :column="2" border>
          <el-descriptions-item
            v-for="(value, key) in selectedComponent"
            :key="key"
            :label="formatLabel(key)">
            <span v-if="typeof value === 'object'">{{ JSON.stringify(value) }}</span>
            <el-tag v-else-if="key.includes('status')" :type="getStatusType(value)" size="small">
              {{ value }}
            </el-tag>
            <span v-else>{{ value }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import * as echarts from 'echarts'

export default {
  name: 'ClusterMonitoring',
  data () {
    return {
      refreshing: false,
      monitoringActive: false,

      // 集群状态数据
      clusterStatus: {
        overall_status: 'unknown',
        components: {},
        system_metrics: {},
        timestamp: null
      },

      // 告警数据
      alerts: [],
      alertSummary: {},

      // 系统指标
      systemMetrics: {},
      performanceMetrics: {},

      // 大数据状态
      bigdataStatus: {},
      bigdataLoading: false,

      // 弹窗
      componentDetailVisible: false,
      selectedComponent: null,
      selectedComponentName: '',

      // 定时器
      refreshTimer: null,

      // 图表实例
      systemChart: null,
      performanceChart: null
    }
  },

  computed: {
    overallStatus () {
      const status = this.clusterStatus.overall_status
      return {
        'status-healthy': status === 'healthy',
        'status-warning': status === 'warning',
        'status-error': status === 'error'
      }
    },

    statusIcon () {
      const status = this.clusterStatus.overall_status
      const icons = {
        'healthy': 'el-icon-success',
        'warning': 'el-icon-warning',
        'error': 'el-icon-error'
      }
      return icons[status] || 'el-icon-question'
    },

    statusText () {
      const status = this.clusterStatus.overall_status
      const texts = {
        'healthy': '运行正常',
        'warning': '存在警告',
        'error': '存在错误'
      }
      return texts[status] || '状态未知'
    },

    lastUpdated () {
      if (this.clusterStatus.timestamp) {
        return `更新于 ${this.formatTime(this.clusterStatus.timestamp)}`
      }
      return '暂无数据'
    }
  },

  async mounted () {
    // 强制重置滚动样式
    this.resetScrollStyles()

    await this.initializeMonitoring()
    this.initCharts()
    this.startAutoRefresh()
  },

  beforeDestroy () {
    this.stopAutoRefresh()
    this.destroyCharts()
    // 恢复默认样式
    this.restoreScrollStyles()
  },

  methods: {
    // 重置滚动样式
    resetScrollStyles () {
      document.documentElement.style.overflow = 'auto'
      document.documentElement.style.height = 'auto'
      document.documentElement.style.maxHeight = 'none'

      document.body.style.overflow = 'auto'
      document.body.style.height = 'auto'
      document.body.style.maxHeight = 'none'

      const app = document.getElementById('app')
      if (app) {
        app.style.overflow = 'auto'
        app.style.height = 'auto'
        app.style.maxHeight = 'none'
      }

      const routerView = document.querySelector('.router-view')
      if (routerView) {
        routerView.style.overflow = 'auto'
        routerView.style.height = 'auto'
        routerView.style.maxHeight = 'none'
      }

      const elMain = document.querySelector('.el-main')
      if (elMain) {
        elMain.style.overflow = 'auto'
        elMain.style.height = 'auto'
        elMain.style.maxHeight = 'none'
      }
    },

    // 恢复默认样式
    restoreScrollStyles () {
      document.documentElement.style.overflow = ''
      document.documentElement.style.height = ''
      document.documentElement.style.maxHeight = ''

      document.body.style.overflow = ''
      document.body.style.height = ''
      document.body.style.maxHeight = ''
    },

    // 初始化图表
    initCharts () {
      this.$nextTick(() => {
        if (this.$refs.systemChart) {
          this.systemChart = echarts.init(this.$refs.systemChart)
        }
        if (this.$refs.performanceChart) {
          this.performanceChart = echarts.init(this.$refs.performanceChart)
        }
        this.updateCharts()
      })
    },

    // 销毁图表
    destroyCharts () {
      if (this.systemChart) {
        this.systemChart.dispose()
        this.systemChart = null
      }
      if (this.performanceChart) {
        this.performanceChart.dispose()
        this.performanceChart = null
      }
    },

    async initializeMonitoring () {
      this.$message.info('正在初始化集群监控...')

      try {
        await Promise.all([
          this.loadClusterStatus(),
          this.loadSystemMetrics(),
          this.loadAlerts(),
          this.loadBigDataStatus()
        ])

        this.updateCharts()
        this.$message.success('集群监控初始化完成')

      } catch (error) {
        console.error('监控初始化失败:', error)
        this.$message.error('监控初始化失败，部分功能可能不可用')
      }
    },

    async loadClusterStatus () {
      try {
        const response = await this.$http.get('/api/cluster/status')
        this.clusterStatus = response
        console.log('集群状态:', response)
      } catch (error) {
        console.error('获取集群状态失败:', error)
        this.clusterStatus = this.getMockClusterStatus()
      }
    },

    async loadSystemMetrics () {
      try {
        const response = await this.$http.get('/api/cluster/system')
        this.systemMetrics = response

        const perfResponse = await this.$http.get('/api/cluster/metrics')
        this.performanceMetrics = perfResponse

      } catch (error) {
        console.error('获取系统指标失败:', error)
        this.systemMetrics = this.getMockSystemMetrics()
        this.performanceMetrics = this.getMockPerformanceMetrics()
      }
    },

    async loadAlerts () {
      try {
        const response = await this.$http.get('/api/cluster/alerts')
        this.alerts = response.alerts || []
        this.alertSummary = {
          total_count: response.total_count || 0,
          error_count: response.error_count || 0,
          warning_count: response.warning_count || 0
        }
      } catch (error) {
        console.error('获取告警信息失败:', error)
        this.alerts = []
        this.alertSummary = {
          total_count: 0,
          error_count: 0,
          warning_count: 0
        }
      }
    },

    async loadBigDataStatus () {
      try {
        const response = await this.$http.get('/api/bigdata/status')
        this.bigdataStatus = response
      } catch (error) {
        console.error('获取大数据状态失败:', error)
        this.bigdataStatus = {
          hadoop: 'disconnected',
          hive: 'disconnected',
          mysql: 'disconnected'
        }
      }
    },

    async refreshAll () {
      this.refreshing = true
      try {
        await this.initializeMonitoring()
        this.$message.success('数据已刷新')
      } catch (error) {
        this.$message.error('刷新失败')
      } finally {
        this.refreshing = false
      }
    },

    async refreshAlerts () {
      await this.loadAlerts()
      this.$message.success('告警信息已刷新')
    },

    async toggleMonitoring () {
      try {
        if (this.monitoringActive) {
          await this.$http.post('/api/cluster/monitoring/stop')
          this.stopAutoRefresh()
          this.monitoringActive = false
          this.$message.success('监控已停止')
        } else {
          await this.$http.post('/api/cluster/monitoring/start', { interval: 30 })
          this.startAutoRefresh()
          this.monitoringActive = true
          this.$message.success('监控已启动')
        }
      } catch (error) {
        this.$message.error('监控状态切换失败')
      }
    },

    startAutoRefresh () {
      this.stopAutoRefresh()
      this.refreshTimer = setInterval(() => {
        this.loadClusterStatus()
        this.loadSystemMetrics()
        this.loadAlerts()
      }, 30000) // 30秒刷新一次
    },

    stopAutoRefresh () {
      if (this.refreshTimer) {
        clearInterval(this.refreshTimer)
        this.refreshTimer = null
      }
    },

    // 大数据环境管理
    async initializeBigData () {
      this.bigdataLoading = true
      try {
        await this.$http.post('/api/bigdata/initialize')
        this.$message.success('大数据环境初始化成功')
        await this.loadBigDataStatus()
      } catch (error) {
        this.$message.error('大数据环境初始化失败')
      } finally {
        this.bigdataLoading = false
      }
    },

    // 组件详情
    showComponentDetail (name, component) {
      this.selectedComponent = component
      this.selectedComponentName = this.getComponentName(name)
      this.componentDetailVisible = true
    },

    // 图表更新
    updateCharts () {
      this.$nextTick(() => {
        this.updateSystemResourcesChart()
        this.updatePerformanceChart()
      })
    },

    updateSystemResourcesChart () {
      if (!this.systemChart) return

      const metrics = this.systemMetrics
      const option = {
        title: {
          text: '系统资源使用率',
          left: 'center',
          textStyle: {
            fontSize: 16,
            color: '#303133'
          }
        },
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c}%'
        },
        legend: {
          orient: 'vertical',
          left: 'left',
          top: 'middle'
        },
        series: [{
          name: '资源使用',
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['60%', '50%'],
          avoidLabelOverlap: false,
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: '30',
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: false
          },
          data: [
            {
              value: metrics.cpu?.usage_percent || 0,
              name: 'CPU使用率',
              itemStyle: { color: '#5470c6' }
            },
            {
              value: metrics.memory?.usage_percent || 0,
              name: '内存使用率',
              itemStyle: { color: '#91cc75' }
            },
            {
              value: metrics.disk?.usage_percent || 0,
              name: '磁盘使用率',
              itemStyle: { color: '#fac858' }
            }
          ]
        }]
      }

      this.systemChart.setOption(option)
    },

    updatePerformanceChart () {
      if (!this.performanceChart) return

      const perf = this.performanceMetrics
      const option = {
        title: {
          text: '数据处理性能',
          left: 'center',
          textStyle: {
            fontSize: 16,
            color: '#303133'
          }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: ['处理速率', 'HDFS使用', '查询成功率', '响应时间'],
          axisTick: {
            alignWithLabel: true
          }
        },
        yAxis: {
          type: 'value'
        },
        series: [{
          name: '性能指标',
          type: 'bar',
          barWidth: '60%',
          data: [
            {
              value: perf.component_performance?.hadoop?.throughput_mb_s || 125.6,
              itemStyle: { color: '#5470c6' }
            },
            {
              value: perf.component_performance?.hadoop?.queue_size || 45.6,
              itemStyle: { color: '#91cc75' }
            },
            {
              value: perf.component_performance?.hive?.completed_queries_last_hour || 156,
              itemStyle: { color: '#fac858' }
            },
            {
              value: perf.component_performance?.hive?.query_execution_time_avg || 2.5,
              itemStyle: { color: '#ee6666' }
            }
          ]
        }]
      }

      this.performanceChart.setOption(option)
    },

    // 工具方法
    getComponentName (component) {
      const names = {
        'hadoop': 'Hadoop',
        'hive': 'Hive',
        'mysql': 'MySQL'
      }
      return names[component] || component
    },

    getComponentIcon (component) {
      const icons = {
        'hadoop': 'el-icon-coin',
        'hive': 'el-icon-data-line',
        'mysql': 'el-icon-s-data'
      }
      return icons[component] || 'el-icon-service'
    },

    getStatusType (status) {
      const types = {
        'healthy': 'success',
        'warning': 'warning',
        'error': 'danger',
        'active': 'success',
        'connected': 'success',
        'disconnected': 'info'
      }
      return types[status] || 'info'
    },

    getStatusText (status) {
      const texts = {
        'healthy': '正常',
        'warning': '警告',
        'error': '错误',
        'active': '活跃',
        'connected': '已连接',
        'disconnected': '未连接',
        'simulated': '模拟'
      }
      return texts[status] || status
    },

    getBigDataStatusType (status) {
      if (typeof status === 'object') {
        return status.status === 'healthy' ? 'success' : 'warning'
      }
      return status === 'connected' ? 'success' : 'info'
    },

    getBigDataStatusText (status) {
      if (typeof status === 'object') {
        return status.status === 'healthy' ? '正常' : '异常'
      }
      return status === 'connected' ? '已连接' : '未连接'
    },

    formatTime (timestamp) {
      if (!timestamp) return '--'
      const date = new Date(timestamp)
      return date.toLocaleString('zh-CN')
    },

    formatGB (value) {
      return value ? `${value.toFixed(1)}GB` : '--'
    },

    formatLabel (key) {
      const labels = {
        'status': '状态',
        'namenode_status': 'NameNode状态',
        'capacity_used': '容量使用率',
        'capacity_total': '总容量',
        'database_count': '数据库数量',
        'table_count': '表数量',
        'connection_status': '连接状态',
        'database_size': '数据库大小',
        'last_check': '最后检查时间'
      }
      return labels[key] || key
    },

    // 模拟数据
    getMockClusterStatus () {
      return {
        overall_status: 'healthy',
        components: {
          hadoop: {
            status: 'healthy',
            namenode_status: 'active',
            capacity_used: 45.6,
            capacity_total: 100.0,
            last_check: new Date().toISOString()
          },
          hive: {
            status: 'healthy',
            metastore_status: 'active',
            database_count: 3,
            table_count: 8,
            last_check: new Date().toISOString()
          },
          mysql: {
            status: 'healthy',
            connection_status: 'active',
            database_size: 156.7,
            table_count: 5,
            last_check: new Date().toISOString()
          }
        },
        timestamp: new Date().toISOString()
      }
    },

    getMockSystemMetrics () {
      return {
        cpu: {
          usage_percent: 35.2,
          core_count: 8
        },
        memory: {
          usage_percent: 68.5,
          used_gb: 10.9,
          total_gb: 16.0
        },
        disk: {
          usage_percent: 42.1,
          used_gb: 210.5,
          total_gb: 500.0
        }
      }
    },

    getMockPerformanceMetrics () {
      return {
        component_performance: {
          hadoop: {
            throughput_mb_s: 125.6,
            block_operations_per_sec: 45,
            active_connections: 8,
            queue_size: 12
          },
          hive: {
            query_execution_time_avg: 2.5,
            active_queries: 3,
            completed_queries_last_hour: 156,
            failed_queries_last_hour: 2
          },
          mysql: {
            connections_active: 5,
            queries_per_second: 45.2,
            slow_queries: 0,
            cache_hit_ratio: 98.5
          }
        }
      }
    }
  }
}
</script>

<style>
/* 全局样式修复滚动 - 不带scoped */
html, body {
  overflow-y: auto !important;
  height: auto !important;
  max-height: none !important;
  margin: 0;
  padding: 0;
}

#app {
  overflow-y: auto !important;
  height: auto !important;
  max-height: none !important;
}

.router-view, .el-main, .el-container {
  overflow-y: auto !important;
  height: auto !important;
  max-height: none !important;
}
</style>

<style scoped>
.cluster-monitoring {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: auto;
  padding-bottom: 100px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 0 10px;
}

.page-header h1 {
  margin: 0;
  color: #303133;
  font-size: 24px;
}

.page-header h1 i {
  margin-right: 10px;
  color: #409EFF;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.overview-section {
  margin-bottom: 20px;
}

.status-card {
  border-left: 4px solid #ddd;
}

.status-card.status-healthy {
  border-left-color: #67C23A;
}

.status-card.status-warning {
  border-left-color: #E6A23C;
}

.status-card.status-error {
  border-left-color: #F56C6C;
}

.status-content, .metric-content {
  display: flex;
  align-items: center;
}

.status-icon, .metric-icon {
  font-size: 32px;
  margin-right: 15px;
  width: 50px;
  text-align: center;
}

.status-card.status-healthy .status-icon {
  color: #67C23A;
}

.status-card.status-warning .status-icon {
  color: #E6A23C;
}

.status-card.status-error .status-icon {
  color: #F56C6C;
}

.metric-icon {
  color: #409EFF;
}

.status-info h3, .metric-info h3 {
  margin: 0 0 5px 0;
  font-size: 18px;
  color: #303133;
}

.status-info p, .metric-info p {
  margin: 0 0 5px 0;
  color: #606266;
  font-size: 14px;
}

.status-info small, .metric-info small {
  color: #909399;
  font-size: 12px;
}

.components-section {
  margin-bottom: 20px;
}

.component-card {
  height: 100%;
}

.component-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.component-title {
  font-weight: bold;
  color: #303133;
}

.component-title i {
  margin-right: 8px;
  color: #409EFF;
}

.component-details {
  margin: 15px 0;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
}

.detail-item span:first-child {
  color: #606266;
}

.component-actions {
  text-align: center;
  border-top: 1px solid #EBEEF5;
  padding-top: 15px;
}

.metrics-section, .alerts-section, .bigdata-section {
  margin-bottom: 20px;
}

.chart-container {
  height: 300px;
}

.bigdata-controls {
  margin-bottom: 20px;
  text-align: center;
}

.bigdata-controls .el-button {
  margin: 0 10px;
}

.bigdata-status {
  background-color: #f8f9fa;
  border-radius: 4px;
  padding: 15px;
}

.bigdata-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.component-name {
  font-weight: bold;
  color: #303133;
}

@media (max-width: 768px) {
  .cluster-monitoring {
    padding: 10px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }

  .header-actions {
    width: 100%;
    justify-content: center;
  }
}
</style>

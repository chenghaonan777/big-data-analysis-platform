<template>
  <div class="dashboard">
    <!-- 头部导航区域 -->
    <div class="dashboard-header">
      <div class="header-bg">
        <!-- 左侧标题 -->
        <div class="header-left">
          <div class="logo-container">
            <div class="logo-icon">
              <i class="el-icon-data-analysis"></i>
            </div>
            <div class="logo-text">
              <h1 class="main-title">山西水泥公司电力大数据分析系统</h1>
              <p class="subtitle">Shanxi Cement Power Data Analysis System</p>
            </div>
          </div>
        </div>

        <!-- 右侧信息 -->
        <div class="header-right">
          <div class="header-stats">
            <div class="stat-item">
              <i class="el-icon-time"></i>
              <span class="current-time">{{ currentTime }}</span>
            </div>
            <div class="stat-item">
              <i class="el-icon-monitor"></i>
              <el-tag :type="systemStatusType" size="medium" class="status-tag">
                {{ systemStatusText }}
              </el-tag>
            </div>
            <el-button type="primary" icon="el-icon-monitor" @click="goToClusterMonitoring">
              集群监控
            </el-button>
            <el-button type="info" icon="el-icon-question" @click="$router.push('/about')">
              关于系统
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 连接状态提示 -->
    <transition name="slide-down">
      <div v-if="!backendConnected" class="connection-warning">
        <el-alert
          title="后端服务连接失败"
          type="warning"
          description="正在使用模拟数据展示，请检查后端服务是否启动"
          show-icon
          :closable="false"
          class="connection-alert">
          <template slot="title">
            <div class="alert-content">
              <span>后端服务连接失败</span>
              <el-button
                type="text"
                size="mini"
                @click="reconnectBackend"
                class="reconnect-btn">
                <i class="el-icon-refresh"></i>
                重新连接
              </el-button>
            </div>
          </template>
        </el-alert>
      </div>
    </transition>

    <!-- 主要内容区域 -->
    <div class="dashboard-content">
      <!-- 第一行：关键指标卡片 -->
      <div class="metrics-section">
        <div class="section-header">
          <h2 class="section-title">
            <i class="el-icon-data-board"></i>
            核心指标概览
          </h2>
          <div class="section-actions">
            <el-button size="mini" icon="el-icon-refresh" circle @click="refreshMetrics"></el-button>
          </div>
        </div>

        <div class="metrics-grid">
          <div class="metric-card" v-for="(metric) in keyMetrics" :key="metric.label">
            <div class="card-decoration" :style="{ background: metric.color }"></div>
            <div class="metric-header">
              <div class="metric-icon" :style="{ background: metric.color }">
                <i :class="metric.icon"></i>
              </div>
              <div class="metric-trend" :class="metric.trend">
                <i :class="metric.trendIcon"></i>
                <span>{{ metric.trendValue }}</span>
              </div>
            </div>
            <div class="metric-body">
              <div class="metric-value">{{ formatNumber(metric.value) }}</div>
              <div class="metric-info">
                <span class="metric-label">{{ metric.label }}</span>
                <span class="metric-unit">{{ metric.unit }}</span>
              </div>
            </div>
            <div class="metric-footer">
              <div class="progress-bar">
                <div class="progress-fill" :style="{
                  width: `${Math.min(100, (metric.value / (metric.value * 1.2)) * 100)}%`,
                  background: metric.color
                }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 第二行：主要图表分析 -->
      <div class="charts-section">
        <div class="section-header">
          <h2 class="section-title">
            <i class="el-icon-s-data"></i>
            数据分析可视化
          </h2>
        </div>

        <div class="charts-grid">
          <!-- 地域分析图表 -->
          <div class="chart-card regional-chart">
            <div class="chart-header">
              <div class="chart-title">
                <i class="el-icon-location"></i>
                <h3>地域电力消耗分布</h3>
              </div>
              <div class="chart-controls">
                <el-button-group size="mini">
                  <el-button type="primary" plain>日</el-button>
                  <el-button plain>月</el-button>
                  <el-button plain>年</el-button>
                </el-button-group>
              </div>
            </div>
            <div class="chart-content">
              <div class="chart-wrapper">
                <v-chart
                  v-if="!chartsLoading && regionalChartOptions.series"
                  class="chart"
                  :options="regionalChartOptions"
                  @click="handleChartClick"
                />
                <div v-else-if="chartsLoading" class="chart-loading">
                  <div class="loading-spinner">
                    <i class="el-icon-loading"></i>
                  </div>
                  <span>图表加载中...</span>
                </div>
                <div v-else class="chart-error">
                  <i class="el-icon-warning"></i>
                  <span>暂无数据</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 趋势分析图表 -->
          <div class="chart-card trend-chart">
            <div class="chart-header">
              <div class="chart-title">
                <i class="el-icon-trending-up"></i>
                <h3>电力消耗时间趋势</h3>
              </div>
              <div class="chart-controls">
                <el-switch
                  v-model="showForecast"
                  active-text="显示预测"
                  inactive-text="隐藏预测"
                  active-color="#67C23A"
                  @change="updateTrendChart">
                </el-switch>
              </div>
            </div>
            <div class="chart-content">
              <div class="chart-wrapper">
                <v-chart
                  v-if="!chartsLoading && trendChartOptions.series"
                  class="chart"
                  :options="trendChartOptions"
                />
                <div v-else-if="chartsLoading" class="chart-loading">
                  <div class="loading-spinner">
                    <i class="el-icon-loading"></i>
                  </div>
                  <span>图表加载中...</span>
                </div>
                <div v-else class="chart-error">
                  <i class="el-icon-warning"></i>
                  <span>暂无数据</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 第三行：详细分析 -->
      <div class="details-section">
        <div class="section-header">
          <h2 class="section-title">
            <i class="el-icon-menu"></i>
            详细数据分析
          </h2>
        </div>

        <div class="details-grid">
          <!-- 企业排名 -->
          <div class="detail-card ranking-card">
            <div class="card-header">
              <div class="header-content">
                <i class="el-icon-trophy"></i>
                <h3>企业电力消耗排名 TOP10</h3>
              </div>
              <div class="header-actions">
                <el-button size="mini" type="text" icon="el-icon-download">导出</el-button>
              </div>
            </div>
            <div class="card-content">
              <v-chart
                v-if="!chartsLoading && enterpriseChartOptions.series"
                class="chart"
                :options="enterpriseChartOptions"
              />
              <div v-else-if="chartsLoading" class="chart-loading">
                <div class="loading-spinner">
                  <i class="el-icon-loading"></i>
                </div>
                <span>图表加载中...</span>
              </div>
              <div v-else class="chart-error">
                <i class="el-icon-warning"></i>
                <span>暂无数据</span>
              </div>
            </div>
          </div>

          <!-- 实时监控 -->
          <div class="detail-card realtime-card">
            <div class="card-header">
              <div class="header-content">
                <i class="el-icon-view"></i>
                <h3>实时监控数据</h3>
              </div>
              <div class="header-actions">
                <div class="refresh-indicator" :class="{ active: isRefreshing }">
                  <i class="el-icon-refresh"></i>
                </div>
              </div>
            </div>
            <div class="card-content">
              <div class="realtime-data">
                <div class="data-item" v-for="(item) in realtimeData" :key="item.name">
                  <div class="data-header">
                    <div class="data-icon" :style="{ background: item.color }">
                      <i class="el-icon-data-line"></i>
                    </div>
                    <div class="data-info">
                      <div class="data-name">{{ item.name }}</div>
                      <div class="data-value" :style="{ color: item.color }">
                        {{ item.value }}
                        <span class="data-unit">{{ item.unit }}</span>
                      </div>
                    </div>
                  </div>
                  <div class="data-progress">
                    <el-progress
                      :percentage="item.percentage"
                      :color="item.color"
                      :show-text="false"
                      :stroke-width="8">
                    </el-progress>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 地图可视化 -->
          <div class="detail-card map-card">
            <div class="card-header">
              <div class="header-content">
                <i class="el-icon-map-location"></i>
                <h3>山西省电力消耗分布</h3>
              </div>
              <div class="header-actions">
                <el-button size="mini" type="text" icon="el-icon-full-screen">全屏</el-button>
              </div>
            </div>
            <div class="card-content">
              <v-chart
                v-if="!chartsLoading && mapChartOptions.series"
                class="chart map-chart"
                :options="mapChartOptions"
              />
              <div v-else-if="chartsLoading" class="chart-loading">
                <div class="loading-spinner">
                  <i class="el-icon-loading"></i>
                </div>
                <span>图表加载中...</span>
              </div>
              <div v-else class="chart-error">
                <i class="el-icon-warning"></i>
                <span>暂无数据</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 数据更新提示 -->
    <transition name="fade">
      <div class="update-indicator" v-show="dataUpdating">
        <div class="update-content">
          <div class="update-spinner">
            <i class="el-icon-loading"></i>
          </div>
          <span>数据更新中...</span>
        </div>
      </div>
    </transition>

    <!-- 浮动操作按钮 -->
    <div class="floating-actions">
      <el-tooltip content="刷新数据" placement="left">
        <el-button
          type="primary"
          icon="el-icon-refresh"
          circle
          size="medium"
          @click="refreshAllData"
          class="float-btn refresh-btn">
        </el-button>
      </el-tooltip>
      <el-tooltip content="系统设置" placement="left">
        <el-button
          type="info"
          icon="el-icon-setting"
          circle
          size="medium"
          class="float-btn setting-btn">
        </el-button>
      </el-tooltip>
    </div>
  </div>
</template>

<script>
import { analysisAPI, systemAPI } from '@/api/request'

export default {
  name: 'DataDashboard',

  data () {
    return {
      currentTime: '',
      backendConnected: false,
      systemStatus: {
        status: 'unknown',
        data_loaded: false,
        data_cleaned: false,
        storage_initialized: false
      },
      keyMetrics: [
        {
          label: '总电力消耗',
          value: 1250000,
          unit: 'kWh',
          icon: 'el-icon-lightning',
          color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          trend: 'up',
          trendIcon: 'el-icon-arrow-up',
          trendValue: '+5.2%'
        },
        {
          label: '企业总数',
          value: 85,
          unit: '家',
          icon: 'el-icon-office-building',
          color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
          trend: 'up',
          trendIcon: 'el-icon-arrow-up',
          trendValue: '+2.1%'
        },
        {
          label: '覆盖地区',
          value: 8,
          unit: '个',
          icon: 'el-icon-map-location',
          color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
          trend: 'stable',
          trendIcon: 'el-icon-minus',
          trendValue: '0.0%'
        },
        {
          label: '平均消耗',
          value: 14705,
          unit: 'kWh',
          icon: 'el-icon-data-line',
          color: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
          trend: 'down',
          trendIcon: 'el-icon-arrow-down',
          trendValue: '-1.8%'
        }
      ],
      regionalData: [],
      temporalData: [],
      enterpriseData: [],
      realtimeData: [
        {
          name: '当前负荷',
          value: '1,234',
          unit: 'MW',
          percentage: 75,
          color: '#409EFF'
        },
        {
          name: '峰值负荷',
          value: '1,580',
          unit: 'MW',
          percentage: 95,
          color: '#E6A23C'
        },
        {
          name: '用电效率',
          value: '87.5',
          unit: '%',
          percentage: 87,
          color: '#67C23A'
        },
        {
          name: '异常警报',
          value: '3',
          unit: '个',
          percentage: 15,
          color: '#F56C6C'
        },
        {
          name: '节能率',
          value: '12.3',
          unit: '%',
          percentage: 65,
          color: '#909399'
        }
      ],
      chartsLoading: false,
      dataUpdating: false,
      isRefreshing: false,
      showForecast: true,
      regionalChartOptions: {},
      trendChartOptions: {},
      enterpriseChartOptions: {},
      mapChartOptions: {},
      timeTimer: null,
      dataTimer: null
    }
  },

  computed: {
    systemStatusType () {
      if (!this.backendConnected) return 'warning'
      return this.systemStatus.status === 'running' ? 'success' : 'danger'
    },

    systemStatusText () {
      if (!this.backendConnected) return '后端连接失败'
      return this.systemStatus.status === 'running' ? '系统运行正常' : '系统异常'
    }
  },

  created () {
    this.initializeDashboard()
    this.startTimeUpdate()
    this.startDataPolling()
  },

  destroyed () {
    if (this.timeTimer) clearInterval(this.timeTimer)
    if (this.dataTimer) clearInterval(this.dataTimer)
  },

  methods: {
    async initializeDashboard () {
      this.chartsLoading = true
      try {
        // 先使用模拟数据
        this.loadMockData()

        // 尝试连接后端
        await Promise.all([
          this.loadSystemStatus(),
          this.loadBasicStats(),
          this.loadRegionalData(),
          this.loadTemporalData(),
          this.loadEnterpriseData()
        ])

        this.backendConnected = true
        this.updateAllCharts()
      } catch (error) {
        console.error('初始化仪表板失败:', error)
        this.backendConnected = false
        // 使用模拟数据
        this.loadMockData()
        this.updateAllCharts()
        this.$message.warning('后端服务连接失败，正在使用模拟数据展示')
      } finally {
        this.chartsLoading = false
      }
    },

    loadMockData () {
      // 模拟地域数据
      this.regionalData = [
        {
          region: '太原市',
          total_consumption: 125000,
          record_count: 15,
          average_consumption: 8333.33
        },
        {
          region: '大同市',
          total_consumption: 98000,
          record_count: 12,
          average_consumption: 8166.67
        },
        {
          region: '阳泉市',
          total_consumption: 87000,
          record_count: 10,
          average_consumption: 8700.00
        },
        {
          region: '长治市',
          total_consumption: 156000,
          record_count: 18,
          average_consumption: 8666.67
        },
        {
          region: '晋城市',
          total_consumption: 134000,
          record_count: 16,
          average_consumption: 8375.00
        },
        {
          region: '朔州市',
          total_consumption: 76000,
          record_count: 8,
          average_consumption: 9500.00
        },
        {
          region: '晋中市',
          total_consumption: 143000,
          record_count: 17,
          average_consumption: 8411.76
        },
        {
          region: '运城市',
          total_consumption: 189000,
          record_count: 22,
          average_consumption: 8590.91
        }
      ]

      // 模拟时间数据
      this.temporalData = [
        {
          month: '2023-01',
          power_consumption: 85000,
          enterprise_count: 45
        },
        {
          month: '2023-02',
          power_consumption: 92000,
          enterprise_count: 48
        },
        {
          month: '2023-03',
          power_consumption: 88000,
          enterprise_count: 46
        },
        {
          month: '2023-04',
          power_consumption: 94000,
          enterprise_count: 50
        },
        {
          month: '2023-05',
          power_consumption: 96000,
          enterprise_count: 52
        },
        {
          month: '2023-06',
          power_consumption: 103000,
          enterprise_count: 55
        },
        {
          month: '2023-07',
          power_consumption: 108000,
          enterprise_count: 58
        },
        {
          month: '2023-08',
          power_consumption: 105000,
          enterprise_count: 56
        },
        {
          month: '2023-09',
          power_consumption: 98000,
          enterprise_count: 53
        },
        {
          month: '2023-10',
          power_consumption: 91000,
          enterprise_count: 49
        },
        {
          month: '2023-11',
          power_consumption: 87000,
          enterprise_count: 47
        },
        {
          month: '2023-12',
          power_consumption: 89000,
          enterprise_count: 48
        }
      ]

      // 模拟企业数据
      this.enterpriseData = [
        {
          enterprise_name: '山西建投水泥有限公司',
          total_consumption: 45000,
          region: '太原市',
          rank: 1
        },
        {
          enterprise_name: '华润水泥(大同)有限公司',
          total_consumption: 42000,
          region: '大同市',
          rank: 2
        },
        {
          enterprise_name: '海螺水泥(长治)有限公司',
          total_consumption: 38000,
          region: '长治市',
          rank: 3
        },
        {
          enterprise_name: '同煤集团水泥有限公司',
          total_consumption: 35000,
          region: '大同市',
          rank: 4
        },
        {
          enterprise_name: '晋城水泥股份有限公司',
          total_consumption: 33000,
          region: '晋城市',
          rank: 5
        },
        {
          enterprise_name: '运城海天水泥有限公司',
          total_consumption: 31000,
          region: '运城市',
          rank: 6
        },
        {
          enterprise_name: '阳泉华新水泥有限公司',
          total_consumption: 29000,
          region: '阳泉市',
          rank: 7
        },
        {
          enterprise_name: '朔州金圆水泥有限公司',
          total_consumption: 27000,
          region: '朔州市',
          rank: 8
        },
        {
          enterprise_name: '晋中亚美水泥有限公司',
          total_consumption: 25000,
          region: '晋中市',
          rank: 9
        },
        {
          enterprise_name: '临汾尧都水泥有限公司',
          total_consumption: 23000,
          region: '临汾市',
          rank: 10
        }
      ]
    },

    async loadSystemStatus () {
      try {
        const status = await systemAPI.getStatus()
        this.systemStatus = status
      } catch (error) {
        console.error('获取系统状态失败:', error)
        throw error
      }
    },

    async loadBasicStats () {
      try {
        const stats = await analysisAPI.getBasicStats()
        this.updateKeyMetrics(stats)
      } catch (error) {
        console.error('获取基础统计失败:', error)
        throw error
      }
    },

    async loadRegionalData () {
      try {
        const data = await analysisAPI.getRegionalData()
        this.regionalData = data
      } catch (error) {
        console.error('获取地域数据失败:', error)
        throw error
      }
    },

    async loadTemporalData () {
      try {
        const data = await analysisAPI.getTemporalData()
        this.temporalData = data
      } catch (error) {
        console.error('获取时间数据失败:', error)
        throw error
      }
    },

    async loadEnterpriseData () {
      try {
        const data = await analysisAPI.getEnterpriseRanking()
        this.enterpriseData = data
      } catch (error) {
        console.error('获取企业数据失败:', error)
        throw error
      }
    },

    updateKeyMetrics (stats) {
      if (stats) {
        this.keyMetrics[0].value = stats.total_consumption || this.keyMetrics[0].value
        this.keyMetrics[1].value = stats.unique_enterprises || this.keyMetrics[1].value
        this.keyMetrics[2].value = stats.unique_regions || this.keyMetrics[2].value
        this.keyMetrics[3].value = stats.average_consumption || this.keyMetrics[3].value
      }
    },

    updateAllCharts () {
      this.updateRegionalChart()
      this.updateTrendChart()
      this.updateEnterpriseChart()
      this.updateMapChart()
    },

    updateRegionalChart () {
      if (!this.regionalData.length) return

      const regions = this.regionalData.map(item => item.region)
      const consumptions = this.regionalData.map(item => item.total_consumption)

      this.regionalChartOptions = {
        backgroundColor: 'transparent',
        title: {
          show: false
        },
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          borderColor: '#409EFF',
          textStyle: {
            color: '#fff',
            fontSize: 14
          },
          formatter: function (params) {
            const data = params[0]
            return `
              <div style="padding: 8px;">
                <div style="color: #409EFF; font-weight: bold;">${data.name}</div>
                <div style="margin-top: 5px;">
                  <span style="display: inline-block; width: 10px; height: 10px; background: ${data.color}; border-radius: 50%; margin-right: 5px;"></span>
                  电力消耗: ${data.value.toLocaleString()} kWh
                </div>
              </div>
            `
          }
        },
        grid: {
          left: 80,
          right: 40,
          top: 40,
          bottom: 80
        },
        xAxis: {
          type: 'category',
          data: regions,
          axisLine: {
            lineStyle: { color: '#4a5568' }
          },
          axisLabel: {
            color: '#cbd5e0',
            fontSize: 12,
            rotate: 45,
            interval: 0
          }
        },
        yAxis: {
          type: 'value',
          name: '电力消耗 (kWh)',
          nameTextStyle: {
            color: '#cbd5e0',
            fontSize: 12
          },
          axisLine: {
            lineStyle: { color: '#4a5568' }
          },
          axisLabel: {
            color: '#cbd5e0',
            fontSize: 12,
            formatter: function (value) {
              return (value / 1000).toFixed(0) + 'K'
            }
          },
          splitLine: {
            lineStyle: {
              color: '#2d3748',
              type: 'dashed'
            }
          },
          min: function (value) {
            return Math.max(0, value.min * 0.9)
          },
          max: function (value) {
            return value.max * 1.1
          }
        },
        series: [{
          data: consumptions.map((value) => ({
            value,
            itemStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  {
                    offset: 0,
                    color: '#667eea'
                  },
                  {
                    offset: 1,
                    color: '#764ba2'
                  }
                ]
              }
            }
          })),
          type: 'bar',
          barWidth: '60%',
          emphasis: {
            itemStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  {
                    offset: 0,
                    color: '#7c8de6'
                  },
                  {
                    offset: 1,
                    color: '#8a5ca8'
                  }
                ]
              }
            }
          }
        }]
      }
    },

    updateTrendChart () {
      if (!this.temporalData.length) return

      const months = this.temporalData.map(item => item.month)
      const consumptions = this.temporalData.map(item => item.power_consumption)

      // 生成预测数据
      const forecastData = []
      if (this.showForecast && consumptions.length > 0) {
        const lastValue = consumptions[consumptions.length - 1]
        for (let i = 1; i <= 3; i++) {
          forecastData.push(lastValue * (1 + (Math.random() - 0.5) * 0.1))
        }
      }

      this.trendChartOptions = {
        backgroundColor: 'transparent',
        title: {
          show: false
        },
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          borderColor: '#67C23A',
          textStyle: {
            color: '#fff',
            fontSize: 14
          }
        },
        legend: {
          data: this.showForecast ? ['实际消耗', '预测消耗'] : ['实际消耗'],
          textStyle: {
            color: '#cbd5e0'
          },
          top: 15,
          right: 30
        },
        grid: {
          left: 80,
          right: 40,
          top: 60,
          bottom: 80
        },
        xAxis: {
          type: 'category',
          data: this.showForecast
            ? [...months, ...['2024-01', '2024-02', '2024-03']]
            : months,
          axisLine: {
            lineStyle: { color: '#4a5568' }
          },
          axisLabel: {
            color: '#cbd5e0',
            fontSize: 12,
            rotate: 45,
            interval: 0
          }
        },
        yAxis: {
          type: 'value',
          name: '电力消耗 (kWh)',
          nameTextStyle: {
            color: '#cbd5e0',
            fontSize: 12
          },
          axisLine: {
            lineStyle: { color: '#4a5568' }
          },
          axisLabel: {
            color: '#cbd5e0',
            fontSize: 12,
            formatter: function (value) {
              return (value / 1000).toFixed(0) + 'K'
            }
          },
          splitLine: {
            lineStyle: {
              color: '#2d3748',
              type: 'dashed'
            }
          },
          min: function (value) {
            return Math.max(0, value.min * 0.9)
          },
          max: function (value) {
            return value.max * 1.1
          }
        },
        series: [
          {
            name: '实际消耗',
            data: this.showForecast
              ? [...consumptions, ...new Array(3).fill(null)]
              : consumptions,
            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: {
              color: '#67C23A',
              width: 3
            },
            itemStyle: {
              color: '#67C23A'
            },
            areaStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  {
                    offset: 0,
                    color: 'rgba(103, 194, 58, 0.3)'
                  },
                  {
                    offset: 1,
                    color: 'rgba(103, 194, 58, 0.1)'
                  }
                ]
              }
            }
          },
          ...(this.showForecast
            ? [{
              name: '预测消耗',
              data: [...new Array(consumptions.length).fill(null), ...forecastData],
              type: 'line',
              smooth: true,
              symbol: 'circle',
              symbolSize: 6,
              lineStyle: {
                color: '#E6A23C',
                width: 3,
                type: 'dashed'
              },
              itemStyle: {
                color: '#E6A23C'
              }
            }]
            : [])
        ]
      }
    },

    updateEnterpriseChart () {
      if (!this.enterpriseData.length) return

      const top10 = this.enterpriseData.slice(0, 10)
      const names = top10.map(item => item.enterprise_name || item.region)
      const values = top10.map(item => item.total_consumption || item.record_count)

      this.enterpriseChartOptions = {
        backgroundColor: 'transparent',
        title: {
          show: false
        },
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          borderColor: '#F56C6C',
          textStyle: {
            color: '#fff',
            fontSize: 14
          }
        },
        grid: {
          left: 160,
          right: 40,
          top: 30,
          bottom: 40
        },
        xAxis: {
          type: 'value',
          axisLine: {
            lineStyle: { color: '#4a5568' }
          },
          axisLabel: {
            color: '#cbd5e0',
            fontSize: 12
          },
          splitLine: {
            lineStyle: {
              color: '#2d3748',
              type: 'dashed'
            }
          }
        },
        yAxis: {
          type: 'category',
          data: names,
          axisLine: {
            lineStyle: { color: '#4a5568' }
          },
          axisLabel: {
            color: '#cbd5e0',
            fontSize: 10,
            formatter: function (value) {
              return value.length > 12 ? value.substring(0, 12) + '...' : value
            }
          }
        },
        series: [{
          data: values.map((value) => ({
            value,
            itemStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 1,
                y2: 0,
                colorStops: [
                  {
                    offset: 0,
                    color: '#f093fb'
                  },
                  {
                    offset: 1,
                    color: '#f5576c'
                  }
                ]
              }
            }
          })),
          type: 'bar',
          barWidth: '60%'
        }]
      }
    },

    updateMapChart () {
      this.mapChartOptions = {
        backgroundColor: 'transparent',
        title: {
          show: false
        },
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          borderColor: '#4facfe',
          textStyle: {
            color: '#fff',
            fontSize: 14
          }
        },
        series: [{
          type: 'pie',
          radius: ['30%', '70%'],
          center: ['50%', '50%'],
          data: this.regionalData.map((item, index) => ({
            value: item.total_consumption,
            name: item.region,
            itemStyle: {
              color: [
                '#667eea', '#764ba2', '#f093fb', '#f5576c',
                '#4facfe', '#00f2fe', '#43e97b', '#38f9d7'
              ][index % 8]
            }
          })),
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          },
          label: {
            color: '#cbd5e0',
            fontSize: 12
          },
          labelLine: {
            lineStyle: {
              color: '#cbd5e0'
            }
          }
        }]
      }
    },

    formatNumber (num) {
      if (!num && num !== 0) return '0'
      return Number(num).toLocaleString()
    },

    startTimeUpdate () {
      this.updateTime()
      this.timeTimer = setInterval(this.updateTime, 1000)
    },

    updateTime () {
      const now = new Date()
      this.currentTime = now.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    },

    startDataPolling () {
      this.dataTimer = setInterval(async () => {
        if (this.backendConnected) {
          this.isRefreshing = true
          try {
            await this.loadSystemStatus()
            this.updateRealtimeData()
          } catch (error) {
            console.error('数据轮询失败:', error)
            this.backendConnected = false
          } finally {
            setTimeout(() => {
              this.isRefreshing = false
            }, 1000)
          }
        }
      }, 30000)
    },

    updateRealtimeData () {
      this.realtimeData.forEach(item => {
        const change = (Math.random() - 0.5) * 10
        const newValue = Math.max(0, parseInt(item.value.replace(/,/g, '')) + change)
        item.value = newValue.toLocaleString()
        item.percentage = Math.min(100, Math.max(0, item.percentage + (Math.random() - 0.5) * 5))
      })
    },

    handleChartClick (params) {
      this.$message.info(`点击了: ${params.name} - ${params.value}`)
    },

    // 新增美化方法
    async reconnectBackend () {
      this.$message.info('正在尝试重新连接...')
      try {
        await this.initializeDashboard()
        this.$message.success('重连成功')
      } catch (error) {
        this.$message.error('重连失败')
      }
    },

    refreshMetrics () {
      this.loadBasicStats()
      this.$message.success('指标数据已刷新')
    },

    refreshAllData () {
      this.dataUpdating = true
      setTimeout(() => {
        this.initializeDashboard()
        this.dataUpdating = false
        this.$message.success('所有数据已刷新')
      }, 2000)
    },

    // 新增导航方法
    goToClusterMonitoring() {
      this.$router.push('/cluster')
    }
  }
}
</script>

<style lang="scss" scoped>
// 导入变量
@import "@/styles/variables.scss";

// 全局动画定义
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

@keyframes slideInUp {
  from {
    transform: translateY(30px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes glow {
  0%, 100% {
    box-shadow: 0 0 5px rgba(64, 158, 255, 0.5);
  }
  50% {
    box-shadow: 0 0 20px rgba(64, 158, 255, 0.8);
  }
}

// 主容器
.dashboard {
  height: 100vh;
  background: linear-gradient(135deg,
    #0c1e35 0%,
    #1a365d 25%,
    #2d3748 50%,
    #1a202c 75%,
    #0d1117 100%);
  overflow: hidden;
  position: relative;

  // 添加背景粒子效果
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.15) 0%, transparent 50%),
    radial-gradient(circle at 40% 40%, rgba(120, 219, 255, 0.1) 0%, transparent 50%);
    pointer-events: none;
    z-index: 1;
  }
}

// 页面过渡动画
.slide-down-enter-active, .slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter, .slide-down-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}

.fade-enter-active, .fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter, .fade-leave-to {
  opacity: 0;
}

// 头部导航区域
.dashboard-header {
  height: 90px;
  position: relative;
  z-index: 10;

  .header-bg {
    height: 100%;
    background: linear-gradient(135deg,
      rgba(64, 158, 255, 0.15) 0%,
      rgba(103, 194, 58, 0.1) 50%,
      rgba(255, 99, 132, 0.05) 100%);
    border-bottom: 2px solid rgba(64, 158, 255, 0.3);
    backdrop-filter: blur(20px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 40px;
    position: relative;

    &::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 1px;
      background: linear-gradient(90deg,
        transparent 0%,
        rgba(64, 158, 255, 0.5) 50%,
        transparent 100%);
    }
  }

  .header-left {
    .logo-container {
      display: flex;
      align-items: center;
      gap: 20px;

      .logo-icon {
        width: 60px;
        height: 60px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        animation: float 3s ease-in-out infinite;

        i {
          font-size: 28px;
          color: white;
        }
      }

      .logo-text {
        .main-title {
          color: #ffffff;
          font-size: 28px;
          font-weight: 700;
          margin: 0 0 5px 0;
          text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.5);
          letter-spacing: 1px;
        }

        .subtitle {
          color: #cbd5e0;
          font-size: 12px;
          margin: 0;
          opacity: 0.8;
          font-weight: 300;
          letter-spacing: 0.5px;
        }
      }
    }
  }

  .header-right {
    .header-stats {
      display: flex;
      align-items: center;
      gap: 30px;

      .stat-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 15px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;

        &:hover {
          background: rgba(255, 255, 255, 0.1);
          transform: translateY(-2px);
        }

        i {
          color: #409EFF;
          font-size: 16px;
        }

        .current-time {
          color: #ffffff;
          font-size: 16px;
          font-weight: 500;
          font-family: 'Consolas', monospace;
        }

        .status-tag {
          font-size: 12px;
          padding: 6px 12px;
          border-radius: 15px;
          font-weight: 500;
        }
      }
    }
  }
}


// 连接警告
.connection-warning {
  padding: 15px 20px;
  position: relative;
  z-index: 10;

  .connection-alert {
    border-radius: 12px;
    border: none;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);

    .alert-content {
      display: flex;
      align-items: center;
      gap: 15px;

      .reconnect-btn {
        color: #E6A23C;
        font-weight: 500;

        &:hover {
          color: #F56C6C;
        }

        i {
          margin-right: 5px;
        }
      }
    }
  }
}

// 主要内容区域
.dashboard-content {
  height: calc(100vh - 90px);
  padding: 25px;
  display: flex;
  flex-direction: column;
  gap: 25px;
  overflow-y: auto;
  position: relative;
  z-index: 5;

  // 自定义滚动条
  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #667eea, #764ba2);
    border-radius: 4px;
    box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.2);

    &:hover {
      background: linear-gradient(180deg, #7c8de6, #8a5ca8);
    }
  }
}

// 通用区域样式
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  .section-title {
    color: #ffffff;
    font-size: 20px;
    font-weight: 600;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 12px;

    i {
      color: #409EFF;
      font-size: 22px;
    }
  }

  .section-actions {
    .el-button {
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(64, 158, 255, 0.3);
      color: #409EFF;

      &:hover {
        background: rgba(64, 158, 255, 0.2);
        border-color: #409EFF;
      }
    }
  }
}

// 指标区域
.metrics-section {
  animation: slideInUp 0.6s ease-out;

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 25px;
  }

  .metric-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(25px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    padding: 25px;
    position: relative;
    overflow: hidden;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    min-height: 160px;

    &:hover {
      transform: translateY(-8px) scale(1.02);
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
      border-color: rgba(64, 158, 255, 0.4);
      background: rgba(255, 255, 255, 0.08);
    }

    .card-decoration {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 4px;
      border-radius: 20px 20px 0 0;
    }

    .metric-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;

      .metric-icon {
        width: 55px;
        height: 55px;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);

        i {
          font-size: 26px;
          color: white;
        }
      }

      .metric-trend {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 14px;
        font-weight: 600;
        padding: 6px 12px;
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.1);

        &.up {
          color: #67C23A;
          background: rgba(103, 194, 58, 0.15);
        }

        &.down {
          color: #F56C6C;
          background: rgba(245, 108, 108, 0.15);
        }

        &.stable {
          color: #E6A23C;
          background: rgba(230, 162, 60, 0.15);
        }
      }
    }

    .metric-body {
      margin-bottom: 15px;

      .metric-value {
        font-size: 36px;
        font-weight: 800;
        color: #ffffff;
        line-height: 1.2;
        margin-bottom: 8px;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
      }

      .metric-info {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .metric-label {
          font-size: 14px;
          color: #cbd5e0;
          font-weight: 500;
        }

        .metric-unit {
          font-size: 12px;
          color: #a0aec0;
          font-weight: 400;
        }
      }
    }

    .metric-footer {
      .progress-bar {
        height: 6px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 3px;
        overflow: hidden;

        .progress-fill {
          height: 100%;
          border-radius: 3px;
          transition: width 1s ease;
        }
      }
    }
  }
}

// 图表区域
.charts-section {
  animation: slideInUp 0.8s ease-out;

  .charts-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 25px;
    height: 480px;
  }

  .chart-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(25px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    overflow: hidden;
    transition: all 0.3s ease;
    position: relative;

    &:hover {
      border-color: rgba(64, 158, 255, 0.4);
      box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
      transform: translateY(-3px);
    }

    .chart-header {
      padding: 25px 30px 20px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(255, 255, 255, 0.02);

      .chart-title {
        display: flex;
        align-items: center;
        gap: 12px;

        i {
          color: #409EFF;
          font-size: 18px;
        }

        h3 {
          margin: 0;
          color: #ffffff;
          font-size: 16px;
          font-weight: 600;
        }
      }

      .chart-controls {
        .el-button-group .el-button {
          padding: 6px 15px;
          font-size: 12px;
          border-radius: 6px;
        }

        .el-switch {
          .el-switch__label {
            color: #cbd5e0;
            font-size: 12px;
            font-weight: 500;
          }
        }
      }
    }

    .chart-content {
      height: calc(100% - 85px);
      padding: 20px;

      .chart-wrapper {
        height: 100%;
        position: relative;
      }

      .chart {
        width: 100%;
        height: 100%;
      }
    }
  }
}

// 详细分析区域
.details-section {
  animation: slideInUp 1s ease-out;

  .details-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 25px;
    height: 420px;
  }

  .detail-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(25px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    overflow: hidden;
    transition: all 0.3s ease;

    &:hover {
      border-color: rgba(64, 158, 255, 0.4);
      box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
      transform: translateY(-3px);
    }

    .card-header {
      padding: 20px 25px 15px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(255, 255, 255, 0.02);

      .header-content {
        display: flex;
        align-items: center;
        gap: 10px;

        i {
          color: #409EFF;
          font-size: 16px;
        }

        h3 {
          margin: 0;
          color: #ffffff;
          font-size: 14px;
          font-weight: 600;
        }
      }

      .header-actions {
        .el-button {
          color: #cbd5e0;
          font-size: 12px;

          &:hover {
            color: #409EFF;
          }
        }

        .refresh-indicator {
          color: #cbd5e0;
          transition: all 0.3s ease;

          &.active {
            color: #409EFF;
            animation: spin 1s linear infinite;
          }

          i {
            font-size: 16px;
          }
        }
      }
    }

    .card-content {
      height: calc(100% - 70px);
      padding: 20px;

      .chart {
        width: 100%;
        height: 100%;
      }
    }
  }

  // 实时数据特殊样式
  .realtime-card {
    .realtime-data {
      height: 100%;
      overflow-y: auto;
      padding: 5px;

      .data-item {
        padding: 15px 18px;
        margin-bottom: 15px;
        background: linear-gradient(135deg,
          rgba(255, 255, 255, 0.08) 0%,
          rgba(255, 255, 255, 0.03) 100%);
        border-radius: 12px;
        border-left: 4px solid #409EFF;
        transition: all 0.3s ease;
        position: relative;

        &:hover {
          background: linear-gradient(135deg,
            rgba(255, 255, 255, 0.12) 0%,
            rgba(255, 255, 255, 0.06) 100%);
          transform: translateX(8px);
          box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
        }

        .data-header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 12px;

          .data-icon {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;

            i {
              color: white;
              font-size: 14px;
            }
          }

          .data-info {
            flex: 1;

            .data-name {
              font-size: 13px;
              color: #cbd5e0;
              margin-bottom: 4px;
              font-weight: 500;
            }

            .data-value {
              font-size: 20px;
              font-weight: 700;
              display: flex;
              align-items: baseline;
              gap: 4px;

              .data-unit {
                font-size: 12px;
                font-weight: 400;
                opacity: 0.8;
              }
            }
          }
        }

        .data-progress {
          .el-progress {
            .el-progress-bar__outer {
              background-color: rgba(255, 255, 255, 0.1);
              border-radius: 4px;
            }
          }
        }
      }
    }
  }
}

// 加载和错误状态
.chart-loading, .chart-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #cbd5e0;
  font-size: 14px;

  .loading-spinner {
    margin-bottom: 15px;

    i {
      font-size: 32px;
      color: #409EFF;
      animation: spin 1s linear infinite;
    }
  }

  i {
    font-size: 32px;
    margin-bottom: 15px;
    opacity: 0.6;
  }
}

// 更新指示器
.update-indicator {
  position: fixed;
  top: 120px;
  right: 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 15px 25px;
  border-radius: 30px;
  font-size: 14px;
  backdrop-filter: blur(15px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
  z-index: 1000;
  animation: pulse 2s infinite;

  .update-content {
    display: flex;
    align-items: center;
    gap: 12px;

    .update-spinner i {
      animation: spin 1s linear infinite;
      font-size: 16px;
    }
  }
}

// 浮动操作按钮
.floating-actions {
  position: fixed;
  bottom: 30px;
  right: 30px;
  display: flex;
  flex-direction: column;
  gap: 15px;
  z-index: 1000;

  .float-btn {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

    &:hover {
      transform: translateY(-3px) scale(1.1);
    }

    &.refresh-btn {
      background: linear-gradient(135deg, #67C23A 0%, #85ce61 100%);
      border: none;

      &:hover {
        background: linear-gradient(135deg, #85ce61 0%, #67C23A 100%);
        box-shadow: 0 12px 30px rgba(103, 194, 58, 0.4);
        animation: glow 1s infinite alternate;
      }
    }

    &.setting-btn {
      background: linear-gradient(135deg, #909399 0%, #b4b7c1 100%);
      border: none;

      &:hover {
        background: linear-gradient(135deg, #b4b7c1 0%, #909399 100%);
        box-shadow: 0 12px 30px rgba(144, 147, 153, 0.4);
      }
    }

    i {
      font-size: 20px;
      color: white;
    }
  }
}

// 响应式设计
@media (max-width: 1400px) {
  .metrics-section .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
  }

  .details-section .details-grid {
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }
}

@media (max-width: 1024px) {
  .dashboard-header .header-bg {
    padding: 0 20px;

    .header-left .logo-container .logo-text .main-title {
      font-size: 24px;
    }
  }

  .dashboard-content {
    padding: 20px;
    gap: 20px;
  }

  .charts-section .charts-grid {
    grid-template-columns: 1fr;
    height: auto;
  }

  .charts-section .chart-card {
    height: 400px;
    min-height: 400px;
  }

  .details-section .details-grid {
    grid-template-columns: 1fr;
    height: auto;
  }

  .details-section .detail-card {
    height: 350px;
    min-height: 350px;
  }

  .floating-actions {
    bottom: 20px;
    right: 20px;
  }
}

@media (max-width: 768px) {
  .metrics-section .metrics-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }

  .dashboard-content {
    padding: 15px;
    gap: 15px;
  }

  .dashboard-header {
    height: auto;
    min-height: 70px;

    .header-bg {
      flex-direction: column;
      padding: 15px 20px;
      gap: 10px;

      .header-left .logo-container {
        gap: 15px;

        .logo-icon {
          width: 45px;
          height: 45px;

          i {
            font-size: 22px;
          }
        }

        .logo-text .main-title {
          font-size: 20px;
        }
      }

      .header-right .header-stats {
        gap: 15px;

        .stat-item {
          padding: 8px 12px;

          .current-time {
            font-size: 14px;
          }
        }
      }
    }
  }

  .dashboard-content {
    height: calc(100vh - 110px);
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;

    .section-title {
      font-size: 18px;
    }
  }

  .floating-actions {
    bottom: 15px;
    right: 15px;
    gap: 10px;

    .float-btn {
      width: 48px;
      height: 48px;

      i {
        font-size: 18px;
      }
    }
  }
}

@media (max-width: 480px) {
  .dashboard-header .header-bg .header-left .logo-container {
    flex-direction: column;
    align-items: center;
    gap: 10px;
    text-align: center;
  }

  .dashboard-content {
    padding: 10px;
    gap: 10px;
  }

  .metric-card {
    padding: 20px;
    min-height: 140px;
  }

  .chart-card .chart-header {
    padding: 20px 15px 15px;
  }

  .detail-card .card-header {
    padding: 15px 20px 10px;
  }
}

// 自定义滚动条样式增强
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 4px;
  box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.2);

  &:hover {
    background: linear-gradient(135deg, #7c8de6, #8a5ca8);
  }
}

::-webkit-scrollbar-corner {
  background: rgba(255, 255, 255, 0.05);
}

// Element UI 组件样式覆盖
.el-alert {
  border-radius: 12px;
  border: none;

  &.el-alert--warning {
    background: linear-gradient(135deg,
      rgba(230, 162, 60, 0.15) 0%,
      rgba(230, 162, 60, 0.05) 100%);
    backdrop-filter: blur(10px);
  }
}

.el-button {
  border-radius: 8px;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-1px);
  }

  &.is-circle {
    border-radius: 50%;
  }
}

.el-tag {
  border-radius: 12px;
  border: none;

  &.el-tag--success {
    background: linear-gradient(135deg, #67C23A, #85ce61);
    color: white;
  }

  &.el-tag--warning {
    background: linear-gradient(135deg, #E6A23C, #f0a020);
    color: white;
  }

  &.el-tag--danger {
    background: linear-gradient(135deg, #F56C6C, #f78989);
    color: white;
  }
}

.el-switch {
  .el-switch__core {
    border-radius: 15px;
  }
}

.el-progress-bar__outer {
  border-radius: 4px;
  overflow: hidden;
}

.el-progress-bar__inner {
  border-radius: 4px;
}

.el-tooltip__popper {
  background: rgba(0, 0, 0, 0.8) !important;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;

  .el-tooltip__arrow::before {
    background: rgba(0, 0, 0, 0.8) !important;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
}
</style>

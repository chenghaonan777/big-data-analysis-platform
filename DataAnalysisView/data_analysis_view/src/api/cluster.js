import api from './request'

// 集群监控相关API
export const clusterAPI = {
  // 获取集群状态概览
  async getClusterStatus () {
    try {
      console.log('正在获取集群状态...')
      return await api.get('/cluster/status')
    } catch (error) {
      console.error('获取集群状态失败:', error)
      throw error
    }
  },

  // 获取集群性能指标
  async getClusterMetrics () {
    try {
      console.log('正在获取集群性能指标...')
      return await api.get('/cluster/metrics')
    } catch (error) {
      console.error('获取性能指标失败:', error)
      throw error
    }
  },

  // 获取集群告警信息
  async getClusterAlerts () {
    try {
      console.log('正在获取集群告警...')
      return await api.get('/cluster/alerts')
    } catch (error) {
      console.error('获取告警信息失败:', error)
      throw error
    }
  },

  // 获取单个组件详细状态
  async getComponentDetail (component) {
    try {
      console.log(`正在获取组件${component}详情...`)
      return await api.get(`/cluster/components/${component}`)
    } catch (error) {
      console.error(`获取组件${component}详情失败:`, error)
      throw error
    }
  },

  // 获取系统资源使用情况
  async getSystemMetrics () {
    try {
      console.log('正在获取系统指标...')
      return await api.get('/cluster/system')
    } catch (error) {
      console.error('获取系统指标失败:', error)
      throw error
    }
  },

  // 启动集群监控
  async startMonitoring (interval = 30) {
    try {
      console.log('正在启动集群监控...')
      return await api.post('/cluster/monitoring/start', { interval })
    } catch (error) {
      console.error('启动监控失败:', error)
      throw error
    }
  },

  // 停止集群监控
  async stopMonitoring () {
    try {
      console.log('正在停止集群监控...')
      return await api.post('/cluster/monitoring/stop')
    } catch (error) {
      console.error('停止监控失败:', error)
      throw error
    }
  }
}

// 大数据环境管理API
export const bigDataAPI = {
  // 初始化大数据环境
  async initializeBigData () {
    try {
      console.log('正在初始化大数据环境...')
      return await api.post('/bigdata/initialize')
    } catch (error) {
      console.error('初始化大数据环境失败:', error)
      throw error
    }
  },

  // 加载数据到数据仓库
  async loadDataToWarehouse () {
    try {
      console.log('正在加载数据到数据仓库...')
      return await api.post('/bigdata/load_data')
    } catch (error) {
      console.error('加载数据失败:', error)
      throw error
    }
  },

  // 执行大数据分析
  async executeBigDataAnalysis () {
    try {
      console.log('正在执行大数据分析...')
      return await api.post('/bigdata/analyze')
    } catch (error) {
      console.error('执行大数据分析失败:', error)
      throw error
    }
  },

  // 获取大数据环境状态
  async getBigDataStatus () {
    try {
      console.log('正在获取大数据环境状态...')
      return await api.get('/bigdata/status')
    } catch (error) {
      console.error('获取大数据状态失败:', error)
      throw error
    }
  }
}

export default {
  clusterAPI,
  bigDataAPI
}

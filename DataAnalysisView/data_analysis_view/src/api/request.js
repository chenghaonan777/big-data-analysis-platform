import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: process.env.NODE_ENV === 'production' ? 'http://127.0.0.1:5000' : '/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: false,
  retry: 3,
  retryDelay: 1000
})

// 添加请求拦截器
api.interceptors.request.use(
  config => {
    console.log('API请求:', config.method?.toUpperCase(), config.url, config.baseURL + config.url)
    return config
  },
  error => {
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 添加响应拦截器 - 增强错误处理
api.interceptors.response.use(
  response => {
    console.log('API响应成功:', response.config.url, response.status)
    return response.data
  },
  error => {
    console.error('API错误详情:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      message: error.message,
      code: error.code,
      stack: error.stack
    })

    // 处理网络连接错误
    if (error.code === 'ECONNREFUSED') {
      console.error('后端服务连接被拒绝，请检查后端服务是否在 http://127.0.0.1:5000 启动')
      return Promise.reject({
        message: '后端服务连接失败，请检查服务是否启动',
        code: 'CONNECTION_REFUSED',
        originalError: error
      })
    }

    // 处理网络超时
    if (error.code === 'ECONNABORTED' && error.message.includes('timeout')) {
      console.error('请求超时')
      return Promise.reject({
        message: '请求超时，请检查网络连接',
        code: 'TIMEOUT',
        originalError: error
      })
    }

    // 处理网络错误
    if (error.message === 'Network Error') {
      console.error('网络错误，可能是跨域问题或服务器不可达')
      return Promise.reject({
        message: '网络连接失败，请检查服务器状态',
        code: 'NETWORK_ERROR',
        originalError: error
      })
    }

    // 处理HTTP状态码错误
    if (error.response) {
      const {
        status,
        data
      } = error.response
      let errorMessage = data?.message || error.message

      switch (status) {
        case 404:
          console.error('API 接口不存在:', error.config.url)
          errorMessage = '请求的接口不存在'
          break
        case 500:
          console.error('服务器内部错误')
          errorMessage = '服务器内部错误，请联系管理员'
          break
        case 502:
          console.error('网关错误')
          errorMessage = '服务器网关错误'
          break
        case 503:
          console.error('服务不可用')
          errorMessage = '服务暂时不可用，请稍后重试'
          break
        default:
          console.error(`HTTP错误 ${status}:`, errorMessage)
      }

      return Promise.reject({
        message: errorMessage,
        code: `HTTP_${status}`,
        status: status,
        originalError: error
      })
    }

    // 其他未知错误
    return Promise.reject({
      message: error.message || '未知错误',
      code: 'UNKNOWN_ERROR',
      originalError: error
    })
  }
)

// 添加重试机制
const retryRequest = async (config, retryCount = 0) => {
  try {
    return await api(config)
  } catch (error) {
    if (retryCount < (config.retry || 3) &&
      (error.code === 'ECONNREFUSED' || error.code === 'TIMEOUT')) {
      console.log(`重试请求 ${retryCount + 1}/${config.retry || 3}:`, config.url)
      await new Promise(resolve => setTimeout(resolve, config.retryDelay || 1000))
      return retryRequest(config, retryCount + 1)
    }
    throw error
  }
}

// 系统状态相关 API
export const systemAPI = {
  async getStatus () {
    try {
      console.log('正在获取系统状态...')
      return await api.get('/status')
    } catch (error) {
      console.error('获取系统状态失败:', error)
      throw error
    }
  },

  async healthCheck () {
    try {
      console.log('正在进行健康检查...')
      return await api.get('/health')
    } catch (error) {
      console.error('健康检查失败:', error)
      throw error
    }
  }
}

// 数据分析相关 API
export const analysisAPI = {
  async getBasicStats () {
    try {
      console.log('正在获取基础统计数据...')
      return await api.get('/analysis/basic-stats')
    } catch (error) {
      console.error('获取基础统计失败:', error)
      throw error
    }
  },

  async getRegionalData () {
    try {
      console.log('正在获取地域数据...')
      return await api.get('/data/regional')
    } catch (error) {
      console.error('获取地域数据失败:', error)
      throw error
    }
  },

  async getTemporalData () {
    try {
      console.log('正在获取时间序列数据...')
      return await api.get('/data/temporal')
    } catch (error) {
      console.error('获取时间数据失败:', error)
      throw error
    }
  },

  async getEnterpriseRanking () {
    try {
      console.log('正在获取企业排名数据...')
      return await api.get('/analysis/enterprise-ranking')
    } catch (error) {
      console.error('获取企业排名失败:', error)
      throw error
    }
  },

  async getComprehensiveAnalysis () {
    try {
      console.log('正在进行综合分析...')
      return await api.post('/analysis/comprehensive')
    } catch (error) {
      console.error('综合分析失败:', error)
      throw error
    }
  }
}

// 存储相关 API
export const storageAPI = {
  async getStorageSummary () {
    try {
      console.log('正在获取存储摘要...')
      return await api.get('/storage/summary')
    } catch (error) {
      console.error('获取存储摘要失败:', error)
      throw error
    }
  },

  async initStorage () {
    try {
      console.log('正在初始化存储...')
      return await api.post('/storage/init')
    } catch (error) {
      console.error('初始化存储失败:', error)
      throw error
    }
  }
}

// 数据相关 API
export const dataAPI = {
  async getDataInfo () {
    try {
      console.log('正在获取数据信息...')
      return await api.get('/data/info')
    } catch (error) {
      console.error('获取数据信息失败:', error)
      throw error
    }
  },

  async previewData () {
    try {
      console.log('正在预览数据...')
      return await api.get('/data/preview')
    } catch (error) {
      console.error('数据预览失败:', error)
      throw error
    }
  },

  async startCleaning () {
    try {
      console.log('正在开始数据清洗...')
      return await api.post('/data/cleaning/start')
    } catch (error) {
      console.error('数据清洗失败:', error)
      throw error
    }
  }
}

// 连接测试 API
export const connectionAPI = {
  async testConnection () {
    try {
      console.log('正在测试后端连接...')
      const response = await api.get('/status', { timeout: 5000 })
      console.log('连接测试成功')
      return {
        connected: true,
        data: response
      }
    } catch (error) {
      console.log('连接测试失败:', error.message)
      return {
        connected: false,
        error: error.message,
        code: error.code
      }
    }
  },

  async ping () {
    try {
      const start = Date.now()
      await api.get('/status', { timeout: 3000 })
      const latency = Date.now() - start
      return {
        success: true,
        latency
      }
    } catch (error) {
      return {
        success: false,
        error: error.message
      }
    }
  }
}

// 集群监控相关API
export const clusterAPI = {
  async getClusterStatus () {
    try {
      console.log('正在获取集群状态...')
      return await api.get('/cluster/status')
    } catch (error) {
      console.error('获取集群状态失败:', error)
      throw error
    }
  },

  async getClusterMetrics () {
    try {
      console.log('正在获取集群性能指标...')
      return await api.get('/cluster/metrics')
    } catch (error) {
      console.error('获取性能指标失败:', error)
      throw error
    }
  },

  async getClusterAlerts () {
    try {
      console.log('正在获取集群告警...')
      return await api.get('/cluster/alerts')
    } catch (error) {
      console.error('获取告警信息失败:', error)
      throw error
    }
  },

  async getSystemMetrics () {
    try {
      console.log('正在获取系统指标...')
      return await api.get('/cluster/system')
    } catch (error) {
      console.error('获取系统指标失败:', error)
      throw error
    }
  },

  async startMonitoring (interval = 30) {
    try {
      console.log('正在启动集群监控...')
      return await api.post('/cluster/monitoring/start', { interval })
    } catch (error) {
      console.error('启动监控失败:', error)
      throw error
    }
  },

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
  async initializeBigData () {
    try {
      console.log('正在初始化大数据环境...')
      return await api.post('/bigdata/initialize')
    } catch (error) {
      console.error('初始化大数据环境失败:', error)
      throw error
    }
  },

  async loadDataToWarehouse () {
    try {
      console.log('正在加载数据到数据仓库...')
      return await api.post('/bigdata/load_data')
    } catch (error) {
      console.error('加载数据失败:', error)
      throw error
    }
  },

  async executeBigDataAnalysis () {
    try {
      console.log('正在执行大数据分析...')
      return await api.post('/bigdata/analyze')
    } catch (error) {
      console.error('执行大数据分析失败:', error)
      throw error
    }
  },

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

// 工具函数
export const apiUtils = {
  // 检查服务器是否可达
  async isServerReachable () {
    try {
      const result = await connectionAPI.testConnection()
      return result.connected
    } catch (error) {
      return false
    }
  },

  // 获取错误信息
  getErrorMessage (error) {
    if (typeof error === 'string') return error
    if (error.message) return error.message
    if (error.code === 'CONNECTION_REFUSED') {
      return '后端服务连接失败，请检查服务是否启动'
    }
    if (error.code === 'TIMEOUT') {
      return '请求超时，请检查网络连接'
    }
    if (error.code === 'NETWORK_ERROR') {
      return '网络连接失败，请检查服务器状态'
    }
    return '未知错误'
  },

  // 重置API配置
  resetApiConfig () {
    api.defaults.baseURL = process.env.NODE_ENV === 'production' ? 'http://127.0.0.1:5000' : '/api'
    api.defaults.timeout = 15000
  }
}

// 导出默认实例和配置
export default api

// 导出配置常量
export const API_CONFIG = {
  PRODUCTION_BASE_URL: 'http://127.0.0.1:5000',
  DEVELOPMENT_BASE_URL: '/api',
  DEFAULT_TIMEOUT: 15000,
  RETRY_COUNT: 3,
  RETRY_DELAY: 1000
}

// 初始化时测试连接
if (process.env.NODE_ENV === 'development') {
  setTimeout(async () => {
    console.log('正在测试后端连接...')
    const result = await connectionAPI.testConnection()
    if (result.connected) {
      console.log('✓ 后端服务连接正常')
    } else {
      console.warn('⚠ 后端服务连接失败:', result.error)
      console.log('请确保后端服务已启动在 http://127.0.0.1:5000')
    }
  }, 1000)
}

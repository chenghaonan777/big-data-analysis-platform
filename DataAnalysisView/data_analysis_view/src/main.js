import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'

// 引入 Element UI
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'

// 引入 axios
import axios from 'axios'

// 引入 ECharts -
import ECharts from 'vue-echarts'
import 'echarts'

Vue.config.productionTip = false

// 使用 Element UI
Vue.use(ElementUI)

// 注册 ECharts 组件
Vue.component('v-chart', ECharts)

// 配置 axios
axios.defaults.timeout = 10000

// 添加请求拦截器
axios.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 添加响应拦截器
axios.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('请求错误:', error)
    if (error.response) {
      const { status, data } = error.response
      if (status === 404) {
        console.error('API 接口不存在')
      } else if (status === 500) {
        console.error('服务器内部错误')
      }
      return Promise.reject(data || error.message)
    }
    return Promise.reject(error.message)
  }
)

Vue.prototype.$http = axios

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')

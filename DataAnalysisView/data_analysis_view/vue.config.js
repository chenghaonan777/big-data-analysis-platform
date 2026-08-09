const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,

  // 开发服务器配置
  devServer: {
    port: 8080,
    host: 'localhost',
    open: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        ws: true,
        secure: false,
        logLevel: 'debug',
        // 添加错误处理
        onError: function (err, req, res) {
          console.log('代理错误:', err)
        },
        // 添加代理请求前的处理
        onProxyReq: function (proxyReq, req, res) {
          console.log('代理请求:', req.url)
        }
      }
    }
  },

  // 打包配置
  publicPath: process.env.NODE_ENV === 'production' ? './' : '/'
})

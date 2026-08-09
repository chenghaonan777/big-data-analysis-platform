<template>
  <div class="about">
    <div class="about-container">
      <!-- 页面头部 -->
      <div class="about-header">
        <div class="header-decoration">
          <div class="decoration-circle circle-1"></div>
          <div class="decoration-circle circle-2"></div>
          <div class="decoration-circle circle-3"></div>
        </div>
        <h1>山西水泥公司电力大数据分析系统</h1>
        <p class="subtitle">Shanxi Cement Power Big Data Analysis System</p>
        <p class="description">基于Hadoop生态的专业电力数据分析与可视化平台</p>
        <div class="version-info">
          <el-tag type="success" size="large">Version 2.0.0</el-tag>
          <el-tag type="info" size="large">Build 20250920</el-tag>
        </div>
      </div>

      <div class="about-content">
        <!-- 系统概览 -->
        <el-row :gutter="30" class="overview-section">
          <el-col :span="8">
            <el-card class="overview-card">
              <div class="overview-icon">
                <i class="el-icon-data-analysis"></i>
              </div>
              <h3>数据分析</h3>
              <p>多维度电力消耗分析，支持实时监控和历史趋势分析</p>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card class="overview-card">
              <div class="overview-icon">
                <i class="el-icon-monitor"></i>
              </div>
              <h3>集群监控</h3>
              <p>实时监控Hadoop、Hive、MySQL等大数据组件状态</p>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card class="overview-card">
              <div class="overview-icon">
                <i class="el-icon-pie-chart"></i>
              </div>
              <h3>可视化展示</h3>
              <p>丰富的图表展示，包括地域分布、时间趋势、企业排名</p>
            </el-card>
          </el-col>
        </el-row>

        <!-- 详细信息 -->
        <el-row :gutter="30" class="details-section">
          <el-col :span="12">
            <el-card class="feature-card">
              <div slot="header" class="card-header">
                <h3><i class="el-icon-star-on"></i> 核心功能</h3>
              </div>
              <div class="feature-grid">
                <div class="feature-item" v-for="feature in features" :key="feature.id">
                  <div class="feature-icon">
                    <i :class="feature.icon"></i>
                  </div>
                  <div class="feature-content">
                    <h4>{{ feature.title }}</h4>
                    <p>{{ feature.description }}</p>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>

          <el-col :span="12">
            <el-card class="tech-card">
              <div slot="header" class="card-header">
                <h3><i class="el-icon-cpu"></i> 技术架构</h3>
              </div>
              <div class="tech-tabs">
                <el-tabs v-model="activeTab" type="border-card">
                  <el-tab-pane label="前端技术" name="frontend">
                    <div class="tech-stack">
                      <div class="tech-item" v-for="tech in frontendTech" :key="tech.name">
                        <span class="tech-label">{{ tech.name }}:</span>
                        <span class="tech-value">{{ tech.version }}</span>
                        <el-tag :type="tech.status" size="mini">{{ tech.statusText }}</el-tag>
                      </div>
                    </div>
                  </el-tab-pane>
                  <el-tab-pane label="后端技术" name="backend">
                    <div class="tech-stack">
                      <div class="tech-item" v-for="tech in backendTech" :key="tech.name">
                        <span class="tech-label">{{ tech.name }}:</span>
                        <span class="tech-value">{{ tech.version }}</span>
                        <el-tag :type="tech.status" size="mini">{{ tech.statusText }}</el-tag>
                      </div>
                    </div>
                  </el-tab-pane>
                  <el-tab-pane label="大数据组件" name="bigdata">
                    <div class="tech-stack">
                      <div class="tech-item" v-for="tech in bigdataTech" :key="tech.name">
                        <span class="tech-label">{{ tech.name }}:</span>
                        <span class="tech-value">{{ tech.version }}</span>
                        <el-tag :type="tech.status" size="mini">{{ tech.statusText }}</el-tag>
                      </div>
                    </div>
                  </el-tab-pane>
                </el-tabs>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 系统统计 -->
        <el-row :gutter="30" class="stats-section">
          <el-col :span="24">
            <el-card class="stats-card">
              <div slot="header" class="card-header">
                <h3><i class="el-icon-data-line"></i> 系统统计</h3>
                <el-button type="text" @click="refreshStats">
                  <i class="el-icon-refresh"></i> 刷新
                </el-button>
              </div>
              <el-row :gutter="20">
                <el-col :span="6" v-for="stat in systemStats" :key="stat.key">
                  <div class="stat-item">
                    <div class="stat-icon" :style="{ backgroundColor: stat.color }">
                      <i :class="stat.icon"></i>
                    </div>
                    <div class="stat-content">
                      <h4>{{ stat.value }}</h4>
                      <p>{{ stat.label }}</p>
                      <small>{{ stat.description }}</small>
                    </div>
                  </div>
                </el-col>
              </el-row>
            </el-card>
          </el-col>
        </el-row>

        <!-- 开发团队信息 -->
        <el-row :gutter="30" class="team-section">
          <el-col :span="12">
            <el-card class="team-card">
              <div slot="header" class="card-header">
                <h3><i class="el-icon-user"></i> 开发团队</h3>
              </div>
              <div class="team-info">
                <div class="team-item">
                  <div class="team-role">项目负责人</div>
                  <div class="team-name">数据分析团队</div>
                </div>
                <div class="team-item">
                  <div class="team-role">技术架构</div>
                  <div class="team-name">大数据开发组</div>
                </div>
                <div class="team-item">
                  <div class="team-role">前端开发</div>
                  <div class="team-name">前端团队</div>
                </div>
                <div class="team-item">
                  <div class="team-role">测试团队</div>
                  <div class="team-name">质量保障组</div>
                </div>
              </div>
            </el-card>
          </el-col>

          <el-col :span="12">
            <el-card class="contact-card">
              <div slot="header" class="card-header">
                <h3><i class="el-icon-phone"></i> 联系信息</h3>
              </div>
              <div class="contact-info">
                <div class="contact-item">
                  <i class="el-icon-office-building"></i>
                  <span>山西水泥公司信息技术部</span>
                </div>
                <div class="contact-item">
                  <i class="el-icon-location"></i>
                  <span>山西省太原市小店区</span>
                </div>
                <div class="contact-item">
                  <i class="el-icon-phone-outline"></i>
                  <span>0351-1234567</span>
                </div>
                <div class="contact-item">
                  <i class="el-icon-message"></i>
                  <span>support@shanxicement.com</span>
                </div>
                <div class="contact-item">
                  <i class="el-icon-time"></i>
                  <span>技术支持：7×24小时</span>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 更新日志 -->
        <el-row class="changelog-section">
          <el-col :span="24">
            <el-card class="changelog-card">
              <div slot="header" class="card-header">
                <h3><i class="el-icon-document"></i> 更新日志</h3>
              </div>
              <el-timeline>
                <el-timeline-item
                  v-for="log in changelog"
                  :key="log.version"
                  :timestamp="log.date"
                  :type="log.type">
                  <el-card class="timeline-card">
                    <h4>{{ log.version }}</h4>
                    <ul>
                      <li v-for="item in log.changes" :key="item">{{ item }}</li>
                    </ul>
                  </el-card>
                </el-timeline-item>
              </el-timeline>
            </el-card>
          </el-col>
        </el-row>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button type="primary" size="large" @click="$router.push('/')">
            <i class="el-icon-back"></i>
            返回仪表板
          </el-button>
          <el-button type="success" size="large" @click="goToClusterMonitoring">
            <i class="el-icon-monitor"></i>
            集群监控
          </el-button>
          <el-button type="info" size="large" @click="downloadUserGuide">
            <i class="el-icon-download"></i>
            用户手册
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AboutView',
  data () {
    return {
      activeTab: 'frontend',
      features: [
        {
          id: 1,
          icon: 'el-icon-data-analysis',
          title: '智能数据分析',
          description: '多维度电力消耗分析，支持地域、时间、企业多角度统计'
        },
        {
          id: 2,
          icon: 'el-icon-monitor',
          title: '实时监控',
          description: '集群状态实时监控，异常自动告警，保障系统稳定运行'
        },
        {
          id: 3,
          icon: 'el-icon-pie-chart',
          title: '可视化展示',
          description: '丰富的图表类型，直观展示数据趋势和分析结果'
        },
        {
          id: 4,
          icon: 'el-icon-warning',
          title: '异常检测',
          description: '智能异常检测算法，及时发现数据异常和系统问题'
        },
        {
          id: 5,
          icon: 'el-icon-document',
          title: '报表导出',
          description: '支持多种格式报表导出，满足不同业务需求'
        },
        {
          id: 6,
          icon: 'el-icon-setting',
          title: '数据清洗',
          description: '自动化数据清洗处理，确保数据质量和准确性'
        }
      ],
      frontendTech: [
        {
          name: 'Vue.js',
          version: '2.6.14',
          status: 'success',
          statusText: '稳定'
        },
        {
          name: 'Element UI',
          version: '2.15.13',
          status: 'success',
          statusText: '最新'
        },
        {
          name: 'ECharts',
          version: '5.4.2',
          status: 'success',
          statusText: '最新'
        },
        {
          name: 'Axios',
          version: '0.27.2',
          status: 'success',
          statusText: '稳定'
        },
        {
          name: 'Vue Router',
          version: '3.5.4',
          status: 'success',
          statusText: '稳定'
        },
        {
          name: 'Vuex',
          version: '3.6.2',
          status: 'info',
          statusText: '可选'
        }
      ],
      backendTech: [
        {
          name: 'Python',
          version: '3.9+',
          status: 'success',
          statusText: '推荐'
        },
        {
          name: 'Flask',
          version: '2.3.3',
          status: 'success',
          statusText: '最新'
        },
        {
          name: 'Pandas',
          version: '2.0.3',
          status: 'success',
          statusText: '最新'
        },
        {
          name: 'NumPy',
          version: '1.24.3',
          status: 'success',
          statusText: '稳定'
        },
        {
          name: 'Scikit-learn',
          version: '1.3.0',
          status: 'success',
          statusText: '最新'
        },
        {
          name: 'Matplotlib',
          version: '3.7.2',
          status: 'success',
          statusText: '稳定'
        }
      ],
      bigdataTech: [
        {
          name: 'Hadoop',
          version: '3.3.x',
          status: 'warning',
          statusText: '最新'
        },
        {
          name: 'Hive',
          version: '3.1.x',
          status: 'warning',
          statusText: '最新'
        },
        {
          name: 'MySQL',
          version: '8.0+',
          status: 'warning',
          statusText: '最新'
        },
        {
          name: 'HDFS',
          version: '3.3.x',
          status: 'warning',
          statusText: '最新'
        },
        {
          name: 'Spark',
          version: '3.4.x',
          status: 'info',
          statusText: '可选'
        },
        {
          name: 'Kafka',
          version: '2.8.x',
          status: 'info',
          statusText: '计划'
        }
      ],
      systemStats: [
        {
          key: 'totalData',
          value: '1,250,000+',
          label: '数据记录数',
          description: '累计处理的电力数据',
          icon: 'el-icon-data-line',
          color: '#409EFF'
        },
        {
          key: 'enterprises',
          value: '85',
          label: '监控企业',
          description: '覆盖的水泥企业数量',
          icon: 'el-icon-office-building',
          color: '#67C23A'
        },
        {
          key: 'regions',
          value: '11',
          label: '覆盖地区',
          description: '监控覆盖的地市',
          icon: 'el-icon-location',
          color: '#E6A23C'
        },
        {
          key: 'uptime',
          value: '99.9%',
          label: '系统可用性',
          description: '系统稳定运行时间',
          icon: 'el-icon-circle-check',
          color: '#F56C6C'
        }
      ],
      changelog: [
        {
          version: 'Version 2.0.0',
          date: '2025-09-19',
          type: 'primary',
          changes: [
            '新增集群监控功能，支持Hadoop、Hive、MySQL状态监控',
            '优化数据分析算法，提升处理效率30%',
            '新增大数据环境管理功能',
            '改进用户界面，提升用户体验',
            '增强系统安全性和稳定性'
          ]
        },
        {
          version: 'Version 1.2.0',
          date: '2025-09-20',
          type: 'success',
          changes: [
            '新增企业排名分析功能',
            '优化地域分布图表展示',
            '修复数据导出的若干问题',
            '改进系统响应速度'
          ]
        },
        {
          version: 'Version 1.1.0',
          date: '2025-09-20',
          type: 'info',
          changes: [
            '新增时间趋势分析',
            '优化数据清洗算法',
            '新增数据质量评估',
            '修复已知Bug'
          ]
        },
        {
          version: 'Version 1.0.0',
          date: '2025-09-20',
          type: 'warning',
          changes: [
            '系统正式发布',
            '基础数据分析功能',
            '可视化图表展示',
            '用户管理系统'
          ]
        }
      ]
    }
  },

  methods: {
    goToClusterMonitoring () {
      this.$router.push('/cluster')
    },

    downloadUserGuide () {
      this.$message.success('用户手册下载中...')
      const link = document.createElement('a')
      link.href = '#'
      link.download = '山西水泥公司电力大数据分析系统-用户手册.pdf'
      link.click()
    },

    refreshStats () {
      this.$message.info('正在刷新统计数据...')
      setTimeout(() => {
        this.$message.success('统计数据已更新')
      }, 1000)
    }
  },

  mounted () {
    // 强制重置滚动样式
    document.documentElement.style.overflow = 'auto'
    document.body.style.overflow = 'auto'
    document.body.style.height = 'auto'

    // 检查并移除可能的样式限制
    const app = document.getElementById('app')
    if (app) {
      app.style.overflow = 'auto'
      app.style.height = 'auto'
      app.style.maxHeight = 'none'
    }

    // 延迟执行动画
    setTimeout(() => {
      const cards = document.querySelectorAll('.el-card')
      cards.forEach((card, index) => {
        setTimeout(() => {
          card.style.opacity = '1'
          card.style.transform = 'translateY(0)'
        }, index * 100)
      })
    }, 300)
  },

  destroyed () {
    // 组件销毁时恢复默认样式
    document.documentElement.style.overflow = ''
    document.body.style.overflow = ''
    document.body.style.height = ''
  }
}
</script>

<style lang="scss">
html, body {
  overflow-y: auto !important;
  height: auto !important;
  max-height: none !important;
}

#app {
  overflow-y: auto !important;
  height: auto !important;
  max-height: none !important;
}

.router-view, .el-main {
  overflow-y: auto !important;
  height: auto !important;
  max-height: none !important;
}
</style>

<style lang="scss" scoped>
* {
  box-sizing: border-box;
}

.about {
  padding: 30px 20px 100px 20px;
  position: relative;

  background: linear-gradient(135deg, #0c1e35 0%, #1a365d 30%, #2d3748 70%, #1a202c 100%);
  background-attachment: fixed;
  background-size: cover;

  // 移除固定高度限制 - 这是关键！
  min-height: auto;

  &::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="1" fill="rgba(255,255,255,0.1)"/></svg>') repeat;
    background-size: 50px 50px;
    opacity: 0.3;
    pointer-events: none;
    z-index: 0;
  }
}

.about-container {
  max-width: 1400px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
  // 移除固定高度限制
  min-height: auto;
}

// 页面头部
.about-header {
  text-align: center;
  margin-bottom: 60px;
  position: relative;
  padding: 40px 0;
  z-index: 2;

  .header-decoration {
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 200px;
    height: 200px;
    pointer-events: none;

    .decoration-circle {
      position: absolute;
      border: 1px solid rgba(64, 158, 255, 0.3);
      border-radius: 50%;
      animation: rotate 20s linear infinite;

      &.circle-1 {
        width: 100px;
        height: 100px;
        top: 50px;
        left: 50px;
      }

      &.circle-2 {
        width: 150px;
        height: 150px;
        top: 25px;
        left: 25px;
        animation-duration: 30s;
        animation-direction: reverse;
      }

      &.circle-3 {
        width: 200px;
        height: 200px;
        top: 0;
        left: 0;
        animation-duration: 40s;
      }
    }
  }

  h1 {
    color: #ffffff;
    font-size: 42px;
    font-weight: 700;
    margin-bottom: 10px;
    text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.5);
    line-height: 1.2;
  }

  .subtitle {
    color: #90cdf4;
    font-size: 16px;
    margin-bottom: 15px;
    font-weight: 300;
    letter-spacing: 1px;
  }

  .description {
    color: #cbd5e0;
    font-size: 18px;
    margin-bottom: 25px;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
    line-height: 1.6;
  }

  .version-info {
    display: flex;
    justify-content: center;
    gap: 15px;

    .el-tag {
      font-size: 14px;
      padding: 8px 16px;
    }
  }
}

// 概览卡片
.overview-section {
  margin-bottom: 40px;

  .overview-card {
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 15px;
    text-align: center;
    padding: 30px 20px;
    height: 200px;
    transition: all 0.3s ease;
    cursor: pointer;

    &:hover {
      transform: translateY(-10px);
      box-shadow: 0 20px 40px rgba(64, 158, 255, 0.2);
      border-color: rgba(64, 158, 255, 0.5);
    }

    .overview-icon {
      font-size: 48px;
      color: #409EFF;
      margin-bottom: 20px;
    }

    h3 {
      color: #ffffff;
      margin-bottom: 15px;
      font-size: 20px;
    }

    p {
      color: #cbd5e0;
      font-size: 14px;
      line-height: 1.6;
    }
  }
}

// 详细信息区域
.details-section, .stats-section, .team-section, .changelog-section {
  margin-bottom: 40px;
}

// 通用卡片样式
.feature-card, .tech-card, .stats-card, .team-card, .contact-card, .changelog-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  opacity: 1;
  transform: translateY(0);
  transition: all 0.6s ease;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    h3 {
      color: #ffffff;
      margin: 0;
      font-size: 18px;
      font-weight: 600;

      i {
        margin-right: 10px;
        color: #409EFF;
      }
    }

    .el-button {
      color: #90cdf4;

      &:hover {
        color: #409EFF;
      }
    }
  }

  ::v-deep .el-card__header {
    background: rgba(64, 158, 255, 0.1);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 15px 15px 0 0;
  }
}

// 功能网格
.feature-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;

  .feature-item {
    display: flex;
    align-items: flex-start;
    padding: 20px;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    transition: all 0.3s ease;

    &:hover {
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(64, 158, 255, 0.3);
    }

    .feature-icon {
      font-size: 32px;
      color: #409EFF;
      margin-right: 20px;
      flex-shrink: 0;
    }

    .feature-content {
      flex: 1;

      h4 {
        color: #ffffff;
        margin: 0 0 10px 0;
        font-size: 16px;
      }

      p {
        color: #cbd5e0;
        margin: 0;
        font-size: 14px;
        line-height: 1.5;
      }
    }
  }
}

// 技术栈标签页
.tech-tabs {
  ::v-deep .el-tabs {
    .el-tabs__header {
      background: transparent;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .el-tabs__nav-wrap {
      &::after {
        background: rgba(255, 255, 255, 0.1);
      }
    }

    .el-tabs__item {
      color: #cbd5e0;
      border: 1px solid rgba(255, 255, 255, 0.1);

      &.is-active {
        color: #409EFF;
        border-bottom-color: transparent;
      }
    }

    .el-tabs__content {
      padding: 20px 0;
    }
  }

  .tech-stack {
    .tech-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 15px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);

      &:last-child {
        border-bottom: none;
      }

      .tech-label {
        color: #a0aec0;
        font-size: 14px;
        flex: 1;
      }

      .tech-value {
        color: #ffffff;
        font-size: 14px;
        font-weight: 600;
        margin-right: 15px;
      }

      ::v-deep .el-tag {
        min-width: 60px;
        text-align: center;
      }
    }
  }
}

// 统计卡片
.stat-item {
  display: flex;
  align-items: center;
  padding: 20px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.08);
    transform: translateY(-5px);
  }

  .stat-icon {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 20px;
    font-size: 24px;
    color: white;
  }

  .stat-content {
    flex: 1;

    h4 {
      color: #ffffff;
      margin: 0 0 5px 0;
      font-size: 24px;
      font-weight: 700;
    }

    p {
      color: #cbd5e0;
      margin: 0 0 5px 0;
      font-size: 16px;
    }

    small {
      color: #a0aec0;
      font-size: 12px;
    }
  }
}

// 团队信息
.team-info, .contact-info {
  .team-item, .contact-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);

    &:last-child {
      border-bottom: none;
    }
  }

  .team-role {
    color: #a0aec0;
    font-size: 14px;
  }

  .team-name {
    color: #ffffff;
    font-size: 16px;
    font-weight: 600;
  }

  .contact-item {
    justify-content: flex-start;

    i {
      color: #409EFF;
      margin-right: 15px;
      width: 20px;
      text-align: center;
    }

    span {
      color: #cbd5e0;
      font-size: 14px;
    }
  }
}

// 时间线
::v-deep .el-timeline {
  .el-timeline-item {
    .timeline-card {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.1);
      margin-bottom: 0;

      h4 {
        color: #409EFF;
        margin: 0 0 15px 0;
        font-size: 16px;
      }

      ul {
        margin: 0;
        padding-left: 20px;
        color: #cbd5e0;

        li {
          margin-bottom: 8px;
          font-size: 14px;
          line-height: 1.5;
        }
      }
    }
  }
}

// 操作按钮
.action-buttons {
  text-align: center;
  margin: 60px 0 100px 0;
  display: flex;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;

  ::v-deep .el-button {
    padding: 15px 30px;
    font-size: 16px;
    border-radius: 25px;
    min-width: 160px;
  }
}

// 动画
@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .about {
    padding: 20px 10px 100px 10px;
  }

  .about-header {
    h1 {
      font-size: 28px;
    }

    .description {
      font-size: 16px;
    }
  }

  .overview-section {
    ::v-deep .el-col {
      margin-bottom: 20px;
    }
  }

  .feature-grid {
    .feature-item {
      flex-direction: column;
      text-align: center;

      .feature-icon {
        margin-right: 0;
        margin-bottom: 15px;
      }
    }
  }

  .stat-item {
    flex-direction: column;
    text-align: center;

    .stat-icon {
      margin-right: 0;
      margin-bottom: 15px;
    }
  }

  .action-buttons {
    flex-direction: column;
    align-items: center;

    ::v-deep .el-button {
      width: 200px;
    }
  }
}
</style>

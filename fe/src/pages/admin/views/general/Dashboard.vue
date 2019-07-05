<template> 
  <!-- 这里使用admin-info-name 下面就可以使用&-name设置样式 -->
  <el-row type="flex" :gutter="20">
    <!-- md和lg 上下两列之和加起来必须为24-->
    <el-col :md="12" :lg="12">
      <el-card class="admin-info">
        <!-- gutter="20"用来调整方块的距离为20 -->
        <el-row :gutter="20">
          <el-col :span="10">
            <img class="avatar" :src="profile.avatar">
          </el-col>
          <el-col :span="14">
            <p class="admin-info-name">{{user.username}}</p>
            <p>{{user.admin_type}}</p>
          </el-col>
        </el-row>
        <hr/>
        <div class="last-info">
          <p class="last-info-title">{{$t('m.Last_Login')}}</p>
          <el-form label-width="80px" class="last-info-body">
            <el-form-item label="时间：">
              <span>{{session.last_activity | localtime}}</span>
            </el-form-item>
            <el-form-item label="IP：">
              <span>{{session.ip}}</span>
            </el-form-item >
            <el-form-item label="OS：">
              <span>{{os}}</span>
            </el-form-item>
            <el-form-item label="浏览器：">
              <span>{{browser}}</span>
            </el-form-item>
          </el-form>
        </div>
      </el-card>
    </el-col>

    <el-col :md="12" :lg="12" v-if="isSuperAdmin">
      <div class="info-container">
        <info-card color="#fb0b9c" icon="el-icon-fa-users" message="总用户数" iconSize="30px" class="info-item"
                    :value="infoData.user_count"></info-card>
        <info-card color="#67C23A" icon="el-icon-fa-list" message="今日提交量" class="Info-item"
                    :value="infoData.today_submission_count"></info-card>
        <info-card color="#ffd440" icon="el-icon-fa-trophy" message="最近的比赛" class="info-item"
                    :value="infoData.recent_contest_count"></info-card>
      </div>
      <panel :title="$t('m.System_Overview')" v-if="isSuperAdmin">
        <p>{{$t('m.DashBoardJudge_Server')}}:  {{infoData.judge_server_count}}</p>

      </panel>

    </el-col>
  </el-row>
</template>-->



<script>
  import { mapGetters } from 'vuex'
  import browserDetector from 'browser-detect'
  import InfoCard from '@admin/components/infoCard.vue'
  import api from '@admin/api'


  export default {
    name: 'dashboard',
    components: {
      InfoCard
    },
    data () {
      return {
        infoData: {
          user_count: 0,
          recent_contest_count: 0,
          today_submission_count: 0,
          judge_server_count: 0,
          env: {}
        },
        activeNames: [1],
        session: {},
        loadingReleases: true,
        releases: []
      }
    },
    mounted () {
      api.getDashboardInfo().then(resp => {
        this.infoData = resp.data.data
      }, () => {})
      api.getSessions().then(resp => {
        this.parseSession(resp.data.data)
      }, () => {})
    },
    methods: {
      parseSession (sessions) {
        let session = sessions[0]
        if (sessions.length > 1) {
          // filter not filters 显示的是上一次登录的参数
          session = sessions.filter(s => !s.current_session).sort((a, b) => {
            return a.last_activity < b.last_activity
          })[0]
        }
        this.session = session
      }
    },
    computed: {
      ...mapGetters(['profile', 'user', 'isSuperAdmin']),
      cdn () {
        return this.infoData.env.STATIC_CDN_HOST
      },
      https () {
        return document.URL.slice(0, 5) === 'https'
      },
      forceHttps () {
        return this.infoData.env.FORCE_HTTPS
      },
      browser () {
        let b = browserDetector(this.session.user_agent)
        if (b.name && b.version) {
          return b.name + ' ' + b.version
        } else {
          return 'Unknown'
        }
      },
      os () {
        let b = browserDetector(this.session.user_agent)
        return b.os ? b.os : 'Unknown'
      }
    }
  }

</script>

<style lang="less">
  .admin-info {
    margin-bottom: 20px;
    &-name {
      font-size: 24px;
      font-weight: 700;
      margin-bottom: 10px;
      color: #198bfd;
    }
    .avatar {
      max-width: 100%;
    }
    .last-info {
      &-title {
        font-size: 16px;
      }
      &-body {
        .el-form-item {
          margin-bottom: 3px;
        }
      }
    }
  }

  .info-container {
    display: flex;
    // ustify-content属性定义了项目在主轴上的对齐方式,从开始时就对齐
    justify-content: flex-start;
    // flex-wrap 项目一行排列不下就换行显示
    flex-wrap: wrap;
    .info-item {
      flex:1 0 auto;
      min-width: 200px;
      margin-bottom: 10px;
    }
    
  }

</style>

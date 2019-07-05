<template>
  <div class="flex-container">
    <div id="contest-main">
      <!--children-->
      <!--fadeInUp也是有样式来控制的,用来控制右边的垂直菜单点击路由router-view跳转-->
      <transition name="fadeInUp">
        <router-view></router-view>
      </transition>
      <!--children end-->
      <div class="flex-container" v-if="route_name === 'contest-details'">
        <template>
          <div id="contest-desc">
            <!--将信息放到一个pannel里面,头部包含的信息有标题和时间的计算-->
            <Panel :padding="20" shadow>
              <div slot="title">
                {{contest.title}}
              </div>

              <div v-html="contest.description" class="markdown-body"></div>
              <!--密码保护: 用于内部的进行的比赛-->
              <div v-if="passwordFormVisible" class="contest-password">
                <Input v-model="contestPassword" type="password"
                       placeholder="参赛密码" class="contest-password-input"
                       @on-enter="checkPassword"/>
                <Button type="info" @click="checkPassword">进 入</Button>
              </div>
            </Panel>
            <!--同样选择在js里面遍历显示比赛数据-->
            <Table :columns="columns" :data="contest_table" disabled-hover style="margin-bottom: 40px;"></Table>
          </div>
        </template>
      </div>
    </div>
    <!--右边的垂直菜单信息:概览,公告,题目,提交信息,比赛排名-->
    <div v-show="showMenu" id="contest-menu">
      <VerticalMenu @on-click="handleRoute">
        <VerticalMenu-item :route="{name: 'contest-details', params: {contestID: contestID}}">
          <Icon type="home"></Icon>
          {{$t('m.Overview')}}
        </VerticalMenu-item>

        <VerticalMenu-item :disabled="contestMenuDisabled"
                           :route="{name: 'contest-announcement-list', params: {contestID: contestID}}">
          <Icon type="chatbubble-working"></Icon>
          {{$t('m.Announcements')}}
        </VerticalMenu-item>

        <VerticalMenu-item :disabled="contestMenuDisabled"
                           :route="{name: 'contest-problem-list', params: {contestID: contestID}}">
          <Icon type="ios-photos"></Icon>
          {{$t('m.Problems')}}
        </VerticalMenu-item>

        <VerticalMenu-item v-if="OIContestRealTimePermission"
                           :disabled="contestMenuDisabled"
                           :route="{name: 'contest-submission-list'}">
          <Icon type="navicon-round"></Icon>
          {{$t('m.Submissions')}}
        </VerticalMenu-item>

        <VerticalMenu-item v-if="OIContestRealTimePermission"
                           :disabled="contestMenuDisabled"
                           :route="{name: 'contest-rank', params: {contestID: contestID}}">
          <Icon type="stats-bars"></Icon>
          {{$t('m.Rankings')}}
        </VerticalMenu-item>


      </VerticalMenu>
    </div>
  </div>
</template>

<script>
  import moment from 'moment'
  import api from '@oj/api'
  import { mapState, mapGetters, mapActions } from 'vuex'
  import { types } from '@/store'
  import { CONTEST_STATUS_REVERSE, CONTEST_STATUS } from '@/utils/constants'
  import time from '@/utils/time'

  export default {
    name: 'ContestDetail',
    components: {},
    data () {
      // 返回的数据信息使用js的方式
      return {
        CONTEST_STATUS: CONTEST_STATUS,
        route_name: '',
        btnLoading: false,
        contestID: '',
        contestPassword: '',
        columns: [
          {
            title: '开始时间',
            render: (h, params) => {
              return h('span', time.utcToLocal(params.row.start_time))
            }
          },
          {
            title: '结束时间',
            render: (h, params) => {
              return h('span', time.utcToLocal(params.row.end_time))
            }
          },
          {
            title: '比赛类型',
            key: 'contest_type'
          },
          {
            title: '规则类型',
            key: 'rule_type'
          },
          {
            title: '创建者',
            render: (h, data) => {
              return h('span', data.row.created_by.username)
            }
          }
        ]
      }
    },
    // HTML加载完成之后进行数据的初始化:比赛ID,路由名称,
    // 存储路由请求路径,DOM标题,响应数据,结束时间,时间计数器
    mounted () {
      this.contestID = this.$route.params.contestID
      this.route_name = this.$route.name
      this.$store.dispatch('getContest').then(res => {
        this.changeDomTitle({title: res.data.data.title})
        let data = res.data.data
        let endTime = moment(data.end_time)
        if (endTime.isAfter(moment(data.now))) {
          this.timer = setInterval(() => {
            this.$store.commit(types.NOW_ADD_1S)
          }, 1000)
        }
      })
    },
    methods: {
      ...mapActions(['changeDomTitle']),
      // 处理路由跳转
      handleRoute (route) {
        this.$router.push(route)
      },
      // 检查密码
      checkPassword () {
        if (this.contestPassword === '') {
          this.$error('密码不能为空')
          return
        }
        this.btnLoading = true
        // 通过查询后台数据库之后验证密码成功可以参加比赛,检查密码成功之后要保存能登录的权限,
        // 不至于下一次再一次输入密码
        api.checkContestPassword(this.contestID, this.contestPassword).then((res) => {
          this.$success('成功!')
          this.$store.commit(types.CONTEST_ACCESS, {access: true})
          this.btnLoading = false
        }, (res) => {
          this.btnLoading = false
        })
      }
    },
    // 设置计算属性state:显示菜单,比赛,比赛表,目前比赛进行情况
    computed: {
      ...mapState({
        showMenu: state => state.contest.itemVisible.menu,
        contest: state => state.contest.contest,
        contest_table: state => [state.contest.contest],
        now: state => state.contest.now
      }),
      // 通过映射获取属性
      ...mapGetters(
        ['contestMenuDisabled', 'contestRuleType', 'contestStatus', 'countdown', 'isContestAdmin',
          'OIContestRealTimePermission', 'passwordFormVisible']
      ),
      // 定时器圆点颜色设置
      countdownColor () {
        if (this.contestStatus) {
          return CONTEST_STATUS_REVERSE[this.contestStatus].color
        }
      },
      // 显示管理员助手,并且只能在比赛规则为ACM的情况下才能显示
      showAdminHelper () {
        return this.isContestAdmin && this.contestRuleType === 'ACM'
      }
    },
    // 监听路由的变化, 做出对应的跳转
    watch: {
      '$route' (newVal) {
        this.route_name = newVal.name
        this.contestID = newVal.params.contestID
        this.changeDomTitle({title: this.contest.title})
      }
    },
    // 在vue生命被销毁之前,先将时间重置,提交比赛状态到本地保存
    beforeDestroy () {
      clearInterval(this.timer)
      this.$store.commit(types.CLEAR_CONTEST)
    }
  }
</script>

<style scoped lang="less">
  pre {
    display: inline-block;
  }

  #countdown {
    font-size: 16px;
  }

  .flex-container {
    #contest-main {
      flex: 1 1;
      #contest-desc {
        flex: auto;
      }
    }
    #contest-menu {
      flex: none;
      width: 210px;
      margin-left: 20px;
    }
    .contest-password {
      margin-top: 20px;
      margin-bottom: -10px;
      &-input {
        width: 200px;
        margin-right: 10px;
      }
    }
  }
</style>

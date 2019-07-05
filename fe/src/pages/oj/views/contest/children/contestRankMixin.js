import api from '@oj/api'
import ScreenFull from '@admin/components/ScreenFull.vue'
import { mapGetters, mapState } from 'vuex'
import { types } from '@/store'
import { CONTEST_STATUS } from '@/utils/constants'

// 比赛排名
export default {
  components: {
    ScreenFull
  },
  methods: {
    // 获取比赛排名数据
    getContestRankData (page = 1, refresh = false) {
      // 缓存设置
      let offset = (page - 1) * this.limit
      if (this.showChart && !refresh) {
        this.$refs.chart.showLoading({maskColor: 'rgba(250, 250, 250, 0.8)'})
      }
      let params = {
        offset,
        limit: this.limit,
        contest_id: this.$route.params.contestID,
        force_refresh: this.forceUpdate ? '1' : '0'
      }
      // 后台请求比赛数据排名,然后将数据通过表格展示出来
      api.getContestRank(params).then(res => {
        if (this.showChart && !refresh) {
          this.$refs.chart.hideLoading()
        }
        this.total = res.data.data.total
        if (page === 1) {
          this.applyToChart(res.data.data.results.slice(0, 10))
        }
        this.applyToTable(res.data.data.results)
      })
    },
    // 处理自动刷新功能:10秒刷新一次
    handleAutoRefresh (status) {
      if (status === true) {
        this.refreshFunc = setInterval(() => {
          this.page = 1
          this.getContestRankData(1, true)
        }, 10000)
      } else {
        clearInterval(this.refreshFunc)
      }
    }
  },
  // 通过映射获取当前用户是否是比赛管理员,如果是就更改状态阶段state
  computed: {
    ...mapGetters(['isContestAdmin']),
    ...mapState({
      'contest': state => state.contest.contest,
      'contestProblems': state => state.contest.contestProblems
    }),
    // 通过表格显示数据,先获取数据保存到本地缓存然后显示
    showChart: {
      get () {
        return this.$store.state.contest.itemVisible.chart
      },
      set (value) {
        this.$store.commit(types.CHANGE_CONTEST_ITEM_VISIBLE, {chart: value})
      }
    },
    // 获取保存显示菜单表格
    showMenu: {
      get () {
        return this.$store.state.contest.itemVisible.menu
      },
      set (value) {
        this.$store.commit(types.CHANGE_CONTEST_ITEM_VISIBLE, {menu: value})
        this.$nextTick(() => {
          if (this.showChart) {
            this.$refs.chart.resize()
          }
          this.$refs.tableRank.handleResize()
        })
      }
    },
    // 获取显示显示真实姓名
    showRealName: {
      get () {
        return this.$store.state.contest.itemVisible.realName
      },
      set (value) {
        this.$store.commit(types.CHANGE_CONTEST_ITEM_VISIBLE, {realName: value})
        if (value) {
          this.columns.splice(2, 0, {
            title: 'RealName',
            align: 'center',
            width: '150px',
            render: (h, {row}) => {
              return h('span', row.user.real_name)
            }
          })
        } else {
          this.columns.splice(2, 1)
        }
      }
    },
    // 获取强制更新数据,保存强制更新数据
    forceUpdate: {
      get () {
        return this.$store.state.contest.forceUpdate
      },
      set (value) {
        this.$store.commit(types.CHANGE_RANK_FORCE_UPDATE, {value: value})
      }
    },
    // 获取比赛排名限制,并保存
    limit: {
      get () {
        return this.$store.state.contest.rankLimit
      },
      set (value) {
        this.$store.commit(types.CHANGE_CONTEST_RANK_LIMIT, {rankLimit: value})
      }
    },
    // 比赛结束之后刷新一下状态并返回,管理员才能做
    refreshDisabled () {
      return this.contest.status === CONTEST_STATUS.ENDED
    }
  },
  // 销毁之刷新一下refreshFunc排名数据
  beforeDestroy () {
    clearInterval(this.refreshFunc)
  }
}

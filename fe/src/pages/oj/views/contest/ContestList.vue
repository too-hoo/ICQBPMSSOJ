<template>
  <Row type="flex">
    <Col :span="24">
    <Panel id="contest-card" shadow>
      <div slot="title">{{query.rule_type === '' ? '全部' : query.rule_type}} 比赛列表</div>
      <!--和标题并列的右边附加信息,使用插槽的方式插入-->
      <div slot="extra">
        <ul class="filter">
          <li>
            <Dropdown @on-click="onRuleChange">
              <span>{{query.rule_type === '' ? '规则' : query.rule_type}}
                <Icon type="arrow-down-b"></Icon>
              </span>
              <Dropdown-menu slot="list">
                <Dropdown-item name="">全部</Dropdown-item>
                <Dropdown-item name="OI">OI</Dropdown-item>
                <Dropdown-item name="ACM">ACM</Dropdown-item>
              </Dropdown-menu>
            </Dropdown>
          </li>
          <li>
            <Dropdown @on-click="onStatusChange">
              <span>{{query.status === '' ? '状态' : CONTEST_STATUS_REVERSE[query.status].name}}
                <Icon type="arrow-down-b"></Icon>
              </span>
              <Dropdown-menu slot="list">
                <Dropdown-item name="">全部</Dropdown-item>
                <Dropdown-item name="0">正在进行</Dropdown-item>
                <Dropdown-item name="1">还没开始</Dropdown-item>
                <Dropdown-item name="-1">已经结束</Dropdown-item>
              </Dropdown-menu>
            </Dropdown>
          </li>
          <li>
            <Input id="keyword" @on-enter="changeRoute" @on-click="changeRoute" v-model="query.keyword"
                   icon="ios-search-strong" placeholder="输入关键字进行检索"/>
          </li>
        </ul>
      </div>
      <p id="no-contest" v-if="contests.length == 0">没有比赛</p>
      <!--按序列排序-->
      <ol id="contest-list">
        <li v-for="contest in contests" :key="contest.title">
          <!--每一行包含一张图片和两个的列(大的跨度18),列中包含主题,小锁,开始结束时间和比赛类型-->
          <Row type="flex" justify="space-between" align="middle">
            <img class="trophy" src="../../../../assets/Cup.png"/>
            <Col :span="18" class="contest-main">
            <p class="title">
              <a class="entry" @click.stop="goContest(contest)">
                {{contest.title}}
              </a>
              <template v-if="contest.contest_type != 'Public'">
                <Icon type="ios-locked-outline" size="20"></Icon>
              </template>
            </p>
            <ul class="detail">
              <li>
                <Icon type="calendar" color="#3091f2"></Icon>
                {{contest.start_time | localtime('YYYY-M-D HH:mm') }}
              </li>
              <li>
                <Icon type="android-time" color="#3091f2"></Icon>
                {{getDuration(contest.start_time, contest.end_time)}}
              </li>
              <li>
                <Button size="small" shape="circle" @click="onRuleChange(contest.rule_type)">
                  {{contest.rule_type}}
                </Button>
              </li>
            </ul>
            </Col>
            <!--小的跨度4,内置一个圆点标签,圆点颜色根据比赛的状态更改-->
            <Col :span="4" style="text-align: center">
            <Tag type="dot" :color="CONTEST_STATUS_REVERSE[contest.status].color">{{CONTEST_STATUS_REVERSE[contest.status].name}}</Tag>
            </Col>
          </Row>
        </li>
      </ol>
    </Panel>
    <Pagination :total="total"
                :pageSize="limit"
                @on-change="getContestList"
                :current.sync="page">
    </Pagination>
    </Col>
  </Row>

</template>

<script>
  import api from '@oj/api'
  import { mapGetters } from 'vuex'
  import utils from '@/utils/utils'
  import Pagination from '@/pages/oj/components/Pagination'
  import time from '@/utils/time'
  import { CONTEST_STATUS_REVERSE, CONTEST_TYPE } from '@/utils/constants'

  // 每页显示的比赛条目
  const limit = 5

  export default {
    name: 'contest-list',
    components: {
      Pagination
    },
    data () {
      return {
        page: 1,
        query: {
          status: '',
          keyword: '',
          rule_type: ''
        },
        limit: limit,
        total: 0,
        rows: '',
        contests: [],
        CONTEST_STATUS_REVERSE: CONTEST_STATUS_REVERSE,
//      for password modal use
        cur_contest_id: ''
      }
    },
    // 在路由进入的之前,首先获取比赛的列表数据
    beforeRouteEnter (to, from, next) {
      api.getContestList(0, limit).then((res) => {
        next((vm) => {
          vm.contests = res.data.data.results
          vm.total = res.data.data.total
        })
      }, (res) => {
        next()
      })
    },
    methods: {
      // 初始化数据:路由,路由状态,比赛规则,关键字,页码,获取比赛列表
      init () {
        let route = this.$route.query
        this.query.status = route.status || ''
        this.query.rule_type = route.rule_type || ''
        this.query.keyword = route.keyword || ''
        this.page = parseInt(route.page) || 1
        this.getContestList()
      },
      // 设置当前页码为1,获取比赛列表
      getContestList (page = 1) {
        let offset = (page - 1) * this.limit
        api.getContestList(offset, this.limit, this.query).then((res) => {
          this.contests = res.data.data.results
          this.total = res.data.data.total
        })
      },
      // 更改路由:过滤空的值
      changeRoute () {
        let query = Object.assign({}, this.query)
        query.page = this.page
        this.$router.push({
          name: 'contest-list',
          query: utils.filterEmptyValue(query)
        })
      },
      // 处理规则的变更:设置当前的页码为1,新规则为rule
      onRuleChange (rule) {
        this.query.rule_type = rule
        this.page = 1
        this.changeRoute()
      },
      // 处理状态的变更:设置当前页码为1,新规则为status
      onStatusChange (status) {
        this.query.status = status
        this.page = 1
        this.changeRoute()
      },
      // 进入比赛: 1首先获取端机的比赛ID,2判断比赛是否公开和用户是否经过验证(登录,具有参赛的密码),通过computed方法,
      // 3经过验证之后显示比赛的详细信息
      goContest (contest) {
        this.cur_contest_id = contest.id
        if (contest.contest_type !== CONTEST_TYPE.PUBLIC && !this.isAuthenticated) {
          this.$error('请先登录.')
          this.$store.dispatch('changeModalStatus', {visible: true})
        } else {
          this.$router.push({name: 'contest-details', params: {contestID: contest.id}})
        }
      },
      // 获取比赛的持续时间
      getDuration (startTime, endTime) {
        return time.duration(startTime, endTime)
      }
    },
    computed: {
      // 使用mapGetters映射的方式获取用户是否经过验证
      ...mapGetters(['isAuthenticated', 'user'])
    },
    // 监听路由的变化实现跳转和数据的初始化
    watch: {
      '$route' (newVal, oldVal) {
        if (newVal !== oldVal) {
          this.init()
        }
      }
    }

  }
</script>
<style lang="less" scoped>
  #contest-card {
    #keyword {
      width: 80%;
      margin-right: 30px;
    }
    #no-contest {
      text-align: center;
      font-size: 16px;
      padding: 20px;
    }
    #contest-list {
      > li {
        padding: 20px;
        border-bottom: 1px solid rgba(187, 187, 187, 0.5);
        list-style: none;

        .trophy {
          height: 40px;
          margin-left: 10px;
          margin-right: -20px;
        }
        .contest-main {
          .title {
            font-size: 18px;
            a.entry {
              color: #495060;
              &:hover {
                color: #2d8cf0;
                border-bottom: 1px solid #2d8cf0;
              }
            }
          }
          li {
            display: inline-block;
            padding: 10px 0 0 10px;
            &:first-child {
              padding: 10px 0 0 0;
            }
          }
        }
      }
    }
  }
</style>

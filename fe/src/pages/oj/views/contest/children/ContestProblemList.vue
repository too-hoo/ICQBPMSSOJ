<template>
  <div>
    <Panel>
      <div slot="title">{{$t('m.Problems_List')}}</div>
      <!--比赛题目列表:同样是使用js方式进行显示-->
      <Table v-if="contestRuleType == 'ACM' || OIContestRealTimePermission"
             :columns="ACMTableColumns"
             :data="problems"
             @on-row-click="goContestProblem"
             no-data-text="No Problems"></Table>
      <Table v-else
             :data="problems"
             :columns="OITableColumns"
             @on-row-click="goContestProblem"
             no-data-text="No Problems"></Table>
    </Panel>
  </div>
</template>

<script>
  import {mapState, mapGetters} from 'vuex'
  import {ProblemMixin} from '@oj/components/mixins'

  export default {
    name: 'ContestProblemList',
    mixins: [ProblemMixin],
    data () {
      return {
        ACMTableColumns: [
          {
            title: 'DisplayID',
            key: '_id',
            sortType: 'asc',
            width: 150
          },
          {
            title: '标 题',
            key: 'title'
          },
          {
            title: '总的提交数量',
            key: 'submission_number'
          },
          {
            title: 'AC通过率',
            render: (h, params) => {
              return h('span', this.getACRate(params.row.accepted_number, params.row.submission_number))
            }
          }
        ],
        OITableColumns: [
          {
            title: 'DisplayID',
            key: '_id',
            width: 150
          },
          {
            title: '标 题',
            key: 'title'
          }
        ]
      }
    },
    mounted () {
      this.getContestProblems()
    },
    methods: {
      // 获取比赛题目
      getContestProblems () {
        this.$store.dispatch('getContestProblems').then(res => {
          if (this.isAuthenticated) {
            if (this.contestRuleType === 'ACM') {
              this.addStatusColumn(this.ACMTableColumns, res.data.data)
            } else if (this.OIContestRealTimePermission) {
              this.addStatusColumn(this.ACMTableColumns, res.data.data)
            }
          }
        })
      },
      // 获取单条比赛题目详细信息
      goContestProblem (row) {
        this.$router.push({
          name: 'contest-problem-details',
          params: {
            contestID: this.$route.params.contestID,
            problemID: row._id
          }
        })
      }
    },
    // 根据映射计算属性,获取对应的属性
    computed: {
      ...mapState({
        problems: state => state.contest.contestProblems
      }),
      ...mapGetters(['isAuthenticated', 'contestRuleType', 'OIContestRealTimePermission'])
    }
  }
</script>

<style scoped lang="less">
</style>

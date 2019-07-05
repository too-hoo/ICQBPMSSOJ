<template>
  <Panel shadow>
    <div slot="title">{{ contest.title }}</div>
    <!--比赛附加元素-->
    <div slot="extra">
      <!--<screen-full :height="18" :width="18" class="screen-full"></screen-full>-->
      <Poptip trigger="hover" placement="left-start">
        <Icon type="android-settings" size="20"></Icon>
        <div slot="content" id="switches">
          <p>
            <span>右侧菜单</span>
            <i-switch v-model="showMenu"></i-switch>

          </p>
          <p>
            <span>自动刷新(10s)</span>
            <i-switch :disabled="refreshDisabled" @on-change="handleAutoRefresh"></i-switch>
          </p>
          <template v-if="isContestAdmin">
            <p>
              <span>真实姓名</span>
              <i-switch v-model="showRealName"></i-switch>
            </p>
            <p>
              <span>强制更新</span>
              <i-switch :disabled="refreshDisabled" v-model="forceUpdate"></i-switch>
            </p>
          </template>
          <template>
            <Button type="primary" size="small" @click="downloadRankCSV">下载csv统计表</Button>
          </template>
        </div>
      </Poptip>
    </div>
    <div v-show="showChart" class="echarts">
      <ECharts :options="options" ref="chart" auto-resize></ECharts>
    </div>
    <Table ref="tableRank" class="auto-resize" :columns="columns" :data="dataRank" disabled-hover></Table>
    <Pagination :total="total"
                :page-size.sync="limit"
                :current.sync="page"
                @on-change="getContestRankData"
                @on-page-size-change="getContestRankData(1)"
                show-sizer></Pagination>
  </Panel>
</template>
<script>
  import moment from 'moment'
  import { mapActions } from 'vuex'

  import Pagination from '@oj/components/Pagination'
  import ContestRankMixin from './contestRankMixin'
  import time from '@/utils/time'
  import utils from '@/utils/utils'

  export default {
    name: 'acm-contest-rank',
    components: {
      Pagination
    },
    mixins: [ContestRankMixin],
    data () {
      return {
        total: 0,
        page: 1,
        contestID: '',
        columns: [
          {
            title: 'ID',
            align: 'center',
            width: 60,
            render: (h, params) => {
              return h('span', {}, params.index + (this.page - 1) * this.limit + 1)
            }
          },
          {
            title: '用户',
            align: 'center',
            render: (h, params) => {
              return h('a', {
                style: {
                  display: 'inline-block',
                  'max-width': '150px'
                },
                on: {
                  click: () => {
                    this.$router.push(
                      {
                        name: 'user-home',
                        query: {username: params.row.user.username}
                      })
                  }
                }
              }, params.row.user.username)
            }
          },
          {
            title: 'AC / Total',
            align: 'center',
            width: 100,
            render: (h, params) => {
              return h('span', {}, [
                h('span', {}, params.row.accepted_number + ' / '),
                h('a', {
                  on: {
                    click: () => {
                      this.$router.push({
                        name: 'contest-submission-list',
                        query: {username: params.row.user.username}
                      })
                    }
                  }
                }, params.row.submission_number)
              ])
            }
          },
          {
            title: '总用时',
            align: 'center',
            render: (h, params) => {
              return h('span', this.parseTotalTime(params.row.total_time))
            }
          }
        ],
        dataRank: [],
        // 下面是统计表格的一些选项设置,其中的xlsx表格的数据依赖于统计图表
        options: {
          title: {
            text: 'Top 10 Teams',
            left: 'center'
          },
          dataZoom: [
            {
              type: 'inside',
              filterMode: 'none',
              xAxisIndex: [0],
              start: 0,
              end: 100
            }
          ],
          toolbox: {
            show: true,
            feature: {
              saveAsImage: {show: true, title: '保存为图片'}
            },
            right: '5%'
          },
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'cross',
              axis: 'x'
            }
          },
          legend: {
            orient: 'vertical',
            y: 'center',
            right: 0,
            data: [],
            formatter: (value) => {
              return utils.breakLongWords(value, 16)
            },
            textStyle: {
              fontSize: 12
            }
          },
          grid: {
            x: 80,
            x2: 200
          },
          xAxis: [{
            type: 'time',
            splitLine: false,
            axisPointer: {
              show: true,
              snap: true
            }
          }],
          yAxis: [
            {
              type: 'category',
              boundaryGap: false,
              data: [0]
            }],
          series: []
        }
      }
    },
    // 加载完成html之后开始初始化数据:contestID,比赛排名数据,同事设置表格的数据和chart的数据
    mounted () {
      this.contestID = this.$route.params.contestID
      this.getContestRankData(1)
      if (this.contestProblems.length === 0) {
        this.getContestProblems().then((res) => {
          this.addTableColumns(res.data.data)
          this.addChartCategory(res.data.data)
        })
      } else {
        this.addTableColumns(this.contestProblems)
        this.addChartCategory(this.contestProblems)
      }
    },
    methods: {
      ...mapActions(['getContestProblems']),
      // 将比赛的题目数据添加到ChartCategory
      addChartCategory (contestProblems) {
        let category = []
        for (let i = 0; i <= contestProblems.length; ++i) {
          category.push(i)
        }
        this.options.yAxis[0].data = category
      },
      // 将排名数据显示到图表上面
      applyToChart (rankData) {
        let [users, seriesData] = [[], []]
        rankData.forEach(rank => {
          users.push(rank.user.username)
          let info = rank.submission_info
          // 提取出已AC题目的时间
          let timeData = []
          Object.keys(info).forEach(problemID => {
            if (info[problemID].is_ac) {
              timeData.push(info[problemID].ac_time)
            }
          })
          timeData.sort((a, b) => {
            return a - b
          })

          let data = []
          data.push([this.contest.start_time, 0])
          // index here can be regarded as stacked accepted number count.
          for (let [index, value] of timeData.entries()) {
            let realTime = moment(this.contest.start_time).add(value, 'seconds').format()
            data.push([realTime, index + 1])
          }
          seriesData.push({
            name: rank.user.username,
            type: 'line',
            data
          })
        })
        this.options.legend.data = users
        this.options.series = seriesData
      },
      // 将数据显示到xlsx表格上面
      applyToTable (data) {
        // deepcopy
        let dataRank = JSON.parse(JSON.stringify(data))
        // 从submission_info中取出相应的problem_id 放入到父object中,这么做主要是为了适应iview table的data格式
        // 见https://www.iviewui.com/components/table
        dataRank.forEach((rank, i) => {
          let info = rank.submission_info
          let cellClass = {}
          Object.keys(info).forEach(problemID => {
            dataRank[i][problemID] = info[problemID]
            dataRank[i][problemID].ac_time = time.secondFormat(dataRank[i][problemID].ac_time)
            let status = info[problemID]
            if (status.is_first_ac) {
              cellClass[problemID] = 'first-ac'
            } else if (status.is_ac) {
              cellClass[problemID] = 'ac'
            } else {
              cellClass[problemID] = 'wa'
            }
          })
          dataRank[i].cellClassName = cellClass
        })
        this.dataRank = dataRank
      },
      // 添加图表的列数据
      addTableColumns (problems) {
        // 根据题目添加table column
        problems.forEach(problem => {
          this.columns.push({
            align: 'center',
            key: problem.id,
            renderHeader: (h, params) => {
              return h('a', {
                'class': {
                  'emphasis': true
                },
                on: {
                  click: () => {
                    this.$router.push({
                      name: 'contest-problem-details',
                      params: {
                        contestID: this.contestID,
                        problemID: problem._id
                      }
                    })
                  }
                }
              }, problem._id)
            },
            render: (h, params) => {
              if (params.row[problem.id]) {
                let status = params.row[problem.id]
                let acTime, errorNumber
                if (status.is_ac) {
                  acTime = h('span', status.ac_time)
                }
                if (status.error_number !== 0) {
                  errorNumber = h('p', '(-' + status.error_number + ')')
                }
                return h('div', [acTime, errorNumber])
              }
            }
          })
        })
      },
      // 解析总用时
      parseTotalTime (totalTime) {
        let m = moment.duration(totalTime, 's')
        return [Math.floor(m.asHours()), m.minutes(), m.seconds()].join(':')
      },
      // 下载排名CSV表格
      downloadRankCSV () {
        utils.downloadFile(`contest_rank?download_csv=1&contest_id=${this.$route.params.contestID}&force_refrash=${this.forceUpdate ? '1' : '0'}`)
      }
    }
  }
</script>
<style scoped lang="less">
   /*设置表格的样式*/
  .echarts {
    margin: 20px auto;
    /*height: 400px;*/
    height: 0px;
    width: 98%;
  }

  .screen-full {
    margin-right: 8px;
  }

  #switches {
    p {
      margin-top: 5px;
      &:first-child {
        margin-top: 0;
      }
      span {
        margin-left: 8px;
      }
    }
  }
</style>

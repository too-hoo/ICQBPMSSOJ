<template>
  <Row type="flex" justify="space-around">
    <Col :span="20" id="status">
      <!--通过alert标签就可以控制每一行显示不同的数据了-->
      <Alert :type="status.type" showIcon>
        <span class="title">{{status.statusName}}</span>
        <div slot="desc" class="content">
          <template v-if="isCE">
            <pre>{{submission.statistic_info.err_info}}</pre>
          </template>
          <template v-else>
            <span>耗时: {{submission.statistic_info.time_cost | submissionTime}}</span>
            <span>内存: {{submission.statistic_info.memory_cost | submissionMemory}}</span>
            <span>语言: {{submission.language}}</span>
            <span>作者: {{submission.username}}</span>
          </template>
        </div>
      </Alert>
    </Col>

    <!--后台返info就显示出来， 权限控制放后台 -->
    <Col v-if="submission.info && !isCE" :span="20">
      <Table stripe :loading="loading" :disabled-hover="true" :columns="columns" :data="submission.info.data"></Table>
    </Col>

    <!--高光显示已经提交的代码-->
    <Col :span="20">
      <Highlight :code="submission.code" :language="submission.language" :border-color="status.color"></Highlight>
    </Col>
    <Col v-if="submission.can_unshare" :span="20">
      <div id="share-btn">
        <Button v-if="submission.shared"
                type="warning" size="large" @click="shareSubmission(false)">
          不分享
        </Button>
        <Button v-else
                type="primary" size="large" @click="shareSubmission(true)">
          分享
        </Button>
      </div>
    </Col>
  </Row>

</template>

<script>
  import api from '@oj/api'
  import {JUDGE_STATUS} from '@/utils/constants'
  import utils from '@/utils/utils'
  import Highlight from '@/pages/oj/components/Highlight'

  const baseColumn = [
    {
      title: 'ID',
      align: 'center',
      type: 'index'
    },
    {
      title: '状态',
      align: 'center',
      render: (h, params) => {
        return h('Tag', {
          props: {
            color: JUDGE_STATUS[params.row.result].color
          }
        }, JUDGE_STATUS[params.row.result].name)
      }
    },
    {
      title: '内存',
      align: 'center',
      render: (h, params) => {
        return h('span', utils.submissionMemoryFormat(params.row.memory))
      }
    },
    {
      title: '耗时',
      align: 'center',
      render: (h, params) => {
        return h('span', utils.submissionTimeFormat(params.row.cpu_time))
      }
    }
  ]
  const scoreColumn = [{
    title: '分数',
    align: 'center',
    key: 'score'
  }]
  const adminColumn = [
    {
      title: '真实用时',
      align: 'center',
      render: (h, params) => {
        return h('span', utils.submissionTimeFormat(params.row.real_time))
      }
    },
    {
      title: '信号',
      align: 'center',
      key: 'signal'
    }
  ]

  export default {
    name: 'submissionDetails',
    components: {
      Highlight
    },
    data () {
      return {
        columns: [],
        submission: {
          result: '0',
          code: '',
          info: {
            data: []
          },
          statistic_info: {
            time_cost: '',
            memory_cost: ''
          }
        },
        isConcat: false,
        loading: false
      }
    },
    mounted () {
      this.getSubmission()
    },
    methods: {
      // 获取提交信息
      getSubmission () {
        this.loading = true
        api.getSubmission(this.$route.params.id).then(res => {
          this.loading = false
          let data = res.data.data
          let columns = baseColumn
          if (data.info && data.info.data && !this.isConcat) {
            // score exist means the submission is OI problem submission
            if (data.info.data[0].score) {
              this.isConcat = true
              columns = columns.concat(scoreColumn)
            }
            if (this.isAdminRole) {
              this.isConcat = true
              columns = columns.concat(adminColumn)
            }
            this.columns = columns
          }
          this.submission = data
        }, () => {
          this.loading = false
        })
      },
      // 分享提交信息:当用户提交信息之后会返回一个评测结果,通过或者错误,用户可以选择分享代码和评测信息,
      // 游客不能查看,只有登录后注册用户才能查看分享信息,超级用户可以查看所有的未分享提交信息
      shareSubmission (shared) {
        let data = {id: this.submission.id, shared: shared}
        api.updateSubmission(data).then(res => {
          this.getSubmission()
          this.$success('Succeeded')
        }, () => {
        })
      }
    },
    // 计算属性
    computed: {
      status () {
        return {
          type: JUDGE_STATUS[this.submission.result].type,
          statusName: JUDGE_STATUS[this.submission.result].name,
          color: JUDGE_STATUS[this.submission.result].color
        }
      },
      isCE () {
        return this.submission.result === -2
      },
      isAdminRole () {
        return this.$store.getters.isAdminRole
      }
    }
  }
</script>

<style scoped lang="less">
  #status {
    .title {
      font-size: 20px;
    }
    .content {
      margin-top: 10px;
      font-size: 14px;
      span {
        margin-right: 10px;
      }
      pre {
        white-space: pre-wrap;
        word-wrap: break-word;
        word-break: break-all;
      }
    }
  }

  .admin-info {
    margin: 5px 0;
    &-content {
      font-size: 16px;
      padding: 10px;
    }
  }

  #share-btn {
    float: right;
    margin-top: 5px;
    margin-right: 10px;
  }

  pre {
    border: none;
    background: none;
  }
</style>

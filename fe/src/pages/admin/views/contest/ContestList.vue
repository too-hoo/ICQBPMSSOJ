<template>
  <div class="view">
    <Panel title="比赛列表">
      <div slot="header">
        <el-input
          v-model="keyword"
          prefix-icon="el-icon-search"
          placeholder="输入关键字检索">
        </el-input>
      </div>
      <el-table
        v-loading="loading"
        element-loading-text="loading"
        ref="table"
        :data="contestList"
        style="width: 100%">
        <el-table-column type="expand">
          <template slot-scope="props">
            <!--props.row代表的就是表格一行的数据,props改成scope也可以-->
            <p>开始时间:{{props.row.start_time | localtime}}</p>
            <p>结束时间:{{props.row.end_time | localtime}}</p>
            <p>创建时间:{{props.row.create_time | localtime}}</p>
            <p>创建者: {{props.row.created_by.username}}</p>
          </template>
        </el-table-column>
        <el-table-column
          prop="id"
          width="80"
          label="ID">
        </el-table-column>
        <el-table-column
          prop="title"
          label="标题">
        </el-table-column>
        <el-table-column
          label="规则类型"
          width="130">
          <template slot-scope="scope">
            <el-tag type="gray">{{scope.row.rule_type}}</el-tag>
          </template>
        </el-table-column>
        <el-table-column
          label="比赛类型"
          width="180">
          <template slot-scope="scope">
            <!--根据比赛类型选择按钮:公开为成功的绿色，保护为主要的蓝色-->
            <el-tag :type="scope.row.contest_type === 'Public' ? 'success' : 'primary'">
              {{ scope.row.contest_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          label="状态"
          width="130">
          <template slot-scope="scope">
            <!--根据状态选择不同的按钮，-1表示已经结束（红色），0表示正在进行（绿色），1表示还没开始（蓝色）-->
            <el-tag :type="scope.row.status === '-1' ? 'danger' : scope.row.status === '0' ? 'success' : 'primary'">
              {{ scope.row.status | contestStatus}}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          width="100"
          label="可见">
          <template slot-scope="scope">
            <el-switch v-model="scope.row.visible"
                        active-text=""
                        inactive-text=""
                        @change="handleVisibleSwitch(scope.row)">
            </el-switch>
          </template>
        </el-table-column>
        <el-table-column
          fixed="right"
          width="250"
          label="操作">
          <!--父组件通过prop传递数据给子组件，子组件触发事件给父组件。
          但父组件想在子组件上监听自己的click的话，需要加上native修饰符。
          如果单纯想要调用本层级的点击事件，直接使用@click=方法即可-->
          <div slot-scope="scope">
            <icon-btn name="编辑" icon="edit"
                      @click.native="goEdit(scope.row.id)"></icon-btn>
            <icon-btn name="题目" icon="list-ol"
                      @click.native="goContestProblemList(scope.row.id)"></icon-btn>
            <icon-btn name="比赛公告" icon="info-circle"
                      @click.native="goContestAnnouncement(scope.row.id)"></icon-btn>
            <icon-btn name="下载 Accepted Submissions" icon="download"
                      @click.native="openDownloadOptions(scope.row.id)"></icon-btn>
          </div>
        </el-table-column>
      </el-table>
      <div class="panel-options">
        <el-pagination
          class="page"
          layout="prev, pager, next"
          @current-change="currentChange"
          :page-size="pageSize"
          :total="total">
        </el-pagination>
      </div>
    </Panel>
    <!--先打开对话框询问一下-->
    <el-dialog title="下载比赛的提交信息"
               width="30%"
               :visible.sync="downloadDialogVisible">
      <el-switch v-model="excludeAdmin" active-text="不包括管理员的提交信息"></el-switch>
      <span slot="footer" class="dialog-footer">
        <el-button type="primary" @click="downloadSubmissions">确 定</el-button>
      </span>
    </el-dialog>
  </div>
</template>


<script>
  import api from '../../api.js'
  import utils from '@/utils/utils'
  import {CONTEST_STATUS_REVERSE} from '@/utils/constants'


  export default {
    name: 'ContestList',
    data () {
      return {
        pageSize: 10,
        total: 0,
        contestList: [],
        keyword: '',
        loading: false,
        excludeAdmin: true,
        currentPage: 1,
        currentId: 1,
        downloadDialogVisible: false
      }
    },
    mounted () {
      this.getContestList(this.currentPage)
    },
    // 过滤返回的比赛状态
    filters: {
      contestStatus (value) {
        return CONTEST_STATUS_REVERSE[value].name
      }
    },
    methods: {
      // 切换页码回调
      currentChange (page) {
        this.currentPage = page
        this.getContestList(page)
      },
      // 获取比赛列表
      getContestList (page) {
        this.loading = true
        api.getContestList((page - 1) * this.pageSize, this.pageSize, this.keyword).then(res => {
          // 首先是关闭加载,获取总的条目数,获取比赛列表数据
          this.loading = false
          this.total = res.data.data.total
          this.contestList = res.data.data.results
        }, res => {
          this.loading = false
        })
      },
      // 打开对话框进行下载选择：是否下载包含管理员的信息，
      // 然后跳转到下面的downloadSubmissions方法
      openDownloadOptions (contestId) {
        this.downloadDialogVisible = true
        this.currentId = contestId
      },
      // 下载提交信息:主要就是用户的提交的代码，下载ac的提交信息
      downloadSubmissions () {
        // 下载的信息去除管理员的提交信息
        let excludeAdmin = this.excludeAdmin ? '1' : '0'
        let url = `/admin/download_submissions?contest_id=${this.currentId}&exclude_admin=${excludeAdmin}`
        utils.downloadFile(url)
        // 当点击之后会关闭当前对话窗口，也可以不关闭，多次下载
        // this.downloadDialogVisible = false
      },
       // router的方法{get:function(){return this._routerRoot._router}
      // router 方法会根据名字进行跳转，跳转的时候push带上参数
      goEdit (contestId) {
        this.$router.push({name: 'edit-contest', params: {contestId}})
      },
      goContestAnnouncement (contestId) {
        this.$router.push({name: 'contest-announcement', params: {contestId}})
      },
      goContestProblemList (contestId) {
        this.$router.push({name: 'contest-problem-list', params: {contestId}})
      },
      handleVisibleSwitch (row) {
        api.editContest(row)
      }
    },
    watch: {
      'keyword' () {
        this.currentChange(1)
      }
    }
  }

</script>

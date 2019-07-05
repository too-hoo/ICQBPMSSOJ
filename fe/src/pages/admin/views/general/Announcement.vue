<template>
  <div class="announcement view">
    <!--Panel是用到了封装好的子组件,通过暴露出来的名称Panel来使用-->
    <Panel :title="$t('m.General_Announcement')">
      <div class="list">
        <el-table
          v-loading="loading"
          element-loading-text="loading"
          ref="table"
          :data="announcementList"
          style="width: 100%">
          <el-table-column
            width="100"
            prop="id"
            label="ID">
          </el-table-column>
          <el-table-column
            prop="title"
            label="主题">
          </el-table-column>
          <el-table-column
            prop="create_time"
            label="创建时间">
            <template slot-scope="scope">
              {{ scope.row.create_time | localtime }}
            </template>
          </el-table-column>
          <el-table-column
            prop="last_update_time"
            label="上次更新时间">
            <template slot-scope="scope">
              {{scope.row.last_update_time | localtime }}
            </template>
          </el-table-column>
          <el-table-column
            prop="created_by.username"
            label="作者">
          </el-table-column>
          <el-table-column
            width="100"
            prop="visible"
            label="是否可见">
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
            label="操作选项"
            width="200">
            <div slot-scope="scope">
              <!--打开创建新的公告的时候会有两种选择:有ID就是修改,没有ID就是新建-->
              <icon-btn name="Edit" icon="edit" @click.native="openAnnouncementDialog(scope.row.id)"></icon-btn>
              <icon-btn name="Delete" icon="trash" @click.native="deleteAnnouncement(scope.row.id)"></icon-btn>
            </div>
          </el-table-column>
        </el-table>
        <div class="panel-options">
          <el-button type="primary" plain size="small" @click="openAnnouncementDialog(null)" icon="el-icon-plus">新建</el-button>
          <!--el-pagination会继承组件的-->
          <!--子组件会通过$emit方法触发父组件的@函数,来更新-->
          <el-pagination
            v-if="!contestID"
            class="page"
            layout="prev, pager, next"
            @current-change="currentChange"
            :page-size="pageSize"
            :total="total">
          </el-pagination>
        </div>
      </div>
    </Panel>

    <!--对话框,公告标题在下面已经定义好-->
    <el-dialog :title="announcementDialogTitle" :visible.sync="showEditAnnouncementDialog"
                @open="onOpenEditDialog" :close-on-click-modal="false">
      <el-form label-position="top">
        <el-form-item :label="$t('m.Announcement_Title')" required>
          <el-input
            v-model="announcement.title"
            :placeholder="$t('m.Announcement_Title')"
            class="title-input">
          </el-input>
        </el-form-item>
        <el-form-item :label="$t('m.Announcement_Content')" required>
          <Simditor v-model="announcement.content"></Simditor>
        </el-form-item>
        <div class="visible-box">
          <span>{{$t('m.Announcement_Status')}}</span>
          <el-switch
            v-model="announcement.visible"
            active-text=""
            inactive-text="">
          </el-switch>
        </div>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <cancel @click.native="showEditAnnouncementDialog = false"></cancel>
        <save type="primary" @click.native="submitAnnouncement"></save>
      </span>
    </el-dialog>
  </div>
</template>

<script>
  import Simditor from '../../components/Simditor.vue'
  import api from '../../api.js'


  export default {
    name: 'Announcement',
    components: {
      Simditor
    },
    data () {
      return {
        contestID: '',
        // 显示编辑公告的对话框
        showEditAnnouncementDialog: false,
        // 公告列表
        announcementList: [],
        // 一页显示的公告数
        pageSize: 15,
        // 总的公告数
        total: 0,
        // 当前的公告ID
        currentAnnouncementId: null,
        mode: 'create',
        // 公告(new|edit) model
        announcement: {
          title: '',
          visible: true,
          content: ''
        },
        // 对话框标题
        announcementDialogTitle: '编辑公告',
        // 是否显示loading
        loading: true,
        // 当前页码
        currentPage: 0
      }
    },
    mounted () {
      // 初始化参数
      this.init()
    },
    methods: {
      init () {
        this.contestID = this.$route.params.contestId
        if (this.contestID) {
          this.getContestAnnouncementList()
        } else {
          // more获得第一页的公告列表
          this.getAnnouncementList(1)
        }
      },
      // 切换页面回调
      currentChange (page) {
        this.currentPage = page
        this.getAnnouncementList(page)
      },
      // 获取公告列表
      getAnnouncementList (page) {
        this.loading = true
        api.getAnnouncementList((page - 1) * this.pageSize, this.pageSize).then(res => {
          this.loading = false
          this.total = res.data.data.total
          this.announcementList = res.data.data.results
        }, res => {
          this.loading = false
        })
      },
      // 获取比赛公告列表;这里的公告是综合系统公告和比赛公告的了
      getContestAnnouncementList () {
        this.loading = true
        // 通过api获取到数据库里面的数据
        api.getContestAnnouncementList(this.contestID).then(res => {
          this.loading = false
          this.announcementList = res.data.data
        }).catch(() => {
          // 获取到数据之后,将加载关停
          this.loading = false
        })
      },
      // 打开编辑对话框的回调
      onOpenEditDialog () {
        // todo 优化
        // 解决 文本编辑器显示异常的bug
        setTimeout(() => {
          if (document.createEvent) {
            let event = document.createEvent('HTMLEvents')
            event.initEvent('resize', true, true)
            window.dispatchEvent(event)
          } else if (document.createEventObject) {
            window.fireEvent('onresize')
          }
        }, 0)
      },
      // 提交编辑
      // 默认传入MouseEvent
      submitAnnouncement (data = undefined) {
        let funcName = ''
        // 初始化数据
        if (!data.title) {
          data = {
            id: this.currentAnnouncementId,
            title: this.announcement.title,
            content: this.announcement.content,
            visible: this.announcement.visible
          }
        }
        // 根据比赛ID是否为空,判断对应的公告操作
        if (this.contestID) {
          data.contest_id = this.contestID
          funcName = this.mode === 'edit' ? 'updateContestAnnouncement' : 'createContestAnnouncement'
        } else {
          funcName = this.mode === 'edit' ? 'updateAnnouncement' : 'createAnnouncement'
        }
        api[funcName](data).then(res => {
          this.showEditAnnouncementDialog = false
          this.init()
        }).catch()
      },
      // 删除公告
      deleteAnnouncement (announcementId) {
        this.$confirm('你确定想要删除这条公告吗?', '警告', {
          confirmButtonText: '删除',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          this.loading = true
          let funcName = this.contestID ? 'deleteContestAnnouncement' : 'deleteAnnouncement'
          // API根据上面的funcName来选择不同的方法去请求后端数据
          api[funcName](announcementId).then(res => {
            this.loading = true
            this.init()
          })
        }).catch(() => {
          this.loading = true
        })
      },
      // 打开公告对话框,打开创建新的公告的时候会有两种选择:有ID就是修改,没有ID就是新建
      openAnnouncementDialog (id) {
        this.showEditAnnouncementDialog = true
        if (id !== null) {
          this.currentAnnouncementId = id
          this.announcementDialogTitle = '编辑公告'
          this.announcementList.find(item => {
            if (item.id === this.currentAnnouncementId) {
              this.announcement.title = item.title
              this.announcement.visible = item.visible
              this.announcement.content = item.content
              this.mode = 'edit'
            }
          })
        } else {
          this.announcementDialogTitle = '创建公告'
          this.announcement.title = ''
          this.announcement.visible = true
          this.announcement.content = ''
          this.mode = 'create'
        }
      },
      // 处理是否可见开关
      handleVisibleSwitch (row) {
        this.mode = 'edit'
        this.submitAnnouncement({
          id: row.id,
          title: row.title,
          content: row.content,
          visible: row.visible
        })
      }
    },
    // 监听器
    watch: {
      $route () {
        this.init()
      }
    }
  }


</script>

<style lang="less" scoped>
  .title-input {
    margin-bottom: 20px;
  }
  /*是否可见按钮的样式*/
  .visible-box {
    margin-top: 10px;
    width: 205px;
    float: left;
  }
</style>

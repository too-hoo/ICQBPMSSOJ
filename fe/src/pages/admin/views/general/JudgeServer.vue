<template>
  <div class="view">
    <Panel :title="$t('m.Judge_Server_Token')">
      <code>{{ token }}</code>
    </Panel>
    <Panel :title="$t('m.Judge_Server_Info')">
      <el-table
        :data="servers"
        :default-expand-all="true"
        border>
        <el-table-column
          type="expand">
          <!--这是一个下拉列表,以一个乡下的尖尖标识-->
          <template slot-scope="props">
            <p>{{$t('m.IP')}}:
              <el-tag type="success">{{ props.row.ip }}</el-tag>
              {{$t('m.Judger_Version')}}
              <el-tag type="success">{{ props.row.judger_version }}</el-tag>
            </p>
            <p>{{$t('m.Service_URL')}}:<code>{{props.row.service_url}}</code></p>
            <p>{{$t('m.Last_Heartbeat')}}: {{ props.row.last_heartbeat | localtime}}</p>
            <p>{{$t('m.Create_Time')}}.{{props.row.create_time | loacltime}}</p>
          </template>
        </el-table-column>
        <el-table-column
          prop="status"
          label="状态">
          <template slot-scope="scope">
            <el-tag
              :type="scope.row.status === 'normal' ? 'success' : 'danger'">
              {{ scope.row.status === 'normal' ? 'Normal' : 'Abnormal'}}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="hostname"
          label="主机名">
        </el-table-column>
        <el-table-column
          prop="task_number"
          label="任务数">
        </el-table-column>
        <el-table-column
          prop="cpu_core"
          label="CPU核数">
        </el-table-column>
        <el-table-column
          prop="cpu_usage"
          label="CPU使用率">
          <template slot-scope="scope">{{ scope.row.cpu_usage }}%</template>
        </el-table-column>
        <el-table-column
          prop="memory_usage"
          label="内存使用率">
          <template slot-scope="scope">{{ scope.row.memory_usage }}%</template>
        </el-table-column>
        <el-table-column label="是否可用">
          <template slot-scope="{row}">
            <el-switch v-model="row.is_disabled" @change="handleDisabledSwitch(row.id, row.is_disabled)"></el-switch>
          </template>
        </el-table-column>
        <el-table-column
          fixed="right"
          label="操作选项">
          <template slot-scope="scope">
            <icon-btn name="Delete" icon="trash" @click.native="deleteJudgeServer(scope.row.hostname)"></icon-btn>
          </template>
        </el-table-column>
      </el-table>
    </Panel>
  </div>
</template>


<script>
  import api from '../../api.js'
  // import api from '../../api.js'

  export default {
    name: 'JudgeServer',
    data () {
      return {
        servers: [],
        token: '',
        intervalId: -1
      }
    },
    // 每隔5秒就刷新一下判题服务器的状态
    mounted () {
      this.refreshJudgeServerList()
      this.intervalId = setInterval(() => {
        this.refreshJudgeServerList()
      }, 5000)
    },
    methods: {
      refreshJudgeServerList () {
        api.getJudgeServer().then(res => {
          this.servers = res.data.data.servers
          this.token = res.data.data.token
        })
      },
      deleteJudgeServer (hostname) {
        this.$confirm('如果你删除这个Judge Server, 就要等到下一次心跳时才能使用Judge Server', '警告', {
          confirmButtonText: '删除',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          api.deleteJudgeServer(hostname).then(res =>
            this.refreshJudgeServerList()
          )
        }).catch(() => {
        })
      },
      // 处理开关按钮事件,直接将开关的值传到后台,然后更新数据库
      handleDisabledSwitch (id, value) {
        let data = {
          id,
          is_disabled: value
        }
        api.updateJudgeServer(data).catch(() => {})
      }
    },
    // 路由跳转之前清除一下Interval
    beforeRouteLeave (to, from, next) {
      clearInterval(this.intervalId)
      next()
    }
  }

</script>

<template>
  <div>
    <div style="padding-bottom: 10px;">
    </div>
    <panel title="导出题目">
      <div slot="header">
        <!--按照关键字检索-->
        <el-input
          v-model="keyword"
          prefix-icon="el-icon-search"
          placeholder="Keywords">
        </el-input>
      </div>
      <el-table :data="problems"
                v-loading="loadingProblems" @selection-change="handleSelectionChange">
        <el-table-column
          type="selection"
          width="60">
        </el-table-column>
        <el-table-column
          label="ID"
          width="100"
          prop="id">
        </el-table-column>
        <el-table-column
          label="DisplayID"
          width="200"
          prop="_id">
        </el-table-column>
        <el-table-column
          label="标题"
          prop="title">
        </el-table-column>
        <el-table-column
          prop="created_by.username"
          label="作者">
        </el-table-column>
        <el-table-column
          prop="create_time"
          label="创建时间">
          <template slot-scope="scope">
            {{scope.row.create_time | localtime}}
          </template>
        </el-table-column>
      </el-table>

      <div class="panel-options">
        <el-button type="primary" size="small" v-show="selected_problems.length"
                    @click="exportProblems" icon="el-icon-fa-arrow-down">导出
        </el-button>
        <el-pagination
          class="page"
          layout="prev, pager, next"
          @current-change="getProblems"
          :page-size="limit"
          :total="total">
        </el-pagination>
      </div>
    </panel>

    <panel title="本地导入题目">
      <el-upload
        ref="QDU"
        action="/api/admin/import_problem"
        name="file"
        :file-list="fileList1"
        :show-file-list="true"
        :with-credentials="true"
        :limit="3"
        :on-change="onFile1Change"
        :auto-upload="false"
        :on-success="uploadSucceeded"
        :on-error="uploadFailed">
        <el-button size="small" type="primary" icon="el-icon-fa-upload" slot="trigger">选择文件</el-button>
        <el-button style="margin-left: 10px;" size="small" type="success" @click="submitUpload('QDU')">上传</el-button>
      </el-upload>
    </panel>
    <!--FPS上传的功能先放下-->
  </div>
</template>


<script>
  import api from '@admin/api'
  import utils from '@/utils/utils'



  export default {
    name: 'import_and_export',
    data () {
      return {
        fileList1: [],
        fileList2: [],
        page: 1,
        limit: 10,
        total: 0,
        loadingProblems: false,
        loadingImporting: false,
        keyword: '',
        problems: [],
        selected_problems: []
      }
    },
    mounted () {
      this.getProblems()
    },
    methods: {
      // 处理选择更改的情况
      handleSelectionChange (val) {
        this.selected_problems = val
      },
      getProblems (page = 1) {
        let params = {
          keyword: this.keyword,
          offset: (page - 1) * this.limit,
          limit: this.limit
        }
        this.loadingProblems = true
        api.getProblemList(params).then(res => {
          this.problems = res.data.data.results
          this.total = res.data.data.total
          this.loadingProblems = false
        })
      },
      exportProblems () {
        let params = []
        for (let p of this.selected_problems) {
          params.push('problem_id=' + p.id)
        }
        // 将选中的id分别链接起来再传到后台
        let url = '/admin/export_problem?' + params.join('&')
        utils.downloadFile(url)
      },
      submitUpload (ref) {
        this.$refs[ref].submit()
      },
      onFile1Change (file, fileList) {
        this.fileList1 = fileList.slice(-1)
      },
      onFile2Change (file, fileList) {
        this.fileList2 = fileList.slice(-1)
      },
      uploadSucceeded (response) {
        if (response.error) {
          this.$error(response.data)
        } else {
          this.$success('成功导入' + response.data.import_count + ' problems')
          this.getProblems()
        }
      },
      uploadFailed () {
        this.$error('上传失败!')
      }
    },
    // 监听器监听keyword的变化然后做出相应的更新
    watch: {
      'keyword' () {
        this.getProblems()
      }
    }
  }

</script>

<style scoped lang="less">

</style>

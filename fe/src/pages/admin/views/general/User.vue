<template>
  <div class="view">
    <Panel :title="$t('m.User_User')">
      <div slot="header">
        <el-row :gutter="20">
          <el-col :span="8">
            <!--这个按钮是在选择到删除用户的时候才会显示-->
            <el-button v-show="selectedUsers.length"
                       type="warning" icon="el-icon-fa-trash"
                       @click="deleteUsers(selectedUserIDs)">删除
            </el-button>
          </el-col>
          <el-col :span="selectedUsers.length ? 16: 24">
            <el-input v-model="keyword" prefix-icon="el-icon-search" placeholder="输入关键字检索"></el-input>
          </el-col>
        </el-row>
      </div>
      <el-table
        v-loading="loadingTable"
        element-loading-text="loading"
        @selection-change="handleSelectionChange"
        ref="table"
        :data="userList"
        style="width: 100%">
        <!--在表头加上@selection-change="handleSelectionChange" 就说明有一个多选框了-->
        <el-table-column type="selection" width="55"></el-table-column>

        <el-table-column prop="id" label="ID"></el-table-column>

        <el-table-column prop="username" label="用户名"></el-table-column>

        <el-table-column prop="create_time" label="创建时间">
          <template slot-scope="scope">
            {{scope.row.create_time | localtime}}
          </template>
        </el-table-column>

        <el-table-column prop="last_login" label="上一次登录时间">
          <template slot-scope="scope">
            {{scope.row.last_login | localtime}}
          </template>
        </el-table-column>

        <el-table-column prop="real_name" label="真实姓名"></el-table-column>

        <el-table-column prop="email" label="电子邮箱"></el-table-column>

        <el-table-column prop="admin_type" label="用户类型">
          <template slot-scope="scope">
            {{ scope.row.admin_type}}
          </template>
        </el-table-column>

        <el-table-column fixed="right" label="操作选项" width="150">
          <template slot-scope="{row}">
            <icon-btn name="Edit" icon="edit" @click.native="openUserDialog(row.id)"></icon-btn>
            <icon-btn name="Delete" icon="trash" @click.native="deleteUsers([row.id])"></icon-btn>
          </template>
        </el-table-column>
      </el-table>
      <!--表格下面是分页组件-->
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

    <Panel>
      <span slot="title">{{$t('m.Import_User')}}
        <el-popover placement="right" trigger="hover">
          <p>只支持CSV格式的文件，且文件不带文件头的格式<a></a></p>
          <i slot="reference" class="el-icon-fa-question-circle import-user-icon"></i>
        </el-popover>
      </span>
      <!--:show-file-list="false" 显示导入的用户列表-->
      <el-upload v-if="!uploadUsers.length"
                  action=""
                  :show-file-list="false"
                  accept=".csv"
                  :before-upload="handleUsersCSV">
        <el-button size="small" icon="el-icon-fa-upload" type="primary">选择文件</el-button>
      </el-upload>
      <template v-else>
        <el-table :data="uploadUsersPage">
          <el-table-column label="Username">
            <template slot-scope="{row}">
              {{row[0]}}
            </template>
          </el-table-column>
          <el-table-column label="Password">
            <template slot-scope="{row}">
              {{row[1]}}
            </template>
          </el-table-column>
          <el-table-column label="Email">
            <template slot-scope="{row}">
              {{row[2]}}
            </template>
          </el-table-column>
        </el-table>
        <div class="panel-options">
          <el-button type="primary" size="small"
                      icon="el-icon-fa-upload"
                      @click="handleUsersUpload">导入所有
          </el-button>
          <el-button type="warning" size="small"
                      icon="el-icon-fa-undo"
                      @click="handleResetData"></el-button>
          <!--导入数据的分页显示，默认设置显示15条，当前页为第一页，上传的总用户为total-->
          <el-pagination
            class="page"
            layout="prev, pager, next"
            :page-size="uploadUsersPageSize"
            :current-page.sync="uploadUsersCurrentPage"
            :total="uploadUsers.length">
          </el-pagination>
        </div>
      </template>
    </Panel>

    <Panel :title="$t('m.Generate_User')">
      <el-form :model="formGenerateUser" ref="formGenerateUser">
        <!--布局样式为flex，中间使用空格隔开,总共占20格，留下4格当做空格-->
        <el-row type="flex" justify="space-between">
          <el-col :span="4">
            <el-form-item label="前缀" prop="prefix">
              <el-input v-model="formGenerateUser.prefix" placeholder="请输入前缀" ></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label="后缀" prop="suffix">
              <el-input v-model="formGenerateUser.suffix" placeholder="请输入后缀"></el-input>
            </el-form-item>
          </el-col>
          <!--el-input-number是一个输入数字的标签-->
          <el-col :span="4">
            <el-form-item label="起始值" prop="number_from" required>
              <el-input-number v-model="formGenerateUser.number_from" style="width: 100%"></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label="结束值" prop="number_to" required>
              <el-input-number v-model="formGenerateUser.number_to" style="width: 100%"></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label="密码长度" prop="password_length" required>
              <el-input v-model="formGenerateUser.password_length"
                        placeholder="请设置密码的长度"></el-input>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <el-button type="primary" @click="generateUser" icon="el-icon-fa-users" :loading="loadingGenerate">生成并导出
          </el-button>
          <!--一定要细致到每个代码，如果开始数值大于结束数值那么全局消息就提示返回的错误消息-->
          <span class="userPreview" v-if="formGenerateUser.number_from && formGenerateUser.number_to &&
                                          formGenerateUser.number_from <= formGenerateUser.number_to">
            用户名将设置为{{formGenerateUser.prefix + formGenerateUser.number_from + formGenerateUser.suffix}},
            <span v-if="formGenerateUser.number_from + 1 < formGenerateUser.number_to">
              {{formGenerateUser.prefix + (formGenerateUser.number_from + 1) + formGenerateUser.suffix + '...'}}
            </span>
            <span v-if="formGenerateUser.number_from + 1 <= formGenerateUser.number_to">
              {{formGenerateUser.prefix + formGenerateUser.number_to + formGenerateUser.suffix}}
            </span>
          </span>
        </el-form-item>

      </el-form>
    </Panel>
    <!--修改用户信息对话框-->
    <el-dialog :title="$t('m.User_Info')" :visible.sync="showUserDialog" :close-on-click-modal="false">
      <!--设置标签显示在做左边，另外表格中使用的user已经在表头以model的形式提供出来-->
      <el-form :model="user" label-width="120px" label-position="left">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="$t('m.User_Username')" required>
              <el-input v-model="user.username"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('m.User_Real_Name')" required>
              <el-input v-model="user.real_name"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('m.User_Email')" required>
              <el-input v-model="user.email"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('m.User_New_Password')">
              <el-input v-model="user.password"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('m.User_Type')">
              <el-select v-model="user.admin_type">
                <el-option label="Regular User" value="Regular User"></el-option>
                <el-option label="Admin" value="Admin"></el-option>
                <el-option label="Super Admin" value="Super Admin"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('m.Problem_Permission')">
              <el-select v-model="user.problem_permission" :disabled="user.admin_type!=='Admin'">
                <el-option label="None" value="None"></el-option>
                <el-option label="Own" value="Own"></el-option>
                <el-option label="All" value="All"></el-option>
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="24">
            <!--账户是否可用-->
            <el-form-item :label="$t('m.Is_Disabled')">
              <el-switch
                v-model="user.is_disabled"
                active-text=""
                inactive-text="">
              </el-switch>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <cancel @click.native="showUserDialog = false">取消</cancel>
        <save @click.native="saveUser()">保存</save>
      </span>
    </el-dialog>
  </div>
</template>


<script>
  import papa from 'papaparse'
  import api from '../../api.js'
  import utils from '@/utils/utils'

export default {
    name: 'User',
    data () {
      return {
        // 一页显示的用户数
        pageSize: 10,
        // 总的用户数
        total: 0,
        // 用户列表
        userList: [],
        uploadUsers: [],
        uploadUsersPage: [],
        uploadUsersCurrentPage: 1,
        uploadUsersPageSize: 15,
        // 搜索关键字
        keyword: '',
        // 是否显示用户对话框
        showUserDialog: false,
        // 当前用户model
        user: {},
        loadingTable: false,
        loadingGenerate: false,
        // 当前页码
        currentPage: 0,
        selectedUsers: [],
        // 自动产生用户结构体参数
        formGenerateUser: {
          prefix: '',
          suffix: '',
          number_from: 0,
          number_to: 0,
          password_length: 8
        }
      }
    },
    mounted () {
      // 调用getUserList方法，进而从api中获得用户列表
      this.getUserList(1)
    },
    methods: {
      // 切换页码回调
      currentChange (page) {
        this.currentPage = page
        this.getUserList(page)
      },
      // 提交修改用户的信息
      saveUser () {
        api.editUser(this.user).then(res => {
          // 更新页面列表
          this.getUserList(this.currentPage)
        }).then(() => {
          // 更新完后关闭对话框
          this.showUserDialog = false
        }).catch(() => {
        })
      },
      // 打开用户对话框
      openUserDialog (id) {
        this.showUserDialog = true
        api.getUser(id).then(res => {
          this.user = res.data.data
          this.user.password = ''
          this.user.real_tfa = this.user.two_factor_auth
        })
      },
      // 获取用户列表
      getUserList (page) {
        this.loadingTable = true
        api.getUserList((page - 1) * this.pageSize, this.pageSize, this.keyword).then(res => {
          this.loadingTable = false
          // 获取用户总数和将查询出来的结果放到用户列表中去, 大小写必须区分
          this.total = res.data.data.total
          this.userList = res.data.data.results
        }, res => {
          this.loadingTable = false
        })
      },
      // 删除用户
      deleteUsers (ids) {
        this.$confirm('确定要删除这个用户吗？', 'confirm', {
          type: 'warning'
        }).then(() => {
          api.deleteUsers(ids.join(',')).then(res => {
            this.getUserList(this.currentPage)
          }).catch(() => {
            this.getUserList(this.currentPage)
          })
        }, () => {
        })
      },
      // 处理选择更改
      handleSelectionChange (val) {
        this.selectedUsers = val
      },
      // 批量产生用户
      generateUser () {
        this.$refs['formGenerateUser'].validate((valid) => {
          if (!valid) {
            this.$error('请先验证错误的字段值')
            return
          }
          this.loadingGenerate = true
          let data = Object.assign({}, this.formGenerateUser)
          api.generateUser(data).then(res => {
            this.loadingGenerate = false
            let url = '/admin/generate_user?file_id=' + res.data.data.file_id
            utils.downloadFile(url).then(() => {
              this.$alert('所有的用户已经全部创建成功，用户名单已经下载到你的硬盘。', 'Notice')
            })
            this.getUserList(1)
          }).catch(() => {
            this.loadingGenerate = false
          })
        })
      },
      // 导入用户CSV文件并处理
      handleUsersCSV (file) {
        papa.parse(file, {
          complete: (results) => {
            let data = results.data.filter(user => {
              return user[0] && user[1] && user[2]
            })
            let delta = results.data.length - data.length
            if (delta > 0) {
              this.$warning(delta + ' 由于空的值，用户已经被过滤掉')
            }
            this.uploadUsersCurrentPage = 1
            this.uploadUsers = data
            this.uploadUsersPage = data.slice(0, this.uploadUsersPageSize)
          },
          error: (error) => {
            this.$error(error)
          }
        })
      },
      // 处理当用户上传csv文件的时候，将文件的内容解析出来
      handleUsersUpload () {
        api.importUsers(this.uploadUsers).then(res => {
          this.getUserList(1)
          this.handleResetData()
        }).catch(() => {
        })
      },
      // 处理当出现问题时候，放弃导入文件的用户的逻辑
      handleResetData () {
        this.uploadUsers = []
      }
    },
    computed: {
      selectedUserIDs () {
        // 将选择到的用户的id以列表的形式存放到ids列表中
        let ids = []
        for (let user of this.selectedUsers) {
          ids.push(user.id)
        }
        return ids
      }
    },
    watch: {
      // 监听属性
      'keyword' () {
        this.currentChange(1)
      },
      // 根据用户选择然后做出相应的更改
      'user.admin_type' () {
        if (this.user.admin_type === 'Super_Admin') {
          this.user.problem_permission = 'All'
        } else if (this.user.admin_type === 'Regular User') {
          this.user.problem_permission = 'None'
        }
      },
      'uploadUsersCurrentPage' (page) {
        this.uploadUsersPage = this.uploadUsers.slice((page - 1) * this.uploadUsersPageSize, page * this.uploadUsersPageSize)
      }
    }
  }

</script>

<style scoped lang="less">
  .import-user-icon {
    color: #555555;
    margin-left: 4px;
  }

  .userPreview {
    padding-left: 10px;
  }

  .notification {
    p {
      margin: 0;
      text-align: left;
    }
  }
</style>

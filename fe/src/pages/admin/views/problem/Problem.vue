<template>
  <div class="problem">
    <Panel :title="title">
      <el-form ref="form" :model="problem" :rules="rules" label-position="top" label-width="70px">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-form-item prop="_id" :label="$t('m.Display_ID')"
                          :required="this.routeName === 'create-contest-problem' || this.routeName === 'edit-contet-problem'">
              <el-input :placeholder="$t('m.Display_ID')" v-model="problem._id"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="18">
            <el-form-item prop="title" :label="$t('m.Title')" required>
              <el-input :placeholder="$t('m.Title')" v-model="problem.title"></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item prop="description" :label="$t('m.Description')" required>
              <Simditor v-model="problem.description"></Simditor>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item prop="input_description" :label="$t('m.Input_Description')" required>
              <Simditor v-model="problem.input_description"></Simditor>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item prop="output_description" :label="$t('m.Output_Description')" required>
              <Simditor v-model="problem.output_description"></Simditor>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item :label="$t('m.Time_Limit') + '(ms)'" required>
              <el-input type="Number" :placeholder="$t('m.Time_Limit')" v-model="problem.time_limit"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item :label="$t('m.Memory_limit') + '(MB)'" required>
              <el-input type="Number" :placeholder="$t('m.Memory_limit')" v-model="problem.memory_limit"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item :label="$t('m.Difficulty')">
              <el-select class="difficulty-select" size="small" :placeholder="$t('m.Difficulty')" v-model="problem.difficulty">
                <el-option label="Low" value="Low"></el-option>
                <el-option label="Mid" value="Mid"></el-option>
                <el-option label="High" value="High"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="6">
            <el-form-item :label="$t('m.Visible')">
              <el-switch
                v-model="problem.visible"
                active-text=""
                inactive-text="">
              </el-switch>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Tag" :error="error.tags" required>
              <span class="tags">
                <el-tag
                  v-for="tag in problem.tags"
                  :closable="true"
                  :close-transition="false"
                  :key="tag"
                  type="success"
                  @close="closeTag(tag)"
                >{{tag}}</el-tag>
              </span>
              <el-autocomplete
                v-if="inputVisible"
                size="mini"
                class="input-new-tag"
                v-model="tagInput"
                :trigger-on-focus="false"
                @keyup.enter.native="addTag"
                @blur="addTag"
                @select="addTag"
                :fatch-suggestions="querySearch">
              </el-autocomplete>
              <el-button class="button-new-tag" v-else size="small" @click="inputVisible = true">+ 新标签</el-button>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item :label="$t('m.Languages')" :error="error.languages" required>
              <el-checkbox-group v-model="problem.languages">
                <el-tooltip class="spj-radio" v-for="lang in allLanguage.languages" :key="'spj' + lang.name" effect="dark"
                            :content="lang.description" placement="top-start">
                  <el-checkbox :label="lang.name"></el-checkbox>
                </el-tooltip>
              </el-checkbox-group>
            </el-form-item>
          </el-col>
        </el-row>
        <div>
          <el-form-item v-for="(sample, index) in problem.samples" :key="'sample'+index">
            <Accordion :title="'样例' + (index + 1)">
              <!--使用插槽将删除按钮插入到头部的右边-->
              <el-button type="warning" size="samll" icon="el-icon-delete" slot="header" @click="deleteSample(index)">
                删除
              </el-button>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item :label="$t('m.Input_Samples')" required>
                    <el-input
                      :row="5"
                      type="textarea"
                      :placeholder="$t('m.Input_Samples')"
                      v-model="sample.input">
                    </el-input>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item :label="$t('m.Output_Samples')" required>
                    <el-input
                      :row="5"
                      type="textarea"
                      :placeholder="$t('m.Output_Samples')"
                      v-model="sample.output">
                    </el-input>
                  </el-form-item>
                </el-col>
              </el-row>
            </Accordion>
          </el-form-item>
        </div>
        <div class="add-sample-btn">
          <button type="button" class="add-samples" @click="addSample()"><i class="el-icon-plus"></i>{{$t('m.Add_Sample')}}
          </button>
        </div>
        <el-form-item style="margin-top: 20px" :label="$t('m.Hint')">
          <Simditor v-model="problem.hint" placeholder=""></Simditor>
        </el-form-item>

        <el-form-item v-if="problem.spj">
          <Accordion :title="$t('m.Special_Judge_Code')">
            <template slot="header">
              <span>{{$t('m.SPJ_language')}}</span>
              <el-radio-group v-model="problem.spj_language">
                <el-tooltip class="spj-radio" v-for="lang in allLanguage.spj_languages" :key="lang.name" effect="dark"
                            :content="lang.description" placement="top-start">
                  <el-radio :label="lang.name">{{lang.name}}</el-radio>
                </el-tooltip>
              </el-radio-group>
              <el-button type="primary" size="small" icon="el-icon-fa-random" @click="compileSPJ"
                          :loading="loadingCompile">
                {{$t('m.Compile')}}
              </el-button>
            </template>
            <code-mirror v-model="problem.spj_code" :mode="spjMode"></code-mirror>
          </Accordion>
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="6">
            <el-form-item :label="$t('m.Type')">
              <el-radio-group v-model="problem.rule_type" :disabled="disableRuleType">
                <el-radio label="ACM">ACM</el-radio>
                <el-radio label="OI">OI</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('m.TestCase')" :error="error.testcase">
              <el-upload
                action="/api/admin/test_case"
                name="file"
                :data="{spj: problem.spj}"
                :show-file-list="true"
                :on-success="uploadSucceeded"
                :on-error="uploadFailed">
                <el-button size="small" type="primary" icon="el-icon-fa-upload">选择文件</el-button>
              </el-upload>
            </el-form-item>
          </el-col>

          <!--上传的测试用例在这里展开-->
          <el-col :span="24">
            <el-table
              :data="problem.test_case_score"
              style="width:100%">
              <el-table-column
                prop="input_name"
                :label="$t('m.Input')">
              </el-table-column>
              <el-table-column
                prop="output_name"
                :label="$t('m.Output')">
              </el-table-column>
              <el-table-column
                prop="score"
                :label="$t('m.Score')">
                <template slot-scope="scope">
                  <!--当规则为OI的时候才显示Score-->
                  <el-input
                    size="small"
                    :placeholder="$t('m.Score')"
                    v-model="scope.row.score"
                    :disabled="problem.rule_type !== 'OI'">
                  </el-input>
                </template>
              </el-table-column>
            </el-table>
          </el-col>

        </el-row>
        <el-form-item :label="$t('m.Source')">
          <el-input :placeholder="$t('m.Source')" v-model="problem.source"></el-input>
        </el-form-item>
        <save @click.native="submit()">保存</save>
      </el-form>
    </Panel>
  </div>
</template>


<script>
  import Simditor from '../../components/Simditor'
  import Accordion from '../../components/Accordion'
  import CodeMirror from '../../components/CodeMirror'
  import api from '../../api'


  export default {
    name: 'Problem',
    components: {
      Simditor,
      Accordion,
      CodeMirror
    },
    data () {
      return {
        rules: {
          _id: {required: true, message: 'Display ID 不能为空', trigger: 'blur'},
          title: {required: true, message: 'Title 不能为空', trigger: 'blur'},
          input_description: {required: true, message: '输入描述不能为空', trigger: 'blur'},
          output_description: {required: true, message: '输出描述不能为空', trigger: 'blur'}
        },
        loadingCompile: false,
        mode: '',
        contest: {},
        problem: {
          languages: []
        },
        reProblem: {
          languages: []
        },
        testCaseUploaded: false,
        allLanguage: {},
        inputVisible: false,
        tagInput: '',
        template: {},
        title: '',
        spjMode: '',
        disableRuleType: false,
        routeName: '',
        error: {
          tags: '',
          spj: '',
          languages: '',
          testCase: ''
        }
      }
    },
    mounted () {
      this.routeName = this.$route.name
      if (this.routeName === 'edit-problem' || this.routeName === 'edit-contest-problem') {
        this.mode = 'edit'
      } else {
        this.mode = 'add'
      }
      api.getLanguages().then(res => {
        this.problem = this.reProblem = {
          _id: '',
          title: '',
          description: '',
          input_description: '',
          output_description: '',
          time_limit: 1000,
          memory_limit: 256,
          difficulty: 'Low',
          visible: true,
          tags: [],
          languages: [],
          template: {},
          samples: [{input: '', output: ''}],
          spj: false,
          spj_language: '',
          spj_code: '',
          spj_compile_ok: false,
          test_case_id: '',
          test_case_score: [],
          rule_type: 'ACM',
          hint: '',
          source: ''
        }
        // 从路由url中获取比赛的ID
        let contestID = this.$route.params.contestId
        if (contestID) {
          // 根据比赛ID从数据库中查找出来的比赛规则赋值给题目的类型
          // 同时将查询出来的数据赋值给比赛数据
          this.problem.contest_id = this.reProblem.contest_id = contestID
          this.disableRuleType = true
          api.getContest(contestID).then(res => {
            this.problem.rule_type = this.reProblem.rule_type = res.data.data.rule_type
            this.contest = res.data.data
          })
        }

        this.problem.spj_language = 'C'

        let allLanguage = res.data.data
        this.allLanguage = allLanguage

        // 在获取到语言列表(language list)之后再去获取题目, 以免在`watch problem.languages`中发现有undefined的值
        if (this.mode === 'edit') {
          this.title = 'Edit Problem'
          // 要想编辑题目就要先获取该题目
          let funcName = {'edit-problem': 'getProblem', 'edit-contest-problem': 'getContestProblem'}[this.routeName]
          api[funcName](this.$route.params.problemId).then(problemRes => {
            let data = problemRes.data.data
            if (!data.spj_code) {
              data.spj_code = ''
            }
            // 从查询出来的spj语言和C语言中选择一种,测试用例上传属性设置为true
            data.spj_language = data.spj_language || 'C'
            this.problem = data
            this.testCaseUploaded = true
          })
        } else {
          this.title = '增加题目'
          for (let item of allLanguage.languages) {
            this.problem.languages.push(item.name)
          }
        }
      })
    },
    watch: {
      '$route' () {
        this.$refs.form.resetFields()
        this.problem = this.reProblem
      },
      // 题目语言处理
      'problem.languages' (newVal) {
        let data = {}
        // 使用deep copy以免infinite loop
        let languages = JSON.parse(JSON.stringify(newVal)).sort()
        for (let item of languages) {
          if (this.template[item] === undefined) {
            let langConfig = this.allLanguage.languages.find(lang => {
              return lang.name === item
            })
            if (this.problem.template[item] === undefined) {
              data[item] = {checked: false, code: langConfig.config.template, mode: langConfig.content_type}
            } else {
              data[item] = {checked: true, code: this.problem.template[item], mode: langConfig.content_type}
            }
          } else {
            data[item] = this.template[item]
          }
        }
        this.template = data
      },
      // 题目特殊评判语言处理
      'problem.spj_language' (newVal) {
        this.spjMode = this.allLanguage.spj_languages.find(item => {
          return item.name === this.problem.spj_language
        }).content_type
      }
    },
    methods: {
      // 更改成为特殊评测的方式
      switchSpj () {
        if (this.testCaseUploaded) {
          this.$confirm('如果你更改题目的评测方法, 你需要重新上传测试用例', '警告', {
            confirmButtonText: '继续',
            cancelButtonText: '取消',
            type: 'warning'
          }).then(() => {
            this.problem.spj = !this.problem.spj
            this.resetTestCase()
          }).catch(() => {
          })
        } else {
          this.problem.spj = !this.problem.spj
        }
      },
      // 查询搜索
      querySearch (queryString, cb) {
        api.getProblemTagList().then(res => {
          let tagList = []
          for (let tag of res.data.data) {
            tagList.push({value: tag.name})
          }
          cb(tagList)
        }).catch(() => {
        })
      },
      // 重置测试用例
      resetTestCase () {
        this.testCaseUploaded = false
        this.problem.test_case_score = []
        this.problem.test_case_id = ''
      },
      // 添加标签
      addTag () {
        let inputValue = this.tagInput
        if (inputValue) {
          this.problem.tags.push(inputValue)
        }
        this.inputVisible = false
        this.tagInput = ''
      },
      // 关闭标签
      closeTag (tag) {
        this.problem.tags.splice(this.problem.tags.indexOf(tag), 1)
      },
      // 添加测试用例
      addSample () {
        this.problem.samples.push({input: '', output: ''})
      },
      // 删除测试用例
      deleteSample (index) {
        this.problem.samples.splice(index, 1)
      },
      // 上传成功响应
      uploadSucceeded (response) {
        if (response.error) {
          this.$error(response.data)
          return
        }
        let fileList = response.data.info
        for (let file of fileList) {
          file.score = (100 / fileList.length).toFixed(0)
          if (this.problem.spj) {
            file.output_name = '-'
          }
        }
        this.problem.test_case_score = fileList
        this.testCaseUploaded = true
        this.problem.test_case_id = response.data.id
      },
      // 上传失败
      uploadFailed () {
        this.$error('上传失败!')
      },
      // 编译特殊评判代码
      compileSPJ () {
        let data = {
          id: this.problem.id,
          spj_code: this.problem.spj_code,
          spj_language: this.problem.spj_language
        }
        this.loadingCompile = true
        api.compileSPJ(data).then(res => {
          this.loadingCompile = false
          this.problem.spj_compile_ok = true
          this.error.spj = ''
        }, err => {
          this.loadingCompile = false
          this.problem.spj_compile_ok = false
          const h = this.$createElement
          this.$msgbox({
            title: 'Compile Error',
            type: 'error',
            message: h('pre', err.data.data),
            showCancelButton: false,
            closeOnClickModal: false,
            customClass: 'dialog-compile-error'
          })
        })
      },
      // 提交表格
      submit () {
        if (!this.problem.samples.length) {
          this.$error('样例不能为空!')
          return
        }
        for (let sample of this.problem.samples) {
          if (!sample.input || !sample.output) {
            this.$error('样例的输入和输出不能为空!')
            return
          }
        }
        if (!this.problem.tags.length) {
          this.error.tags = '请至少添加一个标签!'
          this.$error(this.error.tags)
          return
        }
        if (this.problem.spj) {
          if (!this.problem.spj_code) {
            this.error.spj = 'Spj code 不能为空'
            this.$error(this.error.spj)
          } else if (!this.problem.spj_compile_ok) {
            this.error.spj = 'SPJ 代码没有成功编译通过!'
          }
          if (this.error.spj) {
            this.$error(this.error.spj)
            return
          }
        }
        if (!this.problem.languages.length) {
          this.error.languages = '请为题目至少选择一种语言'
          this.$error(this.error.languages)
          return
        }
        if (!this.testCaseUploaded) {
          this.error.testCase = 'Test case 还没有上传呢!'
          this.$error(this.error.testCase)
          return
        }
        if (this.problem.rule_type === 'OI') {
          for (let item of this.problem.test_case_score) {
            try {
              if (parseInt(item.score) <= 0) {
                this.$error('无效的测试用例分数')
                return
              }
            } catch (e) {
              this.$error('测试用例的分数必须是一个整数!')
              return
            }
          }
        }
        this.problem.languages = this.problem.languages.sort()
        this.problem.template = {}
        for (let k in this.template) {
          if (this.template[k].checked) {
            this.problem.template[k] = this.template[k].code
          }
        }
        let funcName = {
          'create-problem': 'createProblem',
          'edit-problem': 'editProblem',
          'create-contest-problem': 'createContestProblem',
          'edit-contest-problem': 'editContestProblem'
        }[this.routeName]
        // 编辑 contest problem时,contest_id 会被后来的请求覆盖掉
        if (funcName === 'editContestProblem') {
          this.problem.contest_id = this.contest.id
        }
        api[funcName](this.problem).then(res => {
          if (this.routeName === 'create-contest-problem' || this.routeName === 'edit-contest-problem') {
            this.$router.push({name: 'contest-problem-list', params: {contestId: this.$route.params.contestId}})
          } else {
            this.$router.push({name: 'problem-list'})
          }
        }).catch(() => {
        })
      }
    }
  }

</script>

<style lang="less" scoped>
  .problem {
    /*难度下拉列表样式:变窄*/
    .difficulty-select {
      width: 120px;
    }
    .spj-radio {
      margin-left: 10px;
      &:last-child {
        margin-right: 20px;
      }
    }
    .input-new-tag {
      width: 78px;
    }
    .button-new-tag {
      height: 24px;
      line-height: 22px;
      padding-top: 0;
      padding-bottom: 0;
    }
    .tags {
      .el-tag {
        margin-right: 10px;
      }
    }
    .accordion {
      margin-bottom: 10px;
    }
    .add-samples {
      width: 100%;
      background-color: #fff;
      border: 1px dashed #aaa;
      outline: none;
      cursor: pointer;
      color: #666;
      height: 35px;
      font-size: 14px;
      &:hover {
        background-color: #f9fafc;
      }
      i {
        margin-right: 10px;
      }
    }
    .add-sample-btn {
      margin-bottom: 10px;
    }

  }
</style>

<style>
  /*编译错误弹出框的样式*/
  .dialog-compile-error {
    width: auto;
    max-width: 80%;
    overflow-x: scroll;
  }
</style>


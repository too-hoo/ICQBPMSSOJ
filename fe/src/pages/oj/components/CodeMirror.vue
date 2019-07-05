<template>
  <div style="margin: 0px 0px 15px 0px">
    <!--头部分为两列，一列是语言选择，一列是文本编辑器的主题选择-->
    <Row type="flex" justify="space-between" class="header">
      <Col :span=12>
      <div>
        <span>语 言:</span>
        <Select :value="language" @on-change="onLangChange" class="adjust">
          <Option v-for="item in languages" :key="item" :value="item">{{item}}
          </Option>
        </Select>

        <Tooltip content="重置为默认的代码定义样式" placement="top" style="margin-left: 10px">
          <Button icon="refresh" @click="onResetClick"></Button>
        </Tooltip>

      </div>
      </Col>
      <Col :span=12>
      <div class="fl-right">

      </div>
      </Col>
    </Row>
    <!--身体部分主要就是codemirror代码编辑器，注意区分代码编辑器codemirror和富文本编辑器Simditor-->
    <codemirror :value="value" :options="options" @change="onEditorCodeChange" ref="myEditor">
    </codemirror>
  </div>
</template>
<script>
  import utils from '@/utils/utils'
  import { codemirror } from 'vue-codemirror-lite'

  // theme
  import 'codemirror/theme/monokai.css'
  import 'codemirror/theme/solarized.css'
  import 'codemirror/theme/material.css'

  // mode
  import 'codemirror/mode/clike/clike.js'
  import 'codemirror/mode/python/python.js'

  // active-line.js 当前行的样式
  import 'codemirror/addon/selection/active-line.js'

  // foldGutter 代码折叠
  import 'codemirror/addon/fold/foldgutter.css'
  import 'codemirror/addon/fold/foldgutter.js'
  import 'codemirror/addon/fold/brace-fold.js'
  import 'codemirror/addon/fold/indent-fold.js'

  export default {
    name: 'CodeMirror',
    components: {
      codemirror
    },
    // 接受从父组件传递过来的参数：值，语言数组，默认语言，主题
    props: {
      value: {
        type: String,
        default: ''
      },
      languages: {
        type: Array,
        default: () => {
          return ['C', 'C++', 'Java', 'Python2']
        }
      },
      language: {
        type: String,
        default: 'C++'
      },
      theme: {
        type: String,
        default: 'solarized'
      }
    },
    data () {
      return {
        options: {
          // codemirror options
          tabSize: 4,
          mode: 'text/x-csrc',
          theme: 'solarized',
          lineNumbers: true,
          line: true,
          // 代码折叠
          foldGutter: true,
          gutters: ['CodeMirror-linenumbers', 'CodeMirror-foldgutter'],
          // 选中文本自动高亮，及高亮方式
          styleSelectedText: true,
          lineWrapping: false,
          highlightSelectionMatches: {showToken: /\w/, annotateScrollbar: true}
        },
        mode: {
          'C++': 'text/x-csrc'
        },
        themes: [
          // {label: 'Monokai', value: 'monokai'},
          {label: 'Solarized Light', value: 'solarized'}
          // {label: 'Material', value: 'material'}
        ]
      }
    },
    mounted () {
      // 加载玩HTML之后，初始化数据
      utils.getLanguages().then(languages => {
        let mode = {}
        languages.forEach(lang => {
          mode[lang.name] = lang.content_type
        })
        this.mode = mode
        this.editor.setOption('mode', this.mode[this.language])
      })
      this.editor.focus()
    },
    methods: {
      // 代码更改
      onEditorCodeChange (newCode) {
        this.$emit('update:value', newCode)
      },
      // 语言更改
      onLangChange (newVal) {
        this.editor.setOption('mode', this.mode[newVal])
        this.$emit('changeLang', newVal)
      },
      // 主题更改
      onThemeChange (newTheme) {
        this.editor.setOption('theme', newTheme)
        this.$emit('changeTheme', newTheme)
      },
      // 点击重置代码
      onResetClick () {
        this.$emit('resetCode')
      }
    },
    computed: {
      editor () {
        // get current editor object
        // 计算并获取当前的编辑器对象
        return this.$refs.myEditor.editor
      }
    },
    // 监听主题的变换
    watch: {
      'theme' (newVal, oldVal) {
        this.editor.setOption('theme', newVal)
      }
    }
  }
</script>

<style lang="less" scoped>
  .header {
    margin: 5px 5px 15px 5px;
    .adjust {
      width: 150px;
      margin-left: 10px;
    }
    .fl-right {
      float: right;
    }
  }
</style>

<style>
  .CodeMirror {
    height: auto !important;
  }
  .CodeMirror-scroll {
    min-height: 300px;
    max-height: 1000px;
  }
</style>

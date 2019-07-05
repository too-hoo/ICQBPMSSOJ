<template>
  <!--富文本编辑其包含markdown功能,其实就是一个文本域组件-->
  <textarea ref="editor"></textarea>
</template>

<script>


  import Simditor from 'tar-simditor'
  import 'tar-simditor/styles/simditor.css'
  import 'tar-simditor-markdown'
  import 'tar-simditor-markdown/styles/simditor-markdown.css'

  export default {
    name: 'Simditor',
    // name: 'Simditor',
    props: {
      toolbar: {
        type: Array,
        default: () => ['title', 'bold', 'italic', 'underline', 'fontScale', 'color', 'ol', 'ul', '|', 'link', 'image', 'hr', '|', 'indent', 'outdent', 'alignment', '|', 'markdown']
      },
      value: {
        type: String,
        default: ''
      }
    },

    data () {
      return {
        editor: null,
        currentValue: this.value
      }
    },

    mounted () {
      Simditor.locale = 'en-US'
      this.editor = new Simditor({
        textarea: this.$refs.editor,
        toolbar: this.toolbar,
        pasteImage: true,
        markdown: true,
        upload: {
          url: '/api/admin/upload_image/',
          params: null,
          fileKey: 'image',
          connectionCount: 3,
          leaveConfirm: '上传进程正在进行,你确定要离开这一页吗?'
        }
      })
      this.editor.on('valuechanged', (e, src) => {
        this.currentValue = this.editor.getValue()
      })
      this.editor.on('decorate', (e, src) => {
        this.currentValue = this.editor.getValue()
      })

      this.editor.setValue(this.value)
    },

    // 监听更改
    watch: {
      'value' (val) {
        if (this.currentValue !== val) {
          this.currentValue = val
          this.editor.setValue(val)
        }
      },
      // 1、父组件可以使用 props 把数据传给子组件。
      // 2、子组件可以使用 $emit 触发父组件change,input的自定义事件。
      'currentValue' (newVal, oldVal) {
        if (newVal !== oldVal) {
          this.$emit('change', newVal)
          this.$emit('input', newVal)
        }
      }
    }

  }
</script>

<style lang="less" scoped>
</style>

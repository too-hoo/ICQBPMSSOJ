<template>
  <el-form>
    <el-form-item label="输入">
      <el-input type="textarea" v-model="input" @change="changeInput" @keyup.enter.native="changeInput"></el-input>
    </el-form-item>

    <el-form-item label="输出"></el-form-item>
    <div v-html="text"></div>
  </el-form>
</template>



<script>
  // 数学公式输入模块
  import katex from 'katex'
  export default {
    name: '',
    data () {
      return {
        input: 'c= \\pm\\sqrt{a^2 + b^2}',
        text: ''
      }
    },
    mounted () {
      this.text = this.renderTex(this.input)
    },
    methods: {
      renderTex (data) {
        return katex.renderToString(data, {
          displayModel: true,
          throwOnError: false
        })
      },
      changeInput () {
        try {
          this.text = this.renderTex(this.input)
        } catch (e) {
          this.text = '<p style="text-align: center"><span style="coloe:red">错误的输入</span></p>'
        }
      }
    }
  }

</script>

<style scoped>
</style>

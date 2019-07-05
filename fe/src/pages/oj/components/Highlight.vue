<template>
  <pre v-highlight="code"><code :class="language" :style="styleObject"></code></pre>
</template>

<script>
  // 主要负责不同代码的高光样式例如：C/CPP,java,Python
  export default {
    name: 'highlight',
    data () {
      return {
        styleObject: {
          'border-left': '2px solid green'
        }
      }
    },
    // 接收辅助间传递过来的语言，代码，边框颜色，监听边框颜色的变化
    props: {
      language: {
        type: String
      },
      code: {
        required: true,
        type: String
      },
      borderColor: {
        type: String,
        default: 'green'
      }
    },
    watch: {
      'borderColor' (newVal, oldVal) {
        this.styleObject['border-left'] = '2.5px solid ' + newVal
      }
    }
  }
</script>

<style scoped lang="less">
  pre {
    padding: 0;
    display: block;
    code {
      padding: 20px;
      font-size: 1.1em;
    }
  }
</style>

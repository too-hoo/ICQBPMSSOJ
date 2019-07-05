<template>
</template>

<script>
  import api from '../../api.js'

  export default {
    mounted () {
      // 退出三步骤
      // 1、直接请求后台数据销毁session,2、同时删除本地Profile，3、跳转到根目录
      api.logout().then(res => {
        this.$store.dispatch('clearProfile')
        this.$router.replace({
          path: '/'
        })
      })
    }
  }
</script>

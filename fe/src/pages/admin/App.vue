<template>
  <div id="app">
    <!-- 加载路由跳转需要的组件 -->
    <router-view></router-view>
  </div>
</template>

<script>
  export default {
    // 这里是主组件，app绑定上面的id=app
    name: 'app',
    components: {}
  }
</script>

<style lang="less">
/* 设置总体的样式 */
  body {
    margin: 0;
    padding: 0;
    font-family: "Helvetica Neue",Helvetica,"PingFang SC","Hiragino Sans GB","Microsoft YaHei","微软雅黑",Arial,sans-serif;
    font-size: 14px;
    -webkit-font-smoothing: antialiased;
    background-color: #ffffff;
  }
/* 绝对定位，头部和底部不留空，宽度全部填充 */ 
  #app {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 100%;
  }
</style>

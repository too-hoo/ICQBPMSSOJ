<template>
  <div>
    <!-- 首先加载导航栏 -->
    <NavBar></NavBar>
    <div class="content-app">
      <!-- 设置根据路由跳转的样式 -->
      <transition name="fadeInUp" mode="out-in">
        <router-view></router-view>
      </transition>
      <div class="footer">
        <p v-html="website.website_footer"></p>
        <p>权利保留为：<a href="https://blog.csdn.net/ATOOHOO" target="_blank">ICQBPMSSOJ</a>
          <span v-if="version">&nbsp; 构建版本: {{ version }}</span>
        </p>
      </div>
    </div>
    <BackTop></BackTop>
  </div>
</template>

<script>
  import { mapActions, mapState } from 'vuex'
  import NavBar from '@oj/components/NavBar.vue'

  export default {
    name: 'app',
    components: {
      NavBar
    },
    data () {
      return {
        version: process.env.VERSION
      }
    },
    // 去掉预加载的HTML元素，html加载完成之前，执行。执行顺序：父组件-子组件
    created () {
      try {
        document.body.removeChild(document.getElementById('app-loader'))
      } catch (e) {
      }
    },
    // 加载HTML之后，使用mounted 方法中初始化值，使用mapAction获取store中的方法
    mounted () {
      this.getWebsiteConfig()
    },
    // methods：事件方法执行
    methods: {
      // mapActions 用来获取方法（动作）
      ...mapActions(['getWebsiteConfig', 'changeDomTitle'])
    },
    // computed是计算属性，也就是依赖其它的属性计算所得出最后的值
    computed: {
      // mapState相当于映射，获取store中的state对应的website
      ...mapState(['website'])
    },
    // 监听器监听website和路由方面的更改
    watch: {
      'website' () {
        this.changeDomTitle()
      },
      '$route' () {
        this.changeDomTitle()
      }
    }
  }
</script>

<style lang="less">

  * {
    -webkit-box-sizing: border-box;
    -moz-box-sizing: border-box;
    box-sizing: border-box;
  }

  a {
    text-decoration: none;
    background-color: transparent;
    &:active, &:hover {
      outline-width: 0;
    }
  }


  .content-app {
    margin-top: 80px;
    padding: 0 2%;
  }

  .footer {
    margin-top: 20px;
    margin-bottom: 10px;
    text-align: center;
    font-size: small;
  }

  .fadeInUp-enter-active {
    animation: fadeInUp .8s;
  }


</style>

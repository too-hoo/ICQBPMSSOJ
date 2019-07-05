<template>
  <div class="container">
    <div>
      <SideMenu></SideMenu>
    </div>
    <div id="header">
      <!--<i class="el-icon-fa-font katex-editor" @click="katexVisible=true" ></i>-->
      <!--<screen-full :width="14" :height="14" class="screen-full"></screen-full>-->
      <el-dropdown @command="handleCommand">
        <span>{{user.username}}<i class="el-icon-caret-bottom el-icon--right"></i></span>
        <el-dropdown-menu slot="dropdown">
          <el-dropdown-item command="logout">退出</el-dropdown-item>
        </el-dropdown-menu>
      </el-dropdown>
    </div>
    <div class="content-app">
      <transition name="fadeInUp" mode="out-in">
        <router-view></router-view>
      </transition>
    </div>
    <div class="footer">
        构建版本为：{{ version }}
    </div>
    <el-dialog title="Latex Editor" :visible.sync="katexVisible">
      <KatexEditor></KatexEditor>
    </el-dialog>
  </div>
</template>



<script>
  // import { types } from '@/store'
  import { types } from '@/store'
  // import { mapGetters } from 'vuex'
  import { mapGetters } from 'vuex'
  // import SideMenu from '../components/SideMenu.vue'
  import SideMenu from '../components/SideMenu.vue'
  // import ScreenFull from '@admin/components/ScreenFull.vue'
  import ScreenFull from '@admin/components/ScreenFull.vue'
  // import KatexEditor from '@admin/components/KatexEditor.vue'
  import KatexEditor from '@admin/components/KatexEditor.vue'
  // import api from '../api'
  import api from '../api'

  export default {
    name: 'app',
    data () {
      return {
        version: process.env.VERSION,
        katexVisible: false
      }
    },
    components: {
      SideMenu,
      KatexEditor,
      ScreenFull
    },
    // 全屏组件只是占用头部header的部分，其他的没有占用，在写下面的对应的方法的时候，代码不能出错，否则不会显示，很挑剔
    beforeRouteEnter (to, from, next) {
      api.getProfile().then(res => {
        if (!res.data.data) {
          // not login
          next({name: 'login'})
        } else {
          next(vm => {
            vm.$store.commit(types.CHANGE_PROFILE, {profile: res.data.data})
          })
        }
      })
    },
    // 模板里面会请求command这个犯法，所以这里要先写出来
    methods: {
      handleCommand (command) {
        if (command === 'logout') {
          api.logout().then(() => {
            this.$router.push({name: 'login'})
          })
        }
      }
    },
    computed: {
      ...mapGetters(['user'])
    }
  }

</script>

<style lang="less">
  a {
    background-color: transparent;
  }


  a:active, a:hover {
    outline-width: 0
  }


  img {
    border-style: none
  }


  .container {
    overflow: auto;
    font-weight: 400;
    height: 100%;
    -webkit-font-smoothing:antialiased;
    /*background-color: #ededed;*/
    background:url("../../../assets/background.jpg");
    // 页面右边滚动条
    overflow-y:scroll;
    min-width: 1000px;
  }


  * {
    box-sizing: border-box;
  }


  #header {
    text-align: right;
    padding-left: 210px;
    padding-right: 30px;
    // 行高和头部高度一致
    line-height: 50px;
    height: 50px;
    background-color:#F9FAFF;
    .screen-full {
      margin-right: 8px;
    }
  }

  .content-app {
    padding-top: 20px;
    padding-right: 10px;
    padding-left: 210px;
  }


  .footer {
    margin: 15px;
    text-align: center;
    font-size: small;
  }


  // 设置向上升起的样式
  @keyframes fadeInUp {
    from {
      opacity: 0;
      transform: translate(0, 30px);
    }

    to {
      opacity: 1;
      transform: none;
    }
  }


  .fadeInUp-enter-active {
    animation: fadeInUp .8s;
  }


  .katex-editor {
    margin-right: 5px;
   /*font-weight: 18px;*/
  }

</style>

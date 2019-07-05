<template>
  <div id="header">
    <Menu theme="light" mode="horizontal" @on-select="handleRoute" :active-name="activeMenu" class="oj-menu">
      <div class="logo"><span>{{website.website_name}}
      </span></div>
      <Menu-item name="/">
        <!-- <Icon type="home"></Icon> -->
        {{$t('m.Home')}}
      </Menu-item>
      <Menu-item name="/problems">
        <!-- <Icon type="ios-keypad"></Icon> -->
        {{$t('m.NavProblems')}}
      </Menu-item>
      <Menu-item name="/contests">
        <!-- <Icon type="trophy"></Icon> -->
        {{$t('m.Contests')}}
      </Menu-item>
      <Menu-item name="/status">
        <!-- <Icon type="ios-pulse-strong"></Icon> -->
        {{$t('m.NavStatus')}}
      </Menu-item>
      <Menu-item name="/acm-rank">
          {{$t('m.ACM_Rank')}}
      </Menu-item>
      <Menu-item name="/oi-rank">
        {{$t('m.OI_Rank')}}
      </Menu-item>

      <template v-if="!isAuthenticated">
        <div class="btn-menu">
          <Button type="ghost"
                  ref="loginBtn"
                  @click="handleBtnClick('login')">{{$t('m.Login')}}
            <!--按钮样式：shape="circle"-->
          </Button>
          <Button v-if="website.allow_register"
                  type="ghost"
                  @click="handleBtnClick('register')"
                  style="margin-left: 5px;">{{$t('m.Register')}}
          </Button>
        </div>
      </template>
      <template v-else>
        <!--下拉组件:下拉按钮（包括用户名和向下的尖尖），和列表-->
        <Dropdown class="drop-menu" @on-click="handleRoute" placement="bottom" trigger="click">
          <Button type="text" class="drop-menu-title">{{ user.username }}
            <Icon type="arrow-down-b"></Icon>
          </Button>
          <Dropdown-menu slot="list">
            <Dropdown-item name="/user-home">{{$t('m.MyHome')}}</Dropdown-item>
            <Dropdown-item name="/status?myself=1">{{$t('m.MySubmissions')}}</Dropdown-item>
            <Dropdown-item name="/setting/profile">{{$t('m.Settings')}}</Dropdown-item>
            <Dropdown-item v-if="isAdminRole" name="/admin">{{$t('m.Management')}}</Dropdown-item>
            <Dropdown-item divided name="/logout">{{$t('m.Logout')}}</Dropdown-item>
          </Dropdown-menu>
        </Dropdown>
      </template>
    </Menu>
    <!--打开登录信息输入对话框，使用modalVisible全局提示-->
    <Modal v-model="modalVisible" :width="400">
      <div slot="header" class="modal-title">欢迎来到 {{website.website_name_shortcut}}</div>
      <component :is="modalStatus.mode" v-if="modalVisible"></component>
      <div slot="footer" style="display: none"></div>
    </Modal>
  </div>
</template>

<script>
  import { mapGetters, mapActions } from 'vuex'
  import login from '@oj/views/user/Login'
  import register from '@oj/views/user/Register'

  export default {
    components: {
      login,
      register
    },
    mounted () {
      this.getProfile()
    },
    methods: {
      ...mapActions(['getProfile', 'changeModalStatus']),
      // 处理页面跳转，如果检测到路由中没有admin，就直接push路径到路由，否则就跳转到管理员页
      handleRoute (route) {
        if (route && route.indexOf('admin') < 0) {
          this.$router.push(route)
        } else {
          window.open('/admin/')
        }
      },
      // 处理按钮点击事件
      handleBtnClick (mode) {
        this.changeModalStatus({
          visible: true,
          mode: mode
        })
      }
    },
    // 计算属性，获取最后的路径实现路由跳转
    computed: {
      ...mapGetters(['website', 'modalStatus', 'user', 'isAuthenticated', 'isAdminRole']),
      // 跟随路由变化
      activeMenu () {
        return '/' + this.$route.path.split('/')[1]
      },
      // 打开登录信息输入对话框，获取数据并请求后台数据库
      modalVisible: {
        get () {
          return this.modalStatus.visible
        },
        set (value) {
          this.changeModalStatus({visible: value})
        }
      }
    }
  }
</script>

<style lang="less" scoped>
  #header {
    min-width: 1100px;
    position: fixed;
    top: 0;
    left: 0;
    height: 60px;
    width: 100%;
    z-index: 1000;
    background-color: #fff;
    box-shadow: 0 1px 5px 0 rgba(0, 0, 0, 0.1);
    .oj-menu {
      background: #fdfdfd;
    }

    .logo {
      margin-left: 2%;
      margin-right: 2%;
      font-size: 20px;
      float: left;
      line-height: 60px;
    }

    .drop-menu {
      float: right;
      margin-right: 30px;
      position: absolute;
      right: 10px;
      &-title {
        font-size: 18px;
      }
    }
    .btn-menu {
      font-size: 16px;
      float: right;
      margin-right: 10px;
    }
  }

  .modal {
    &-title {
      font-size: 18px;
      font-weight: 600;
    }
  }
</style>

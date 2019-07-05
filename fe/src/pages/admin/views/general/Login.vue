
<template>
  <el-form :model="ruleForm2" :rules="rules2" ref="ruleForm2" label-position="left" label-width="0px"
                  class="demo-ruleForm login-container">
    <h3 class="title">欢迎登录ICQBPMSSOJ后台管理系统</h3>
    <el-form-item prop="account">
      <el-input type="text" v-model="ruleForm2.account" auto-complete="off"  placeholder="输入用户名" @keyup.enter.native="handleLogin"></el-input>
    </el-form-item>
    <el-form-item prop="password">
      <el-input type="password" v-model="ruleForm2.password" auto-complete="off" placeholder="输入密码" @keyup.enter.native="handleLogin"></el-input>
    </el-form-item >
    <el-form-item style="with:100%;">
      <el-button type="primary" plain style="width:100%;" @click.native.prevent="handleLogin" :loading="logining">登 录</el-button>
    </el-form-item>
  </el-form>
</template>


<script>
  import api from '../../api'

  export default {
    data () {
      return {
        logining: false,
        ruleForm2: {
          account: '',
          password: ''
        },
        // 设置输入框是必须的 account is required
        rules2: {
          account: [
            {required: true, trigger: 'blur'}
          ],
          password: [
            {required: true, trigger: 'blur'}
          ]
        },
        checked: true
      }
    },
    methods: {
      handleLogin (ev) {
        // 引用ruleForm2的值
        this.$refs.ruleForm2.validate((valid) => {
          if (valid) {
            this.logining = true
            api.login(this.ruleForm2.account, this.ruleForm2.password).then(data => {
              this.logining = false
              // after login then redirect to dashboard
              this.$router.push({name: 'dashboard'})
            }, () => {
              this.logining = false
            })
          } else {
            // 调用全局消息显示框，显示错误消息！
            this.$error('请检查错误的字段:用户名或者密码！')
          }
        })
      }
    }
  }

</script>

<style lang="less" scoped>
  .login-container {
    box-shadow: 0 0px 8px 0 rgba(0, 0, 0, 0.06), 0 1px 0px 0 rgba(0, 0, 0, 0.02);
    -webkit-border-radius:5px;
    border-radius: 5px;
    -moz-border-radius:5px;
    background-clip:padding-box;/*背景裁剪*/
    margin: 180px auto;/*顶部高度*/
    width: 350px;
    padding: 35px 35px 15px 35px;/*边框的内边距*/
    background:#ffffff;
    border: 1px solid #eaeaea; /*灰色*/
    box-shadow: 0 0 25px #cac6c6;
    .title {
      // left right
      margin: 0px auto 40px auto;
      text-align: center;
      color: #505458;
    }
  }
  
</style>

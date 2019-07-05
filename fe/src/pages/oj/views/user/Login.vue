<template>
  <div>
    <Form ref="formLogin" :model="formLogin" :rules="ruleLogin">
      <FormItem prop="username">
        <Input type="text" v-model="formLogin.username" :placeholder="$t('m.LoginUsername')" size="large" @on-enter="handleLogin">
        <Icon type="ios-person-outline" slot="prepend"></Icon>
        </Input>
      </FormItem>
      <FormItem prop="password">
        <Input type="password" v-model="formLogin.password" :placeholder="$t('m.LoginPassword')" size="large" @on-enter="handleLogin">
        <Icon type="ios-locked-outline" slot="prepend"></Icon>
        </Input>
      </FormItem>
      <!--如果需要双因素验证的话就要输入双因素验证码-->
      <FormItem prop="tfa_code" v-if="tfaRequired">
        <Input v-model="formLogin.tfa_code" :placeholder="$t('m.TFA_Code')">
        <Icon type="ios-lightbulb-outline" slot="prepend"></Icon>
        </Input>
      </FormItem>
    </Form>
    <div class="footer">
      <!--对话框脚：登录按钮，系统注册和找回密码-->
      <Button
        type="primary"
        @click="handleLogin"
        class="btn" long
        :loading="btnLoginLoading">
        {{$t('m.UserLogin')}}
      </Button>
      <a v-if="website.allow_register" @click.stop="handleBtnClick('register')">{{$t('m.No_Account')}}</a>
      <a @click.stop="goResetPassword" style="float: right">{{$t('m.Forget_Password')}}</a>
    </div>
  </div>
</template>

<script>
  import { mapGetters, mapActions } from 'vuex'
  import api from '@oj/api'
  import { FormMixin } from '@oj/components/mixins'

  export default {
    mixins: [FormMixin],
    data () {
      // 检查是否需要双因素验证，默认是关闭的
      const CheckRequiredTFA = (rule, value, callback) => {
        if (value !== '') {
          api.tfaRequiredCheck(value).then(res => {
            this.tfaRequired = res.data.data.result
          })
        }
        callback()
      }

      return {
        tfaRequired: false,
        btnLoginLoading: false,
        formLogin: {
          username: '',
          password: '',
          tfa_code: ''
        },
        ruleLogin: {
          username: [
            {required: true, trigger: 'blur'},
            {validator: CheckRequiredTFA, trigger: 'blur'}
          ],
          password: [
            {required: true, trigger: 'change', min: 6, max: 20}
          ]
        }
      }
    },
    methods: {
      ...mapActions(['changeModalStatus', 'getProfile']),
      handleBtnClick (mode) {
        this.changeModalStatus({
          mode,
          visible: true
        })
      },
      // 处理登录信息
      handleLogin () {
        this.validateForm('formLogin').then(valid => {
          this.btnLoginLoading = true
          let formData = Object.assign({}, this.formLogin)
          // 如果不要求双因素登录，就先去除双因素验证码
          if (!this.tfaRequired) {
            delete formData['tfa_code']
          }
          // 请求后台的数据
          api.login(formData).then(res => {
            this.btnLoginLoading = false
            this.changeModalStatus({visible: false})
            this.getProfile()
            this.$success('欢迎回到ICQBPMSSOJ')
          }, _ => {
            this.btnLoginLoading = false
          })
        })
      },
      // 重置密码
      goResetPassword () {
        this.changeModalStatus({visible: false})
        this.$router.push({name: 'apply-reset-password'})
      }
    },
    // 获取网站的状态
    computed: {
      ...mapGetters(['website', 'modalStatus']),
      visible: {
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

<style scoped lang="less">
  .footer {
    overflow: auto;
    margin-top: 20px;
    margin-bottom: -15px;
    text-align: left;
    .btn {
      margin: 0 0 15px 0;
      &:last-child {
        margin: 0;
      }
    }
  }
</style>

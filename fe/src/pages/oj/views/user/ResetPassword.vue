<template>
  <!--当点击电子邮箱发送的邮件里面的链接时:重新设置密码-->
  <Panel :padding="30" class="container">
    <div slot="title" class="center">{{$t('m.Reset_Password')}}</div>
    <template v-if="!resetSuccess">
      <!--调用规则重置密码-->
    <Form :model=formResetPassword ref="formResetPassword" :rules="ruleResetPassword">
      <Form-item prop="password">
        <Input type="password" v-model="formResetPassword.password" :placeholder="$t('m.RPassword')" size="large">
        <Icon type="ios-locked-outline" slot="prepend"></Icon>
        </Input>
      </Form-item>
      <Form-item prop="passwordAgain">
        <Input type="password" v-model="formResetPassword.passwordAgain" :placeholder="$t('m.RPassword_Again')" size="large">
        <Icon type="ios-locked-outline" slot="prepend"></Icon>
        </Input>
      </Form-item>
      <Form-item prop="captcha" style="margin-bottom:10px">
        <div id="captcha">
          <div id="captchaCode">
            <Input v-model="formResetPassword.captcha" :placeholder="$t('m.RCaptcha')" size="large">
            <Icon type="ios-lightbulb-outline" slot="prepend"></Icon>
            </Input>
          </div>
          <div id="captchaImg">
            <Tooltip content="点击刷新验证码" placement="top">
              <img :src="captchaSrc" @click="getCaptchaSrc"/>
            </Tooltip>
          </div>
        </div>
      </Form-item>
    </Form>
    <Button type="primary"
            @click="resetPassword"
            class="btn" long
            :loading="btnLoading">重置密码
    </Button>
    </template>

    <!--Alert标签提示密码重置成功-->
    <template v-else>
      <Alert type="success">你的密码已经被重置.</Alert>
    </template>
  </Panel>
</template>

<script>
  import {FormMixin} from '@oj/components/mixins'
  import api from '@oj/api'

  export default {
    name: 'reset-password',
    mixins: [FormMixin],
    data () {
      // 检查密码字段的值是否为空,非空就提示再次输入密码
      const CheckPassword = (rule, value, callback) => {
        if (this.formResetPassword.passwdCheck !== '') {
          // 对第二个密码框再次验证
          this.$refs.formResetPassword.validateField('passwordAgain')
        }
        callback()
      }

      const CheckAgainPassword = (rule, value, callback) => {
        if (value !== this.formResetPassword.password) {
          callback(new Error('password does not match'))
        }
        callback()
      }
      return {
        btnLoading: false,
        captchaSrc: '',
        resetSuccess: false,
        formResetPassword: {
          captcha: '',
          password: '',
          passwordAgain: '',
          token: ''
        },
        ruleResetPassword: {
          password: [
            {required: true, trigger: 'blur', min: 6, max: 20},
            {validator: CheckPassword, trigger: 'blur'}
          ],
          passwordAgain: [
            {required: true, validator: CheckAgainPassword, trigger: 'change'}
          ],
          captcha: [
            {required: true, trigger: 'blur', min: 1, max: 10}
          ]
        }
      }
    },
    mounted () {
      this.formResetPassword.token = this.$route.params.token
      this.getCaptchaSrc()
    },
    methods: {
      resetPassword () {
        this.validateForm('formResetPassword').then(valid => {
          this.btnLoading = true
          let data = Object.assign({}, this.formResetPassword)
          delete data.passwordAgain
          api.resetPassword(data).then(res => {
            this.btnLoading = false
            this.resetSuccess = true
          }, _ => {
            this.btnLoading = false
            this.formResetPassword.captcha = ''
            this.getCaptchaSrc()
          })
        })
      }
    }
  }
</script>
<style lang="less" scoped>
  .container {
    width: 450px;
    margin: auto;
    .center {
      text-align: center;
    }
    #captcha {
      display: flex;
      flex-wrap: nowrap;
      justify-content: space-between;
      width: 100%;
      height: 36px;
      #captchaCode {
        flex: auto;
      }
      #captchaImg {
        margin-left: 10px;
        padding: 3px;
        flex: initial;
      }
    }
    .btn {
      margin-top: 18px;
      text-align: center;
    }
  }
</style>

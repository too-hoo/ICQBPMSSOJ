<template>
  <Panel :padding="30" class="container">
    <div slot="title" class="center">{{$t('m.Reset_Password')}}</div>
    <template v-if="!successApply">
      <!--在登录框点击忘记密码链接之后跳转到应用重置密码页面:输入邮箱和输入验证码-->
      <Form :rules="ruleResetPassword" :model=formResetPassword ref="formResetPassword">
        <Form-item prop="email">
          <Input v-model="formResetPassword.email" :placeholder="$t('m.ApplyEmail')" size="large">
          <Icon type="ios-email-outline" slot="prepend"></Icon>
          </Input>
        </Form-item>
        <Form-item prop="captcha" style="margin-bottom:10px">
          <div class="oj-captcha">
            <div class="oj-captcha-code">
              <Input v-model="formResetPassword.captcha" :placeholder="$t('m.RCaptcha')" size="large">
              <Icon type="ios-lightbulb-outline" slot="prepend"></Icon>
              </Input>
            </div>
            <div class="oj-captcha-img">
              <Tooltip content="Click to refresh" placement="top">
                <img :src="captchaSrc" @click="getCaptchaSrc"/>
              </Tooltip>
            </div>
          </div>
        </Form-item>
      </Form>
      <!--按钮提示:发送重置密码到邮箱-->
      <Button type="primary"
              @click="sendEmail"
              class="btn" long
              :loading="btnLoading">{{$t('m.Send_Password_Reset_Email')}}
      </Button>
    </template>
    <!--成功之后更新Template的内容为成功提示信息-->
    <template v-else>
      <Alert type="success" show-icon>
        成功
        <span slot="desc">密码重置邮件已经发送到你的邮箱.</span>
      </Alert>
    </template>
  </Panel>
</template>
<script>
  import api from '@oj/api'
  import {FormMixin} from '@oj/components/mixins'

  export default {
    mixins: [FormMixin],
    data () {
      // 首先会查询数据库,如果不存在就提示错误信息
      const CheckEmailExist = (rule, value, callback) => {
        if (value !== '') {
          api.checkUsernameOrEmail(undefined, value).then(res => {
            if (res.data.data.email === false) {
              callback(new Error('系统不存在此邮箱'))
            } else {
              callback()
            }
          }, _ => callback())
        } else {
          callback()
        }
      }
      return {
        captchaSrc: '',
        successApply: false,
        btnLoading: false,
        formResetPassword: {
          email: '',
          captcha: ''
        },
        ruleResetPassword: {
          email: [
            {required: true, type: 'email', trigger: 'blur'},
            {validator: CheckEmailExist, trigger: 'blur'}
          ],
          captcha: [
            {required: true, trigger: 'blur', min: 1, max: 10}
          ]
        }
      }
    },
    mounted () {
      this.getCaptchaSrc()
    },
    methods: {
      // 发送电子邮件到邮箱重置信息
      sendEmail () {
        this.validateForm('formResetPassword').then(() => {
          this.btnLoading = true
          api.applyResetPassword(this.formResetPassword).then(res => {
            // 伪加载
            setTimeout(() => {
              this.btnLoading = false
              this.successApply = true
            }, 2000)
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

<style scoped lang="less">
  .container {
    width: 450px;
    margin: auto;
    .center {
      text-align: center;
    }
    .btn {
      margin-top: 18px;
      text-align: center;
    }
  }
</style>

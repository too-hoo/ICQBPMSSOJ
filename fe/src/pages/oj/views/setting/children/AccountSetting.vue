<template>
  <div class="setting-main">
    <!--使用flex格式的容器包裹div-->
    <div class="flex-container">
      <div class="left">
        <p class="section-title">{{$t('m.ChangePassword')}}</p>
        <Form class="setting-content" ref="formPassword" :model="formPassword" :rules="rulePassword">
          <FormItem label="旧密码" prop="old_password">
            <Input v-model="formPassword.old_password" type="password"/>
          </FormItem>
          <FormItem label="新密码" prop="new_password">
            <Input v-model="formPassword.new_password" type="password"/>
          </FormItem>
          <FormItem label="确认新密码" prop="again_password">
            <Input v-model="formPassword.again_password" type="password"/>
          </FormItem>
          <FormItem v-if="visible.tfaRequired" label="Two Factor Auth" prop="tfa_code">
            <Input v-model="formPassword.tfa_code"/>
          </FormItem>
          <FormItem v-if="visible.passwordAlert">
            <Alert type="success">你需要在5秒之后重新登录..</Alert>
          </FormItem>
          <Button type="primary" @click="changePassword">{{$t('m.Update_Password')}}</Button>
        </Form>
      </div>

      <div class="middle separator"></div>

      <div class="right">
        <p class="section-title">{{$t('m.ChangeEmail')}}</p>
        <Form class="setting-content" ref="formEmail" :model="formEmail" :rules="ruleEmail">
          <FormItem label="当前登录密码" prop="password">
            <Input v-model="formEmail.password" type="password"/>
          </FormItem>
          <FormItem label="旧邮箱">
            <Input v-model="formEmail.old_email" disabled/>
          </FormItem>
          <FormItem label="新邮箱" prop="new_email">
            <Input v-model="formEmail.new_email"/>
          </FormItem>
          <FormItem v-if="visible.tfaRequired" label="Two Factor Auth" prop="tfa_code">
            <Input v-model="formEmail.tfa_code"/>
          </FormItem>
          <Button type="primary" @click="changeEmail">{{$t('m.ChangeEmail')}}</Button>
        </Form>
      </div>
    </div>
  </div>
</template>

<script>
  import api from '@oj/api'
  import { FormMixin } from '@oj/components/mixins'

  export default {
    mixins: [FormMixin],
    data () {
      // 使用回调callback方法提示方框信息
      const oldPasswordCheck = [{required: true, trigger: 'blur', min: 6, max: 20}]
      const tfaCheck = [{required: true, trigger: 'change'}]
      const CheckAgainPassword = (rule, value, callback) => {
        if (value !== this.formPassword.new_password) {
          callback(new Error('密码不匹配'))
        }
        callback()
      }
      // 检查密码是否发生过更改
      const CheckNewPassword = (rule, value, callback) => {
        if (this.formPassword.old_password !== '') {
          if (this.formPassword.old_password === this.formPassword.new_password) {
            callback(new Error('和旧密码一样,新密码没有更改'))
          } else {
            // 对第二个密码框再次验证
            this.$refs.formPassword.validateField('again_password')
          }
        }
        callback()
      }
      return {
        loading: {
          btnPassword: false,
          btnEmail: false
        },
        visible: {
          passwordAlert: false,
          emailAlert: false,
          tfaRequired: false
        },
        formPassword: {
          tfa_code: '',
          old_password: '',
          new_password: '',
          again_password: ''
        },
        formEmail: {
          tfa_code: '',
          password: '',
          old_email: '',
          new_email: ''
        },
        rulePassword: {
          old_password: oldPasswordCheck,
          new_password: [
            {required: true, trigger: 'blur', min: 6, max: 20},
            {validator: CheckNewPassword, trigger: 'blur'}
          ],
          again_password: [
            {required: true, validator: CheckAgainPassword, trigger: 'change'}
          ],
          tfa_code: tfaCheck
        },
        ruleEmail: {
          password: oldPasswordCheck,
          new_email: [{required: true, type: 'email', trigger: 'change'}],
          tfa_code: tfaCheck
        }
      }
    },
    mounted () {
      this.formEmail.old_email = this.$store.getters.user.email || ''
    },
    methods: {
      // 更改密码
      changePassword () {
        this.validateForm('formPassword').then(valid => {
          this.loading.btnPassword = true
          let data = Object.assign({}, this.formPassword)
          delete data.again_password
          if (!this.visible.tfaRequired) {
            delete data.tfa_code
          }
          // 1API传递信息到后台更新数据库,2并返回成功信息,3定时5秒退出系统重新登录
          api.changePassword(data).then(res => {
            this.loading.btnPassword = false
            this.visible.passwordAlert = true
            this.$success('成功更新了密码!')
            setTimeout(() => {
              this.visible.passwordAlert = false
              this.$router.push({name: 'logout'})
            }, 5000)
          }, res => {
            if (res.data.data === 'tfa_required') {
              this.visible.tfaRequired = true
            }
            this.loading.btnPassword = false
          })
        })
      },
      // 更改邮箱,需要登录密码
      changeEmail () {
        this.validateForm('formEmail').then(valid => {
          this.loading.btnEmail = true
          let data = Object.assign({}, this.formEmail)
          if (!this.visible.tfaRequired) {
            delete data.tfa_code
          }
          api.changeEmail(data).then(res => {
            this.loading.btnEmail = false
            this.visible.emailAlert = true
            this.$success('成功更改了邮箱!')
            this.$refs.formEmail.resetFields()
          }, res => {
            if (res.data.data === 'tfa_required') {
              this.visible.tfaRequired = true
            }
          })
        })
      }
    }
  }
</script>

<style lang="less" scoped>

  .flex-container {
    justify-content: flex-start;
    .left {
      flex: 1 0;
      width: 250px;
      padding-right: 5%;
    }
    > .middle {
      flex: none;
    }
    .right {
      flex: 1 0;
      width: 250px;
    }
  }
</style>


import api from '@oj/api'

// 表单验证，包括：字段验证和验证码验证
export default {
  data () {
    return {
      captchaSrc: ''
    }
  },
  methods: {
    // 表单字段验证方法
    validateForm (formName) {
      return new Promise((resolve, reject) => {
        this.$refs[formName].validate(valid => {
          if (!valid) {
            this.$error('请验证错误的字段域！')
          } else {
            resolve(valid)
          }
        })
      })
    },
    // 获取验证吗的源数据
    getCaptchaSrc () {
      api.getCaptcha().then(res => {
        this.captchaSrc = res.data.data
      })
    }
  }
}

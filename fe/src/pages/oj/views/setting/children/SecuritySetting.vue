<template>
  <div class="setting-main">
    <!--显示标题-->
    <p class="section-title">{{$t('m.Sessions')}}</p>
    <div class="flex-container setting-content">
      <template v-for="session in sessions">
        <!--使用自定义的Card组件：头部和body部分-->
        <Card :padding="20" class="flex-child">
          <span slot="title" style="line-height: 20px">{{session.ip}}</span>
          <div slot="extra">
            <Tag v-if="session.current_session" color="green">当前</Tag>
            <Button v-else
                    type="info"
                    size="small"
                    @click="deleteSession(session.session_key)">删除
            </Button>
          </div>
          <!--使用表格的形式展示出来信息-->
          <Form :label-width="100">
            <FormItem label="OS :" class="item">
              {{session.user_agent | platform}}
            </FormItem>
            <FormItem label="Browser :" class="item">
              {{session.user_agent | browser}}
            </FormItem>
            <FormItem label="Last Activity :" class="item">
              {{session.last_activity | localtime }}
            </FormItem>
          </Form>
        </Card>
      </template>
    </div>
    <!--双因素验证二维码-->
    <p class="section-title">{{$t('m.Two_Factor_Authentication')}}</p>
    <div class="mini-container setting-content">
      <Form>
        <Alert v-if="TFAOpened"
               type="success"
               class="notice"
               showIcon>You have enabled two-factor authentication.
        </Alert>
        <FormItem v-if="!TFAOpened">
          <div class="oj-relative">
            <img :src="qrcodeSrc" id="qr-img">
            <Spin size="large" fix v-if="loadingQRcode"></Spin>
          </div>
        </FormItem>
        <template v-if="!loadingQRcode">
          <FormItem style="width: 250px">
            <Input v-model="formTwoFactor.code" placeholder="为你的应用输入对应的代码"/>
          </FormItem>
          <Button type="primary"
                  :loading="loadingBtn"
                  @click="updateTFA(false)"
                  v-if="!TFAOpened">打开 TFA
          </Button>
          <Button type="error"
                  :loading="loadingBtn"
                  @click="closeTFA"
                  v-else>关闭 TFA
          </Button>
        </template>
      </Form>
    </div>
  </div>
</template>

<script>
  import api from '@oj/api'
  import {mapGetters, mapActions} from 'vuex'
  import browserDetector from 'browser-detect'

  const browsers = {}
  const loadBrowser = (userAgent) => {
    let browser = {}
    if (userAgent in Object.keys(browsers)) {
      browser = browsers[userAgent]
    } else {
      browser = browserDetector(userAgent)
      browsers[userAgent] = browser
    }
    return browser
  }

  export default {
    data () {
      return {
        qrcodeSrc: '',
        loadingQRcode: false,
        loadingBtn: false,
        formTwoFactor: {
          code: ''
        },
        sessions: []
      }
    },
    mounted () {
      this.getSessions()
      if (!this.TFAOpened) {
        this.getAuthImg()
      }
    },
    methods: {
      ...mapActions(['getProfile']),
      // 获取验证图片
      getAuthImg () {
        this.loadingQRcode = true
        api.twoFactorAuth('get').then(res => {
          this.loadingQRcode = false
          this.qrcodeSrc = res.data.data
        })
      },
      // 获取session
      getSessions () {
        api.getSessions().then(res => {
          let data = res.data.data
          // 将当前session放到第一个
          let sessions = data.filter(session => {
            return session.current_session
          })
          // 将每个session遍历出来
          data.forEach(session => {
            if (!session.current_session) {
              sessions.push(session)
            }
          })
          this.sessions = sessions
        })
      },
      // 删除session
      deleteSession (sessionKey) {
        this.$Modal.confirm({
          title: 'Confirm',
          content: '你确定要删除这个session吗？',
          onOk: () => {
            api.deleteSession(sessionKey).then(res => {
              this.getSessions()
            }, _ => {
            })
          }
        })
      },
      closeTFA () {
        this.$Modal.confirm({
          title: 'Confirm',
          content: '双因素验证是一种能保护你的账户安全的强大工具，你确定要关闭它吗？',
          onOk: () => {
            this.updateTFA(true)
          }
        })
      },
      updateTFA (close) {
        let method = close === false ? 'post' : 'put'
        this.loadingBtn = true
        api.twoFactorAuth(method, this.formTwoFactor).then(res => {
          this.loadingBtn = false
          this.getProfile()
          if (close === true) {
            this.getAuthImg()
            this.formTwoFactor.code = ''
          }
          this.formTwoFactor.code = ''
        }, err => {
          this.formTwoFactor.code = ''
          this.loadingBtn = false
          if (err.data.data.indexOf('session') > -1) {
            this.getProfile()
            this.getAuthImg()
          }
        })
      }
    },
    computed: {
      ...mapGetters(['user']),
      TFAOpened () {
        return this.user && this.user.two_factor_auth
      }
    },
    filters: {
      browser (value) {
        let b = loadBrowser(value)
        if (b.name && b.version) {
          return b.name + ' ' + b.version
        } else {
          return 'Unknown'
        }
      },
      platform (value) {
        let b = loadBrowser(value)
        return b.os ? b.os : 'Unknown'
      }
    }
  }
</script>

<style lang="less" scoped>
  .notice {
    font-size: 16px;
    margin-bottom: 20px;
    display: inline-block;
  }

  .oj-relative {
    width: 150px;
    #qr-img {
      width: 300px;
      margin: -10px 0 -30px -20px;
    }
  }

  .flex-container {
    flex-flow: row wrap;
    justify-content: flex-start;
    .flex-child {
      flex: 1 0;
      max-width: 350px;
      margin-right: 30px;
      margin-bottom: 30px;
      .item {
        margin-bottom: 0;
      }
    }
  }
</style>

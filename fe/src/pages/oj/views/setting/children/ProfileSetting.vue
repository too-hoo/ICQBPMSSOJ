<template>
  <div class="setting-main">
    <div class="section-title">{{$t('m.Avatar_Setting')}}</div>
    <template v-if="!avatarOption.imgSrc">
      <!--上传的图片格式有限制-->
      <Upload type="drag"
              class="mini-container"
              accept=".jpg,.jpeg,.png,.bmp,.gif"
              action=""
              :before-upload="handleSelectFile">
        <div style="padding: 30px 0">
          <Icon type="ios-cloud-upload" size="52" style="color: #3399ff"></Icon>
          <p>点击覆盖或者手动选择上传头像吧</p>
        </div>
      </Upload>
    </template>

    <!--使用vueCropper裁剪标签对上传的照片进行修改设置-->
    <template v-else>
      <div class="flex-container">
        <div class="cropper-main inline">
          <vueCropper
            ref="cropper"
            autoCrop
            fixed
            :autoCropWidth="200"
            :autoCropHeight="200"
            :img="avatarOption.imgSrc"
            :outputSize="avatarOption.size"
            :outputType="avatarOption.outputType"
            :info="true"
            @realTime="realTime">
          </vueCropper>
        </div>
        <!--按钮组对图片进行操作:左右移动,重新选择,完成裁剪-->
        <ButtonGroup vertical class="cropper-btn">
          <Button @click="rotate('left')">
            <Icon type="arrow-return-left" size="20"></Icon>
          </Button>
          <Button @click="rotate('right')">
            <Icon type="arrow-return-right" size="20"></Icon>
          </Button>
          <Button @click="reselect">
            <Icon type="refresh" size="20"></Icon>
          </Button>
          <Button @click="finishCrop">
            <Icon type="checkmark-round" size="20"></Icon>
          </Button>
        </ButtonGroup>
        <div class="cropper-preview" :style="previewStyle">
          <div :style=" preview.div">
            <img :src="avatarOption.imgSrc" :style="preview.img">
          </div>
        </div>
      </div>
    </template>
    <!--使用Model弹框提示头像的设置情况-->
    <Modal v-model="uploadModalVisible"
           title="Upload the avatar">
      <div class="upload-modal">
        <p class="notice">你的头像将会被设置成为:</p>
        <img :src="uploadImgSrc"/>
      </div>
      <div slot="footer">
        <Button @click="uploadAvatar" :loading="loadingUploadBtn">上传</Button>
      </div>
    </Modal>

    <!--更改用户配置信息使用的是表单信息提交:一个大行分为两列-->
    <div class="section-title">{{$t('m.Profile_Setting')}}</div>
    <Form ref="formProfile" :model="formProfile">
      <Row type="flex" :gutter="30" justify="space-around">
        <Col :span="11">
          <FormItem label="真实姓名">
            <Input v-model="formProfile.real_name"/>
          </FormItem>
          <Form-item label="学校">
            <Input v-model="formProfile.school"/>
          </Form-item>
          <Form-item label="喜欢什么专业">
            <Input v-model="formProfile.major"/>
          </Form-item>
          <FormItem label="使用语言">
            <Select v-model="formProfile.language">
              <Option v-for="lang in languages" :key="lang.value" :value="lang.value">{{lang.label}}</Option>
            </Select>
          </FormItem>
          <Form-item>
            <Button type="primary" @click="updateProfile" :loading="loadingSaveBtn">保存信息</Button>
          </Form-item>
        </Col>

        <Col :span="11">
          <Form-item label="心情">
            <Input v-model="formProfile.mood"/>
          </Form-item>
          <Form-item label="你的博客">
            <Input v-model="formProfile.blog"/>
          </Form-item>
          <Form-item label="Github地址">
            <Input v-model="formProfile.github"/>
          </Form-item>
        </Col>
      </Row>
    </Form>
  </div>
</template>

<script>
  import api from '@oj/api'
  import utils from '@/utils/utils'
  import {VueCropper} from 'vue-cropper'
  import {types} from '@/store'
  import {languages} from '@/i18n'

  export default {
    components: {
      VueCropper
    },
    data () {
      return {
        loadingSaveBtn: false,
        loadingUploadBtn: false,
        uploadModalVisible: false,
        preview: {},
        uploadImgSrc: '',
        avatarOption: {
          imgSrc: '',
          size: 0.8,
          outputType: 'png'
        },
        languages: languages,
        formProfile: {
          real_name: '',
          mood: '',
          major: '',
          blog: '',
          school: '',
          github: '',
          language: ''
        }
      }
    },
    // 初始化数据
    mounted () {
      let profile = this.$store.state.user.profile
      Object.keys(this.formProfile).forEach(element => {
        if (profile[element] !== undefined) {
          this.formProfile[element] = profile[element]
        }
      })
    },
    methods: {
      // 使用正则表达式的内置测试方法test测试文件格式是否正确
      checkFileType (file) {
        if (!/\.(gif|jpg|jpeg|png|bmp|GIF|JPG|PNG)$/.test(file.name)) {
          this.$Notice.warning({
            title: '文件类型不支持',
            desc: '格式为 ' + file.name + ' 不正确 ，请选择图片格式文件.'
          })
          return false
        }
        return true
      },
      // 检查上传图片的尺寸大小
      checkFileSize (file) {
        // max size is 2MB
        if (file.size > 2 * 1024 * 1024) {
          this.$Notice.warning({
            title: '超出最大尺寸限制了',
            desc: '图片文件 ' + file.name + ' 尺寸过大了, 你只能上传最大尺寸不超过2M的图片'
          })
          return false
        }
        return true
      },
      // 处理用户手动上传的图片
      handleSelectFile (file) {
        let isOk = this.checkFileType(file) && this.checkFileSize(file)
        if (!isOk) {
          return false
        }
        let reader = new window.FileReader()
        reader.onload = (e) => {
          this.avatarOption.imgSrc = e.target.result
        }
        reader.readAsDataURL(file)
        return false
      },
      // 裁剪图片的时间
      realTime (data) {
        this.preview = data
      },
      // 旋转左右移动操作
      rotate (direction) {
        if (direction === 'left') {
          this.$refs.cropper.rotateLeft()
        } else {
          this.$refs.cropper.rotateRight()
        }
      },
      // 重新选择图片
      reselect () {
        this.$Modal.confirm({
          content: '你确定要删除已做的更改吗?',
          onOk: () => {
            this.avatarOption.imgSrc = ''
          }
        })
      },
      // 完成图片的裁剪:对当前图片的信息进行确定,同时打开确认的对话窗口
      finishCrop () {
        this.$refs.cropper.getCropData(data => {
          this.uploadImgSrc = data
          this.uploadModalVisible = true
        })
      },
      // 上传图片只是到本地并保存到本地,真正保存数据还要请求数据库更改
      uploadAvatar () {
        this.$refs.cropper.getCropBlob(blob => {
          let form = new window.FormData()
          let file = new window.File([blob], 'avatar.' + this.avatarOption.outputType)
          form.append('image', file)
          this.loadingUploadBtn = true
          this.$http({
            method: 'post',
            url: 'upload_avatar',
            data: form,
            headers: {'content-type': 'multipart/form-data'}
          }).then(res => {
            this.loadingUploadBtn = false
            this.$success('已经成功设置了新的头像')
            this.uploadModalVisible = false
            this.avatarOption.imgSrc = ''
            // 本地保存触发获取用户的配置信息
            this.$store.dispatch('getProfile')
          }, () => {
            this.loadingUploadBtn = false
          })
        })
      },
      // 真正更改配置信息
      updateProfile () {
        // 设置保存按钮可以点击,同时过滤一些空值,因为一些控制例如github可能没设置,就直接过滤掉,默认是空值
        this.loadingSaveBtn = true
        let updateData = utils.filterEmptyValue(Object.assign({}, this.formProfile))
        api.updateProfile(updateData).then(res => {
          this.$success('Success')
          this.$store.commit(types.CHANGE_PROFILE, {profile: res.data.data})
          this.loadingSaveBtn = false
        }, _ => {
          this.loadingSaveBtn = false
        })
      }
    },
    computed: {
      previewStyle () {
        return {
          'width': this.preview.w + 'px',
          'height': this.preview.h + 'px',
          'overflow': 'hidden'
        }
      }
    }
  }
</script>

<style lang="less" scoped>
  .inline {
    display: inline-block;
  }

  .copper-img {
    width: 400px;
    height: 300px;
  }

  .flex-container {
    flex-wrap: wrap;
    justify-content: flex-start;
    margin-bottom: 10px;
    .cropper-main {
      flex: none;
      .copper-img;
    }
    .cropper-btn {
      flex: none;
      vertical-align: top;
    }
    .cropper-preview {
      flex: none;
      /*margin: 10px;*/
      margin-left: 20px;
      box-shadow: 0 0 1px 0;
      .copper-img;
    }
  }

  .upload-modal {
    .notice {
      font-size: 16px;
      display: inline-block;
      vertical-align: top;
      padding: 10px;
      padding-right: 15px;
    }
    img {
      box-shadow: 0 0 1px 0;
      border-radius: 50%;
    }
  }
</style>

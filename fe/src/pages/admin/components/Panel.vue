<template>
  <div class="panel" :class="{'small': small}">
    <header>
      <!--头部分为左边和右边,右边看情况使用,例如在公告里面是可以删除的,但是在
      其他的例如用户,右边可以放搜索框和一些按钮等等-->
      <div class="title">
        <template v-if="$slots.title">
          <slot name="title"></slot>
        </template>
        <template v-else>
          {{title}}
        </template>
      </div>

      <div class="header_right">
        <slot name="header"></slot>
      </div>
    </header>

    <div class="body">
      <slot></slot>
    </div>
  </div>
</template>
<!--学习-->

<script>
  export default {
    name: 'Panel',
    props: {
      title: {
        type: String,
        required: false
      },
      small: {
        type: Boolean,
        default: false
      }
    }
  }

</script>
<style scoped lang="less">
  .panel {
    margin-bottom: 20px;
    background-color: #fff;
    border: 1px solid transparent;
    /*border-radius: 4px;*/
    box-shadow: 0 1px 1px rgba(0, 0, 0, .05);
    // 设置整个图版的样式.大小,边距
    &.small {
      max-width: 830px;
      min-width: 700px;
      margin-left: 20px;
      margin-top: 10px;
    }
    header {
      position: relative;
      z-index: 10;
      > .title {
        margin: 0;
        color: #333;
        border-color: #ddd;
        font-size: 18px;
        font-weight: 300;
        letter-spacing: 0.025em;
        height: 60px;
        line-height: 45px;
        padding: 10px 15px;
        border-bottom: 1px solid #eee;
        border-top-left-radius: 3px;
        border-top-right-radius: 3px;
      }
      > .header_right {
        position: absolute;
        top: 50%;
        right: 20px;
        transform: translate(0, -50%);
      }
    }
    .body {
      padding: 15px;
    }
  }
  /*学习*/
  /*.panel {*/
    /*margin-bottom: 20px;*/
    /*background-color: #fff;*/
    /*!*透明边框*!*/
    /*border: 1px solid transparent;*/
    /*border-radius: 4px;*/
    /*box-shadow: 0 1px 1px rgba(0, 0, 0, .05);*/
    /*&.small {*/
      /*max-width: 830px;*/
      /*min-width: 700px;*/
      /*margin-left: 20px;*/
      /*margin-top: 10px;*/
    /*}*/
    /*header {*/
      /*position: relative;*/
      /*z-index: 10;*/
      /*> .title {*/
        /*margin: 0;*/
        /*color: #333;*/
        /*border-color: #ddd;*/
        /*font-size: 18px;*/
        /*font-weight: 300;*/
        /*letter-spacing: 0.025em;*/
        /*height: 60px;*/
        /*line-height: 45px;*/
        /*padding: 10px 15px;*/
        /*border-bottom: 1px solid #eee;*/
        /*border-top-left-radius: 3px;*/
        /*border-top-right-radius: 3px;*/
      /*}*/
      /*> .header_right {*/
        /*position: absolute;*/
        /*top: 50%;*/
        /*right: 20px;*/
        /*transform: translate(0, -50%);*/
      /*}*/
    /*}*/
    /*.body {*/
      /*padding: 15px;*/
    /*}*/
  /*}*/
</style>
<style lang="less">
  .panel-options {
    background-color: transparent;
    position: relative;
    height: 50px;
    button {
      margin-top: 18px;
      margin-right: 10px;
    }
    > .page {
      position: absolute;
      right:20px;
      top: 20px;
    }
  }
  /*.panel-options {*/
    /*background-color: transparent;*/
    /*position: relative;*/
    /*height: 50px;*/
    /*button {*/
      /*margin-top: 18px;*/
      /*margin-right: 10px;*/
    /*}*/
    /*> .page {*/
      /*position: absolute;*/
      /*right: 20px;*/
      /*top: 20px;*/
    /*}*/
  /*}*/
</style>

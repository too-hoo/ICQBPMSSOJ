<template>
  <div class="accordion">
    <header>
      <h2>{{title}}</h2>
      <div class="header_right">
        <slot name="header"></slot>
      </div>
    </header>
    <div class="body" v-show="isOpen">
      <slot></slot>
    </div>
    <!--底部是可以折叠的样式,有一个向下的尖尖提示-->
    <footer @click="isOpen = !isOpen"><i :class="{'rotate': !isOpen}" class="el-icon-caret-top"></i></footer>
  </div>
</template>


<script>
  export default{
    name: 'Accordion',
    props: {
      title: {
        type: String,
        required: true
      }
    },
    data () {
      return {
        isOpen: true
      }
    }
  }

</script>

<style lang="less" scoped>
.accordion{
  /*背景颜色\位置(相对和绝对)\字号\内外边距\行高\与上下左右的距离\悬浮\边框(颜色,粗细样式等)\文字位置*/
  /*border: 1px solid #eaeefb;*/
  border: 1px solid #eaeefb;
  header{
    position: relative;
    h2{
      font-size: 14px;
      margin: 0 0 0 10px;
      line-height: 50px;
    }
    .header_right{
      right: 5px;
      top: 5px;
      position: absolute;
    }
  }

  .body{
    background-color: #f9fafc;
    border-top: 1px solid #eaeefb;
    clear: both;
    overflow: hidden;
    padding: 15px 10px;
  }

  footer{
    border-top: 1px solid #eaeefb;
    height: 36px;
    box-sizing: border-box;
    background-color: #fff;
    border-bottom-left-radius: 4px;
    border-bottom-right-radius: 4px;
    text-align: center;
    margin-top: -1px;
    color: #d3dce6;
    cursor: pointer;
    transition: .2s;
    &:hover{
      background-color: #f9fafc;
    }
    .rotate{
      transform: rotate(180deg);
    }
  }

}
</style>

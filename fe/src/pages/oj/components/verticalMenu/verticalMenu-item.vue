<template>
  <li @click.stop="handleClick" :class="{disabled: disabled}">
    <slot></slot>
  </li>
</template>

<script>
  import Emitter from '../mixins/emitter'

  // 垂直方式的菜单向，使用到组件触发器
  export default {
    name: 'VerticalMenu-item',
    mixins: [Emitter],
    // 接受来自父组件：路由类型、是否可用
    props: {
      route: {
        type: [String, Object]
      },
      disabled: {
        type: Boolean,
        default: false
      }
    },
    methods: {
      // 处理点击事件的路由跳转：右边的菜单栏目会用到
      handleClick () {
        if (this.route) {
          this.dispatch('VerticalMenu', 'on-click', this.route)
        }
      }
    }
  }
</script>

<style scoped lang="less">
  .disabled {
    /*background-color: #ccc;*/
    opacity: 1;
    /*cursor: not-allowed;*/
    pointer-events: none;
    color: #ccc;
    &:hover {
      border-left: none;
      color: #ccc;
      background: #fff;
    }
  }

  li {
    border-bottom: 1px dashed #e9eaec;
    color: #495060;
    display: block;
    text-align: left;
    padding: 15px 20px;
    &:hover {
      background: #f8f8f9;
      border-left: 2px solid #5cadff;
      color: #2d8cf0;
    }
    & > .ivu-icon {
      font-size: 16px;
      margin-right: 8px;
    }
    &:last-child {
      border-bottom: none;
    }
  }
</style>

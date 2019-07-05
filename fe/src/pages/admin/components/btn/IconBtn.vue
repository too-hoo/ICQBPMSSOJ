<template>
  <div style="display: inline-block;">
    <el-tooltip class="item" effect="dark" :content="name" placement="top">
      <el-button plain :icon="'el-icon-fa-' + icon" size="mini">
      </el-button>
    </el-tooltip>
  </div>
</template>

<script>
  export default {
    name: 'IconBtn',
    // 图标按钮会通过props接受父组件传递过来的name,icon属性,并生效
    props: {
      name: {
        type: String,
        required: true
      },
      icon: {
        type: String,
        required: true
      }
    }
  }
</script>

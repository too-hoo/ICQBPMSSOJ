<template>
  <Card :padding="0" dis-hover>
    <ul>
      <slot></slot>
    </ul>
  </Card>
</template>

<script>
  // 垂直方式的卡片菜单：例如在404页面用到
  export default {
    name: 'VerticalMenu'
  }
</script>

<style scoped lang="less">
</style>

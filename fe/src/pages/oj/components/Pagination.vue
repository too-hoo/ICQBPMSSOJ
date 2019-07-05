<template>
  <div class="page">
    <!--封装page标签功能成组件，往外提供调用接口，使用属性page-size-opts进行下拉列表的选择-->
    <Page :total="total"
          :page-size="pageSize"
          @on-change="onChange"
          @on-page-size-change="onPageSizeChange"
          :show-sizer="showSizer"
          :page-size-opts="[10, 30, 50, 100, 200]"
          :current="current"></Page>
  </div>

</template>

<script>
  export default {
    name: 'pagination',
    // name: 'pagination',
    // props 接收从父组件中传递过来的参数：总页数，每页数据量，显示的每页数据量，当前页
    props: {
      total: {
        required: true,
        type: Number
      },
      pageSize: {
        required: false,
        type: Number
      },
      showSizer: {
        required: false,
        type: Boolean,
        default: false
      },
      current: {
        required: false,
        type: Number
      }
    },

    methods: {
      onChange (page) {
        if (page < 1) {
          page = 1
        }
        // 子组件触发父组件更改数据
        this.$emit('update:current', page)
        this.$emit('on-change', page)
      },
      onPageSizeChange (pageSize) {
        this.$emit('update:pageSize', pageSize)
        this.$emit('on-page-size-change', pageSize)
      }
    }

  }
</script>

<style scoped lang="less">
  .page {
    margin: 20px;
    float: right;
  }
</style>

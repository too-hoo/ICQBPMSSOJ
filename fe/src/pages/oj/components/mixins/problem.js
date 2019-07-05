import utils from '@/utils/utils'

// 对外暴露方法：获取AC率，添加做题状态列column
export default {
  data () {
    return {
      statusColumn: false
    }
  },
  methods: {
    // 获取AC率
    getACRate (ACCount, TotalCount) {
      return utils.getACRate(ACCount, TotalCount)
    },
    // 添加做题状态列column
    addStatusColumn (tableColumns, dataProblems) {
      // 已添加过直接返回
      if (this.statusColumn) return
      // 只在有做题记录时才添加column
      let needAdd = dataProblems.some((item, index) => {
        if (item.my_status !== null && item.my_status !== undefined) {
          return true
        }
      })
      if (!needAdd) {
        return
      }
      tableColumns.splice(0, 0, {
        width: 60,
        title: ' ',
        render: (h, params) => {
          let status = params.row.my_status
          if (status === null || status === undefined) {
            return undefined
          }
          return h('Icon', {
            props: {
              type: status === 0 ? 'checkmark-round' : 'minus-round',
              size: '16'
            },
            style: {
              color: status === 0 ? '#19be6b' : '#ed3f14'
            }
          })
        }
      })
      this.statusColumn = true
    }
  }
}

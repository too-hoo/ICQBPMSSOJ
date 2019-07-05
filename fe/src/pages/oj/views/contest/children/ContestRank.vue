<template>
  <div>
    <component :is="currentView"></component>
  </div>
</template>

<script>
  import { mapGetters } from 'vuex'
  import { types } from '../../../../../store'
  import ACMContestRank from './ACMContestRank.vue'
  import OIContestRank from './OIContestRank.vue'

  const NullComponent = {
    name: 'null-component',
    template: '<div></div>'
  }

  // 总的比赛排名:包括ACM和OI排名,但是显示的情况是根据currentView情况显示不同的比赛规则排名状况
  // 这样避免写两个相同的文件
  export default {
    name: 'contest-rank',
    components: {
      ACMContestRank,
      OIContestRank,
      NullComponent
    },
    computed: {
      // 获取比赛规则,根据不同的比赛规则显示不同的排名状态,如果比赛规则为null,就显示空数据
      ...mapGetters(['contestRuleType']),
      currentView () {
        if (this.contestRuleType === null) {
          return 'NullComponent'
        }
        return this.contestRuleType === 'ACM' ? 'ACMContestRank' : 'OIContestRank'
      }
    },
    // 在路由离开的时候保存一下数据
    beforeRouteLeave (to, from, next) {
      this.$store.commit(types.CHANGE_CONTEST_ITEM_VISIBLE, {menu: true})
      next()
    }
  }
</script>
<style lang="less" scoped>
</style>

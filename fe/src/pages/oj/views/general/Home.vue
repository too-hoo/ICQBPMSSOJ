<template>
  <Row type="flex" justify="space-around">
    <Col :span="22">
      <!--比赛通知：用于还没有开始进行的比赛-->
    <panel shadow v-if="contests.length" class="contest">
      <!--点击跳转到对应的比赛-->
      <div slot="title">
        <Button type="text"  class="contest-title" @click="goContest">{{contests[index].title}}</Button>
      </div>
      <!--比赛内容展示:这是一个轮播公告显示,使用Carousel标签设置自动播放属性即可自动轮播,非常简单,例如设置播放速度为
          6秒钟,遍历比赛即可. 比赛的提示信息使用按钮标签即可-->
      <Carousel v-model="index" trigger="hover" autoplay :autoplay-speed="6000" class="contest">
        <CarouselItem v-for="(contest, index) of contests" :key="index">
          <div class="contest-content">
            <div class="contest-content-tags">
              <Button type="warning" shape="square" size="small" icon="trophy">
                {{contest.rule_type}}
              </Button>
              <Button type="info" shape="square" size="small" icon="calendar">
                {{contest.start_time | localtime('YYYY-M-D HH:mm') }}
              </Button>
              <Button type="success" shape="square" size="small" icon="android-time">
                {{getDuration(contest.start_time, contest.end_time)}}
              </Button>
            </div>
            <div class="contest-content-description">
              <blockquote v-html="contest.description"></blockquote>
            </div>
          </div>
        </CarouselItem>
      </Carousel>
    </panel>
    <Announcements class="announcement"></Announcements>
    </Col>
  </Row>
</template>

<script>
  import Announcements from './Announcements.vue'
  import api from '@oj/api'
  import time from '@/utils/time'
  import { CONTEST_STATUS } from '@/utils/constants'

  export default {
    name: 'home',
    components: {
      Announcements
    },
    data () {
      return {
        contests: [],
        index: 0
      }
    },
    mounted () {
      // 获取比赛列表
      let params = {status: CONTEST_STATUS.NOT_START}
      api.getContestList(0, 5, params).then(res => {
        this.contests = res.data.data.results
      })
    },
    methods: {
      // 获取持续时间
      getDuration (startTime, endTime) {
        return time.duration(startTime, endTime)
      },
      goContest () {
        this.$router.push({
          name: 'contest-details',
          params: {contestID: this.contests[this.index].id}
        })
      }
    }
  }
</script>

<style lang="less" scoped>
  .contest {
    &-title {
      font-style: italic;
      font-size: 21px;
    }
    &-content {
      padding: 0 70px 40px 70px;
      &-description {
        margin-top: 25px;
      }
    }
  }

  .announcement {
    margin-top: 20px;
  }
</style>

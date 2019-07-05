import Vue from 'vue'
import VueRouter from 'vue-router'
// 引入 view 组件
import { Login, Home, Dashboard, Announcement, Conf, Contest, ContestList, JudgeServer,
  Problem, ProblemList, User, PruneTestCase, ProblemImportOrExport } from './views'
// 设置vue使用VueRouter
Vue.use(VueRouter)

export default new VueRouter({
  mode: 'history',
  base: '/admin/',
  // 滚动行为箭头函数
  scrollBehavior: () => ({y: 0}),
  routes: [
    // 仅仅引入了login组件时候，背面空白背景色
    {
      path: '/login',
      name: 'login',
      component: Login
    },
    {
      // 登录之后会跳转到主目录,主目录然后再细分
      path: '/',
      component: Home,
      children: [
        {
          path: '',
          name: 'dashboard',
          component: Dashboard
        },
        {
          path: '/user',
          name: 'user',
          component: User
        },
        {
          path: '/announcement',
          name: 'announcement',
          component: Announcement
        },
        {
          path: '/conf',
          name: 'conf',
          component: Conf
        },
        {
          path: '/judge-server',
          name: 'judge-server',
          component: JudgeServer
        },
        {
          path: '/prune-test-case',
          name: 'prune-test-case',
          component: PruneTestCase
        },
        {
          path: '/problems',
          name: 'problem-list',
          component: ProblemList
        },
        {
          path: '/problem/create',
          name: 'create-problem',
          component: Problem
        },
        {
          path: '/problem/edit/:problemId',
          name: 'edit-problem',
          component: Problem
        },
        {
          path: '/problem/batch_ops',
          name: 'problem_batch_ops',
          component: ProblemImportOrExport
        },
        {
          path: '/contest/create',
          name: 'create-contest',
          component: Contest
        },
        {
          path: '/contest',
          name: 'contest-list',
          component: ContestList
        },
        {
          path: '/contest/:contestId/edit',
          name: 'edit-contest',
          component: Contest
        },
        {
          path: '/contest/:contestId/announcement',
          name: 'contest-announcement',
          component: Announcement
        },
        {
          path: '/contest/:contestId/problems',
          name: 'contest-problem-list',
          component: ProblemList
        },
        {
          path: '/contest/:contestId/problem/create',
          name: 'create-contest-problem',
          component: Problem
        },
        {
          path: '/contest/:contestId/problem/:problemId/edit',
          name: 'edit-contest-problem',
          component: Problem
        }
      ]
    },
    // 如果要请求后面的路径然而路由又没有的话就跳到登录
    {
      path: '*', redirect: '/login'
    }
  ]
})

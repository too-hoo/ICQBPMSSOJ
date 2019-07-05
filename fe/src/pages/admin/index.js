import 'babel-polyfill'
// 引入项目的核心模块：Vue、App、store、i18国际化引入、Element
import Vue from 'vue'
import App from './App.vue'
import store from '@/store'
import i18n from '@/i18n'
import Element from 'element-ui'
// 使用element-ui 对应的css文件，引入element框架的国际化语言为en，并定义变量为locale
import 'element-ui/lib/theme-chalk/index.css'
import locale from 'element-ui/lib/locale/lang/en'

// 导入过滤工具、路由、谷歌分析ID，vue分析器、数学工具组件
import filters from '@/utils/filters'
import router from './router'
import { GOOGLE_ANALYTICS_ID } from '@/utils/constants'
import VueAnalytics from 'vue-analytics'
import katex from '@/plugins/katex'

// 导入自定义组件
import Panel from './components/Panel.vue'
import IconBtn from './components/btn/IconBtn.vue'
import Save from './components/btn/Save.vue'
import Cancel from './components/btn/Cancel.vue'
import './style.less'

// register global utility filters.
// 注册全局实体过滤器
Object.keys(filters).forEach(key => {
  Vue.filter(key, filters[key])
})

// 使用谷歌分析ID
Vue.use(VueAnalytics, {
  id: GOOGLE_ANALYTICS_ID,
  router
})
// 使用Element框架
Vue.use(Element, {locale})
// 使用数学公式编辑器
Vue.use(katex)

// == 下面引入自定义组件的使用
// 使用自定义图标按钮组件
Vue.component(IconBtn.name, IconBtn)
// 使用自定义图板组件
Vue.component(Panel.name, Panel)
// 使用自定义保存按钮组件
Vue.component(Save.name, Save)
// 使用自定义取消按钮组件
Vue.component(Cancel.name, Cancel)

// 使用i18n国际化
Vue.use(Element, {
  i18n: (key, value) => i18n.t(key, value)
})

// 使用箭头函数定义全局的提示信息：错误、警告、
// 不想污染全局作用域。这种情况下，可以通过在原型上定义它们使其在每个 Vue 的实例中可用，success也是一样
// 在Vue实例里面使用this.$error,$ 是在 Vue 所有实例中都可用的属性的一个简单约定。
// 这样做会避免和已被定义的数据、方法、计算属性产生冲突。$可以换成￥，$_等，
// 大部分的消息在路由接口api.js里面实现了提示。
Vue.prototype.$error = (msg) => {
  Vue.prototype.$message({'message': msg, 'type': 'error'})
}

Vue.prototype.$warning = (msg) => {
  Vue.prototype.$message({'message': msg, 'type': 'warning'})
}

// 成功信息分成两种类型：成功信息不空：显示已经成功-ed，成功信息空了，显示首次成功
Vue.prototype.$success = (msg) => {
  if (!msg) {
    Vue.prototype.$message({'message': 'Succeeded', 'type': 'success'})
  } else {
    Vue.prototype.$message({'message': msg, 'type': 'success'})
  }
}

// 扩展Vue的工具包含：router，store，i18n国际化，并将其绑定到inde.html中id为app的盒子中
new Vue(Vue.util.extend({router, store, i18n}, App)).$mount('#app')

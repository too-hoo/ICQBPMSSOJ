<template>
  <Row type="flex" :gutter="18">
    <Col :span=24>
    <Panel shadow>
      <div slot="title">题目列表</div>
      <div slot="extra">
        <ul class="filter">
          <li>
            <Dropdown @on-click="filterByDifficulty">
              <span>{{query.difficulty === '' ? '难易程度' : query.difficulty}}
                <Icon type="arrow-down-b"></Icon>
              </span>
              <Dropdown-menu slot="list">
                <Dropdown-item name="">所有</Dropdown-item>
                <Dropdown-item name="较低">较低</Dropdown-item>
                <Dropdown-item name="中等">中等</Dropdown-item>
                <Dropdown-item name="较难">较难</Dropdown-item>
              </Dropdown-menu>
            </Dropdown>
          </li>
          <li>
            <i-switch size="large" @on-change="handleTagsVisible">
              <span slot="open">标签</span>
              <span slot="close">标签</span>
            </i-switch>
          </li>
          <li>
            <Input v-model="query.keyword"
                   @on-enter="filterByKeyword"
                   @on-click="filterByKeyword"
                   placeholder="输入关键字检索"
                   icon="ios-search-strong"/>
          </li>
          <li>
            <Button type="info" @click="onReset">
              <Icon type="refresh"></Icon>
              重 置
            </Button>
          </li>
        </ul>
      </div>
      <!--这里只使用了标签table，具体的显示交给js处理，这样才能将标签栏目控制显示或者隐藏-->
      <Table style="width: 100%; font-size: 16px;"
             :columns="problemTableColumns"
             :data="problemList"
             :loading="loadings.table"
             disabled-hover></Table>
    </Panel>
      <!--设置页码:总的数量，每页显示数量限制，路由的更改，同步当前页码-->
    <Pagination :total="total"
                :page-size="limit"
                @on-change="pushRouter"
                :current.sync="query.page">
    </Pagination>

    </Col>

    <!--<Col :span="0">-->
      <!--&lt;!&ndash;这里使用的也是一个panel组件，随便选择一个标签进行答题&ndash;&gt;-->
    <!--<Panel :padding="10">-->
      <!--<div slot="title" class="taglist-title">标 签</div>-->
      <!--<Button v-for="tag in tagList"-->
              <!--:key="tag.name"-->
              <!--@click="filterByTag(tag.name)"-->
              <!--type="ghost"-->
              <!--:disabled="query.tag === tag.name"-->
              <!--shape="circle"-->
              <!--class="tag-btn">{{tag.name}}-->
      <!--</Button>-->

      <!--<Button long id="pick-one" @click="pickone">-->
        <!--<Icon type="shuffle"></Icon>-->
        <!--Pick one-->
      <!--</Button>-->
    <!--</Panel>-->
    <!--<Spin v-if="loadings.tag" fix size="large"></Spin>-->
    <!--</Col>-->
  </Row>
</template>

<script>
  import { mapGetters } from 'vuex'
  import api from '@oj/api'
  import utils from '@/utils/utils'
  import { ProblemMixin } from '@oj/components/mixins'
  import Pagination from '@oj/components/Pagination'

  export default {
    name: 'ProblemList',
    mixins: [ProblemMixin],
    // 使用页码组件：每页的限制决定显示题目的数量
    components: {
      Pagination
    },
    data () {
      return {
        tagList: [],
        // 题目列表，点击显示ID和标题都可以进入到该题目的而详细页面
        problemTableColumns: [
          {
            title: 'DisplayID',
            key: '_id',
            width: 100,
            render: (h, params) => {
              return h('Button', {
                props: {
                  type: 'text',
                  size: 'large'
                },
                on: {
                  click: () => {
                    this.$router.push({name: 'problem-details', params: {problemID: params.row._id}})
                  }
                },
                style: {
                  padding: '2px 0'
                }
              }, params.row._id)
            }
          },
          {
            title: '标 题',
            width: 400,
            render: (h, params) => {
              return h('Button', {
                props: {
                  type: 'text',
                  size: 'large'
                },
                on: {
                  click: () => {
                    this.$router.push({name: 'problem-details', params: {problemID: params.row._id}})
                  }
                },
                style: {
                  padding: '2px 0',
                  overflowX: 'auto',
                  textAlign: 'left',
                  width: '100%'
                }
              }, params.row.title)
            }
          },
          {
            title: '等 级',
            render: (h, params) => {
              let t = params.row.difficulty
              let color = 'blue'
              if (t === 'Low') color = 'green'
              else if (t === 'High') color = 'yellow'
              return h('Tag', {
                props: {
                  color: color
                }
              }, params.row.difficulty)
            }
          },
          {
            title: '总提交数量',
            key: 'submission_number'
          },
          {
            title: 'AC通过率',
            render: (h, params) => {
              return h('span', this.getACRate(params.row.accepted_number, params.row.submission_number))
            }
          }
        ],
        problemList: [],
        // 每页限制显示的题目数为20条，首先定义一下页码组件的初始参数：总页数，加载，按条件查询
        limit: 20,
        total: 0,
        loadings: {
          table: true,
          tag: true
        },
        routeName: '',
        query: {
          keyword: '',
          difficulty: '',
          tag: '',
          page: 1
        }
      }
    },
    // html加载完成之后初始化数据
    mounted () {
      this.init()
    },
    methods: {
      // 初始化参数：路由名称，查询集，难易程度，关键字，标签，页码（如果页码小于1，就设置为1）
      init (simulate = false) {
        this.routeName = this.$route.name
        let query = this.$route.query
        this.query.difficulty = query.difficulty || ''
        this.query.keyword = query.keyword || ''
        this.query.tag = query.tag || ''
        this.query.page = parseInt(query.page) || 1
        if (this.query.page < 1) {
          this.query.page = 1
        }
        // simulate为false时候获取标签列表
        if (!simulate) {
          this.getTagList()
        }
        this.getProblemList()
      },
      // 设置路由跳转，首先过滤一下题目的信息是否为空
      pushRouter () {
        this.$router.push({
          name: 'problem-list',
          query: utils.filterEmptyValue(this.query)
        })
      },
      // 获取题目列表，根据页码的显示查询题目的数据：缓存大小，每页显示量，查询的数据
      getProblemList () {
        let offset = (this.query.page - 1) * this.limit
        this.loadings.table = true
        api.getProblemList(offset, this.limit, this.query).then(res => {
          this.loadings.table = false
          this.total = res.data.data.total
          this.problemList = res.data.data.results
          if (this.isAuthenticated) {
            this.addStatusColumn(this.problemTableColumns, res.data.data.results)
          }
        }, res => {
          this.loadings.table = false
        })
      },
      // 获取标签列表
      getTagList () {
        api.getProblemTagList().then(res => {
          this.tagList = res.data.data
          this.loadings.tag = false
        }, res => {
          this.loadings.tag = false
        })
      },
      // 通过标签过滤
      filterByTag (tagName) {
        this.query.tag = tagName
        this.query.page = 1
        this.pushRouter()
      },
      // 通过难度等级过滤
      filterByDifficulty (difficulty) {
        this.query.difficulty = difficulty
        this.query.page = 1
        this.pushRouter()
      },
      // 通过关键字过滤
      filterByKeyword () {
        this.query.page = 1
        this.pushRouter()
      },
      // 控制标签是否可见：可见value=true，就将列push进去，否则就将最后一列使用splice分割掉
      handleTagsVisible (value) {
        if (value) {
          this.problemTableColumns.push(
            {
              title: 'Tags',
              align: 'center',
              render: (h, params) => {
                let tags = []
                params.row.tags.forEach(tag => {
                  tags.push(h('Tag', {}, tag))
                })
                return h('div', {
                  style: {
                    margin: '8px 0'
                  }
                }, tags)
              }
            })
        } else {
          this.problemTableColumns.splice(this.problemTableColumns.length - 1, 1)
        }
      },
      // 重置题目列表
      onReset () {
        this.$router.push({name: 'problem-list'})
      },
      // 随机选择
      pickone () {
        api.pickone().then(res => {
          this.$success('祝你好运！')
          this.$router.push({name: 'problem-details', params: {problemID: res.data.data}})
        })
      }
    },
    // 涉及到用户提交，所以需要验证
    computed: {
      ...mapGetters(['isAuthenticated'])
    },
    // 监听路由的变化和用户是否已经经过验证
    watch: {
      '$route' (newVal, oldVal) {
        if (newVal !== oldVal) {
          this.init(true)
        }
      },
      'isAuthenticated' (newVal) {
        if (newVal === true) {
          this.init()
        }
      }
    }
  }
</script>

<style scoped lang="less">
  .taglist-title {
    margin-left: -10px;
    margin-bottom: -10px;
  }

  .tag-btn {
    margin-right: 5px;
    margin-bottom: 10px;
  }

  #pick-one {
    margin-top: 10px;
  }
</style>

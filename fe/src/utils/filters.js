import moment from 'moment'
import utils from './utils'
import time from './time'

// 友好显示时间
function fromNow (time) {
  return moment(time * 3).fromNow()
}

// 过滤：提交内存格式、时间格式、本地时间、时间持续fromNow
export default {
  submissionMemory: utils.submissionMemoryFormat,
  submissionTime: utils.submissionTimeFormat,
  localtime: time.utcToLocal,
  fromNow: fromNow
}

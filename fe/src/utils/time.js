import moment from 'moment'

// convert utc time to localtime
// 将utc格式的时间转换成为本地时间
function utcToLocal (utcDt, format = 'YYYY-M-D  HH:mm:ss') {
  return moment.utc(utcDt).local().format(format)
}

// get duration from startTime to endTime, return like 3 days, 2 hours, one year ..
// 获取从开始到结束的时间，返回的格式如：3 days， 2 hours， one year
function duration (startTime, endTime) {
  let start = moment(startTime)
  let end = moment(endTime)
  let duration = moment.duration(start.diff(end, 'seconds'), 'seconds')
  if (duration.days() !== 0) {
    return duration.humanize()
  }
  return Math.abs(duration.asHours().toFixed(1)) + ' hours'
}

// 秒的格式
function secondFormat (seconds) {
  let m = moment.duration(seconds, 'seconds')
  return m.hours() + ':' + m.minutes() + ':' + m.seconds()
}

export default {
  utcToLocal: utcToLocal,
  duration: duration,
  secondFormat: secondFormat
}

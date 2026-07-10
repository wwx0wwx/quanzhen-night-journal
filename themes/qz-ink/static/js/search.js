(function () {
  var input = document.getElementById('search-input')
  var status = document.getElementById('search-status')
  var results = document.getElementById('search-results')
  if (!input || !results) return

  var index = []
  var ready = false

  function esc(s) {
    return String(s || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
  }

  function render(items, q) {
    if (!q) {
      results.innerHTML = ''
      status.textContent = ready ? '输入关键词开始搜索。' : '加载索引中…'
      return
    }
    if (!items.length) {
      results.innerHTML = ''
      status.textContent = '没有找到相关文章。'
      return
    }
    status.textContent = '找到 ' + items.length + ' 篇'
    results.innerHTML = items
      .map(function (item) {
        return (
          '<article class="post-item">' +
          '<time datetime="' +
          esc(item.date) +
          '">' +
          esc(item.date) +
          '</time>' +
          '<h2><a href="' +
          esc(item.permalink) +
          '">' +
          esc(item.title) +
          '</a></h2>' +
          (item.summary
            ? '<p class="summary">' + esc(item.summary).slice(0, 120) + '</p>'
            : '') +
          '</article>'
        )
      })
      .join('')
  }

  function search(q) {
    q = (q || '').trim().toLowerCase()
    if (!q) return render([], '')
    var hits = index.filter(function (item) {
      var hay = ((item.title || '') + ' ' + (item.summary || '')).toLowerCase()
      return hay.indexOf(q) !== -1
    })
    render(hits, q)
  }

  fetch('/index.json')
    .then(function (r) {
      return r.json()
    })
    .then(function (data) {
      index = Array.isArray(data) ? data : []
      ready = true
      status.textContent = '共 ' + index.length + ' 篇文章可检索。'
      if (input.value) search(input.value)
    })
    .catch(function () {
      status.textContent = '索引加载失败，请稍后重试。'
    })

  input.addEventListener('input', function () {
    search(input.value)
  })
})()

(function () {
  var btn = document.getElementById('theme-toggle')
  if (!btn) return

  function current() {
    return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light'
  }

  function apply(theme) {
    document.documentElement.setAttribute('data-theme', theme)
    try {
      localStorage.setItem('qz-ink-theme', theme)
    } catch (e) {}
  }

  btn.addEventListener('click', function () {
    apply(current() === 'dark' ? 'light' : 'dark')
  })
})()

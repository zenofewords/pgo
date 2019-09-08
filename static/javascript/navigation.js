const ready = (runGeneric) => {
  if (document.attachEvent ? document.readyState === 'complete' : document.readyState !== 'loading') {
    runGeneric()
  } else {
    document.addEventListener('DOMContentLoaded', runGeneric)
  }
}

ready(() => {
  const inputMenuToggle = document.getElementById('inputMenuToggle')
  const menuLines = document.querySelectorAll('.menu-line')
  const changelogInfoWrapper = document.querySelector('.changelog-info-wrapper')

  inputMenuToggle.addEventListener('focus', () => {
    for (let i = 0; i < menuLines.length; i++) {
      menuLines[i].classList.add('focus')
    }
  })
  inputMenuToggle.addEventListener('blur', () => {
    for (let i = 0; i < menuLines.length; i++) {
      menuLines[i].classList.remove('focus')
    }
  })
  document.querySelector('.changelog-toggle').addEventListener('click', () => {
    changelogInfoWrapper.hidden = !changelogInfoWrapper.hidden
  })
})

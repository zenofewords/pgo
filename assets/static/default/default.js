import Choices from 'choices.js'

const ready = (runDefault) => {
  if (document.attachEvent ? document.readyState === 'complete' : document.readyState !== 'loading') {
    runDefault()
  } else {
    document.addEventListener('DOMContentLoaded', runDefault)
  }
}

ready(() => {
  const searchInput = new Choices(
    '.list-search',
    {
      searchPlaceholderValue: 'Type name',
      searchResultLimit: 5,
      itemSelectText: '',
    }
  )
  searchInput.passedElement.addEventListener('change', (event) => {
    window.location = `${window.pgoURLs['list-url']}${event.currentTarget.value}`
  })

  const backToTop = document.getElementById('back-to-top')
  if (backToTop) {
    backToTop.addEventListener('click', (event) => {
      event.preventDefault()
      window.scroll(0, 0)
    })
  }
})

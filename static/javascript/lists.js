import '../sass/lists.sass'
import './navigation.js'
import {
  choicesOptions,
  processInput,
} from './utils.js'
import Choices from 'choices.js'

const ready = (runGeneric) => {
  if (document.attachEvent ? document.readyState === 'complete' : document.readyState !== 'loading') {
    runGeneric()
  } else {
    document.addEventListener('DOMContentLoaded', runGeneric)
  }
}

ready(() => {
  const listSearchInput = document.querySelector('.list-search')
  const searchInput = listSearchInput ? new Choices('.list-search', choicesOptions) : undefined
  const moveTypeFilter = document.getElementById('move-type-filter')

  if (listSearchInput && listSearchInput.id === 'pokemon-search') {
    searchInput.input.element.addEventListener('input', processInput.bind(null, searchInput))
  }
  moveTypeFilter && moveTypeFilter.addEventListener('change', event => {
    const searchParams = window.location.search.split(/[?&]+/).slice(1)
    const index = searchParams.findIndex(element => element.includes('selected-move-type'))
    searchParams[index] = `selected-move-type=${event.currentTarget.value}`

    let query
    if (searchParams.length > 1) {
      query = searchParams.join('&')
    } else {
      query = searchParams[index]
    }
    window.location = `${window.pgoURLs['list-url']}?${query}`
  })

  searchInput && searchInput.passedElement.element.addEventListener('change', event => {
    window.location = `${window.pgoURLs['list-url']}${event.currentTarget.value}`
  })
})

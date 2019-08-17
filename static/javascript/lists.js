import '../sass/lists.sass'
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
  const searchInput = listSearchInput ? new Choices(
    '.list-search',
    {
      searchPlaceholderValue: 'Type name',
      searchResultLimit: 5,
      itemSelectText: '',
    }
  ) : undefined

  const typeFilterSelectInput = document.querySelector('.type-filter')
  const typeFilterSelect = typeFilterSelectInput ? new Choices(
    '.type-filter',
    {
      maxItemCount: 4,
      placeholderValue: 'Filter by type (up to 4)',
    }
  ) : undefined

  const resistanceFilterSelectInput = document.querySelector('.resistance-filter')
  const resistanceFilterSelect = resistanceFilterSelectInput ? new Choices(
    '.resistance-filter',
    {
      maxItemCount: 6,
      placeholderValue: 'Filter by resistance (up to 6)',
    }
  ) : undefined

  const superEffectivenessFilterSelectInput = document.querySelector('.super-effectiveness-filter')
  const superEffectivenessFilterSelect = superEffectivenessFilterSelectInput ? new Choices(
    '.super-effectiveness-filter',
    {
      maxItemCount: 2,
      placeholderValue: 'Filter by super effectiveness (up to 2)',
    }
  ) : undefined

  const pokemonListFilterWrapper = document.getElementById('pokemon-list-filter-wrapper')
  const searchPokemonWrapper = document.querySelector('.search-pokemon-wrapper')
  const moveTypeFilter = document.getElementById('move-type-filter')

  moveTypeFilter && moveTypeFilter.addEventListener('change', event => {
    const searchParams = window.location.search.split(/[?&]+/).slice(1)
    const index = searchParams.findIndex(element => element.includes('selected-move-type'))
    searchParams[index] = `selected-move-type=${event.currentTarget.value}`

    let query
    if (searchParams.length > 1) {
      query = searchParams.join('&')
    } else {
      query = searchParams[0]
    }
    window.location = `${window.pgoURLs['list-url']}?${query}`
  })

  searchInput && searchInput.passedElement.element.addEventListener('change', event => {
    window.location = `${window.pgoURLs['list-url']}${event.currentTarget.value}`
  })

  typeFilterSelect && typeFilterSelect.passedElement.element.addEventListener('change', event => {
    const placeholder = typeFilterSelect.placeholder
    if (typeFilterSelect.passedElement.element.selectedOptions.length > 0) {
      typeFilterSelect.input.placeholder = ''
    } else {
      typeFilterSelect.input.placeholder = placeholder
    }
  })

  resistanceFilterSelect && resistanceFilterSelect.passedElement.element.addEventListener('change', event => {
    const placeholder = resistanceFilterSelect.placeholder
    if (resistanceFilterSelect.passedElement.element.selectedOptions.length > 0) {
      resistanceFilterSelect.input.placeholder = ''
    } else {
      resistanceFilterSelect.input.placeholder = placeholder
    }
  })

  superEffectivenessFilterSelect && superEffectivenessFilterSelect.passedElement.element.addEventListener('change', event => {
    const placeholder = superEffectivenessFilterSelect.placeholder
    if (superEffectivenessFilterSelect.passedElement.element.selectedOptions.length > 0) {
      superEffectivenessFilterSelect.input.placeholder = ''
    } else {
      superEffectivenessFilterSelect.input.placeholder = placeholder
    }
  })

  const removePlaceholderIfSelected = () => {
    if (typeFilterSelect && typeFilterSelect.passedElement.element.selectedOptions.length > 0) {
      typeFilterSelect.input.placeholder = ''
    }
    if (resistanceFilterSelect && resistanceFilterSelect.passedElement.element.selectedOptions.length > 0) {
      resistanceFilterSelect.input.placeholder = ''
    }
    if (superEffectivenessFilterSelect && superEffectivenessFilterSelect.passedElement.element.selectedOptions.length > 0) {
      superEffectivenessFilterSelect.input.placeholder = ''
    }
  }

  removePlaceholderIfSelected()
  if (pokemonListFilterWrapper) {
    pokemonListFilterWrapper.hidden = false
  }
  if (searchPokemonWrapper) {
    searchPokemonWrapper.hidden = false
  }
})

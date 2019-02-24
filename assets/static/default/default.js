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

  const typeFilterSelectInput = document.querySelector('.type-filter')
  let typeFilterSelect
  if (typeFilterSelectInput) {
    typeFilterSelect = new Choices(
      '.type-filter',
      {
        maxItemCount: 4,
        placeholderValue: 'Filter by type (up to 4)',
      }
    )
  }

  const resistanceFilterSelectInput = document.querySelector('.resistance-filter')
  let resistanceFilterSelect
  if (resistanceFilterSelectInput) {
    resistanceFilterSelect = new Choices(
      '.resistance-filter',
      {
        maxItemCount: 6,
        placeholderValue: 'Filter by resistance (up to 6)',
      }
    )
  }

  const superEffectivenessFilterSelectInput = document.querySelector('.super-effectiveness-filter')
  let superEffectivenessFilterSelect
  if (superEffectivenessFilterSelectInput) {
    superEffectivenessFilterSelect = new Choices(
      '.super-effectiveness-filter',
      {
        maxItemCount: 2,
        placeholderValue: 'Filter by super effectiveness (up to 2)',
      }
    )
  }
  const pokemonListFilterWrapper = document.getElementById('pokemon-list-filter-wrapper')
  const searchPokemonWrapper = document.querySelector('.search-pokemon-wrapper')
  const moveTypeFilter = document.getElementById('move-type-filter')

  if (moveTypeFilter) {
    moveTypeFilter.addEventListener('change', event => {
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
  }

  searchInput.passedElement.addEventListener('change', event => {
    window.location = `${window.pgoURLs['list-url']}${event.currentTarget.value}`
  })

  if (typeFilterSelect) {
    typeFilterSelect.passedElement.addEventListener('change', event => {
      const placeholder = typeFilterSelect.placeholder
      if (typeFilterSelect.passedElement.selectedOptions.length > 0) {
        typeFilterSelect.input.placeholder = ''
      } else {
        typeFilterSelect.input.placeholder = placeholder
      }
    })
  }

  if (resistanceFilterSelect) {
    resistanceFilterSelect.passedElement.addEventListener('change', event => {
      const placeholder = resistanceFilterSelect.placeholder
      if (resistanceFilterSelect.passedElement.selectedOptions.length > 0) {
        resistanceFilterSelect.input.placeholder = ''
      } else {
        resistanceFilterSelect.input.placeholder = placeholder
      }
    })
  }

  if (superEffectivenessFilterSelect) {
    superEffectivenessFilterSelect.passedElement.addEventListener('change', event => {
      const placeholder = superEffectivenessFilterSelect.placeholder
      if (superEffectivenessFilterSelect.passedElement.selectedOptions.length > 0) {
        superEffectivenessFilterSelect.input.placeholder = ''
      } else {
        superEffectivenessFilterSelect.input.placeholder = placeholder
      }
    })
  }

  const removePlaceholderIfSelected = () => {
    if (typeFilterSelect && typeFilterSelect.passedElement.selectedOptions.length > 0) {
      typeFilterSelect.input.placeholder = ''
    }
    if (resistanceFilterSelect && resistanceFilterSelect.passedElement.selectedOptions.length > 0) {
      resistanceFilterSelect.input.placeholder = ''
    }
    if (superEffectivenessFilterSelect && superEffectivenessFilterSelect.passedElement.selectedOptions.length > 0) {
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

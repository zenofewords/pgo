export const breakpointCalcURL = '/breakpoint-calc/'

export const choicesOptions = {
  searchPlaceholderValue: 'Type 3 or more characters',
  searchFloor: 3,
  searchResultLimit: 10,
  itemSelectText: '',
  loadingText: '',
  shouldSort: false,
}

const debounceEvent = (callbackFn, time, interval) =>
  (...args) => {
    clearTimeout(interval)
    interval = setTimeout(() => {
      interval = null
      callbackFn(...args)
    }, time)
  }

export const processInput = debounceEvent((select, event) => {
  const value = event.target.value

  if (value.length > 2) {
    fetchPokemon(select, value)
  }
}, 500)

const fetchPokemon = (select, value) => {
  const request = new XMLHttpRequest()
  request.open(
    'GET',
    `${window.pgoAPIURLs['simple-pokemon-list']}?pokemon-slug=${value}`,
    true
  )
  request.onload = () => {
    if (request.status >= 200 && request.status < 400) {
      const json = JSON.parse(request.responseText)
      select.setChoices(json.results, 'value', 'label', true)
    } else {
      showErrors()
    }
  }
  request.onerror = () => {
    showErrors()
  }
  request.send()
}

export const showErrors = () => {
  const results = document.querySelector('.results')
  results.hidden = false
  results.classList.add('error-text')
  results.innerHTML = ':( something broke, let me know if refreshing the page does not help.'
}

export const formatParams = (params) => {
  const paramsCopy = {...params}
  delete paramsCopy.status
  delete paramsCopy.staleTab

  return `?${Object.keys(paramsCopy).map((key) =>
    `${key}=${encodeURIComponent(paramsCopy[key])}`
  ).join('&')}`
}

export const updateBrowserHistory = (getParams, url) => {
  window.history.pushState(
    {}, null, url + getParams
  )
}

export const fetchPokemonChoice = (select, pokemonSlug) => {
  const request = new XMLHttpRequest()
  request.open(
    'GET',
    `${window.pgoAPIURLs['simple-pokemon-list']}${pokemonSlug}/`,
    true
  )
  request.onload = () => {
    if (request.status >= 200 && request.status < 400) {
      const json = JSON.parse(request.responseText)
      select.setChoices([
        {value: json.value, label: json.label, selected: true}
      ], 'value', 'label', true)
    } else {
      showErrors()
    }
  }
  request.onerror = () => {
    showErrors()
  }
  request.send()
}

export const validateLevel = (input) => {
  const val = input.value.replace(',', '.')
  let level = parseFloat(val)

  if (level < 0) {
    level *= -1
  }
  if (level < 1) {
    level = 1
  }
  if (level > 41) {
    level = 41
  }
  if (level > 40 && level % 2 !== 0) {
    level = Math.floor(level)
  }
  if ((level * 10) % 5 !== 0) {
    level = parseInt(level)
  }
  return level
}

export const createMoveOption = (moveData, moveId, moveKey, form, pokemon = 'attacker') => {
  const move = moveData.move

  return new Option(
    pokemon === 'attacker' ? `${move.name} ${moveData.legacy ? '*' : ''} (${move.power})` : move.name,
    move.id,
    false,
    determineSelectedMove(moveId, move, moveKey, form)
  )
}

const determineSelectedMove = (moveId, move, type, form) => {
  if (moveId > 0 && moveId === move.id) {
    form[type] = move.id
    return true
  }
  return false
}

export const processParams = (params) => {
  const queryDict = {}
  params.substr(1).split('&').forEach((item) => {
    queryDict[item.split('=')[0]] = item.split('=')[1]
  })
  return queryDict
}

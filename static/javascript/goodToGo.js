import '../sass/goodToGo.sass'
import './navigation.js'
import Choices from 'choices.js'

const ready = (run) => {
  if (document.attachEvent ? document.readyState === 'complete' : document.readyState !== 'loading') {
    run()
  } else {
    document.addEventListener('DOMContentLoaded', run)
  }
}

ready(() => {
  // constants
  const FORM_STATE = {
    SUBMITTING: 'submitting',
    READY: 'ready',
    ERROR: 'error',
  }

  // inputs
  const selectAttacker = new Choices(
    '.select-attacker',
    {
      searchPlaceholderValue: 'Type in the attacker\'s name',
      searchResultLimit: 5,
      itemSelectText: '',
      loadingText: '',
    }
  )
  const selectAttackerQuickMove = document.getElementById('select-quick-move')
  const selectAttackerAtkIv = document.getElementById('select-atk-iv')
  const selectWeatherCondition = document.getElementById('select-weather-condition')
  const selectFriendshipBoost = document.getElementById('select-friendship-boost')

  const tier36BossesToggle = document.querySelector('.toggle-tier-3-6-raid-bosses')
  const tier12BossesToggle = document.querySelector('.toggle-tier-1-2-raid-bosses')

  const summary = document.querySelector('.output-wrapper')
  const results = document.querySelector('.results')

  let form = {
    attacker: selectAttacker.value,
    attack_iv: selectAttackerAtkIv.value,
    quick_move: selectAttackerQuickMove.value,
    cinematic_move: 1,
    weather_condition: selectWeatherCondition.value,
    friendship_boost: selectFriendshipBoost.value,
    tier_3_6_raid_bosses: true,
    tier_1_2_raid_bosses: false,
    status: FORM_STATE.READY,
  }

  // events
  selectAttacker.passedElement.element.addEventListener('change', (event) => {
    clearMoveInputs()
    selectPokemonMoves(event.currentTarget.value)

    form.attacker = event.currentTarget.value
    submitForm()
  })
  selectAttackerAtkIv.addEventListener('change', (event) => {
    form.attack_iv = event.currentTarget.value

    submitForm().then(() => selectAttackerAtkIv.focus())
  })
  selectAttackerQuickMove.addEventListener('change', (event) => {
    form.quick_move = event.currentTarget.value

    submitForm().then(() => selectAttackerQuickMove.focus())
  })
  selectWeatherCondition.addEventListener('change', (event) => {
    form.weather_condition = event.currentTarget.value

    submitForm().then(() => selectWeatherCondition.focus())
  })
  selectFriendshipBoost.addEventListener('change', (event) => {
    form.friendship_boost = event.currentTarget.value

    submitForm().then(() => selectFriendshipBoost.focus())
  })
  tier36BossesToggle.addEventListener('click', (event) => {
    togglePressed(tier36BossesToggle)
    form.tier_3_6_raid_bosses = !form.tier_3_6_raid_bosses
    submitForm().then(() => tier36BossesToggle.focus())
  })
  tier12BossesToggle.addEventListener('click', (event) => {
    togglePressed(tier12BossesToggle)
    form.tier_1_2_raid_bosses = !form.tier_1_2_raid_bosses
    submitForm().then(() => tier12BossesToggle.focus())
  })

  const clearMoveInputs = () => {
    if (form.status !== FORM_STATE.SUBMITTING) {
      const quickMoveSelect = selectAttackerQuickMove

      quickMoveSelect.innerHTML = ''
      quickMoveSelect.append(
        '<option value="-1" disabled selected>Select quick move</option>'
      )
      form['quick_move'] = -1
    }
  }

  const selectPokemonMoves = (value) => {
    if (parseInt(value) > 0) {
      const request = new XMLHttpRequest()
      request.open('GET', window.pgoAPIURLs['move-list'] + '?pokemon-id=' + value, true)

      request.onload = () => {
        if (request.status >= 500) {
          showErrors()
        }
        if (request.status >= 200 && request.status < 400) {
          const json = JSON.parse(request.responseText)
          selectMoves(json)
        } else {
          showErrors()
        }
      }
      request.onerror = () => {
        form.status = FORM_STATE.ERROR
      }
      request.send()
    } else {
      selectAttackerQuickMove.disabled = true

      clearMoveInputs()
    }
  }

  const selectMoves = (data) => {
    const quickMoveSelect = selectAttackerQuickMove
    const quickMoveKey = 'quick_move'
    const quickMoveId = parseInt(form[quickMoveKey])

    data.results.forEach((moveData, i) => {
      const move = moveData.move

      if (move.category === 'QK') {
        if (form.status !== FORM_STATE.SUBMITTING) {
          quickMoveSelect.disabled = false
        }
        quickMoveSelect.options.add(createMoveOption(move, quickMoveId, quickMoveKey))
      }
    })
    form[quickMoveKey] = quickMoveSelect.value

    submitForm()
  }

  const createMoveOption = (move, moveId, moveKey) => {
    return new Option(
      move.name + ' (' + move.power + ')',
      move.id,
      false,
      determineSelectedMove(moveId, move, moveKey)
    )
  }

  const determineSelectedMove = (moveId, move, type) => {
    if (moveId > 0 && moveId === move.id) {
      form[type] = move.id
      return true
    }
    return false
  }

  const togglePressed = (button) => {
    if (button.classList.contains('pressed')) {
      button.classList.remove('pressed')
    } else {
      button.classList.add('pressed')
    }
  }

  const submitForm = () => {
    if (form.status !== FORM_STATE.SUBMITTING) {
      for (const key in form) {
        const value = String(form[key])

        if (value === 'undefined' || value === '-1') {
          return new Promise(() => {
            return false
          })
        }
      }

      return new Promise((resolve) => {
        if (form.status !== FORM_STATE.SUBMITTING) {
          form.status = FORM_STATE.SUBMITTING
          toggleLoading()

          const request = new XMLHttpRequest()
          const getParams = formatParams(form)
          const url = window.pgoAPIURLs['good-to-go'] + getParams
          request.open('GET', url, true)

          request.onload = () => {
            if (request.status >= 500) {
              showErrors()
            } else {
              const json = JSON.parse(request.responseText)

              if (request.status >= 200 && request.status < 400) {
                updateBrowserHistory(getParams)
              } else {
                showErrors()
              }
              form.status = FORM_STATE.READY

              toggleLoading()
              renderResults(json)
              resolve()
            }
          }
          request.onerror = () => {
            form.status = FORM_STATE.ERROR
            showErrors()
            resolve()
          }
          request.send()
        }
      })
    }
  }

  const toggleLoading = () => {
    const submitting = form.status === FORM_STATE.SUBMITTING
    submitting ? selectAttacker.disable() : selectAttacker.enable()

    selectAttackerQuickMove.disabled = submitting || selectAttackerQuickMove.value < 0
    selectAttackerAtkIv.disabled = submitting
    selectWeatherCondition.disabled = submitting
    selectFriendshipBoost.disabled = submitting
    tier36BossesToggle.disabled = submitting
    tier12BossesToggle.disabled = submitting
  }

  const renderResults = (data) => {
    summary.innerHTML = data.summary
    results.innerHTML = ''
    results.appendChild(document.createElement('hr'))

    if (data.tier_3_6_raid_bosses.length === 0 && data.tier_1_2_raid_bosses.length === 0) {
      results.innerHTML = 'Please select at least one option (tier 3-6 bosses or tier 1-2 bosses).'
    }

    if (data.tier_3_6_raid_bosses.length > 0) {
      renderResultSubcategory(results, data.tier_3_6_raid_bosses)
    }
    if (data.tier_1_2_raid_bosses.length > 0) {
      renderResultSubcategory(results, data.tier_1_2_raid_bosses)
    }
    results.hidden = false
  }

  const renderResultSubcategory = (rootElement, data) => {
    for (var i = data.length - 1; i >= 0; i--) {
      const result = data[i]
      const resultsWrapper = document.createElement('div')
      const resultsHeader = document.createElement('p')

      resultsWrapper.className = 'results-wrapper'
      resultsHeader.className = 'results-header'
      resultsHeader.innerHTML = 'Tier ' + result.tier + ' | ' + result.quick_move +
        ' breakpoints: ' + result.final_breakpoints_reached + ' / ' + result.total_breakpoints

      const indicator = document.createElement('span')
      indicator.className = (result.final_breakpoints_reached !== result.total_breakpoints && 'warning-icon')

      resultsHeader.appendChild(indicator)
      resultsWrapper.appendChild(resultsHeader)
      resultsWrapper.addEventListener('click', (event) => {
        const target = event.currentTarget

        target.childNodes.forEach((node, i) => {
          if (i > 0) {
            node.hidden = !node.hidden
          }
        })
      })

      for (var j = result.matchups.length - 1; j >= 0; j--) {
        const matchup = result.matchups[j]

        const resultRow = document.createElement('p')
        resultRow.className = 'single-result'
        resultRow.hidden = true

        const rowIndicator = document.createElement('span')
        rowIndicator.className = (!matchup.final_breakpoint_reached && 'warning-icon')
        resultRow.innerHTML = matchup.damage_per_hit + ' / ' + matchup.max_damage_per_hit +
          ' damage per hit vs ' + matchup.defender
        resultRow.prepend(rowIndicator)

        resultsWrapper.appendChild(resultRow)
      }
      rootElement.appendChild(resultsWrapper)
    }
  }

  const updateBrowserHistory = (getParams) => {
    window.history.pushState(
      {}, null, '/good-to-go/' + getParams
    )
  }

  const formatParams = (params) => {
    const paramsCopy = Object.assign({}, params)
    delete paramsCopy.status

    return '?' + Object.keys(paramsCopy).map((key) => {
      return key + '=' + encodeURIComponent(paramsCopy[key])
    }).join('&')
  }

  const restoreTierSelection = (data) => {
    data.tier_3_6_raid_bosses
      ? tier36BossesToggle.classList.add('pressed')
      : tier36BossesToggle.classList.remove('pressed')
    data.tier_1_2_raid_bosses
      ? tier12BossesToggle.classList.add('pressed')
      : tier12BossesToggle.classList.remove('pressed')
  }

  const restoreForm = (data) => {
    selectAttacker.setChoiceByValue(String(data.attacker))

    selectAttackerAtkIv.value = data.attack_iv
    selectWeatherCondition.value = data.weather_condition
    selectFriendshipBoost.value = data.friendship_boost

    selectPokemonMoves(data.attacker, 'attacker')
    selectPokemonMoves(data.defender, 'defender')
    restoreTierSelection(data)

    form = data
    form.status = FORM_STATE.READY
    submitForm()
  }

  const showErrors = () => {
    results.hidden = false
    results.classList.add('error-text')
    results.innerHTML = ':( something broke, let me know if refreshing the page does not help.'
  }

  if (form.attacker && !(form.attacker_quick_move)) {
    const queryDict = {}
    location.search.substr(1).split('&').forEach((item) => {
      queryDict[item.split('=')[0]] = item.split('=')[1]
    })
    restoreForm(queryDict)
  } else if (Object.keys(window.initialData).length > 0) {
    restoreForm(window.initialData)
  }
})

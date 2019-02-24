import Choices from 'choices.js'

const ready = (runGoodToGo) => {
  if (document.attachEvent ? document.readyState === 'complete' : document.readyState !== 'loading') {
    runGoodToGo()
  } else {
    document.addEventListener('DOMContentLoaded', runGoodToGo)
  }
}

ready(() => {
  const FORM_STATE = {
    SUBMITTING: 'submitting',
    READY: 'ready',
    ERROR: 'error',
  }

  const selectAttacker = new Choices(
    '.good-to-go-select-attacker',
    {
      searchPlaceholderValue: 'Type in the attacker\'s name',
      searchResultLimit: 5,
      itemSelectText: '',
    }
  )
  const selectAttackerQuickMove = document.getElementById('good-to-go-select-quick-move')
  const selectAttackerCinematicMove = document.getElementById('good-to-go-select-cinematic-move')
  const selectAttackerAtkIv = document.getElementById('good-to-go-select-atk-iv')
  const selectWeatherCondition = document.getElementById('good-to-go-select-weather-condition')
  const selectFriendshipBoost = document.getElementById('good-to-go-select-friendship-boost')

  const tier36BossesButton = document.getElementById('toggle-tier-3-6-raid-bosses')
  const tier36BossesCheckbox = document.getElementById('tier-3-6-raid-bosses')
  const tier12BossesButton = document.getElementById('toggle-tier-1-2-raid-bosses')
  const tier12BossesCheckbox = document.getElementById('tier-1-2-raid-bosses')
  const relevantDefendersButton = document.getElementById('toggle-relevant-defenders')
  const relevantDefendersCheckbox = document.getElementById('relevant-defenders')

  const goodToGoSummary = document.getElementById('good-to-go-summary-text')
  const goodToGoResults = document.querySelector('.good-to-go-results')

  let goodToGoForm = {
    attacker: selectAttacker.value,
    attack_iv: selectAttackerAtkIv.value,
    quick_move: selectAttackerQuickMove.value,
    cinematic_move: selectAttackerCinematicMove.value,
    weather_condition: selectWeatherCondition.value,
    friendship_boost: selectFriendshipBoost.value,
    tier_3_6_raid_bosses: tier36BossesCheckbox.checked,
    tier_1_2_raid_bosses: tier12BossesCheckbox.checked,
    relevant_defenders: relevantDefendersCheckbox.checked,
    status: FORM_STATE.READY,
  }

  selectAttacker.passedElement.addEventListener('change', (event) => {
    clearMoveInputs()
    selectPokemonMoves(event.currentTarget.value)

    goodToGoForm.attacker = event.currentTarget.value
    submitGoodToGoForm()
  })
  selectAttackerAtkIv.addEventListener('change', (event) => {
    goodToGoForm.attack_iv = event.currentTarget.value

    submitGoodToGoForm().then(() => selectAttackerAtkIv.focus())
  })
  selectAttackerQuickMove.addEventListener('change', (event) => {
    goodToGoForm.quick_move = event.currentTarget.value

    submitGoodToGoForm().then(() => selectAttackerQuickMove.focus())
  })
  selectAttackerCinematicMove.addEventListener('change', (event) => {
    goodToGoForm.cinematic_move = event.currentTarget.value

    submitGoodToGoForm().then(() => selectAttackerCinematicMove.focus())
  })
  selectWeatherCondition.addEventListener('change', (event) => {
    goodToGoForm.weather_condition = event.currentTarget.value

    submitGoodToGoForm().then(() => selectWeatherCondition.focus())
  })
  selectFriendshipBoost.addEventListener('change', (event) => {
    goodToGoForm.friendship_boost = event.currentTarget.value

    submitGoodToGoForm().then(() => selectFriendshipBoost.focus())
  })
  tier36BossesButton.addEventListener('click', (event) => {
    event.preventDefault()

    toggleButtonCheckbox(tier36BossesButton, tier36BossesCheckbox)
    goodToGoForm.tier_3_6_raid_bosses = tier36BossesCheckbox.checked

    submitGoodToGoForm().then(() => tier36BossesButton.focus())
  })
  tier12BossesButton.addEventListener('click', (event) => {
    event.preventDefault()

    toggleButtonCheckbox(tier12BossesButton, tier12BossesCheckbox)
    goodToGoForm.tier_1_2_raid_bosses = tier12BossesCheckbox.checked

    submitGoodToGoForm().then(() => tier12BossesButton.focus())
  })
  relevantDefendersButton.addEventListener('click', (event) => {
    // event.preventDefault()

    // toggleButtonCheckbox(relevantDefendersButton, relevantDefendersCheckbox)
    // goodToGoForm.relevant_defenders = relevantDefendersCheckbox.checked

    // submitGoodToGoForm().then(() => relevantDefendersButton.focus())()
  })

  // functions
  const initialFetch = () => {
    return new Promise((resolve) => {
      if (goodToGoForm.status !== FORM_STATE.SUBMITTING) {
        goodToGoForm.status = FORM_STATE.SUBMITTING
        toggleLoading()

        selectAttacker.ajax((callback) => {
          fetch(window.pgoAPIURLs['simple-pokemon-list']).then((response) => {
            response.json().then((data) => {
              callback(data, 'value', 'label')
            }).then(() => {
              goodToGoForm.status = FORM_STATE.READY
              toggleLoading()
              resolve()
            })
          }).catch(() => {
            goodToGoForm.status = FORM_STATE.ERROR
            showErrors()
            resolve()
          })
        })
      }
    })
  }

  const clearMoveInputs = () => {
    if (goodToGoForm.status !== FORM_STATE.SUBMITTING) {
      const quickMoveSelect = selectAttackerQuickMove
      const cinematicMoveSelect = selectAttackerCinematicMove

      quickMoveSelect.innerHTML = ''
      quickMoveSelect.append(
        '<option value="-1" disabled selected>Select quick move</option>'
      )
      cinematicMoveSelect.innerHTML = ''
      cinematicMoveSelect.append(
        '<option value="-1" disabled selected>Select cinematic move</option>'
      )
      goodToGoForm['quick_move'] = -1
      goodToGoForm['cinematic_move'] = -1
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
        goodToGoForm.status = FORM_STATE.ERROR
      }
      request.send()
    } else {
      selectAttackerQuickMove.disabled = true
      selectAttackerCinematicMove.disabled = true

      clearMoveInputs()
    }
  }

  const selectMoves = (data) => {
    const quickMoveSelect = selectAttackerQuickMove
    const cinematicMoveSelect = selectAttackerCinematicMove

    const quickMoveKey = 'quick_move'
    const cinematicMoveKey = 'cinematic_move'

    const quickMoveId = parseInt(goodToGoForm[quickMoveKey])
    const cinematicMoveId = parseInt(goodToGoForm[cinematicMoveKey])

    data.forEach((moveData, i) => {
      const move = moveData.move

      if (move.category === 'QK') {
        if (goodToGoForm.status !== FORM_STATE.SUBMITTING) {
          quickMoveSelect.disabled = false
        }
        quickMoveSelect.options.add(createMoveOption(move, quickMoveId, quickMoveKey))
      } else {
        cinematicMoveSelect.disabled = true
        cinematicMoveSelect.options.add(createMoveOption(move, cinematicMoveId, cinematicMoveKey))
      }
    })
    goodToGoForm[quickMoveKey] = quickMoveSelect.value
    goodToGoForm[cinematicMoveKey] = cinematicMoveSelect.value

    submitGoodToGoForm()
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
      goodToGoForm[type] = move.id
      return true
    }
    return false
  }

  const toggleButtonCheckbox = (button, checkbox) => {
    checkbox.checked = !checkbox.checked

    if (checkbox.checked) {
      button.classList.add('btn-info')
      button.classList.remove('btn-default')
    } else {
      button.classList.add('btn-default')
      button.classList.remove('btn-info')
    }
  }

  const submitGoodToGoForm = () => {
    if (goodToGoForm.status !== FORM_STATE.SUBMITTING) {
      for (const key in goodToGoForm) {
        const value = String(goodToGoForm[key])

        if (value === 'undefined' || value === '-1') {
          return new Promise(() => {
            return false
          })
        }
      }

      return new Promise((resolve) => {
        if (goodToGoForm.status !== FORM_STATE.SUBMITTING) {
          goodToGoForm.status = FORM_STATE.SUBMITTING
          toggleLoading()

          const request = new XMLHttpRequest()
          const getParams = formatParams(goodToGoForm)
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
              goodToGoForm.status = FORM_STATE.READY

              toggleLoading()
              renderResults(json)
              resolve()
            }
          }
          request.onerror = () => {
            goodToGoForm.status = FORM_STATE.ERROR
            showErrors()
            resolve()
          }
          request.send()
        }
      })
    }
  }

  const toggleLoading = () => {
    const submitting = goodToGoForm.status === FORM_STATE.SUBMITTING
    submitting ? selectAttacker.disable() : selectAttacker.enable()

    selectAttackerQuickMove.disabled = submitting || selectAttackerQuickMove.value < 0
    selectAttackerAtkIv.disabled = submitting
    selectWeatherCondition.disabled = submitting
    selectFriendshipBoost.disabled = submitting
    tier36BossesButton.disabled = submitting
    tier36BossesCheckbox.disabled = submitting
    tier12BossesButton.disabled = submitting
    tier12BossesCheckbox.disabled = submitting
  }

  const renderResults = (data) => {
    goodToGoSummary.innerHTML = data.summary
    goodToGoResults.innerHTML = ''
    goodToGoResults.appendChild(document.createElement('hr'))

    if (data.tier_3_6_raid_bosses.length === 0 && data.tier_1_2_raid_bosses.length === 0) {
      goodToGoResults.innerHTML = 'Please select at least one option (tier 3-6, tier 1-2).'
    }

    if (data.tier_3_6_raid_bosses.length > 0) {
      renderResultSubcategory(goodToGoResults, data.tier_3_6_raid_bosses)
    }
    if (data.tier_1_2_raid_bosses.length > 0) {
      renderResultSubcategory(goodToGoResults, data.tier_1_2_raid_bosses)
    }
    // if (data.relevant_defenders.length > 0) {
    //   renderResultSubcategory(goodToGoResults, data.relevant_defenders)
    // }
    goodToGoResults.hidden = false
  }

  const renderResultSubcategory = (rootElement, data) => {
    for (var i = data.length - 1; i >= 0; i--) {
      const result = data[i]
      const resultsWrapper = document.createElement('div')
      const resultsHeader = document.createElement('p')

      const chevron = document.createElement('span')
      chevron.setAttribute('class', 'glyphicon glyphicon-chevron-down')
      chevron.setAttribute('aria-hidden', true)

      resultsWrapper.className = 'good-to-go-results-wrapper'
      resultsHeader.className = 'good-to-go-results-header'
      resultsHeader.innerHTML = 'Tier ' + result.tier + ' | ' + result.quick_move +
        ' breakpoints: ' + result.final_breakpoints_reached + ' / ' + result.total_breakpoints

      const indicator = document.createElement('span')
      indicator.className = (result.final_breakpoints_reached !== result.total_breakpoints
        ? 'glyphicon glyphicon-exclamation-sign good-to-go-warning-indicator'
        : 'glyphicon glyphicon-ok good-to-go-ok-indicator'
      )

      resultsHeader.appendChild(indicator)
      resultsHeader.appendChild(chevron)
      resultsWrapper.appendChild(resultsHeader)
      resultsWrapper.addEventListener('click', (event) => {
        const target = event.currentTarget

        target.childNodes.forEach((node, i) => {
          if (i > 0) {
            node.hidden = !node.hidden
          } else {
            const chev = node.childNodes[2]

            if (chev.classList.contains('glyphicon-chevron-down')) {
              chev.classList.remove('glyphicon-chevron-down')
              chev.classList.add('glyphicon-chevron-up')
            } else {
              chev.classList.remove('glyphicon-chevron-up')
              chev.classList.add('glyphicon-chevron-down')
            }
          }
        })
      })

      for (var j = result.matchups.length - 1; j >= 0; j--) {
        const matchup = result.matchups[j]

        const resultRow = document.createElement('p')
        resultRow.className = 'good-to-go-single-result'
        resultRow.hidden = true

        const rowIndicator = document.createElement('span')
        rowIndicator.className = (matchup.final_breakpoint_reached
          ? 'glyphicon glyphicon-ok good-to-go-ok-indicator'
          : 'glyphicon glyphicon-exclamation-sign good-to-go-warning-indicator'
        )
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

  const restoreCheckboxButtons = (data) => {
    tier36BossesCheckbox.checked = data.tier_3_6_raid_bosses
    toggleButtonClass(tier36BossesButton, data.tier_3_6_raid_bosses)

    tier12BossesCheckbox.checked = data.tier_1_2_raid_bosses
    toggleButtonClass(tier12BossesButton, data.tier_1_2_raid_bosses)

    // relevantDefendersCheckbox.checked = data.relevant_defenders
    // toggleButtonClass(relevantDefendersButton, data.relevant_defenders)
  }

  const toggleButtonClass = (button, checked) => {
    if (checked) {
      button.classList.remove('btn-default')
      button.classList.add('btn-info')
    } else {
      button.classList.remove('btn-info')
      button.classList.add('btn-default')
    }
  }

  const restoreGoodToGoForm = (data) => {
    initialFetch().then(() => {
      selectAttacker.setValueByChoice(String(data.attacker))

      selectAttackerAtkIv.value = data.attack_iv
      selectWeatherCondition.value = data.weather_condition
      selectFriendshipBoost.value = data.friendship_boost

      selectPokemonMoves(data.attacker, 'attacker')
      selectPokemonMoves(data.defender, 'defender')
      restoreCheckboxButtons(data)

      goodToGoForm = data
      goodToGoForm.status = FORM_STATE.READY
      submitGoodToGoForm()
    })
  }

  const showErrors = () => {
    goodToGoResults.hidden = false
    goodToGoResults.classList.add('error-text')
    goodToGoResults.innerHTML = ':( something broke, let me know if refreshing the page does not help.'
  }

  if (goodToGoForm.attacker && !(goodToGoForm.attacker_quick_move && goodToGoForm.attacker_cinematic_move)) {
    const queryDict = {}
    location.search.substr(1).split('&').forEach((item) => {
      queryDict[item.split('=')[0]] = item.split('=')[1]
    })
    restoreGoodToGoForm(queryDict)
  } else if (Object.keys(initialData).length > 0) {
    restoreGoodToGoForm(initialData)
  }

  initialFetch()
})

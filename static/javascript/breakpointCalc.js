import '../sass/breakpointCalc.sass'
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
  const TAB = {
    BREAKPOINTS: 'breakpoints',
    COUNTERS: 'counters',
  }

  // inputs
  const selectAttacker = new Choices(
    '#select-attacker',
    {
      searchPlaceholderValue: 'Type in the attacker\'s name',
      searchResultLimit: 5,
      itemSelectText: '',
      loadingText: '',
    }
  )
  const inputAttackerLevel = document.getElementById('input-attacker-level')
  const selectAttackerQuickMove = document.getElementById('select-quick-move')
  const selectAttackerCinematicMove = document.getElementById('select-cinematic-move')
  const selectAttackerAtkIv = document.getElementById('select-attacker-atk-iv')
  const selectDefender = new Choices(
    '#select-defender',
    {
      searchPlaceholderValue: 'Type in the defender\'s name',
      searchResultLimit: 5,
      itemSelectText: '',
      loadingText: '',
    }
  )
  const selectDefenderQuickMove = document.getElementById('select-defender-quick-move')
  const selectDefenderCinematicMove = document.getElementById('select-defender-cinematic-move')

  const selectWeatherCondition = document.getElementById('select-weather-condition')
  const selectFriendShipBoost = document.getElementById('select-friendship-boost')
  const selectDefenderCPM = document.getElementById('select-defender-tier')

  const outputTable = document.getElementById('output-table')
  const inputToggleCinematicBreakpoints = document.getElementById('toggle-cinematic-breakpoints')
  const inputToggleTopCounterSort = document.getElementById('top-counter-sort-toggle')

  const tabBreakpoints = document.getElementById('breakpoints')
  const tabTopCounters = document.getElementById('top-counters')
  const breakpointsTable = document.getElementById('breakpoints-table')
  const topCountersTable = document.getElementById('top-counters-detail-table')
  const summary = document.querySelector('.output-wrapper')
  const faqLegend = document.getElementById('faq-legend-content')

  let form = {
    attacker: selectAttacker.value,
    attacker_level: inputAttackerLevel.value,
    attacker_quick_move: selectAttackerQuickMove.value,
    attacker_cinematic_move: selectAttackerCinematicMove.value,
    attacker_atk_iv: selectAttackerAtkIv.value,
    weather_condition: selectWeatherCondition.value,
    friendship_boost: selectFriendShipBoost.value,
    defender: selectDefender.value,
    defender_quick_move: selectDefenderQuickMove.value,
    defender_cinematic_move: selectDefenderCinematicMove.value,
    defender_cpm: selectDefenderCPM.value,
    top_counter_order: 'rnk',
    tab: TAB.BREAKPOINTS,
    status: FORM_STATE.READY,
    staleTab: false,
  }

  // events
  selectAttacker.passedElement.element.addEventListener('change', (event) => {
    clearMoveInputs('attacker')
    selectPokemonMoves(event.currentTarget.value, 'attacker')
    clearChoicesFieldError('select-attacker')

    form.attacker = event.currentTarget.value
    form.staleTab = true
    submitForm()
  })
  inputAttackerLevel.addEventListener('change', (event) => {
    setValidLevel(event.currentTarget, 'attacker_level')
    inputAttackerLevel.classList.remove('error')

    form.staleTab = true
    submitForm().then(() => inputAttackerLevel.focus())
  })
  selectAttackerQuickMove.addEventListener('change', (event) => {
    form.attacker_quick_move = event.currentTarget.value

    form.staleTab = true
    submitForm().then(() => selectAttackerQuickMove.focus())
  })
  selectAttackerCinematicMove.addEventListener('change', (event) => {
    form.attacker_cinematic_move = event.currentTarget.value

    form.staleTab = true
    submitForm().then(() => selectAttackerCinematicMove.focus())
  })
  selectAttackerAtkIv.addEventListener('change', (event) => {
    form.attacker_atk_iv = event.currentTarget.value

    form.staleTab = true
    submitForm().then(() => selectAttackerAtkIv.focus())
  })
  selectWeatherCondition.addEventListener('change', (event) => {
    form.weather_condition = event.currentTarget.value

    form.staleTab = true
    submitForm().then(() => selectWeatherCondition.focus())
  })
  selectFriendShipBoost.addEventListener('change', (event) => {
    form.friendship_boost = event.currentTarget.value

    form.staleTab = true
    submitForm().then(() => selectFriendShipBoost.focus())
  })
  selectDefender.passedElement.element.addEventListener('change', (event) => {
    clearMoveInputs('defender')
    selectPokemonMoves(event.currentTarget.value, 'defender')
    clearChoicesFieldError('select-defender')

    form.defender = event.currentTarget.value
    form.staleTab = true
    submitForm()
  })
  selectDefenderQuickMove.addEventListener('change', (event) => {
    form.defender_quick_move = event.currentTarget.value

    form.staleTab = true
    submitForm().then(() => selectDefenderQuickMove.focus())
  })
  selectDefenderCinematicMove.addEventListener('change', (event) => {
    form.defender_cinematic_move = event.currentTarget.value

    form.staleTab = true
    submitForm().then(() => selectDefenderCinematicMove.focus())
  })
  selectDefenderCPM.addEventListener('change', (event) => {
    form.defender_cpm = event.currentTarget.value
    clearMoveInputs('defender')
    selectPokemonMoves(form.defender, 'defender')

    form.staleTab = true
    submitForm().then(() => selectDefenderCPM.focus())
  })
  inputToggleCinematicBreakpoints.addEventListener('click', (event) => {
    form.staleTab = true
    toggleCinematicBreakpoints()
  })
  inputToggleTopCounterSort.addEventListener('click', event => {
    form.staleTab = true

    if (!inputToggleTopCounterSort.disabled) {
      toggleTopCounterOrder(form.top_counter_order)
      submitForm()
    }
  })
  tabBreakpoints.addEventListener('click', (event) => {
    form.tab = TAB.BREAKPOINTS
    toggleTab(form.tab)
    toggleElementsByTab(TAB.BREAKPOINTS)
  })
  tabTopCounters.addEventListener('click', (event) => {
    form.tab = TAB.COUNTERS
    toggleTab(form.tab)
    toggleElementsByTab(TAB.COUNTERS)

    if (form.staleTab) {
      form.staleTab = false
      submitForm()
    }
  })
  document.getElementById('faq-legend').addEventListener('click', (event) => {
    faqLegend.hidden = !faqLegend.hidden
  })

  // functions
  // const initialFetch = () => {
  //   if (form.status !== FORM_STATE.SUBMITTING) {
  //     form.status = FORM_STATE.SUBMITTING
  //     toggleLoading()

  //     return new Promise(resolve => {
  //       selectAttacker.ajax(callback => {
  //         fetch(window.pgoAPIURLs['simple-pokemon-list'])
  //           .then(response => {
  //             response.json()
  //               .then(data => {
  //                 callback(data, 'value', 'label')
  //                 resolve()
  //               })
  //               .then(() => {
  //                 selectDefender.setChoices(
  //                   selectAttacker._currentState.choices.slice(1),
  //                   'value', 'label', false
  //                 )
  //               })
  //               .then(() => {
  //                 form.status = FORM_STATE.READY
  //                 toggleLoading()
  //               })
  //               .catch(() => {
  //                 form.status = FORM_STATE.ERROR
  //                 showErrors()
  //               })
  //           })
  //           .catch(() => {
  //             form.status = FORM_STATE.ERROR
  //             showErrors()
  //           })
  //       })
  //     })
  //   }
  // }

  const updateBrowserHistory = (getParams) => {
    window.history.pushState(
      {}, null, '/breakpoint-calc/' + getParams
    )
  }

  const formatParams = (params) => {
    const paramsCopy = Object.assign({}, params)
    delete paramsCopy.status
    delete paramsCopy.staleTab

    return '?' + Object.keys(paramsCopy).map((key) => {
      return key + '=' + encodeURIComponent(paramsCopy[key])
    }).join('&')
  }

  const toggleTab = (currentTab) => {
    if (currentTab === TAB.BREAKPOINTS) {
      breakpointsTable.hidden = false
      topCountersTable.hidden = true

      tabBreakpoints.classList.add('selected-tab')
      tabTopCounters.classList.remove('selected-tab')

      updateBrowserHistory(formatParams(form))
    } else if (currentTab === TAB.COUNTERS) {
      breakpointsTable.hidden = true
      topCountersTable.hidden = false

      tabTopCounters.classList.add('selected-tab')
      tabBreakpoints.classList.remove('selected-tab')

      updateBrowserHistory(formatParams(form))
    }
  }

  const toggleElementsByTab = (tab) => {
    if (tab === TAB.COUNTERS) {
      selectAttacker.disable()
      selectAttackerQuickMove.disabled = true
      selectAttackerCinematicMove.disabled = true

      summary.hidden = true
    } else {
      selectAttacker.enable()
      selectAttackerQuickMove.disabled = false
      selectAttackerCinematicMove.disabled = false

      summary.hidden = false
    }
  }

  const selectPokemonMoves = (value, pokemon) => {
    if (parseInt(value) > 0) {
      const request = new XMLHttpRequest()
      const excludeLegacy = pokemon === 'defender' && selectDefenderCPM.value.slice(-1) !== '0'
      request.open(
        'GET',
        `${window.pgoAPIURLs['move-list']}?pokemon-id=${value}&exclude-legacy=${excludeLegacy}`,
        true
      )

      request.onload = () => {
        if (request.status >= 200 && request.status < 400) {
          const json = JSON.parse(request.responseText)
          selectMoves(json, pokemon)
        } else {
          showErrors()
        }
      }
      request.onerror = () => {
        form.status = FORM_STATE.ERROR
        showErrors()
      }
      request.send()
    } else {
      selectAttackerQuickMove.disabled = true
      selectAttackerCinematicMove.disabled = true
      selectDefenderQuickMove.disabled = true
      selectDefenderCinematicMove.disabled = true

      clearMoveInputs('attacker')
      clearMoveInputs('defender')
    }
  }

  const toggleLoading = () => {
    const submitting = form.status === FORM_STATE.SUBMITTING
    const breakpointsTab = form.tab === 'breakpoints'

    if (submitting) {
      selectAttacker.disable()
      selectDefender.disable()
    } else {
      if (breakpointsTab) {
        selectAttacker.enable()
      }
      selectDefender.enable()
    }
    inputAttackerLevel.disabled = submitting
    selectAttackerAtkIv.disabled = submitting
    selectDefenderQuickMove.disabled = submitting
    selectDefenderCinematicMove.disabled = submitting
    selectWeatherCondition.disabled = submitting
    selectFriendShipBoost.disabled = submitting
    selectDefenderCPM.disabled = submitting

    inputToggleCinematicBreakpoints.disabled = submitting
    inputToggleTopCounterSort.disabled = submitting

    tabBreakpoints.disabled = submitting
    tabTopCounters.disabled = submitting

    selectAttackerQuickMove.disabled = submitting || selectAttackerQuickMove.value < 0 || !breakpointsTab
    selectAttackerCinematicMove.disabled = submitting || selectAttackerCinematicMove.value < 0 || !breakpointsTab
  }

  const submitForm = () => {
    if (form.status !== FORM_STATE.SUBMITTING) {
      for (const key in form) {
        if (form[key] === undefined || form[key].toString() === '-1') {
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
          const url = window.pgoAPIURLs['breakpoint-calc'] + getParams
          request.open('GET', url, true)

          request.onload = () => {
            if (request.status >= 500) {
              showErrors()
            } else {
              const json = JSON.parse(request.responseText)

              if (request.status >= 200 && request.status < 400) {
                summary.innerHTML = json.attack_iv_assessment

                displayDetails(json)
                generateTopCountersTable(json.top_counters)
                updateBrowserHistory(getParams)
              } else {
                showErrors(json)
              }
              form.status = FORM_STATE.READY

              if (form.tab === TAB.COUNTERS) {
                form.staleTab = false
                toggleElementsByTab(TAB.COUNTERS)
              }
              toggleLoading()
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

  const selectMoves = (data, pokemon) => {
    const quickMoveSelect = pokemon === 'attacker' ? selectAttackerQuickMove : selectDefenderQuickMove
    const cinematicMoveSelect = pokemon === 'attacker' ? selectAttackerCinematicMove : selectDefenderCinematicMove

    const quickMoveKey = pokemon + '_quick_move'
    const cinematicMoveKey = pokemon + '_cinematic_move'

    const quickMoveId = parseInt(form[quickMoveKey])
    const cinematicMoveId = parseInt(form[cinematicMoveKey])

    data.results.forEach((moveData, i) => {
      if (moveData.move.category === 'QK') {
        quickMoveSelect.disabled = false
        quickMoveSelect.options.add(createMoveOption(moveData, quickMoveId, quickMoveKey, pokemon))
      } else {
        cinematicMoveSelect.disabled = false
        cinematicMoveSelect.options.add(createMoveOption(moveData, cinematicMoveId, cinematicMoveKey, pokemon))
      }
    })
    form[quickMoveKey] = quickMoveSelect.value
    form[cinematicMoveKey] = cinematicMoveSelect.value

    submitForm()
  }

  const toggleTopCounterOrder = (value) => {
    form.top_counter_order = value === 'rnk' ? 'dps' : 'rnk'
    inputToggleTopCounterSort.innerHTML = form.top_counter_order.toUpperCase()
  }

  const restoreForm = (data) => {
    // initialFetch().then(() => {
    toggleTab(data.tab)

    selectAttacker.setChoiceByValue(`${data.attacker}`)
    selectDefender.setChoiceByValue(`${data.defender}`)

    inputAttackerLevel.value = data.attacker_level
    selectAttackerAtkIv.value = data.attacker_atk_iv
    selectWeatherCondition.value = data.weather_condition
    selectFriendShipBoost.value = data.friendship_boost
    selectDefenderCPM.value = data.defender_cpm

    selectPokemonMoves(data.attacker, 'attacker')
    selectPokemonMoves(data.defender, 'defender')

    form = data
    form.staleTab = true
    form.status = FORM_STATE.READY
    form.top_counter_order = data.top_counter_order

    toggleTopCounterOrder(data.top_counter_order === 'dps' ? 'rnk' : 'dps')
    submitForm()
    // })
  }

  if (form.attacker && !(form.attacker_quick_move && form.attacker_cinematic_move)) {
    const queryDict = {}
    location.search.substr(1).split('&').forEach((item) => {
      queryDict[item.split('=')[0]] = item.split('=')[1]
    })
    restoreForm(queryDict)
  } else if (Object.keys(window.initialData).length > 0) {
    restoreForm(window.initialData)
  }

  const createMoveOption = (moveData, moveId, moveKey, pokemon) => {
    const move = moveData.move

    return new Option(
      pokemon === 'attacker' ? `${move.name} ${moveData.legacy ? '*' : ''} (${move.power})` : move.name,
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

  const displayDetails = (json) => {
    outputTable.hidden = false

    if (json.breakpoint_details.length < 2) {
      inputToggleCinematicBreakpoints.enabled = false
    } else {
      inputToggleCinematicBreakpoints.enabled = true
    }

    generateBreakpointTable(json.breakpoint_details)
  }

  const generateBreakpointTable = (data) => {
    const dataTable = document.getElementById('breakpoint-details-table-body')
    dataTable.innerHTML = ''

    for (let i = 0; i < data.length; i++) {
      const dataRow = document.createElement('tr')

      for (let j = 0; j < data[i].length; j++) {
        const dataCell = document.createElement('td')

        dataCell.innerHTML = data[i][j]
        dataRow.appendChild(dataCell)
      }
      dataTable.appendChild(dataRow)
    }
  }

  const generateTopCountersTable = (dataset) => {
    const attackerStats = document.getElementById('top-counters-table-attacker-stats')
    attackerStats.innerHTML = `L${form.attacker_level} ${form.attacker_atk_iv}ATK`
    const dataTable = document.getElementById('top-counters-table-body')
    let dataRow
    let dataCell
    let href
    dataTable.innerHTML = ''

    for (const [key, data] of Object.entries(dataset)) {
      for (let i = 0; i < data[1].length; i++) {
        dataRow = document.createElement('tr')
        dataCell = document.createElement('td')
        href = document.createElement('a')
        href.href = `${data[0]}`
        dataCell.innerHTML = data[0]
        dataRow.appendChild(dataCell)

        for (let j = 0; j < data[1][i].length - 1; j++) {
          dataCell = document.createElement('td')
          dataCell.innerHTML = data[1][i][j]

          if (j < data[1][i].length - 1) {
            dataRow.appendChild(dataCell)
          }
        }

        let className = key.toLowerCase()
        if (i > 0) {
          className = 'toggle_' + className + ' top-counter-subrow'
          dataRow.hidden = true
          dataCell.classList.add('top-counter-subrow-td')
        } else {
          const arrow = document.createElement('span')
          arrow.setAttribute('class', 'top-counter-arrow')

          href = document.createElement('a')
          href.onclick = () => {
            const elements = document.getElementsByClassName('toggle_' + className)
            for (var i = 0; i < elements.length; i++) {
              elements[i].hidden = !elements[i].hidden
            }
          }
          href.appendChild(arrow)
          dataCell.appendChild(href)
        }
        dataRow.appendChild(dataCell)
        dataRow.setAttribute('class', className)
        dataTable.appendChild(dataRow)
      }
    }
  }

  const toggleCinematicBreakpoints = () => {
    if (form.show_cinematic_breakpoints) {
      delete form.show_cinematic_breakpoints
    } else {
      form.show_cinematic_breakpoints = true
    }
    submitForm()
  }

  const showErrors = (errorObject = null) => {
    if (errorObject) {
      for (const field in errorObject) {
        if (field !== 'attacker_level') {
          const invalidInput = document.querySelector('.select-' + field)
          if (invalidInput) {
            invalidInput.parentElement.parentElement.classList.add('error')
          }
        } else {
          document.querySelector('.' + field).classList.add('error')
        }
      }
    } else {
      outputTable.hidden = false
      outputTable.classList.add('error-text')
      outputTable.innerHTML = ':( something broke, let me know if refreshing the page does not help.'
    }
  }

  const clearChoicesFieldError = (elementName) => {
    const input = document.getElementById(elementName)[0]
    input.parentElement.parentElement.classList.remove('error')
  }

  const clearMoveInputs = (pokemon) => {
    if (form.status !== FORM_STATE.SUBMITTING) {
      const quickMoveSelect = pokemon === 'attacker' ? selectAttackerQuickMove : selectDefenderQuickMove
      const cinematicMoveSelect = pokemon === 'attacker' ? selectAttackerCinematicMove : selectDefenderCinematicMove

      const quickMoveKey = pokemon + '_quick_move'
      const cinematicMoveKey = pokemon + '_cinematic_move'

      quickMoveSelect.innerHTML = ''
      quickMoveSelect.append(
        '<option value="-1" disabled selected>Select quick move</option>'
      )
      cinematicMoveSelect.innerHTML = ''
      cinematicMoveSelect.append(
        '<option value="-1" disabled selected>Select cinematic move</option>'
      )
      form[quickMoveKey] = -1
      form[cinematicMoveKey] = -1
    }
  }

  const setValidLevel = (input, inputName) => {
    const choice = validateLevel(input)

    if (!isNaN(choice)) {
      input.value = choice
      form[inputName] = input.value
    } else {
      form[inputName] = '-1'
    }
  }

  const validateLevel = (input) => {
    const val = input.value.replace(',', '.')
    let level = parseFloat(val)

    if (level < 0) {
      level *= -1
    }
    if (level < 1) {
      level = 1
    }
    if (level > 40) {
      level = 40
    }
    if ((level * 10) % 5 !== 0) {
      level = parseInt(level)
    }
    return level
  }

  // initialFetch()
})

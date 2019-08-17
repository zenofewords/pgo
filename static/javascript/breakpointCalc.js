import '../sass/breakpointCalc.sass'
import Choices from 'choices.js'


const ready = (runBreakpointCalc) => {
  if (document.attachEvent ? document.readyState === 'complete' : document.readyState !== 'loading') {
    runBreakpointCalc()
  } else {
    document.addEventListener('DOMContentLoaded', runBreakpointCalc)
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
    }
  )
  const selectDefenderQuickMove = document.getElementById('select-defender-quick-move')
  const selectDefenderCinematicMove = document.getElementById('select-defender-cinematic-move')

  const selectWeatherCondition = document.getElementById('select-weather-condition')
  const selectFriendShipBoost = document.getElementById('select-friendship-boost')
  const selectDefenderCPM = document.getElementById('select-defender-tier')

  const moveEffectiveness = document.getElementById('move-effectiveness')
  const detailsTable = document.getElementById('breakpoint-details-table')
  const inputToggleCinematicBreakpoints = document.getElementById('toggle-cinematic-breakpoints')
  const inputToggleTopCounterSort = document.getElementById('top-counter-sort-toggle')

  const tabBreakpoints = document.getElementById('breakpoints')
  const tabTopCounters = document.getElementById('top-counters')
  const breakpointsTable = document.getElementById('breakpoints-table')
  const topCountersTable = document.getElementById('top-counters-table')
  const ivAssessment = document.getElementById('atk-iv-assessment')
  const faqLegend = document.getElementById('faq-legend-content')

  let breakpointCalcForm = {
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

    breakpointCalcForm.attacker = event.currentTarget.value
    breakpointCalcForm.staleTab = true
    submitBreakpointCalcForm()
  })
  inputAttackerLevel.addEventListener('change', (event) => {
    setValidLevel(event.currentTarget, 'attacker_level')
    inputAttackerLevel.classList.remove('error')

    breakpointCalcForm.staleTab = true
    submitBreakpointCalcForm().then(() => inputAttackerLevel.focus())
  })
  selectAttackerQuickMove.addEventListener('change', (event) => {
    breakpointCalcForm.attacker_quick_move = event.currentTarget.value

    breakpointCalcForm.staleTab = true
    submitBreakpointCalcForm().then(() => selectAttackerQuickMove.focus())
  })
  selectAttackerCinematicMove.addEventListener('change', (event) => {
    breakpointCalcForm.attacker_cinematic_move = event.currentTarget.value

    breakpointCalcForm.staleTab = true
    submitBreakpointCalcForm().then(() => selectAttackerCinematicMove.focus())
  })
  selectAttackerAtkIv.addEventListener('change', (event) => {
    breakpointCalcForm.attacker_atk_iv = event.currentTarget.value

    breakpointCalcForm.staleTab = true
    submitBreakpointCalcForm().then(() => selectAttackerAtkIv.focus())
  })
  selectWeatherCondition.addEventListener('change', (event) => {
    breakpointCalcForm.weather_condition = event.currentTarget.value

    breakpointCalcForm.staleTab = true
    submitBreakpointCalcForm().then(() => selectWeatherCondition.focus())
  })
  selectFriendShipBoost.addEventListener('change', (event) => {
    breakpointCalcForm.friendship_boost = event.currentTarget.value

    breakpointCalcForm.staleTab = true
    submitBreakpointCalcForm().then(() => selectFriendShipBoost.focus())
  })
  selectDefender.passedElement.element.addEventListener('change', (event) => {
    clearMoveInputs('defender')
    selectPokemonMoves(event.currentTarget.value, 'defender')
    clearChoicesFieldError('select-defender')

    breakpointCalcForm.defender = event.currentTarget.value
    breakpointCalcForm.staleTab = true
    submitBreakpointCalcForm()
  })
  selectDefenderQuickMove.addEventListener('change', (event) => {
    breakpointCalcForm.defender_quick_move = event.currentTarget.value

    breakpointCalcForm.staleTab = true
    submitBreakpointCalcForm().then(() => selectDefenderQuickMove.focus())
  })
  selectDefenderCinematicMove.addEventListener('change', (event) => {
    breakpointCalcForm.defender_cinematic_move = event.currentTarget.value

    breakpointCalcForm.staleTab = true
    submitBreakpointCalcForm().then(() => selectDefenderCinematicMove.focus())
  })
  selectDefenderCPM.addEventListener('change', (event) => {
    breakpointCalcForm.defender_cpm = event.currentTarget.value
    clearMoveInputs('defender')
    selectPokemonMoves(breakpointCalcForm.defender, 'defender')

    breakpointCalcForm.staleTab = true
    submitBreakpointCalcForm().then(() => selectDefenderCPM.focus())
  })
  inputToggleCinematicBreakpoints.addEventListener('click', (event) => {
    breakpointCalcForm.staleTab = true
    toggleCinematicBreakpoints()
  })
  inputToggleTopCounterSort.addEventListener('click', event => {
    breakpointCalcForm.staleTab = true

    if (!inputToggleTopCounterSort.disabled) {
      toggleTopCounterOrder(breakpointCalcForm.top_counter_order)
      submitBreakpointCalcForm()
    }
  })
  tabBreakpoints.addEventListener('click', (event) => {
    event.preventDefault()

    breakpointCalcForm.tab = TAB.BREAKPOINTS
    toggleTab(breakpointCalcForm.tab)
    toggleElementsByTab(TAB.BREAKPOINTS)
  })
  tabTopCounters.addEventListener('click', (event) => {
    event.preventDefault()

    breakpointCalcForm.tab = TAB.COUNTERS
    toggleTab(breakpointCalcForm.tab)
    toggleElementsByTab(TAB.COUNTERS)

    if (breakpointCalcForm.staleTab) {
      breakpointCalcForm.staleTab = false
      submitBreakpointCalcForm()
    }
  })
  document.getElementById('faq-legend-link').addEventListener('click', (event) => {
    event.preventDefault()

    faqLegend.hidden = !faqLegend.hidden
    const faqLegendChevrons = event.currentTarget.getElementsByClassName('faq-legend-chevron')

    for (var i = 0; i < faqLegendChevrons.length; i++) {
      if (faqLegendChevrons[i].classList.contains('chevron-down')) {
        faqLegendChevrons[i].classList.remove('chevron-down')
        faqLegendChevrons[i].classList.add('chevron-up')
      } else {
        faqLegendChevrons[i].classList.remove('chevron-up')
        faqLegendChevrons[i].classList.add('chevron-down')
      }
    }
  })

  // functions
  const initialFetch = () => {
    return new Promise((resolve) => {
      if (breakpointCalcForm.status !== FORM_STATE.SUBMITTING) {
        breakpointCalcForm.status = FORM_STATE.SUBMITTING
        toggleLoading()

        selectAttacker.ajax((callback) => {
          fetch(window.pgoAPIURLs['simple-pokemon-list']).then((response) => {
            response.json().then((data) => {
              callback(data, 'value', 'label')
            }).then(() => {
              selectDefender.setChoices(
                selectAttacker._currentState.choices.slice(1),
                'value', 'label', false
              )
              breakpointCalcForm.status = FORM_STATE.READY
              toggleLoading()
              resolve()
            })
          }).catch(() => {
            breakpointCalcForm.status = FORM_STATE.ERROR
            showErrors()
            resolve()
          })
        })
      }
    })
  }

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

      updateBrowserHistory(formatParams(breakpointCalcForm))
    } else if (currentTab === TAB.COUNTERS) {
      breakpointsTable.hidden = true
      topCountersTable.hidden = false

      tabTopCounters.classList.add('selected-tab')
      tabBreakpoints.classList.remove('selected-tab')

      updateBrowserHistory(formatParams(breakpointCalcForm))
    }
  }

  const toggleElementsByTab = (tab) => {
    if (tab === TAB.COUNTERS) {
      selectAttacker.disable()
      selectAttackerQuickMove.disabled = true
      selectAttackerCinematicMove.disabled = true

      ivAssessment.hidden = true
    } else {
      selectAttacker.enable()
      selectAttackerQuickMove.disabled = false
      selectAttackerCinematicMove.disabled = false

      ivAssessment.hidden = false
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
        breakpointCalcForm.status = FORM_STATE.ERROR
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
    const submitting = breakpointCalcForm.status === FORM_STATE.SUBMITTING
    const breakpointsTab = breakpointCalcForm.tab === 'breakpoints'

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

  const submitBreakpointCalcForm = () => {
    if (breakpointCalcForm.status !== FORM_STATE.SUBMITTING) {
      for (const key in breakpointCalcForm) {
        if (breakpointCalcForm[key] === undefined || breakpointCalcForm[key].toString() === '-1') {
          return new Promise(() => {
            return false
          })
        }
      }

      return new Promise((resolve) => {
        if (breakpointCalcForm.status !== FORM_STATE.SUBMITTING) {
          breakpointCalcForm.status = FORM_STATE.SUBMITTING
          toggleLoading()

          const request = new XMLHttpRequest()
          const getParams = formatParams(breakpointCalcForm)
          const url = window.pgoAPIURLs['breakpoint-calc'] + getParams
          request.open('GET', url, true)

          request.onload = () => {
            if (request.status >= 500) {
              showErrors()
            } else {
              const json = JSON.parse(request.responseText)

              if (request.status >= 200 && request.status < 400) {
                moveEffectiveness.innerHTML = ''
                ivAssessment.innerHTML = json.attack_iv_assessment

                displayBreakpointCalcDetails(json)
                generateTopCountersTable(json.top_counters)
                updateBrowserHistory(getParams)
              } else {
                showErrors(json)
              }
              breakpointCalcForm.status = FORM_STATE.READY

              if (breakpointCalcForm.tab === TAB.COUNTERS) {
                breakpointCalcForm.staleTab = false
                toggleElementsByTab(TAB.COUNTERS)
              }
              toggleLoading()
              resolve()
            }
          }
          request.onerror = () => {
            breakpointCalcForm.status = FORM_STATE.ERROR
            showErrors()
            resolve()
          }
          request.send()
        }
      })
    }
  }

  const restoreBreakpointCalcForm = (data) => {
    initialFetch().then(() => {
      toggleTab(data.tab)

      selectAttacker.setChoiceByValue(String(data.attacker))
      selectDefender.setChoiceByValue(String(data.defender))

      inputAttackerLevel.value = data.attacker_level
      selectAttackerAtkIv.value = data.attacker_atk_iv
      selectWeatherCondition.value = data.weather_condition
      selectFriendShipBoost.value = data.friendship_boost
      selectDefenderCPM.value = data.defender_cpm

      selectPokemonMoves(data.attacker, 'attacker')
      selectPokemonMoves(data.defender, 'defender')

      breakpointCalcForm = data
      breakpointCalcForm.staleTab = true
      breakpointCalcForm.status = FORM_STATE.READY
      breakpointCalcForm.top_counter_order = data.top_counter_order

      toggleTopCounterOrder(data.top_counter_order === 'dps' ? 'rnk' : 'dps')
      submitBreakpointCalcForm()
    })
  }

  if (breakpointCalcForm.attacker && !(breakpointCalcForm.attacker_quick_move && breakpointCalcForm.attacker_cinematic_move)) {
    const queryDict = {}
    location.search.substr(1).split('&').forEach((item) => {
      queryDict[item.split('=')[0]] = item.split('=')[1]
    })
    restoreBreakpointCalcForm(queryDict)
  } else if (Object.keys(initialData).length > 0) {
    restoreBreakpointCalcForm(initialData)
  }

  const selectMoves = (data, pokemon) => {
    const quickMoveSelect = pokemon === 'attacker' ? selectAttackerQuickMove : selectDefenderQuickMove
    const cinematicMoveSelect = pokemon === 'attacker' ? selectAttackerCinematicMove : selectDefenderCinematicMove

    const quickMoveKey = pokemon + '_quick_move'
    const cinematicMoveKey = pokemon + '_cinematic_move'

    const quickMoveId = parseInt(breakpointCalcForm[quickMoveKey])
    const cinematicMoveId = parseInt(breakpointCalcForm[cinematicMoveKey])

    data.forEach((moveData, i) => {
      if (moveData.move.category === 'QK') {
        quickMoveSelect.disabled = false
        quickMoveSelect.options.add(createMoveOption(moveData, quickMoveId, quickMoveKey, pokemon))
      } else {
        cinematicMoveSelect.disabled = false
        cinematicMoveSelect.options.add(createMoveOption(moveData, cinematicMoveId, cinematicMoveKey, pokemon))
      }
    })
    breakpointCalcForm[quickMoveKey] = quickMoveSelect.value
    breakpointCalcForm[cinematicMoveKey] = cinematicMoveSelect.value

    submitBreakpointCalcForm()
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
      breakpointCalcForm[type] = move.id
      return true
    }
    return false
  }

  const displayBreakpointCalcDetails = (json) => {
    detailsTable.hidden = false

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
    attackerStats.innerHTML = `L${breakpointCalcForm.attacker_level} ${breakpointCalcForm.attacker_atk_iv}ATK`
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
          dataCell.classList.add('top-counter-subrow')
        } else {
          const chevron = document.createElement('span')
          chevron.setAttribute(
            'class', 'chevron-down top-counter-chevron')

          href = document.createElement('a')
          href.onclick = () => {
            if (chevron.classList.contains('chevron-down')) {
              chevron.classList.remove('chevron-down')
              chevron.classList.add('chevron-up')
            } else {
              chevron.classList.remove('chevron-up')
              chevron.classList.add('chevron-down')
            }

            const elements = document.getElementsByClassName('toggle_' + className)
            for (var i = 0; i < elements.length; i++) {
              elements[i].hidden = !elements[i].hidden
            }
          }
          href.appendChild(chevron)
          dataCell.appendChild(href)
          dataCell.classList.add('align-right')
        }
        dataRow.appendChild(dataCell)
        dataRow.setAttribute('class', className)
        dataTable.appendChild(dataRow)
      }
    }
  }

  const toggleCinematicBreakpoints = () => {
    if (breakpointCalcForm.show_cinematic_breakpoints) {
      delete breakpointCalcForm.show_cinematic_breakpoints
    } else {
      breakpointCalcForm.show_cinematic_breakpoints = true
    }
    submitBreakpointCalcForm()
  }

  const toggleTopCounterOrder = (value) => {
    breakpointCalcForm.top_counter_order = value === 'rnk' ? 'dps' : 'rnk'
    inputToggleTopCounterSort.innerHTML = breakpointCalcForm.top_counter_order.toUpperCase()
  }

  const showErrors = (errorObject = null) => {
    if (errorObject) {
      for (let field in errorObject) {
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
      detailsTable.hidden = false
      detailsTable.classList.add('error-text')
      detailsTable.innerHTML = ':( something broke, let me know if refreshing the page does not help.'
    }
  }

  const clearChoicesFieldError = (elementName) => {
    const input = document.getElementById(elementName)[0]
    input.parentElement.parentElement.classList.remove('error')
  }

  const clearMoveInputs = (pokemon) => {
    if (breakpointCalcForm.status !== FORM_STATE.SUBMITTING) {
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
      breakpointCalcForm[quickMoveKey] = -1
      breakpointCalcForm[cinematicMoveKey] = -1
    }
  }

  const setValidLevel = (input, inputName) => {
    const choice = validateLevel(input)

    if (!isNaN(choice)) {
      input.value = choice
      breakpointCalcForm[inputName] = input.value
    } else {
      breakpointCalcForm[inputName] = '-1'
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

  initialFetch()
})

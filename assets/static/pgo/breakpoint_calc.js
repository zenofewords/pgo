import Choices from 'choices.js'

const ready = (runBreakpointCalc) => {
  if (document.attachEvent ? document.readyState === 'complete' : document.readyState !== 'loading') {
    runBreakpointCalc()
  } else {
    document.addEventListener('DOMContentLoaded', runBreakpointCalc)
  }
}

ready(() => {
  const FORM = {
    SUBMITTING: 'submitting',
    READY: 'ready',
    ERROR: 'error',
  }
  const TAB = {
    BREAKPOINTS: 'breakpoints',
    COUNTERS: 'counters',
  }

  const selectAttacker = new Choices(
    '.breakpoint-calc-select-attacker',
    {
      searchPlaceholderValue: 'Type in the attacker\'s name',
      searchResultLimit: 3,
      itemSelectText: '',
    }
  )
  const inputAttackerLevel = document.getElementById('breakpoint-calc-input-attacker-level')
  const selectAttackerQuickMove = document.getElementById('breakpoint-calc-select-quick-move')
  const selectAttackerCinematicMove = document.getElementById('breakpoint-calc-select-cinematic-move')
  const selectAttackerAtkIv = document.getElementById('breakpoint-calc-select-attacker-atk-iv')
  const selectDefender = new Choices(
    '.breakpoint-calc-select-defender',
    {
      searchPlaceholderValue: 'Type in the defender\'s name',
      searchResultLimit: 3,
      itemSelectText: '',
    }
  )
  const selectDefenderQuickMove = document.getElementById('breakpoint-calc-select-defender-quick-move')
  const selectDefenderCinematicMove = document.getElementById('breakpoint-calc-select-defender-cinematic-move')

  const selectWeatherCondition = document.getElementById('breakpoint-calc-select-weather-condition')
  const selectDefenderCPM = document.getElementById('breakpoint-calc-select-defender-tier')

  const moveEffectivness = document.getElementById('breakpoint-calc-move-effectivness')
  const detailsTable = document.getElementById('breakpoint-calc-breakpoint-details-table')
  const inputToggleCinematicBreakpoints = document.getElementById('breakpoint-calc-toggle-cinematic-breakpoints')

  const tabBreakpoints = document.getElementById('breakpoint-calc-breakpoints')
  const tabTopCounters = document.getElementById('breakpoint-calc-top-counters')
  const breakpointsTable = document.getElementById('breakpoint-calc-breakpoints-table')
  const topCountersTable = document.getElementById('breakpoint-calc-top-counters-table')

  let breakpointCalcForm = {
    attacker: selectAttacker.value,
    attacker_level: inputAttackerLevel.value,
    attacker_quick_move: selectAttackerQuickMove.value,
    attacker_cinematic_move: selectAttackerCinematicMove.value,
    attacker_atk_iv: selectAttackerAtkIv.value,
    weather_condition: selectWeatherCondition.value,
    defender: selectDefender.value,
    defender_quick_move: selectDefenderQuickMove.value,
    defender_cinematic_move: selectDefenderCinematicMove.value,
    defender_cpm: selectDefenderCPM.value,
    tab: TAB.BREAKPOINTS,
    status: FORM.READY,
    staleTab: false,
  }

  selectAttacker.passedElement.addEventListener('change', (event) => {
    clearMoveInputs('attacker')
    selectPokemonMoves(event.currentTarget.value, 'attacker')
    clearChoicesFieldError('breakpoint-calc-select-attacker')

    breakpointCalcForm.attacker = event.currentTarget.value
    breakpointCalcForm.staleTab = true
    submitFormIfValid()
  })
  inputAttackerLevel.addEventListener('change', (event) => {
    setValidLevel(event.currentTarget, 'attacker_level')
    inputAttackerLevel.classList.remove('error')

    breakpointCalcForm.staleTab = true
    submitFormIfValid()
  })
  selectAttackerQuickMove.addEventListener('change', (event) => {
    breakpointCalcForm.attacker_quick_move = event.currentTarget.value

    breakpointCalcForm.staleTab = true
    submitFormIfValid()
  })
  selectAttackerCinematicMove.addEventListener('change', (event) => {
    breakpointCalcForm.attacker_cinematic_move = event.currentTarget.value

    breakpointCalcForm.staleTab = true
    submitFormIfValid()
  })
  selectAttackerAtkIv.addEventListener('change', (event) => {
    breakpointCalcForm.attacker_atk_iv = event.currentTarget.value

    breakpointCalcForm.staleTab = true
    submitFormIfValid()
  })
  selectWeatherCondition.addEventListener('change', (event) => {
    breakpointCalcForm.weather_condition = event.currentTarget.value

    breakpointCalcForm.staleTab = true
    submitFormIfValid()
  })
  selectDefender.passedElement.addEventListener('change', (event) => {
    clearMoveInputs('defender')
    selectPokemonMoves(event.currentTarget.value, 'defender')
    clearChoicesFieldError('breakpoint-calc-select-defender')

    breakpointCalcForm.defender = event.currentTarget.value
    breakpointCalcForm.staleTab = true
    submitFormIfValid()
  })
  selectDefenderQuickMove.addEventListener('change', (event) => {
    breakpointCalcForm.defender_quick_move = event.currentTarget.value

    breakpointCalcForm.staleTab = true
    submitFormIfValid()
  })
  selectDefenderCinematicMove.addEventListener('change', (event) => {
    breakpointCalcForm.defender_cinematic_move = event.currentTarget.value

    breakpointCalcForm.staleTab = true
    submitFormIfValid()
  })
  selectDefenderCPM.addEventListener('change', (event) => {
    breakpointCalcForm.defender_cpm = event.currentTarget.value

    breakpointCalcForm.staleTab = true
    submitFormIfValid()
  })
  inputToggleCinematicBreakpoints.addEventListener('click', (event) => {
    event.preventDefault()
    toggleCinematicBreakpoints()
  })
  tabBreakpoints.addEventListener('click', (event) => {
    event.preventDefault()

    breakpointCalcForm.tab = TAB.BREAKPOINTS
    toggleTab(breakpointCalcForm.tab)
  })
  tabTopCounters.addEventListener('click', (event) => {
    event.preventDefault()

    breakpointCalcForm.tab = TAB.COUNTERS
    toggleTab(breakpointCalcForm.tab)

    if (breakpointCalcForm.staleTab) {
      breakpointCalcForm.staleTab = false
      submitFormIfValid()
    }
  })

  const submitFormIfValid = () => {
    if (breakpointCalcForm.status !== FORM.SUBMITTING) {
      let valid = true
      for (const key in breakpointCalcForm) {
        if (breakpointCalcForm[key] === undefined || breakpointCalcForm[key] === -1) {
          valid = false
        }
      }

      if (valid) {
        submitBreakpointCalcForm()
      }
    }
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

      tabBreakpoints.classList.add('breakpoint-calc-selected-tab')
      tabTopCounters.classList.remove('breakpoint-calc-selected-tab')

      updateBrowserHistory(formatParams(breakpointCalcForm))
    } else if (currentTab === TAB.COUNTERS) {
      breakpointsTable.hidden = true
      topCountersTable.hidden = false

      tabTopCounters.classList.add('breakpoint-calc-selected-tab')
      tabBreakpoints.classList.remove('breakpoint-calc-selected-tab')

      updateBrowserHistory(formatParams(breakpointCalcForm))
    }
  }

  const selectPokemonMoves = (value, pokemon) => {
    if (parseInt(value) > 0) {
      const request = new XMLHttpRequest()
      request.open('GET', window.pgoAPIURLs['move-list'] + '?pokemon-id=' + value, true)

      request.onload = () => {
        if (request.status >= 200 && request.status < 400) {
          const json = JSON.parse(request.responseText)
          selectMoves(json.results, pokemon)
        }
      }
      request.onerror = () => {
        breakpointCalcForm.status = FORM.ERROR
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

  const submitBreakpointCalcForm = () => {
    if (breakpointCalcForm.status !== FORM.SUBMITTING) {
      breakpointCalcForm.status = FORM.SUBMITTING

      const request = new XMLHttpRequest()
      const getParams = formatParams(breakpointCalcForm)
      const url = window.pgoAPIURLs['breakpoint-calc'] + getParams
      request.open('GET', url, true)

      request.onload = () => {
        const json = JSON.parse(request.responseText)

        if (request.status >= 200 && request.status < 400) {
          document.getElementById('breakpoint-calc-atk-iv-assessment').innerHTML = json.attack_iv_assessment
          displayBreakpointCalcDetails(json)
          generateTopCountersTable(json.top_counters)
          updateBrowserHistory(getParams)
        } else {
          showErrors(json)
        }
        breakpointCalcForm.status = FORM.READY

        if (breakpointCalcForm.tab === TAB.COUNTERS) {
          breakpointCalcForm.staleTab = false
        }
      }
      request.onerror = () => {
        breakpointCalcForm.status = FORM.ERROR
      }
      request.send()
    }
  }

  const restoreBreakpointCalcForm = (data) => {
    toggleTab(data.tab)
    selectAttacker.setValueByChoice(String(data.attacker))
    selectDefender.setValueByChoice(String(data.defender))

    inputAttackerLevel.value = data.attacker_level
    selectAttackerAtkIv.value = data.attacker_atk_iv
    selectWeatherCondition.value = data.weather_condition
    selectDefenderCPM.value = data.defender_cpm

    selectPokemonMoves(data.attacker, 'attacker')
    selectPokemonMoves(data.defender, 'defender')

    breakpointCalcForm = data
    breakpointCalcForm.status = FORM.READY
    submitBreakpointCalcForm()
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
      const move = moveData.move

      if (move.category === 'QK') {
        quickMoveSelect.disabled = false
        quickMoveSelect.options.add(createMoveOption(move, quickMoveId, quickMoveKey, pokemon))
      } else {
        cinematicMoveSelect.disabled = false
        cinematicMoveSelect.options.add(createMoveOption(move, cinematicMoveId, cinematicMoveKey, pokemon))
      }
    })
    breakpointCalcForm[quickMoveKey] = quickMoveSelect.value
    breakpointCalcForm[cinematicMoveKey] = cinematicMoveSelect.value

    submitFormIfValid()
  }

  const createMoveOption = (move, moveId, moveKey, pokemon) => {
    return new Option(
      pokemon === 'attacker' ? move.name + ' (' + move.power + ')' : move.name,
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
    moveEffectivness.innerHTML = ''

    generateBreakpointTable(json.breakpoint_details)
  }

  const generateBreakpointTable = (data) => {
    const dataTable = document.getElementById('breakpoint-calc-breakpoint-details-table-body')
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
    const dataTable = document.getElementById('breakpoint-calc-top-counters-table-body')
    let dataRow
    let dataCell
    const frailtyMap = {
      neutral: '',
      resilient: '<img class="frailty-resilient" src="/static/static/icons/shield.png">',
      fragile: '<span class="glyphicon glyphicon-glass frailty-fragile" aria-hidden="true"></span>',
    }
    dataTable.innerHTML = ''

    for (const [key, data] of Object.entries(dataset)) {
      for (let i = 0; i < data.length; i++) {
        dataRow = document.createElement('tr')

        for (let j = 0; j < data[i].length; j++) {
          dataCell = document.createElement('td')
          dataCell.innerHTML = String(data[i][j]).replace(/\{([^}]+)\}/g, (i, match) => {
            return frailtyMap[match]
          })
          dataRow.appendChild(dataCell)
        }

        let className = key.toLowerCase()
        if (i > 0) {
          className = 'toggle_' + className + ' breakpoint-calc-top-counter-subrow'
          dataRow.hidden = true
        } else {
          const chevron = document.createElement('span')
          chevron.setAttribute(
            'class', 'glyphicon glyphicon-chevron-down breakpoint-calc-top-counter-chevron')
          chevron.setAttribute('aria-hidden', true)

          const href = document.createElement('a')
          href.setAttribute('class', 'breakpoint-calc-toggle-chevron')
          href.onclick = () => {
            if (chevron.classList.contains('glyphicon-chevron-down')) {
              chevron.classList.remove('glyphicon-chevron-down')
              chevron.classList.add('glyphicon-chevron-up')
            } else {
              chevron.classList.remove('glyphicon-chevron-up')
              chevron.classList.add('glyphicon-chevron-down')
            }

            const elements = document.getElementsByClassName('toggle_' + className)
            for (var i = 0; i < elements.length; i++) {
              elements[i].hidden = !elements[i].hidden
            }
          }

          href.appendChild(chevron)
          dataCell.appendChild(href)
        }
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

  const showErrors = (errorObject) => {
    for (let field in errorObject) {
      if (field !== 'attacker_level') {
        const invalidInput = document.querySelector('.breakpoint-calc-select-' + field)
        invalidInput.parentElement.parentElement.classList.add('error')
      } else {
        document.querySelector('.' + field).classList.add('error')
      }
    }
  }

  const clearChoicesFieldError = (elementName) => {
    const input = document.getElementsByClassName(elementName)[0]
    input.parentElement.parentElement.classList.remove('error')
  }

  const clearMoveInputs = (pokemon) => {
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
})

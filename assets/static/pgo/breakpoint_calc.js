import Choices from 'choices.js'

ready(function () {
  const selectAttacker = new Choices(
    '.breakpoint-calc-select-attacker',
    {
      searchPlaceholderValue: 'Type in the attacker\'s name',
      searchResultLimit: 3,
      itemSelectText: '',
    }
  )
  const selectDefender = new Choices(
    '.breakpoint-calc-select-defender',
    {
      searchPlaceholderValue: 'Type in the defender\'s name',
      searchResultLimit: 3,
      itemSelectText: '',
    }
  )
  const inputAttackerLevel = document.getElementById('breakpoint-calc-input-attacker-level')
  const selectAttackerQuickMove = document.getElementById('breakpoint-calc-select-quick-move')
  const selectAttackerCinematicMove = document.getElementById('breakpoint-calc-select-cinematic-move')
  const selectAttackerAtkIv = document.getElementById('breakpoint-calc-select-attacker-atk-iv')
  const selectWeatherCondition = document.getElementById('breakpoint-calc-select-weather-condition')
  const selectDefenderCPM = document.getElementById('breakpoint-calc-select-defender-tier')

  const inputSubmit = document.getElementById('breakpoint-calc-input-submit')
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
    quick_move: selectAttackerQuickMove.value,
    cinematic_move: selectAttackerCinematicMove.value,
    attacker_atk_iv: selectAttackerAtkIv.value,
    weather_condition: selectWeatherCondition.value,
    defender: selectDefender.value,
    defender_cpm: selectDefenderCPM.value,
    tab: 'breakpoints',
  }

  if (breakpointCalcForm.attacker && !(breakpointCalcForm.quick_move && breakpointCalcForm.cinematic_move)) {
    const queryDict = {}
    location.search.substr(1).split('&').forEach(function (item) {
      queryDict[item.split('=')[0]] = item.split('=')[1]
    })
    restoreBreakpointCalcForm(queryDict)
  } else if (Object.keys(initialData).length > 0) {
    restoreBreakpointCalcForm(initialData)
  }

  selectAttacker.passedElement.addEventListener('change', function () {
    clearMoveInputs()
    filterQueryset(this.value)
    clearError('breakpoint-calc-select-attacker')

    breakpointCalcForm.attacker = this.value
  })
  inputAttackerLevel.addEventListener('change', function () {
    setValidLevel(this, 'attacker_level')
  })
  selectAttackerQuickMove.addEventListener('change', function () {
    breakpointCalcForm.quick_move = this.value
  })
  selectAttackerCinematicMove.addEventListener('change', function () {
    breakpointCalcForm.cinematic_move = this.value
  })
  selectAttackerAtkIv.addEventListener('change', function () {
    breakpointCalcForm.attacker_atk_iv = this.value
  })
  selectWeatherCondition.addEventListener('change', function () {
    breakpointCalcForm.weather_condition = this.value
  })
  selectDefender.passedElement.addEventListener('change', function () {
    clearError('breakpoint-calc-select-defender')

    breakpointCalcForm.defender = this.value
  })
  selectDefenderCPM.addEventListener('change', function () {
    breakpointCalcForm.defender_cpm = this.value
  })
  inputToggleCinematicBreakpoints.addEventListener('click', function (event) {
    event.preventDefault()
    toggleCinematicBreakpoints()
  })
  document.getElementById('breakpoint-calc-form').addEventListener('submit', function (event) {
    event.preventDefault()
    submitBreakpointCalcForm()
  })
  tabBreakpoints.addEventListener('click', function (event) {
    event.preventDefault()

    breakpointCalcForm.tab = 'breakpoints'
    toggleTab(breakpointCalcForm.tab)
  })
  tabTopCounters.addEventListener('click', function (event) {
    event.preventDefault()

    breakpointCalcForm.tab = 'counters'
    toggleTab(breakpointCalcForm.tab)
  })

  function restoreBreakpointCalcForm (data) {
    toggleTab(data.tab)
    selectAttacker.setValueByChoice(String(data.attacker))
    selectDefender.setValueByChoice(String(data.defender))

    inputAttackerLevel.value = data.attacker_level
    selectAttackerAtkIv.value = data.attacker_atk_iv
    selectWeatherCondition.value = data.weather_condition
    selectDefenderCPM.value = data.defender_cpm

    filterQueryset(data.attacker)
    breakpointCalcForm = data
    submitBreakpointCalcForm()
  }

  function toggleTab (currentTab) {
    if (currentTab === 'breakpoints') {
      breakpointsTable.hidden = false
      topCountersTable.hidden = true

      tabBreakpoints.classList.add('breakpoint-calc-selected-tab')
      tabTopCounters.classList.remove('breakpoint-calc-selected-tab')

      updateBrowserHistory(formatParams(breakpointCalcForm))
    } else if (currentTab === 'counters') {
      breakpointsTable.hidden = true
      topCountersTable.hidden = false

      tabTopCounters.classList.add('breakpoint-calc-selected-tab')
      tabBreakpoints.classList.remove('breakpoint-calc-selected-tab')

      updateBrowserHistory(formatParams(breakpointCalcForm))
    }
  }

  function filterQueryset (value) {
    if (parseInt(value) > 0) {
      inputSubmit.disabled = true

      const request = new XMLHttpRequest()
      request.open('GET', window.pgoAPIURLs['move-list'] + '?pokemon-id=' + value, true)

      request.onload = function () {
        if (request.status >= 200 && request.status < 400) {
          const json = JSON.parse(request.responseText)
          selectMoves(json.results)
          inputSubmit.disabled = false
        }
      }
      request.onerror = function () {
        inputSubmit.disabled = false
      }
      request.send()
    } else {
      selectAttackerQuickMove.disabled = true
      selectAttackerCinematicMove.disabled = true
      clearMoveInputs()
    }
  }

  function selectMoves (data) {
    const quickMoveId = parseInt(breakpointCalcForm.quick_move)
    const cinematicMoveId = parseInt(breakpointCalcForm.cinematic_move)

    data.forEach(function (moveData, i) {
      const move = moveData.move

      if (move.category === 'QK') {
        selectAttackerQuickMove.disabled = false
        selectAttackerQuickMove.options.add(
          new Option(
            move.name + ' (' + move.power + ')',
            move.id,
            false,
            determineSelectedMove(quickMoveId, move, 'quick_move')
          )
        )
      } else {
        selectAttackerCinematicMove.disabled = false
        selectAttackerCinematicMove.options.add(
          new Option(
            move.name + ' (' + move.power + ')',
            move.id,
            false,
            determineSelectedMove(cinematicMoveId, move, 'cinematic_move')
          )
        )
      }
    })
    breakpointCalcForm.quick_move = selectAttackerQuickMove.value
    breakpointCalcForm.cinematic_move = selectAttackerCinematicMove.value
  }

  function determineSelectedMove (moveId, move, type) {
    if (moveId > 0 && moveId === move.id) {
      breakpointCalcForm[type] = move.id
      return true
    }
    return false
  }

  function submitBreakpointCalcForm () {
    inputSubmit.disabled = true

    const request = new XMLHttpRequest()
    const getParams = formatParams(breakpointCalcForm)
    const url = window.pgoAPIURLs['breakpoint-calc'] + getParams
    request.open('GET', url, true)

    request.onload = function () {
      const json = JSON.parse(request.responseText)

      if (request.status >= 200 && request.status < 400) {
        document.getElementById('breakpoint-calc-atk-iv-assessment').innerHTML = json.attack_iv_assessment

        displayBreakpointCalcDetails(json)
        generateTopCountersTable(json.top_counters)
        updateBrowserHistory(getParams)
      } else {
        showErrors(json)
      }
    }
    request.send()
    inputSubmit.disabled = false
  }

  function displayBreakpointCalcDetails (json) {
    detailsTable.hidden = false

    if (json.breakpoint_details.length < 2) {
      inputToggleCinematicBreakpoints.parentElement.hidden = true
    } else {
      inputToggleCinematicBreakpoints.parentElement.hidden = false
    }
    moveEffectivness.innerHTML = ''
    generateBreakpointTable(json.breakpoint_details)
  }

  function generateBreakpointTable (data) {
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

  function generateTopCountersTable (dataset) {
    const dataTable = document.getElementById('breakpoint-calc-top-counters-table-body')
    let dataRow
    let dataCell
    dataTable.innerHTML = ''

    for (const [key, data] of Object.entries(dataset)) {
      for (let i = 0; i < data.length; i++) {
        dataRow = document.createElement('tr')

        for (let j = 0; j < data[i].length; j++) {
          dataCell = document.createElement('td')

          dataCell.innerHTML = data[i][j]
          dataRow.appendChild(dataCell)
        }

        let className = key.toLowerCase()
        if (i > 0) {
          className = 'toggle_' + className + ' breakpoint-calc-top-counter-subrow'
          dataRow.hidden = true
        } else if (!key.includes('user')) {
          const chevron = document.createElement('span')
          chevron.setAttribute(
            'class', 'glyphicon glyphicon-chevron-down breakpoint-calc-top-counter-chevron')
          chevron.setAttribute('aria-hidden', true)

          const href = document.createElement('a')
          href.setAttribute('class', 'breakpoint-calc-toggle-chevron')
          href.onclick = function () {
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

  function toggleCinematicBreakpoints () {
    if (breakpointCalcForm.show_cinematic_breakpoints) {
      delete breakpointCalcForm.show_cinematic_breakpoints

      inputToggleCinematicBreakpoints.classList.remove('glyphicon-minus')
      inputToggleCinematicBreakpoints.classList.add('glyphicon-plus')
    } else {
      breakpointCalcForm.show_cinematic_breakpoints = true

      inputToggleCinematicBreakpoints.classList.remove('glyphicon-plus')
      inputToggleCinematicBreakpoints.classList.add('glyphicon-minus')
    }
    submitBreakpointCalcForm()
  }

  function formatParams (params) {
    return '?' + Object.keys(params).map(function (key) {
      return key + '=' + encodeURIComponent(params[key])
    }).join('&')
  }

  function showErrors (errorObject) {
    for (let field in errorObject) {
      const invalidInput = document.getElementsByClassName('breakpoint-calc-select-' + field)[0]
      invalidInput.parentElement.parentElement.classList.add('error')
    }
  }

  function clearError (elementName) {
    const input = document.getElementsByClassName(elementName)[0]
    input.parentElement.parentElement.classList.remove('error')
  }

  function clearMoveInputs () {
    selectAttackerQuickMove.innerHTML = ''
    selectAttackerQuickMove.append(
      '<option value="-1" disabled selected>Select quick move</option>'
    )
    selectAttackerCinematicMove.innerHTML = ''
    selectAttackerCinematicMove.append(
      '<option value="-1" disabled selected>Select cinematic move</option>'
    )
    breakpointCalcForm['quick_move'] = -1
    breakpointCalcForm['cinematic_move'] = -1
  }

  function updateBrowserHistory (getParams) {
    window.history.pushState(
      {}, null, '/breakpoint-calc/' + getParams
    )
  }

  function setValidLevel (input, inputName) {
    const choice = validateLevel(input)

    if (!isNaN(choice)) {
      input.value = choice
      breakpointCalcForm[inputName] = input.value
    } else {
      breakpointCalcForm[inputName] = '-1'
    }
  }

  function validateLevel (input) {
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

function ready (runBreakpointCalc) {
  if (document.attachEvent ? document.readyState === 'complete' : document.readyState !== 'loading') {
    runBreakpointCalc()
  } else {
    document.addEventListener('DOMContentLoaded', runBreakpointCalc)
  }
}

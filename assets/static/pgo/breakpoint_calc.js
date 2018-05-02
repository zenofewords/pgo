import Choices from 'choices.js'

ready(function() {
  const breakpointCalcSelectAttacker = new Choices(
    '.breakpoint-calc-select-attacker',
    {
      searchPlaceholderValue: 'Type in the attacker\'s name',
      searchResultLimit: 3,
      itemSelectText: ''
    }
  )
  const breakpointCalcSelectDefender = new Choices(
    '.breakpoint-calc-select-defender',
    {
      searchPlaceholderValue: 'Type in the defender\'s name',
      searchResultLimit: 3,
      itemSelectText: '',
    }
  )
  const breakpointCalcInputAttackerLevel = document.getElementById('breakpoint-calc-input-attacker-level')
  const breakpointCalcSelectQuickMove = document.getElementById('breakpoint-calc-select-quick-move')
  const breakpointCalcSelectCinematicMove = document.getElementById('breakpoint-calc-select-cinematic-move')
  const breakpointCalcSelectAttackerAtkIv = document.getElementById('breakpoint-calc-select-attacker-atk-iv')
  const breakpointCalcSelectWeatherCondition = document.getElementById('breakpoint-calc-select-weather-condition')
  const breakpointCalcSelectDefenderCPM = document.getElementById('breakpoint-calc-select-defender-tier')

  const breakpointCalcInputSubmit = document.getElementById('breakpoint-calc-input-submit')
  const breakpointCalcPokemonMaxed = document.getElementById('breakpoint-calc-pokemon-maxed-text')
  const breakpointCalcDetailsTable = document.getElementById('breakpoint-calc-breakpoint-details-table')
  const breakpointCalcToggleCinematicBreakpoints = document.getElementById('breakpoint-calc-toggle-cinematic-breakpoints')

  let breakpointCalcForm = {
    attacker: breakpointCalcSelectAttacker.value,
    attacker_level: breakpointCalcInputAttackerLevel.value,
    quick_move: breakpointCalcSelectQuickMove.value,
    cinematic_move: breakpointCalcSelectCinematicMove.value,
    attacker_atk_iv: breakpointCalcSelectAttackerAtkIv.value,
    weather_condition: breakpointCalcSelectWeatherCondition.value,
    defender: breakpointCalcSelectDefender.value,
    defender_cpm: breakpointCalcSelectDefenderCPM.value,
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

  breakpointCalcSelectAttacker.passedElement.addEventListener('change', function () {
    clearMoveInputs()
    filterQueryset(this.value)
    clearError('breakpoint-calc-select-attacker')

    breakpointCalcForm.attacker = this.value
  })
  breakpointCalcInputAttackerLevel.addEventListener('change', function () {
    setValidLevel(this, 'attacker_level')
  })
  breakpointCalcSelectQuickMove.addEventListener('change', function () {
    breakpointCalcForm.quick_move = this.value
  })
  breakpointCalcSelectCinematicMove.addEventListener('change', function () {
    breakpointCalcForm.cinematic_move = this.value
  })
  breakpointCalcSelectAttackerAtkIv.addEventListener('change', function () {
    breakpointCalcForm.attacker_atk_iv = this.value
  })
  breakpointCalcSelectWeatherCondition.addEventListener('change', function () {
    breakpointCalcForm.weather_condition = this.value
  })
  breakpointCalcSelectDefender.passedElement.addEventListener('change', function () {
    clearError('breakpoint-calc-select-defender')

    breakpointCalcForm.defender = this.value
  })
  breakpointCalcSelectDefenderCPM.addEventListener('change', function () {
    breakpointCalcForm.defender_cpm = this.value
  })
  breakpointCalcToggleCinematicBreakpoints.addEventListener('click', function (event) {
    event.preventDefault()
    toggleCinematicBreakpoints()
  })
  document.getElementById('breakpoint-calc-form').addEventListener('submit', function (event) {
    event.preventDefault()
    submitBreakpointCalcForm()
  })

  function restoreBreakpointCalcForm (data) {
    breakpointCalcSelectAttacker.setValueByChoice(String(data.attacker))
    breakpointCalcSelectDefender.setValueByChoice(String(data.defender))

    breakpointCalcInputAttackerLevel.value = data.attacker_level
    breakpointCalcSelectAttackerAtkIv.value = data.attacker_atk_iv
    breakpointCalcSelectWeatherCondition.value = data.weather_condition
    breakpointCalcSelectDefenderCPM.value = data.defender_cpm

    filterQueryset(data.attacker)
    breakpointCalcForm = data
    submitBreakpointCalcForm()
  }

  function filterQueryset (value) {
    if (parseInt(value) > 0) {
      breakpointCalcInputSubmit.disabled = true

      const request = new XMLHttpRequest()
      request.open('GET', window.pgoAPIURLs['move-list'] + '?pokemon-id=' + value, true)

      request.onload = function() {
        if (request.status >= 200 && request.status < 400) {
          const json = JSON.parse(request.responseText)
          selectMoves(json.results)
          breakpointCalcInputSubmit.disabled = false
        }
      }
      request.onerror = function() {
        breakpointCalcInputSubmit.disabled = false
      }
      request.send()
    } else {
      breakpointCalcSelectQuickMove.disabled = true
      breakpointCalcSelectCinematicMove.disabled = true
      clearMoveInputs()
    }
  }

  function selectMoves (data) {
    const quickMoveId = parseInt(breakpointCalcForm.quick_move)
    const cinematicMoveId = parseInt(breakpointCalcForm.cinematic_move)

    data.forEach(function(moveData, i){
      const move = moveData.move

      if (move.category === 'QK') {
        breakpointCalcSelectQuickMove.disabled = false
        breakpointCalcSelectQuickMove.options.add(
          new Option(
            move.name + ' (' + move.power + ')',
            move.id,
            false,
            determineSelectedMove(quickMoveId, move, 'quick_move')
          )
        )
      } else {
        breakpointCalcSelectCinematicMove.disabled = false
        breakpointCalcSelectCinematicMove.options.add(
          new Option(
            move.name + ' (' + move.power + ')',
            move.id,
            false,
            determineSelectedMove(cinematicMoveId, move, 'cinematic_move')
          )
        )
      }
    })
    breakpointCalcForm.quick_move = breakpointCalcSelectQuickMove.value
    breakpointCalcForm.cinematic_move = breakpointCalcSelectCinematicMove.value
  }

  function determineSelectedMove (moveId, move, type) {
    if (moveId > 0 && moveId === move.id) {
      breakpointCalcForm[type] = move.id
      return true
    }
    return false
  }

  function submitBreakpointCalcForm () {
    breakpointCalcInputSubmit.disabled = true

    const request = new XMLHttpRequest()
    const url = window.pgoAPIURLs['breakpoint-calc'] + formatParams(breakpointCalcForm)
    request.open('GET', url, true)

    request.onload = function() {
      const json = JSON.parse(request.responseText)

      if (request.status >= 200 && request.status < 400) {
        displayBreakpointCalcData(json)
        getBreakpointCalcDetails()
        updateBrowserHistory()
      } else {
        showErrors(json)
        breakpointCalcInputSubmit.disabled = false
      }
    }
    request.onerror = function() {
      breakpointCalcInputSubmit.disabled = false
    }
    request.send()
  }

  function displayBreakpointCalcData (json) {
    document.getElementById('breakpoint-calc-atk-iv-assessment').innerHTML = json.attack_iv_assessment
    document.getElementById('breakpoint-calc-move-effectivness').innerHTML = json.weather_boost

    document.getElementById('breakpoint-calc-move-details').innerHTML = (
      json.damager_per_hit_details.quick_move +
      json.damager_per_hit_details.cinematic_move
    )
  }

  function getBreakpointCalcDetails () {
    const request = new XMLHttpRequest()
    const url = window.pgoAPIURLs['breakpoint-calc-detail'] + formatParams(breakpointCalcForm)
    request.open('GET', url, true)

    request.onload = function() {
      if (request.status >= 200 && request.status < 400) {
        const json = JSON.parse(request.responseText)

        displayBreakpointCalcDetails(json)
      }
    }
    request.onerror = function() {
      breakpointCalcInputSubmit.disabled = false
    }
    request.send()
    breakpointCalcInputSubmit.disabled = false
  }

  function displayBreakpointCalcDetails (json) {
    document.getElementById('breakpoint-calc-summary').innerHTML = json.summary

    if (json.details.length < 1) {
      breakpointCalcDetailsTable.hidden = true
      breakpointCalcPokemonMaxed.hidden = false
    } else {
      breakpointCalcPokemonMaxed.hidden = true
      breakpointCalcDetailsTable.hidden = false
      buildTableData(json.details)
    }
  }

  function buildTableData (data) {
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

  function toggleCinematicBreakpoints () {
    if (breakpointCalcForm.show_cinematic_breakpoints) {
      delete breakpointCalcForm.show_cinematic_breakpoints

      breakpointCalcToggleCinematicBreakpoints.classList.remove('glyphicon-minus')
      breakpointCalcToggleCinematicBreakpoints.classList.add('glyphicon-plus')
    }
    else {
      breakpointCalcForm.show_cinematic_breakpoints = true

      breakpointCalcToggleCinematicBreakpoints.classList.remove('glyphicon-plus')
      breakpointCalcToggleCinematicBreakpoints.classList.add('glyphicon-minus')
    }
    getBreakpointCalcDetails()
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
    breakpointCalcSelectQuickMove.innerHTML = ''
    breakpointCalcSelectQuickMove.append(
      '<option value="-1" disabled selected>Select quick move</option>'
    )
    breakpointCalcSelectCinematicMove.innerHTML = ''
    breakpointCalcSelectCinematicMove.append(
      '<option value="-1" disabled selected>Select cinematic move</option>'
    )
    breakpointCalcForm['quick_move'] = -1
    breakpointCalcForm['cinematic_move'] = -1
  }

  function updateBrowserHistory () {
    window.history.pushState(
      {}, null, '/breakpoint-calc/' +
      '?attacker=' + breakpointCalcForm.attacker +
      '&attacker_level=' + breakpointCalcForm.attacker_level +
      '&quick_move=' + breakpointCalcForm.quick_move +
      '&cinematic_move=' + breakpointCalcForm.cinematic_move +
      '&attacker_atk_iv=' + breakpointCalcForm.attacker_atk_iv +
      '&weather_condition=' + breakpointCalcForm.weather_condition +
      '&defender=' + breakpointCalcForm.defender +
      '&defender_cpm=' + breakpointCalcForm.defender_cpm
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
    const level = parseFloat(val)

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

function ready(runBreakpointCalc) {
  if (document.attachEvent ? document.readyState === 'complete' : document.readyState !== 'loading'){
    runBreakpointCalc()
  } else {
    document.addEventListener('DOMContentLoaded', runBreakpointCalc);
  }
}

$(document).ready(function () {
  // assign selectors
  var $breakpointCalcSelect = $('.breakpoint-calc-select')
  var $loaderGlyph = $('.loader-glyph')
  var $breakpointCalcSelectAttacker = $('#breakpoint-calc-select-attacker')
  var $breakpointCalcInputAttackerLevel = $('#breakpoint-calc-input-attacker-level')
  var $breakpointCalcSelectQuickMove = $('#breakpoint-calc-select-quick-move')
  var $breakpointCalcSelectCinematicMove = $('#breakpoint-calc-select-cinematic-move')
  var $breakpointCalcSelectAttackerAtkIv = $('#breakpoint-calc-select-attacker-atk-iv')
  var $breakpointCalcSelectWeatherCondition = $('#breakpoint-calc-select-weather-condition')
  var $breakpointCalcSelectDefender = $('#breakpoint-calc-select-defender')
  var $breakpointCalcSelectDefenderCPM = $('#breakpoint-calc-select-defender-tier')
  var $breakpointCalcInputSubmit = $('#breakpoint-calc-input-submit')
  var $breakpointCalcBreakpointDetails = $('#breakpoint-calc-breakpoint-details')

  // attach select2
  $breakpointCalcSelect.select2()

  // show select2 inputs when ready
  $loaderGlyph.toggle()
  $breakpointCalcSelect.toggle()

  var breakpointCalcForm = {
    attacker: $breakpointCalcSelectAttacker.val(),
    attacker_level: $breakpointCalcInputAttackerLevel.val(),
    quick_move: $breakpointCalcSelectQuickMove.val(),
    cinematic_move: $breakpointCalcSelectCinematicMove.val(),
    attacker_atk_iv: $breakpointCalcSelectAttackerAtkIv.val(),
    weather_condition: $breakpointCalcSelectWeatherCondition.val(),
    defender: $breakpointCalcSelectDefender.val(),
    defender_cpm: $breakpointCalcSelectDefenderCPM.val(),
  }

  if (breakpointCalcForm.attacker && !(breakpointCalcForm.quick_move && breakpointCalcForm.cinematic_move)) {
    var queryDict = {}
    location.search.substr(1).split('&').forEach(function (item) {
      queryDict[item.split('=')[0]] = item.split('=')[1]
    })
    restoreBreakpointCalcForm(queryDict)
  } else if (Object.keys(initialData).length > 0) {
    restoreBreakpointCalcForm(initialData)
  }

  // handle events
  $breakpointCalcSelectAttacker.on('change', function () {
    clearMoveInputs()

    filterQueryset(this.value)
    clearError('breakpoint-calc-select-attacker')

    breakpointCalcForm.attacker = this.value
  })
  $breakpointCalcInputAttackerLevel.on('change', function () {
    setValidLevel(this, 'attacker_level')
  })
  $breakpointCalcSelectQuickMove.on('change', function () {
    breakpointCalcForm.quick_move = this.value
  })
  $breakpointCalcSelectCinematicMove.on('change', function () {
    breakpointCalcForm.cinematic_move = this.value
  })
  $breakpointCalcSelectAttackerAtkIv.on('change', function () {
    breakpointCalcForm.attacker_atk_iv = this.value
  })
  $breakpointCalcSelectWeatherCondition.on('change', function () {
    breakpointCalcForm.weather_condition = this.value
  })
  $breakpointCalcSelectDefender.on('change', function () {
    clearError('breakpoint-calc-select-defender')

    breakpointCalcForm.defender = this.value
  })
  $breakpointCalcSelectDefenderCPM.on('change', function () {
    breakpointCalcForm.defender_cpm = this.value
  })
  $('#breakpoint-calc-form').on('submit', function (event) {
    event.preventDefault()
    submitBreakpointCalcForm()
  })

  // define functions
  function restoreBreakpointCalcForm (data) {
    breakpointCalcForm = data

    $breakpointCalcSelectAttacker.val(breakpointCalcForm.attacker).trigger('change')
    $breakpointCalcInputAttackerLevel.val(breakpointCalcForm.attacker_level).trigger('change')
    $breakpointCalcSelectAttackerAtkIv.val(breakpointCalcForm.attacker_atk_iv).trigger('change')
    $breakpointCalcSelectWeatherCondition.val(breakpointCalcForm.weather_condition).trigger('change')
    $breakpointCalcSelectDefender.val(breakpointCalcForm.defender).trigger('change')
    $breakpointCalcSelectDefenderCPM.val(breakpointCalcForm.defender_cpm).trigger('change')

    filterQueryset(breakpointCalcForm.attacker)
    submitBreakpointCalcForm(breakpointCalcForm)
  }

  function filterQueryset (value) {
    if (parseInt(value) > 0) {
      $breakpointCalcInputSubmit.prop('disabled', true)

      $.ajax({
        url: window.pgoAPIURLs['move-list'],
        type: 'GET',
        data: {
          'pokemon-id': value,
        },
        success: function (json) {
          selectMoves(json.results)
          $breakpointCalcInputSubmit.prop('disabled', false)
        },
        error: function (xhr, errmsg, err) {
          $breakpointCalcInputSubmit.prop('disabled', false)
        },
      })
    } else {
      $breakpointCalcSelectQuickMove.prop('disabled', true)
      $breakpointCalcSelectCinematicMove.prop('disabled', true)
      clearMoveInputs()
    }
  }

  function selectMoves (data) {
    var quickMoveId = parseInt(breakpointCalcForm.quick_move)
    var cinematicMoveId = parseInt(breakpointCalcForm.cinematic_move)

    $.each(data, function (i, pokemonMove) {
      var move = pokemonMove.move

      if (move.category === 'QK') {
        $breakpointCalcSelectQuickMove.prop('disabled', false)
        $breakpointCalcSelectQuickMove.append(
          '<option ' + (determineSelectedMove(quickMoveId, move, 'quick_move') ? 'selected' : '') +
          ' value=' + move.id + '>' + move.name + ' (' + move.power + ')</option>'
        )
      } else {
        $breakpointCalcSelectCinematicMove.prop('disabled', false)
        $breakpointCalcSelectCinematicMove.append(
          '<option ' + (determineSelectedMove(cinematicMoveId, move, 'cinematic_move') ? 'selected' : '') +
          ' value=' + move.id + '>' + move.name + ' (' + move.power + ')</option>'
        )
      }
    })
    // set first item as default if none selected so far
    if ($breakpointCalcSelectQuickMove[0].selectedIndex <= 0) {
      $breakpointCalcSelectQuickMove.prop('selectedIndex', 1)
      breakpointCalcForm.quick_move = $breakpointCalcSelectQuickMove.val()
    }
    if ($breakpointCalcSelectCinematicMove[0].selectedIndex <= 0) {
      $breakpointCalcSelectCinematicMove.prop('selectedIndex', 1)
      breakpointCalcForm.cinematic_move = $breakpointCalcSelectCinematicMove.val()
    }
  }

  function determineSelectedMove (moveId, move, type) {
    if (moveId > 0 && moveId === move.id) {
      breakpointCalcForm[type] = move.id
      return true
    }
    return false
  }

  function submitBreakpointCalcForm () {
    $breakpointCalcInputSubmit.prop('disabled', true)

    $.ajax({
      url: window.pgoAPIURLs['breakpoint-calc'],
      type: 'GET',
      data: breakpointCalcForm,
      success: function (json) {
        displayBreakpointCalcData(json)
        getBreakpointCalcDetails()
        updateBrowserHistory()
      },
      error: function (xhr, errmsg, err) {
        showErrors(xhr.responseJSON)
        $breakpointCalcInputSubmit.prop('disabled', false)
      },
    })
  }

  function displayBreakpointCalcData (json) {
    $('#breakpoint-calc-atk-iv-assessment').html(json.attack_iv_assessment)
    $('#breakpoint-calc-move-effectivness').html(json.weather_boost)

    $('#breakpoint-calc-move-details').html(
      json.damager_per_hit_details.quick_move +
      json.damager_per_hit_details.cinematic_move
    )
  }

  function getBreakpointCalcDetails () {
    $.ajax({
      url: window.pgoAPIURLs['breakpoint-calc-detail'],
      type: 'GET',
      data: breakpointCalcForm,
      success: function (json) {
        displayBreakpointCalcDetails(json)
      },
      error: function (xhr, errmsg, err) {
        console.log('detail error', xhr)
      },
    })
    $breakpointCalcInputSubmit.prop('disabled', false)
  }

  function displayBreakpointCalcDetails (json) {
    $('#breakpoint-calc-summary').html(json.summary)
    $breakpointCalcBreakpointDetails.prop('hidden', false)

    if (json.details.length < 1) {
      $breakpointCalcBreakpointDetails.html(
        'Your pokemon has reached its maximum potential for this matchup.')
    } else {
      buildTableData(json.details)
    }
  }

  function buildTableData (data) {
    var $dataTable = $('#breakpoint-calc-breakpoint-details-table-body')
    $dataTable.empty()

    for (var i = 0; i < data.length; i++) {
      var dataRow = $('<tr></tr>')

      for (var j = 0; j < data[i].length; j++) {
        var dataCell = $('<td></td>')

        dataCell.html(data[i][j])
        dataRow.append(dataCell)
      }
      $dataTable.append(dataRow)
    }
  }

  function showErrors (errorObject) {
    for (var field in errorObject) {
      $('#select2-breakpoint-calc-select-' + field + '-container').addClass('error')
    }
  }

  function clearError (elementName) {
    $('#select2-' + elementName + '-container').removeClass('error')
  }

  function clearMoveInputs () {
    $breakpointCalcSelectQuickMove.empty()
    $breakpointCalcSelectQuickMove.append(
      '<option value="-1" disabled selected>Select quick move</option>'
    )
    $breakpointCalcSelectCinematicMove.empty()
    $breakpointCalcSelectCinematicMove.append(
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
    var choice = validateLevel(input)

    if (!isNaN(choice)) {
      input.value = choice
      breakpointCalcForm[inputName] = input.value
    } else {
      breakpointCalcForm[inputName] = '-1'
    }
  }

  function validateLevel (input) {
    var val = input.value.replace(',', '.')
    var level = parseFloat(val)

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

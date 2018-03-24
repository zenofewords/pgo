$(document).ready(function(){
  // get inputs
  var $attackerSelect = $('#good-to-go-select-attacker')
  var $quickMoveSelect = $('#good-to-go-select-quick-move')
  var $cinematicMoveSelect = $('#good-to-go-select-cinematic-move')
  var $attackIvSelect = $('#good-to-go-select-atk-iv')
  var $weatherConditionSelect = $('#good-to-go-select-weather-condition')
  var $currentRaidBossesButton = $('#toggle_current_raid_bosses')
  var $currentRaidBossesCheckbox = $('#current_raid_bosses')
  var $pastRaidBossesButton = $('#toggle_past_raid_bosses')
  var $pastRaidBossesCheckbox = $('#past_raid_bosses')
  var $relevantDefendersButton = $('#toggle_relevant_defenders')
  var $relevantDefendersCheckbox = $('#relevant_defenders')
  var $goodToGoSubmitButton = $('#good_to_go_submit')
  var $goodToGoResults = $('.good-to-go-results')
  var $goodToGoSummary = $('.good-to-go-summary-text')

  // set select2 on inputs
  $attackerSelect.select2({
    dropdownAutoWidth: false,
    width: 280
  })
  $quickMoveSelect.select2({
    minimumResultsForSearch: -1,
    dropdownAutoWidth: false,
    width: 280
  })
  $cinematicMoveSelect.select2({
    minimumResultsForSearch: -1,
    dropdownAutoWidth: false,
    width: 280
  })
  $attackIvSelect.select2({
    minimumResultsForSearch: -1,
    dropdownAutoWidth: false,
    width: 90
  })
  $weatherConditionSelect.select2({
    dropdownAutoWidth: false,
    width: 180
  })

  // load form after select 2 is applied (looks nicer)
  $('.good-to-go-form-wrapper').toggle()
  var goodToGoForm = {
    attacker: $attackerSelect.val(),
    quick_move: $quickMoveSelect.val(),
    cinematic_move: $cinematicMoveSelect.val(),
    attack_iv: $attackIvSelect.val(),
    weather_condition: $weatherConditionSelect.val(),
    current_raid_bosses: $currentRaidBossesCheckbox.prop('checked'),
    past_raid_bosses: $pastRaidBossesCheckbox.prop('checked'),
    relevant_defenders: $relevantDefendersCheckbox.prop('checked'),
  }

  // handle values on browser back button
  if (goodToGoForm.attacker && !(goodToGoForm.quick_move && goodToGoForm.cinematic_move)) {
    var queryDict = {}
    location.search.substr(1).split('&').forEach(function(item) {queryDict[item.split('=')[0]] = item.split('=')[1]})
    restoreGoodToGoForm(queryDict)
  }
  // // load initial data and submit request
  else if (Object.keys(initialData).length > 0) {
    restoreGoodToGoForm(initialData)
  }

  // handle events
  $attackerSelect.on('change', function() {
    filterQueryset(this.value)
    goodToGoForm.attacker = this.value
    goodToGoForm.quick_move = - 1
    goodToGoForm.cinematic_move = - 1
    clearErrors()
  })
  $quickMoveSelect.on('change', function() {
    goodToGoForm.quick_move = this.value
  })
  $cinematicMoveSelect.on('change', function() {
    goodToGoForm.cinematic_move = this.value
  })
  $attackIvSelect.on('change', function() {
    goodToGoForm.attack_iv = this.value
  })
  $weatherConditionSelect.on('change', function() {
    goodToGoForm.weather_condition = this.value
  })
  $currentRaidBossesButton.on('click', function(event) {
    event.preventDefault()

    toggleButtonCheckbox($currentRaidBossesButton, $currentRaidBossesCheckbox)
    goodToGoForm.current_raid_bosses = $currentRaidBossesCheckbox.prop('checked')
  })
  $pastRaidBossesButton.on('click', function(event) {
    event.preventDefault()

    toggleButtonCheckbox($pastRaidBossesButton, $pastRaidBossesCheckbox)
    goodToGoForm.past_raid_bosses = $pastRaidBossesCheckbox.prop('checked')
  })
  $relevantDefendersButton.on('click', function(event) {
    event.preventDefault()

    toggleButtonCheckbox($relevantDefendersButton, $relevantDefendersCheckbox)
    goodToGoForm.relevant_defenders = $relevantDefendersCheckbox.prop('checked')
  })
  $('#good-to-go-form').on('submit', function(event) {
    event.preventDefault()
    submitForm(goodToGoForm)
  })
  $goodToGoResults.on('click', '.good-to-go-results-wrapper', function(event) {
    event.stopPropagation()
    $(this).children().slice(1).toggle()
  })
  $goodToGoResults.on('click', '.good-to-go-single-result', function(event) {
    event.stopPropagation()
  })

  function restoreGoodToGoForm(data) {
    goodToGoForm = data

    $attackerSelect.val(goodToGoForm.attacker).trigger('change')
    $attackIvSelect.val(goodToGoForm.attack_iv).trigger('change')
    $weatherConditionSelect.val(goodToGoForm.weather_condition).trigger('change')

    setButtonCheckbox($currentRaidBossesButton, $currentRaidBossesCheckbox,
      goodToGoForm.current_raid_bosses.toString() === 'true')
    setButtonCheckbox($pastRaidBossesButton, $pastRaidBossesCheckbox,
      goodToGoForm.past_raid_bosses.toString() === 'true')
    setButtonCheckbox($relevantDefendersButton, $relevantDefendersCheckbox,
      goodToGoForm.relevant_defenders.toString() === 'true')

    filterQueryset(goodToGoForm.attacker)
    submitForm(goodToGoForm)
  }

  function filterQueryset(value){
    if (parseInt(value) > 0) {
      $goodToGoSubmitButton.prop('disabled', true)

      $.ajax({
        url: window.pgoAPIURLs['move-list'],
        type: 'GET',
        data: {
          'pokemon-id': value
        },
        success: function(json){
          clearMoveInputs()
          selectMoves(json.results)
          $goodToGoSubmitButton.prop('disabled', false)
        },
        error: function(xhr, errmsg, err){
          console.log('filter error', xhr)
          $goodToGoSubmitButton.prop('disabled', false)
        }
      })
    }
    else {
      $quickMoveSelect.prop('disabled', true)
      $cinematicMoveSelect.prop('disabled', true)
      clearMoveInputs()
    }
  }

  function selectMoves(data) {
    var quickMoveId = parseInt(goodToGoForm.quick_move)
    var cinematicMoveId = parseInt(goodToGoForm.cinematic_move)

    $.each(data, function(i, pokemonMove) {
      var move = pokemonMove.move

      if (move.category === 'QK') {
        $quickMoveSelect.prop('disabled', false)
        $quickMoveSelect.append(
          '<option ' + (determineSelectedMove(quickMoveId, move, 'quick_move') ? 'selected' : '')
          + ' value=' + move.id + '>' + move.name + ' (' + move.power + ' DPH)</option>'
        )
      }
      else {
        // $cinematicMoveSelect.prop('disabled', false)
        $cinematicMoveSelect.append(
          '<option ' + (determineSelectedMove(cinematicMoveId, move, 'cinematic_move') ? 'selected' : '')
          + ' value=' + move.id + '>' + move.name + ' (' + move.power + ' DPH)</option>'
        )
      }
    })
    // set first item as default if none selected so far
    if ($quickMoveSelect[0].selectedIndex <= 0) {
      $quickMoveSelect.prop('selectedIndex', 1)
      goodToGoForm.quick_move = $quickMoveSelect.val()
    }
    if ($cinematicMoveSelect[0].selectedIndex <= 0) {
      $cinematicMoveSelect.prop('selectedIndex', 1)
      goodToGoForm.cinematic_move = $cinematicMoveSelect.val()
    }
  }

  function determineSelectedMove(moveId, move, type) {
    if (moveId > 0 && moveId === move.id) {
      goodToGoForm[type] = move.id
      return true
    }
    return false
  }

  function setButtonCheckbox(button, checkbox, state) {
    checkbox.prop('checked', state)

    if (state) {
      button.addClass('btn-success').removeClass('btn-default')
    }
    else {
      button.addClass('btn-default').removeClass('btn-success')
    }
  }

  function toggleButtonCheckbox(button, checkbox) {
    if (checkbox.prop('checked')) {
      checkbox.prop('checked', false)
      button.addClass('btn-default').removeClass('btn-success')
    }
    else {
      checkbox.prop('checked', true)
      button.addClass('btn-success').removeClass('btn-default')
    }
  }

  function clearErrors() {
    $('.error').removeClass('error')
    $('.form-error').empty()
  }

  function displayFieldErrors(errorObject) {
    for (field in errorObject) {
      $('#select2-good-to-go-select-' + field.replace('_', '-') + '-container').addClass('error')
    }
  }

  function clearMoveInputs() {
    $quickMoveSelect.empty()
    $quickMoveSelect.append(
      '<option value="-1" disabled selected>Select quick move</option>'
    )
    $cinematicMoveSelect.empty()
    $cinematicMoveSelect.append(
      '<option value="-1" disabled selected>Select cinematic move</option>'
    )
  }

  function submitForm(goodToGoForm) {
    $goodToGoSubmitButton.prop('disabled', true)
    $goodToGoResults.empty()
    $goodToGoResults.html('<hr />')
    $goodToGoResults.append(
      '<span class="glyphicon glyphicon-hourglass" aria-hidden="true"></span> One moment, please...')

    $.ajax({
      url: window.pgoAPIURLs['good-to-go'],
      type: 'GET',
      data: goodToGoForm,
      success: function(json){
        clearErrors()
        renderResults(json)
        updateBrowserHistory()
        $goodToGoSubmitButton.prop('disabled', false)
      },
      error: function(xhr, errmsg, err){
        displayFieldErrors(xhr.responseJSON)
        $goodToGoSubmitButton.prop('disabled', false)
        $goodToGoResults.empty()
      }
    })
  }

  function renderResults(data) {
    $goodToGoSummary.empty()
    $goodToGoResults.empty()
    $goodToGoResults.html('<hr />')

    if (data.current.length > 0) {
      var subcategoryWrapper = $('<div class="good-to-go-results-wrapper">'
        + '<p class="good-to-go-results-subcategory-header">Current & anticipated raid bosses</p></div>')
      $goodToGoResults.append(renderResultSubcategory(subcategoryWrapper, data.current, false))
    }

    if (data.past.length > 0) {
      var subcategoryWrapper = $('<div class="good-to-go-results-wrapper">'
        + '<p class="good-to-go-results-subcategory-header">Past raid bosses</p></div>')
      $goodToGoResults.append(renderResultSubcategory(subcategoryWrapper, data.past, true))
    }
    $goodToGoSummary.html(data.summary)
  }

  function renderResultSubcategory(rootElement, data, hide) {

    for (var i = data.length - 1; i >= 0; i--) {
      var result = data[i]
      var $resultsWrapper = $('<div class="good-to-go-results-wrapper"></div>')

      $resultsWrapper.append(
        '<p class="good-to-go-results-header">Raid tier ' + result.tier
        + ' | ' + result.quick_move + ' reaches the final breakpoint in ' +
        + result.final_breakpoints_reached + ' / ' + result.total_breakpoints
        + ' matchups '
        + (result.final_breakpoints_reached !== result.total_breakpoints
          ? '<span class="glyphicon glyphicon-exclamation-sign good-to-go-red"></span>' : '')
        + '</p>'
      )

      for (var j = result.matchups.length - 1; j >= 0; j--) {
        var matchup = result.matchups[j]

        $resultsWrapper.append(
          '<p class="good-to-go-single-result"' + (result.tier < 5 || hide ? ' hidden' : '')
            + '><span aria-hidden="true" class="glyphicon '
            + (matchup.final_breakpoint_reached
              ? 'glyphicon-ok good-to-go-green"' : 'glyphicon-remove good-to-go-red"') + '></span>'
            + matchup.damage_per_hit + ' / '
            + matchup.max_damage_per_hit + ' damage per hit possible vs '
            + matchup.defender + ' '
          + '</p>'
        )
      }
      rootElement.append($resultsWrapper)
    }
    return rootElement
  }

  function updateBrowserHistory() {
    window.history.pushState(
      {}, null, '/good-to-go/?attacker=' + goodToGoForm.attacker
      + '&quick_move=' + goodToGoForm.quick_move
      + '&cinematic_move=' + goodToGoForm.cinematic_move
      + '&weather_condition=' + goodToGoForm.weather_condition
      + '&attack_iv=' + goodToGoForm.attack_iv
      + '&current_raid_bosses=' + goodToGoForm.current_raid_bosses
      + '&past_raid_bosses=' + goodToGoForm.past_raid_bosses
      + '&relevant_defenders=' + goodToGoForm.relevant_defenders
    )
  }
})

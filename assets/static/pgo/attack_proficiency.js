$(document).ready(function(){
    $('.attack-pro-select').select2({
        'dropdownAutoWidth': false,
        'width': 250
    })
    // maintain tab index order
    $('select').on('select2:close', function() {
        $(this).focus()
    })

    var quickMoveSelect = $('#quick_move')
    var cinematicMoveSelect = $('#cinematic_move')
    var defenderLevelInput = $('#defender_level')
    var defenseIVInput = $('#defense_iv')
    var submitButton = $('#submit')
    var helpButton = $('#help_button')
    var formData = {
        defenderLevel: defenderLevelInput.val(),
        defenseIV: defenseIVInput.val(),
    }
    var tableBody = $('#attack-proficiency-stats').find('tbody')
    var autoSubmit = false

    $('#attacker').change(function() {
        filterQueryset(this.value)
        formData.attacker = this.value
        formData.quickMove = - 1
        formData.cinematicMove = - 1
    })
    quickMoveSelect.change(function() {
        formData.quickMove = this.value
    })
    cinematicMoveSelect.change(function() {
        formData.cinematicMove = this.value
    })
    $('#attacker_level').on('change', function() {
        setValidLevel(this, 'attackerLevel')
    })
    $('#attack_iv').on('change keyup', function() {
        setValidIV(this, 'attackIV')
    })
    defenderLevelInput.on('change', function() {
        setValidLevel(this, 'defenderLevel')
    })
    defenseIVInput.on('change keyup', function() {
        setValidIV(this, 'defenseIV')
    })

    $('#defender').change(function() {
        formData.defender = this.value
    })

    $('#attack-pro-form').on('submit', function(event) {
        event.preventDefault()
        submitForm(formData)
    })

    helpButton.on('click', function(event) {
        event.preventDefault()
        $('.help-text').toggle('fast')
    })

    var formInputs = $('.attack-pro-select, .attack-pro-input')
    formInputs.on('change keyup paste', function() {
        var disabled = true

        if (Object.keys(formData).length === formInputs.length) {
            disabled = false
            for (prop in formData) {
                if (formData[prop] < 0) {
                    disabled = true
                }
            }
        }
        submitButton.prop('disabled', disabled)

        if (disabled === false && autoSubmit === true) {
            submitForm(formData)
        }
    })

    tableBody.one('click', 'td.attack-proficiency-detail', handleAttackProficiencyDetail)


    function handleAttackProficiencyDetail(event) {
        event.preventDefault()
        $('.table-explanation-text').hide('fast')
        var currentTarget = $(event.currentTarget)
        var clickedCell = tableBody.find('#clicked-cell')

        if (clickedCell.length === 1 && clickedCell[0] === currentTarget[0]) {
            clickedCell.removeAttr('id')
            tableBody.find('#detail-summary').remove()
            tableBody.one('click', 'td.attack-proficiency-detail', handleAttackProficiencyDetail)
        }
        else {
            clickedCell.removeAttr('id')
            tableBody.find('#detail-summary').remove()

            $(this).attr('id', 'clicked-cell')

            var level = tableBody.find('tr').eq(
                currentTarget.parent().index()).find('td').eq(0)[0].textContent
            var defenseIV = tableBody.find('tr').eq(
                0).find('td').eq(currentTarget.index())[0].textContent

            var element = currentTarget
            getAttackProficiencyDetail(level, defenseIV, formData, element.parent())
        }
    }

    function setValidLevel(input, inputName) {
        var choice = validateLevel(input)

        if (!isNaN(choice)) {
            input.value = choice
            formData[inputName] = input.value
        }
        else {
            formData[inputName] = "-1"
        }
    }

    function setValidIV(input, inputName) {
        var choice = validateIV(input)

        if (!isNaN(choice)) {
            input.value = choice
            formData[inputName] = input.value
        }
        else {
            formData[inputName] = "-1"
        }
    }

    function filterQueryset(value){
        if (parseInt(value) > 0) {
            $.ajax({
                url: window.pgoAPIURLs['move-list'],
                type: 'GET',
                data: {
                    'pokemon-id': value
                },
                success: function(json){
                    clearMoveInputs()
                    $.each(json.results, function(i, move) {
                        if (move.category === 'QK') {
                            quickMoveSelect.prop('disabled', false)
                            quickMoveSelect.append(
                                '<option value=' + move.id + '>' + move.name + ' (' + move.power + ' DPH)</option>'
                            )
                        }
                        else {
                            cinematicMoveSelect.prop('disabled', false)
                            cinematicMoveSelect.append(
                                '<option value=' + move.id + '>' + move.name + ' (' + move.power + ' DPH)</option>'
                            )
                        }
                    })
                },
                error: function(xhr, errmsg, err){
                    console.log('filter error', xhr)
                }
            })
        }
        else {
            quickMoveSelect.prop('disabled', true)
            cinematicMoveSelect.prop('disabled', true)
            clearMoveInputs()
        }
    }

    function submitForm(formData) {
        $.ajax({
            url: window.pgoAPIURLs['attack-proficiency'],
            type: 'POST',
            data: {
                'attacker': formData.attacker,
                'quick_move': formData.quickMove,
                'cinematic_move': formData.cinematicMove,
                'attacker_level': formData.attackerLevel,
                'attack_iv': formData.attackIV,
                'defender': formData.defender,
                'defender_level': formData.defenderLevel,
                'defense_iv': formData.defenseIV,
            },
            success: function(json){
                displayAttackProficiency(json)
                generateAttackProficiencyStats(json)
                autoSubmit = true
            },
            error: function(xhr, errmsg, err){
                displayFieldErrors(xhr.responseJSON)
            }
        })
    }

    function generateAttackProficiencyStats(json) {
        $.ajax({
            url: window.pgoAPIURLs['attack-proficiency-stats'],
            type: 'POST',
            data: {
                'attacker': JSON.stringify(json.attacker),
                'quick_move': JSON.stringify(json.quick_move),
                'cinematic_move': JSON.stringify(json.cinematic_move),
                'defender': JSON.stringify(json.defender),
            },
            success: function(json){
                tableBody.empty()

                for (var i = 0; i < json.length; i++) {
                    var tr = $('<tr>')
                    for (value in json[i]) {
                        tr.append($('<td>').append(value))

                        var td = $('<td>')
                        for (var j = 0; j < json[i][value].length; j++) {
                            td.append(json[i][value][j])

                            if (j % 2 === 1) {
                                if (td[0].textContent.length > 2) {
                                    td.addClass('attack-proficiency-detail')
                                }
                                tr.append(td)
                                td = $('<td>')
                            }
                        }
                    }
                    tableBody.append(tr)
                }
                $('.attack-proficiency-stats-wrapper').show('fast')
            },
            error: function(xhr, errmsg, err){
                console.log('stats error', xhr)
            }
        })
    }

    function displayAttackProficiency(json) {
        $('.attack-proficiency-intro').hide('fast')
        $('.attack-proficiency-current').show('fast')
        $('#summary').html(json.summary)
        $('#attack_iv_assessment').html(json.attack_iv_assessment)

        $('#attacker_quick_move').html(json.quick_move.name)
        $('#quick_attack_damage').html(json.quick_move.damage_per_hit)
        $('#quick_attack_dps').html(json.quick_move.dps)

        $('#attacker_cinematic_move').html(json.cinematic_move.name)
        $('#cinematic_attack_damage').html(json.cinematic_move.damage_per_hit)
        $('#cinematic_attack_dps').html(json.cinematic_move.dps)

        $('.attacker_name').html(json.attacker.name)
        $('.defender_name').html(json.defender.name)
    }

    function getAttackProficiencyDetail(level, defenseIV, formData, rowToAppend) {
        $.ajax({
            url: window.pgoAPIURLs['attack-proficiency-detail'],
            type: 'POST',
            data: {
                'attacker': formData.attacker,
                'quick_move': formData.quickMove,
                'cinematic_move': formData.cinematicMove,
                'attacker_level': formData.attackerLevel,
                'attack_iv': formData.attackIV,
                'defender': formData.defender,
                'defender_level': level,
                'defense_iv': defenseIV,
            },
            success: function(json) {
                displayAttackProficiencyDetail(json, rowToAppend)
                rowToAppend.parent().one(
                    'click', 'td.attack-proficiency-detail', handleAttackProficiencyDetail)
            },
            error: function(xhr, errmsg, err){
                console.log('detail error', xhr)
            }
        })
    }

    function displayAttackProficiencyDetail(json, rowToAppend) {
        var marginLength = rowToAppend.children().length * 4
        var totalWidth = rowToAppend.outerWidth(true) - marginLength
        var wrapper = $('<tr id="detail-summary"><td id="detail-summary-cell" width="'
            + totalWidth + '" colspan="7"></td></tr>').hide()
        var summary = $('<p class="detail-summary-text">' + json.summary + '</p>')
        var wrapperTd = wrapper.find('td')
        wrapperTd.append(summary)

        var details = json.details
        if (details.length > 1) {
            wrapperTd.append($('<p>It could do better if it was powered up!</p>'))
            var detailsTable = $('<table class="table table-striped" width="'
                + totalWidth + '"></table>')
            detailsTable.append($('<tr id="detail-summary"><td width="10%">' +
                details[0][0] + '</td><td width="30%">' + details[0][1] +
                '</td><td width="30%">' + details[0][2] + '</td><td width="30%">'
                + details[0][3] + '</td></tr>'))

            for (row in details) {
                if (row > 0) {
                    detailsTable.append($(
                        '<tr><td>' + details[row][0] +
                        '</td><td>' + details[row][1] +
                        '</td><td>' + details[row][2] +
                        '</td><td>' + details[row][3] +
                        '</td></tr>'
                    ))
                }
            }
            wrapperTd.append(detailsTable)
        }
        rowToAppend.after(wrapper)
        wrapper.show('fast')
    }

    function displayFieldErrors(errorObject) {
        for (error in errorObject) {
            var selector = '#' + error + '_error'
            $(selector).html(errorObject[error])
        }
    }

    function clearMoveInputs() {
        quickMoveSelect.empty()
        quickMoveSelect.append(
            '<option value="-1" disabled selected>Select quick move</option>'
        )
        cinematicMoveSelect.empty()
        cinematicMoveSelect.append(
            '<option value="-1" disabled selected>Select cinematic move</option>'
        )
        formData['quickMove'] = -1
        formData['cinematicMove'] = -1
    }

    function validateLevel(input) {
        var level = parseFloat(input.value)

        if (level < 0) {
            level *= - 1
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

    function validateIV(input) {
        var attack = parseInt(input.value)

        if (attack < 0) {
            attack = 0
        }
        if (attack > 15) {
            attack = 15
        }
        return attack
    }

    function getCookie(name) {
        var cookieValue = null
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';')
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i])
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
                    break
                }
            }
        }
        return cookieValue
    }
    var csrftoken = getCookie('csrftoken')

    function csrfSafeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method))
    }
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken)
            }
        }
    })
})

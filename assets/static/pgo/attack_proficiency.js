$(document).ready(function(){
    $('.attack-pro-select').select2({
        'dropdownAutoWidth': false,
        'width': 250
    })
    // maintain tab index order
    $('select').on('select2:close', function() {
        $(this).focus()
    })
    var csrfToken = $('#csrf_token').val()
    var quickMoveSelect = $('#quick_move')
    var cinematicMoveSelect = $('#cinematic_move')
    var defenderSelect = $('#defender')
    var defenderLevelInput = $('#defender_lvl')
    var defenseIVInput = $('#defense_iv')
    var submitButton = $('#submit')
    var helpButton = $('#help_button')
    var formData = {
        defenderLevel: defenderLevelInput.val(),
        defenseIV: defenseIVInput.val(),
        raidTier: 5
    }
    var tableBody = $('#attack-proficiency-stats').find('tbody')
    var raidBossCheck = $('#raid_boss_check')
    var raidTier1 = $('#tier_1_radio')
    var raidTier2 = $('#tier_2_radio')
    var raidTier3 = $('#tier_3_radio')
    var raidTier4 = $('#tier_4_radio')
    var raidTier5 = $('#tier_5_radio')
    var raidTier = 5
    var dirty = false

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
    $('#attacker_lvl').on('change', function() {
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

    defenderSelect.change(function() {
        formData.defender = this.value
    })

    $('#attack-pro-form').on('submit', function(event) {
        event.preventDefault()
        tableBody.off('click')
        submitForm(formData)
    })

    filterDefenderSelect(raidTier)
    raidBossCheck.change(function() {
        if (this.checked) {
            filterDefenderSelect(raidTier)
            $('.raid_tier_radio').prop('disabled', false)
            formData.raidTier = raidTier
        }
        else {
            filterDefenderSelect(0)
            $('.raid_tier_radio').prop('disabled', true)
            formData.raidTier = 0
            formData.defender = undefined
        }
    })
    raidTier1.change(function() {
        if (this.checked) {
            raidTier = 1
            formData.raidTier = raidTier
        }
        formData.defender = undefined
        filterDefenderSelect(raidTier)
    })
    raidTier2.change(function() {
        if (this.checked) {
            raidTier = 2
            formData.raidTier = raidTier
        }
        formData.defender = undefined
        filterDefenderSelect(raidTier)
    })
    raidTier3.change(function() {
        if (this.checked) {
            raidTier = 3
            formData.raidTier = raidTier
        }
        formData.defender = undefined
        filterDefenderSelect(raidTier)
    })
    raidTier4.change(function() {
        if (this.checked) {
            raidTier = 4
            formData.raidTier = raidTier
        }
        formData.defender = undefined
        filterDefenderSelect(raidTier)
    })
    raidTier5.change(function() {
        if (this.checked) {
            raidTier = 5
            formData.raidTier = raidTier
        }
        formData.defender = undefined
        filterDefenderSelect(raidTier)
    })

    helpButton.on('click', function(event) {
        event.preventDefault()

        $('.help-text').toggle()
    })

    tableBody.one('click', 'td.attack-proficiency-detail', handleAttackProficiencyDetail)

    function handleAttackProficiencyDetail(event) {
        if (dirty) {
            submitForm(formData)
            return
        }

        event.preventDefault()
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
            var defenseIV = tableBody.find('tr').eq(0).find('td').eq(
                currentTarget.index())[0].textContent.replace(/[^0-9]/g,'')

            getAttackProficiencyDetail(level, defenseIV, formData, currentTarget.parent())
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

    function filterDefenderSelect(value) {
        if (parseInt(value) > 0) {
            $.ajax({
                url: window.pgoAPIURLs['defender-list'],
                type: 'GET',
                data: {
                    'raid-boss-tier-group': value
                },
                success: function(json) {
                    clearDefenderSelect('raid boss (Tier ' + value + ')')
                    $.each(json.results, function(i, pokemon) {
                        defenderSelect.append(
                            '<option value=' + pokemon.id + '>' + pokemon.name + ' (' + pokemon.pgo_defense + ' DEF)</option>'
                        )
                    })
                },
                error: function(xhr, errmsg, err) {
                    console.log('defender fileter error', xhr)
                }
            })
        }
        else {
            $.ajax({
                url: window.pgoAPIURLs['defender-list'],
                type: 'GET',
                success: function(json) {
                    clearDefenderSelect('defender')
                    $.each(json.results, function(i, pokemon) {
                        defenderSelect.append(
                            '<option value=' + pokemon.id + '>' + pokemon.name + ' (' + pokemon.pgo_defense + ' DEF)</option>'
                        )
                    })
                },
                error: function(xhr, errmsg, err) {
                    console.log('defender filter error', xhr)
                }
            })
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
                'attacker_lvl': formData.attackerLevel,
                'attack_iv': formData.attackIV,
                'defender': formData.defender,
                'defender_lvl': formData.defenderLevel,
                'defense_iv': formData.defenseIV,
                'raid_tier': formData.raidTier,
                'csrfmiddlewaretoken': csrfToken
            },
            success: function(json){
                clearErrors()
                displayAttackProficiency(json)
                generateAttackProficiencyStats(json)
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
                'raid_tier': json.raid_tier,
                'csrfmiddlewaretoken': csrfToken
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
                                if (td[0].textContent !== 'Attack breakdown against 15 DEF IV') {
                                    td.addClass('attack-proficiency-detail')
                                }
                                tr.append(td)
                                td = $('<td>')
                            }
                        }
                    }
                    tableBody.append(tr)
                }
                $('.attack-proficiency-stats-wrapper').show()

                var $lastRow = $('#attack-proficiency-stats tr:last')
                $lastRow.find('td:last').attr('id', 'clicked-cell')
                getAttackProficiencyDetail(40, 15, formData, $lastRow)
                dirty = false
            },
            error: function(xhr, errmsg, err){
                console.log('stats error', xhr)
            }
        })
    }

    function displayAttackProficiency(json) {
        $('.attack-proficiency-intro').hide()
        $('.attack-proficiency-current').show()
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
                'attacker_lvl': formData.attackerLevel,
                'attack_iv': formData.attackIV,
                'defender': formData.defender,
                'defender_lvl': level,
                'defense_iv': defenseIV,
                'raid_tier': formData.raidTier,
                'csrfmiddlewaretoken': csrfToken
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
            var detailsTable = $('<table class="table table-striped inner-table" width="'
                + totalWidth + '"></table>')
            detailsTable.append($(
                '<tr><td width="12%">' + details[0][0] +
                '</td><td width="22%">' + details[0][1] +
                '</td><td width="22%">' + details[0][2] +
                '</td><td width="22%">' + details[0][3] +
                '</td><td width="22%">' + details[0][4] +
            '</td></tr>'))

            for (row in details) {
                if (row > 0) {
                    detailsTable.append($(
                        '<tr><td>' + details[row][0] +
                        '</td><td>' + details[row][1] +
                        '</td><td>' + details[row][2] +
                        '</td><td>' + details[row][3] +
                        '</td><td>' + details[row][4] +
                        '</td></tr>'
                    ))
                }
            }
            wrapperTd.append(detailsTable)
        }
        rowToAppend.after(wrapper)
        $('.inner-table').after(
            $('<span>* powering pokemon over level 39 is currently not possible<span>'))
        wrapper.show()
    }

    function displayFieldErrors(errorObject) {
        for (error in errorObject) {
            var selector = '#' + error
            $(selector).addClass('error')
            $(selector).next().addClass('error')
        }
    }

    function clearErrors() {
        $('.error').removeClass('error')
        $('.form-error').empty()
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

    function clearDefenderSelect(text) {
        defenderSelect.empty()
        defenderSelect.append(
            '<option value="-1" disabled selected>Select ' + text + ' </option>'
        )
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
})

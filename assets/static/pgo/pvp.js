import Choices from 'choices.js'

const ready = (runPvP) => {
  if (document.attachEvent ? document.readyState === 'complete' : document.readyState !== 'loading') {
    runPvP()
  } else {
    document.addEventListener('DOMContentLoaded', runPvP)
  }
}

ready(() => {
  // constants
  const FORM_STATE = {
    SUBMITTING: 'submitting',
    READY: 'ready',
    ERROR: 'error',
  }
  const pvpForm = {
    state: FORM_STATE.READY,
    slotInFocus: null,
    selectedCount: 0,
    slot1: null,
    slot2: null,
    slot3: null,
  }
  const pokemonSlot1Id = 'pvp-pokemon-slot-1'
  const pokemonSlot2Id = 'pvp-pokemon-slot-2'
  const pokemonSlot3Id = 'pvp-pokemon-slot-3'

  // inputs
  const selectPokemon = new Choices(
    '.pvp-select-pokemon',
    {
      searchPlaceholderValue: 'Type in the pokemon\'s name',
      searchResultLimit: 5,
      itemSelectText: '',
    }
  )
  const help = document.querySelector('.pvp-help')
  const pokemonSlot1 = document.getElementById(pokemonSlot1Id)
  const pokemonSlot2 = document.getElementById(pokemonSlot2Id)
  const pokemonSlot3 = document.getElementById(pokemonSlot3Id)
  const pokemonWrapper1 = document.getElementById('pvp-pokemon-wrapper-1')
  const pokemonWrapper2 = document.getElementById('pvp-pokemon-wrapper-2')
  const pokemonWrapper3 = document.getElementById('pvp-pokemon-wrapper-3')

  // events
  selectPokemon.passedElement.addEventListener('change', (event) => {
    const pokemonId = event.currentTarget.value

    if (pokemonId > 0) {
      fetchPokemon(event.currentTarget.value, assignToSlot)
    }
  })
  pokemonSlot1.addEventListener('click', (event) => {
    switchSlotFocus(event.target.id, pvpForm.slot1)
  })
  pokemonSlot2.addEventListener('click', (event) => {
    switchSlotFocus(event.target.id, pvpForm.slot2)
  })
  pokemonSlot3.addEventListener('click', (event) => {
    switchSlotFocus(event.target.id, pvpForm.slot3)
  })

  // functions
  const initialFetch = () => {
    if (pvpForm.state !== FORM_STATE.SUBMITTING) {
      toggleState(FORM_STATE.SUBMITTING)

      selectPokemon.ajax((callback) => {
        fetch(window.pgoAPIURLs['simple-pokemon-list'])
          .then((response) => {
            response.json().then((data) => {
              callback(data, 'value', 'label')
              toggleState(FORM_STATE.READY)
            })
          })
          .catch((error) => {
            console.log(error)
            toggleState(FORM_STATE.ERROR)
          })
      })
    }
  }

  const fetchPokemon = (pokemonId, callback) => {
    if (pvpForm.state !== FORM_STATE.SUBMITTING) {
      toggleState(FORM_STATE.SUBMITTING)

      fetch(window.pgoAPIURLs['pokemon-list'] + `${pokemonId}/`)
        .then((response) => {
          response.json().then((data) => {
            toggleState(FORM_STATE.READY)
            callback(data)

            resetSelectPokemon()
          })
        })
        .catch((error) => {
          console.log(error)
          toggleState(FORM_STATE.ERROR)
        })
    }
  }

  const toggleState = (state) => {
    pvpForm.state = state
    pvpForm.state === FORM_STATE.SUBMITTING ? selectPokemon.disable() : selectPokemon.enable()
  }

  const assignToSlot = (data) => {
    if (!data) {
      return
    }
    let slot

    if (pvpForm.slot1 === null) {
      pvpForm.slot1 = data
      slot = pokemonSlot1Id
    } else if (pvpForm.slot2 === null) {
      pvpForm.slot2 = data
      slot = pokemonSlot2Id
    } else if (pvpForm.slot3 === null) {
      pvpForm.slot3 = data
      slot = pokemonSlot3Id
    } else {
      reassignSlot(data)
      return
    }
    pvpForm.selectedCount += 1
    switchSlotFocus(slot, data)
  }

  const switchSlotFocus = (slot, data) => {
    if (!data || slot === pvpForm.slotInFocus) {
      return
    }
    pvpForm.slotInFocus = slot

    switch (pvpForm.slotInFocus) {
      case pokemonSlot1Id:
        pokemonSlot1.classList.add('focused-slot')
        pokemonSlot1.classList.add('btn-primary')

        pokemonSlot1.classList.remove('empty-slot')
        pokemonSlot2.classList.remove('focused-slot')
        pokemonSlot3.classList.remove('focused-slot')
        renderPokemon(pokemonWrapper1, data)
        break
      case pokemonSlot2Id:
        pokemonSlot2.classList.add('focused-slot')
        pokemonSlot2.classList.add('btn-primary')

        pokemonSlot2.classList.remove('empty-slot')
        pokemonSlot1.classList.remove('focused-slot')
        pokemonSlot3.classList.remove('focused-slot')
        renderPokemon(pokemonWrapper2, data)
        break
      case pokemonSlot3Id:
        pokemonSlot3.classList.add('focused-slot')
        pokemonSlot3.classList.add('btn-primary')

        pokemonSlot3.classList.remove('empty-slot')
        pokemonSlot1.classList.remove('focused-slot')
        pokemonSlot2.classList.remove('focused-slot')
        renderPokemon(pokemonWrapper3, data)
        break
      default:
        break
    }
    updateHelpText()
  }

  const reassignSlot = (data) => {
    switch (pvpForm.slotInFocus) {
      case pokemonSlot1Id:
        pvpForm.slot1 = data
        renderPokemon(pokemonWrapper1, data)
        break
      case pokemonSlot2Id:
        pvpForm.slot2 = data
        renderPokemon(pokemonWrapper2, data)
        break
      case pokemonSlot3Id:
        pvpForm.slot3 = data
        renderPokemon(pokemonWrapper3, data)
        break
      default:
        break
    }
    updateHelpText()
  }

  const renderPokemon = (element, data) => {
    console.log(data)
    element.innerHTML = ''

    // extract name
    const header = document.createElement('div')
    header.classList.add('pvp-pokemon-header')
    const pokemonNameAndCP = document.createElement('span')
    const pokemonName = document.createElement('p')
    pokemonName.innerHTML = data.name
    pokemonNameAndCP.append(pokemonName)

    // extract cp
    const maximumCP = document.createElement('p')
    maximumCP.innerHTML = `${Math.round(data.maximum_cp)} CP`
    pokemonNameAndCP.append(maximumCP)
    header.append(pokemonNameAndCP)

    // extract types
    const typeWrapper = document.createElement('span')
    const primaryType = document.createElement('span')
    primaryType.innerHTML = data.primary_type.name
    primaryType.classList.add(...[`type-${data.primary_type.slug}`, 'type-label'])
    typeWrapper.append(primaryType)

    if (data.secondary_type) {
      const secondaryType = document.createElement('span')
      secondaryType.innerHTML = data.secondary_type.name
      secondaryType.classList.add(...[`type-${data.secondary_type.slug}`, 'type-label'])
      typeWrapper.append(secondaryType)
    }
    header.append(typeWrapper)
    element.append(header)

    // extract compound resistance / weakness
    const typeEffectivness = document.createElement('div')
    typeEffectivness.classList.add('pvp-pokemon-type-effectivness-wrapper')
    const compoundResistance = document.createElement('ul')
    compoundResistance.classList.add('pvp-compound-resistance')
    const compoundWeakness = document.createElement('ul')
    compoundWeakness.classList.add('pvp-compound-weakness')

    for (const [key, value] of Object.entries(data.compound_resistance)) {
      let resistance = document.createElement('li')
      resistance.classList.add(...[`type-${key.toLowerCase()}`, 'type-label', 'type-label-small'])
      let label = document.createElement('span')
      label.innerHTML = `${key}`
      let percentage = document.createElement('span')
      percentage.innerHTML = `${(Number.parseFloat(value).toPrecision(3) * 100)}%`
      resistance.append(label)
      resistance.append(percentage)
      compoundResistance.append(resistance)
    }
    typeEffectivness.append(compoundResistance)

    for (const [key, value] of Object.entries(data.compound_weakness)) {
      let resistance = document.createElement('li')
      resistance.classList.add(...[`type-${key.toLowerCase()}`, 'type-label', 'type-label-small'])
      let label = document.createElement('span')
      label.innerHTML = `${key}`
      let percentage = document.createElement('span')
      percentage.innerHTML = `${(Number.parseFloat(value).toPrecision(3) * 100)}%`
      resistance.append(label)
      resistance.append(percentage)
      compoundWeakness.append(resistance)
    }
    typeEffectivness.append(compoundWeakness)

    typeEffectivness.append(compoundWeakness)
    element.append(typeEffectivness)
    element.classList.add('pvp-pokemon-wrapper')
  }

  const updateHelpText = () => {
    help.innerHTML = ''

    const p = document.createElement('p')
    p.innerHTML = pvpForm.selectedCount < 3
      ? 'You can select ' + (3 - pvpForm.selectedCount) + ' more pokemon.'
      : `Selected ${pvpForm.slot1.name}, ${pvpForm.slot2.name}, and ${pvpForm.slot3.name}.`

    help.append(p)
    help.append(document.createElement('hr'))
  }

  const resetSelectPokemon = () => {
    selectPokemon.removeActiveItems()
    selectPokemon.setValueByChoice('-1')
  }

  // inital load
  initialFetch()
})

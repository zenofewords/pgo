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
  const summary = document.querySelector('.pvp-summary')
  const pokemonSlot1 = document.getElementById(pokemonSlot1Id)
  const pokemonSlot2 = document.getElementById(pokemonSlot2Id)
  const pokemonSlot3 = document.getElementById(pokemonSlot3Id)
  const pokemonWrapper1 = document.getElementById('pvp-pokemon-wrapper-1')

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

            updateSelectInput()
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

    if (data === pvpForm.slot1) {
      pokemonSlot1.classList.add('focused-slot')
      pokemonSlot1.classList.add('btn-primary')

      pokemonSlot1.classList.remove('empty-slot')
      pokemonSlot2.classList.remove('focused-slot')
      pokemonSlot3.classList.remove('focused-slot')
    } else if (data === pvpForm.slot2) {
      pokemonSlot2.classList.add('focused-slot')
      pokemonSlot2.classList.add('btn-primary')

      pokemonSlot2.classList.remove('empty-slot')
      pokemonSlot1.classList.remove('focused-slot')
      pokemonSlot3.classList.remove('focused-slot')
    } else if (data === pvpForm.slot3) {
      pokemonSlot3.classList.add('focused-slot')
      pokemonSlot3.classList.add('btn-primary')

      pokemonSlot3.classList.remove('empty-slot')
      pokemonSlot1.classList.remove('focused-slot')
      pokemonSlot2.classList.remove('focused-slot')
    }
    renderPokemon(data)
  }

  const reassignSlot = (data) => {
    switch (pvpForm.slotInFocus) {
      case pokemonSlot1Id:
        pvpForm.slot1 = data
        break
      case pokemonSlot2Id:
        pvpForm.slot2 = data
        break
      case pokemonSlot3Id:
        pvpForm.slot3 = data
        break
      default:
        break
    }
    renderPokemon(data)
  }

  const renderPokemon = (data) => {
    summary.innerHTML = ''
    pokemonWrapper1.innerHTML = data.name
  }

  const updateSelectInput = () => {
    selectPokemon.removeActiveItems()
    selectPokemon.setValueByChoice('-1')

    console.log(pvpForm)
  }

  // inital load
  initialFetch()
})

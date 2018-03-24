$(document).ready(function(){
  var moveSelect = $('.move-select')
  moveSelect.select2({
    'width': 145
  })
  var moveSelectForm = $('#move-select-form')

  moveSelect.on('change', function (event) {
    if (parseInt(this.value)) {
      moveSelectForm.append(
        '<input type="hidden" name="move_id" value="' + this.value + '" />')
      moveSelectForm.submit()
    }
  })

  var movesetSelectPokemon = $('.moveset-select-pokemon')
  var movesetSelectPokemonForm = $('#moveset-select-pokemon')
  movesetSelectPokemon.select2({
    'width': 95
  })

  movesetSelectPokemon.on('change', function (event) {
    if (parseInt(this.value)) {
      movesetSelectPokemonForm.append(
        '<input type="hidden" name="pokemon_id" value="' + this.value + '" />')
      movesetSelectPokemonForm.submit()
    }
  })

  var pokemonSelect = $('.pokemon-select')
  var typeSelect = $('.type-select')
  pokemonSelect.select2({
    'width': 145
  })
  typeSelect.select2({
    'width': 125
  })
  var pokemonSelectForm = $('#pokemon-select-form')
  var typeFilterForm = $('#type-filter-form')

  pokemonSelect.on('change', function (event) {
    if (parseInt(this.value)) {
      pokemonSelectForm.append(
        '<input type="hidden" name="pokemon_id" value="' + this.value + '" />')
      pokemonSelectForm.submit()
    }
  })
  typeSelect.on('change', function (event) {
    if (parseInt(this.value)) {
      typeFilterForm.append(
        '<input type="hidden" name="type_id" value="' + this.value + '" />')
      typeFilterForm.submit()
    }
  })
})

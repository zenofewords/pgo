import json
import re

from decimal import Decimal

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from pgo.models import (
    Move,
    MoveCategory,
    Moveset,
    MoveType,
    Pokemon,
    PokemonMove,
    Type,
)


class Command(BaseCommand):
    help = '''Add Pokemon data from Game Master json.'''

    def get_or_create_type(self, slug):
        if slug != '':
            obj, created = Type.objects.get_or_create(
                slug=slug,
                defaults={'name': slug.capitalize()}
            )
            return obj

    def get_or_create_pokemon(self, number, slug):
        obj, created = Pokemon.objects.get_or_create(number=number, slug=slug)

        if created:
            print('created', obj.slug)
        return obj, created

    def get_or_create_move(self, slug, category):
        obj, created = Move.objects.get_or_create(
            slug=slug,
            defaults={
                'name': slug.replace('-', ' ').title(),
                'category': category
            }
        )
        if created:
            print('created', obj.slug)
        return obj, created

    def get_or_create_pokemon_move(self, pokemon, move):
        obj, created = PokemonMove.objects.get_or_create(
            pokemon=pokemon,
            move=move,
            defaults={
                'stab': move.move_type in [pokemon.primary_type, pokemon.secondary_type],
                'cinematic': move.category == MoveCategory.CC,
                'move_type': move.move_type.slug,
            }
        )
        if created:
            print('created', obj)
        return obj

    def _append_move(self, move, pokemon):
        pokemon.quick_moves.add(self.get_or_create_pokemon_move(pokemon, move))

    def _process_pokemon(self, pokemon_data):
        new_movesets = []

        for pokemon_number, data in pokemon_data.items():
            pokemon, created = self.get_or_create_pokemon(data[0]['number'], data[1]['slug'])

            pokemon_types = []
            for detail in data:
                if 'slug' in detail:
                    slug = detail['slug']

                    name = slug.capitalize()
                    if slug == 'mr-mime':
                        name = 'Mr. Mime'
                    if slug == 'ho-oh':
                        name = 'Ho-Oh'

                    pokemon.slug = slug
                    pokemon.name = name

                if 'pokemon_types' in detail:
                    for pokemon_type in detail['pokemon_types']:
                        pokemon_types.append(
                            self.get_or_create_type(slugify(pokemon_type)))

                    if len(pokemon_types) == 2:
                        pokemon.secondary_type = pokemon_types[1]
                    pokemon.primary_type = pokemon_types[0]

                if 'stats' in detail:
                    pokemon.pgo_stamina = detail['stats'][0]['stamina']
                    pokemon.pgo_attack = detail['stats'][1]['attack']
                    pokemon.pgo_defense = detail['stats'][2]['defense']
            pokemon.save()

            for detail in data:
                if 'moves' in detail:
                    for move_name in detail['moves']['quick']:
                        quick_move = self.get_or_create_move(
                            slugify(move_name.replace('_', '-')), 'QK'
                        )[0]
                        if quick_move.slug == 'hidden-power':
                            PokemonMove.objects.filter(move=quick_move, pokemon=pokemon).delete()

                            for move_type in MoveType.CHOICES:
                                if move_type[0] != 'fairy' and move_type[0] != 'normal':
                                    self._append_move(self.get_or_create_move(
                                        'hidden-power-{}'.format(move_type[0]), 'QK')[0], pokemon)
                        else:
                            self._append_move(quick_move, pokemon)

                    for move_name in detail['moves']['cinematic']:
                        cinematic_move = self.get_or_create_move(
                            slugify(move_name.replace('_', '-')), 'CC'
                        )[0]
                        pokemon_cinematic_move = self.get_or_create_pokemon_move(
                            pokemon, cinematic_move)
                        pokemon.cinematic_moves.add(pokemon_cinematic_move)

            pokemon.legendary = data[5].get('legendary')

            for quick_move in pokemon.quick_moves.all():
                for cinematic_move in pokemon.cinematic_moves.all():
                    new_movesets.append(Moveset.objects.get_or_create(
                        pokemon=pokemon,
                        key='{} - {}'.format(quick_move.move, cinematic_move.move),
                        defaults={
                            'quick_move': quick_move,
                            'cinematic_move': cinematic_move,
                        }
                    ))
            pokemon.save()

    def _process_moves(self, move_data):
        for move_slug, data in move_data.items():
            move = None
            for detail in data:
                if 'category' in detail:
                    move, _ = self.get_or_create_move(
                        move_slug, detail['category'])
                if 'move_type' in detail:
                    move.move_type_id = \
                        self.get_or_create_type(detail['move_type']).id
                if 'power' in detail:
                    move.power = Decimal(detail['power'])
                if 'duration' in detail:
                    move.duration = int(detail['duration'])
                if 'damage_window_start' in detail:
                    move.damage_window_start = int(detail['damage_window_start'])
                if 'damage_window_end' in detail:
                    move.damage_window_end = int(detail['damage_window_end'])
                if 'energy_delta' in detail:
                    move.energy_delta = int(detail['energy_delta'])

            if move.move_type_id and move.power:
                move.save()

    def _process_pvp_moves(self, pvp_move_data):
        for pvp_move in pvp_move_data:
            slug = pvp_move[0]

            if slug in ['scald-blastoise', 'hydro-pump-blastoise', 'water-gun-blastoise']:
                continue

            power = int(float(pvp_move[1]))
            duration = int(pvp_move[2])
            delta = int(pvp_move[3]) if pvp_move[3] else 0

            pvp_move_data = {
                'pvp_power': power,
                'pvp_duration': duration,
                'pvp_energy_delta': delta,
                'dpt': Decimal(power / duration if duration > 0 else 0),
                'ept': Decimal(delta / duration if duration > 0 else 0),
                'dpe': Decimal(power / abs(delta) if abs(delta) > 0 else 0) if delta < 0 else 0,
            }

            if slug == 'hidden-power':
                Move.objects.filter(slug__startswith=slug).update(**pvp_move_data)
            else:
                Move.objects.filter(slug=slug).update(**pvp_move_data)

    def add_arguments(self, parser):
        parser.add_argument('path', nargs='?', type=str)

    def handle(self, *args, **options):
        path = '{0}{1}'.format(settings.BASE_DIR, '')
        file_path = options.get('path') if options.get('path') else path

        pokemon_data = {}
        move_data = {}
        pvp_move_data = []

        with open(file_path, 'r') as file:
            json_data = json.load(file)

        pokemon_pattern = re.compile('^V\\d+_POKEMON_[A-Z_*-*]+$', re.IGNORECASE)
        move_pattern = re.compile('^V\\d+_MOVE_[A-Z_*-*]+$', re.IGNORECASE)
        pvp_move_pattern = re.compile('^COMBAT_V\\d+_MOVE_[A-Z_*-*]+$', re.IGNORECASE)
        exclude = ('NORMAL', 'SHADOW', 'PURIFIED', )

        for data_line in json_data['itemTemplates']:
            data = []
            template_id = data_line['templateId']

            if pokemon_pattern.match(template_id) and all([x not in template_id for x in exclude]):
                pokemon_id = data_line['templateId'][2:5]
                pokemon_settings = data_line['pokemonSettings']
                pokemon_name = pokemon_settings['pokemonId']
                stats = pokemon_settings['stats']
                quick_moves = pokemon_settings.get('quickMoves')
                cinematic_moves = pokemon_settings.get('cinematicMoves')

                form = pokemon_settings.get('form')
                pokemon_name = form if form else pokemon_name

                data.append({'number': '#{}'.format(pokemon_id)})
                data.append({'slug': slugify(pokemon_name.replace('_', '-'))})

                if 'type2' in pokemon_settings:
                    data.append({'pokemon_types': (
                        pokemon_settings['type'][13:],
                        pokemon_settings['type2'][13:],
                    )})
                else:
                    data.append({'pokemon_types': (
                        pokemon_settings['type'][13:],
                    )})
                data.append({
                    'stats': (
                        {'stamina': stats['baseStamina']},
                        {'attack': stats['baseAttack']},
                        {'defense': stats['baseDefense']}
                    )
                })
                data.append({'moves': {
                    'quick': [m.replace('_FAST', '') for m in quick_moves] if quick_moves else [],
                    'cinematic': [m for m in cinematic_moves] if cinematic_moves else [],
                }})
                data.append({'legendary': bool(pokemon_settings.get('rarity', False))})
                pokemon_data[pokemon_name] = data

            if move_pattern.match(template_id):
                move_settings = data_line['moveSettings']
                move_name = slugify(move_settings['movementId']).replace('_', '-')

                category = 'CM'
                if 'blastoise' in move_name:
                    continue

                if 'fast' in move_name:
                    category = 'QK'
                    move_slug = move_name.replace('-fast', '')
                else:
                    move_slug = move_name

                data.append({'category': category})
                data.append({'move_type': slugify(move_settings['pokemonType'][13:])})
                data.append({'power': move_settings.get('power', 0)})
                data.append({'duration': move_settings.get('durationMs', 0)})
                data.append({'damage_window_start': move_settings.get('damageWindowStartMs', 0)})
                data.append({'damage_window_end': move_settings.get('damageWindowEndMs', 0)})
                data.append({'energy_delta': move_settings.get('energyDelta', 0)})
                move_data[move_slug] = data

            if pvp_move_pattern.match(template_id):
                move_settings = data_line['combatMove']
                move_name = slugify(move_settings['uniqueId']).replace('_', '-')

                data.append(move_name.replace('-fast', ''))
                data.append(move_settings.get('power', 0))
                data.append(move_settings.get('energyDelta', 0))
                data.append(move_settings.get('durationTurns', 0))
                data.append(move_settings.get('energyDelta', 0))
                data.append(slugify(move_settings.get('type')[13:]))

                pvp_move_data.append(data)

        self._process_moves(move_data)
        print('moves processed')
        self._process_pvp_moves(pvp_move_data)
        print('pvp moves processed')
        self._process_pokemon(pokemon_data)
        print('pokemon processed')

        call_command('pgo_calculate_stats')
        print('cp processed')
        call_command('pgo_compound_weakness_resistance')
        print('weakness and resistance processed')
        call_command('pgo_calculate_move_stats')
        print('move stats processed')
        call_command('pgo_calculate_weave_damage')
        print('moveset weave processed')
        call_command('pgo_populate_pokemon_moves')
        print('move scores processed')
        call_command('pgo_assign_goodtogo_bosses')
        print('good to go bosses processed')

        Pokemon.objects.filter(slug__in=(
            'shellos-west-sea',
            'shellos-east-sea',
            'gastrodon-east-sea',
            'gastrodon-west-sea',
            'giratina',
            'shaymin',
        )).delete()
        Pokemon.objects.filter(slug='mewtwo-a').update(name='Mewtwo-armored')
        Pokemon.objects.filter(slug='deoxys').update(name='Deoxys-normal')
        print('clean up redundant entries')

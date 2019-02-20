import csv
import re

from decimal import Decimal

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from pgo.models import (
    Pokemon,
    PokemonMove,
    Move,
    Moveset,
    Type,
)


class Command(BaseCommand):
    help = '''
        Build the CPM, Pokemon, Move and Type models, parsed from the .csv source file.
    '''

    def get_or_create_type(self, slug):
        if slug != '':
            obj, created = Type.objects.get_or_create(
                slug=slug,
                defaults={'name': slug.capitalize()}
            )
            return obj

    def get_or_create_pokemon(self, number, slug):
        obj, created = Pokemon.objects.get_or_create(number=number, slug=slug)
        return obj, created

    def get_or_create_move(self, slug, category):
        obj, created = Move.objects.get_or_create(
            slug=slug,
            defaults={
                'name': slug.replace('-', ' ').title(),
                'category': category
            }
        )
        return obj, created

    def get_or_create_pokemon_move(self, pokemon, move):
        obj, created = PokemonMove.objects.get_or_create(
            pokemon=pokemon,
            move=move,
            defaults={
               'stab': move.move_type in [pokemon.primary_type, pokemon.secondary_type],
            }
        )
        return obj

    def _process_pokemon(self, pokemon_data):
        new_movesets = []

        for pokemon_number, data in pokemon_data.items():
            quick_moves = []
            cinematic_moves = []
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
                        pokemon_quick_move = self.get_or_create_pokemon_move(pokemon, quick_move)
                        pokemon.quick_moves.add(pokemon_quick_move)
                        quick_moves.append(pokemon_quick_move)

                    for move_name in detail['moves']['cinematic']:
                        cinematic_move = self.get_or_create_move(
                            slugify(move_name.replace('_', '-')), 'CC'
                        )[0]
                        pokemon_cinematic_move = self.get_or_create_pokemon_move(pokemon, cinematic_move)
                        pokemon.cinematic_moves.add(pokemon_cinematic_move)
                        cinematic_moves.append(pokemon_cinematic_move)

                if 'legendary' in detail:
                    pokemon.legendary = True

            self._legacy_check_existing_moves(pokemon, quick_moves, cinematic_moves)
            for quick_move in quick_moves:
                for cinematic_move in cinematic_moves:
                    new_movesets.append(Moveset.objects.get_or_create(
                        pokemon=pokemon,
                        key='{} - {}'.format(quick_move.move, cinematic_move.move),
                        defaults={
                            'quick_move': quick_move,
                            'cinematic_move': cinematic_move,
                        }
                    ))
            pokemon.save()

    def _legacy_check_existing_moves(self, pokemon, quick_moves, cinematic_moves):
        hidden_powers = []
        for quick_move in quick_moves:
            if quick_move.move.slug == 'hidden-power':
                quick_moves.remove(quick_move)

                hidden_powers = PokemonMove.objects.filter(
                    pokemon=pokemon, move__slug__startswith=quick_move.move.slug)

        for hidden_power in hidden_powers:
            quick_moves.append(hidden_power)

        legacy_moves = PokemonMove.objects.filter(
            pokemon=pokemon).exclude(id__in=[x.pk for x in quick_moves + cinematic_moves])
        if legacy_moves:
            legacy_moves.update(legacy=True)

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
            energy_delta = int(pvp_move[3]) if pvp_move[3] else 0

            pvp_move_data = {
                'pvp_power': power,
                'pvp_duration': duration,
                'pvp_energy_delta': energy_delta,
                'dpt': Decimal(power / duration if duration > 0 else 0),
                'ept': Decimal(energy_delta / duration if duration > 0 else 0),
                'dpe': Decimal(power / abs(energy_delta) if abs(energy_delta) > 0 else 0) if energy_delta < 0 else 0,
            }

            if slug == 'hidden-power':
                Move.objects.filter(slug__startswith=slug).update(**pvp_move_data)
            else:
                Move.objects.filter(slug=slug).update(**pvp_move_data)

    def _next(self, csv_object, slice_start=None, slice_end=None):
        return next(csv_object)[0][slice_start:slice_end].strip()

    def _next_clean_string(self, csv_object):
        return re.sub(r'[^A-Za-z_,]+', '', str(next(csv_object)).lower())

    def _next_clean_numeric(self, csv_object):
        return re.sub(r'[^0-9.-]+', '', str(next(csv_object)))

    def _clean_numeric(self, line):
        return re.sub(r'[^0-9.-]+', '', str(line))

    def add_arguments(self, parser):
        parser.add_argument('path', nargs='?', type=str)

    def handle(self, *args, **options):
        path = '{0}{1}'.format(settings.BASE_DIR, '/pgo/game_master_genIV')
        file_path = options.get('path') if options.get('path') else path

        pokemon_data = {}
        move_data = {}
        pvp_move_data = []

        with open(file_path) as csvfile:
            csv_object = csv.reader(csvfile)

            for row in csv_object:
                if 'templateId": "V' in row[0]:
                    template_id = '#{0}'.format(row[0][23:26])

                    if 'pokemonSettings' in self._next(csv_object):
                        # name
                        data = []
                        name_string = row[0][35:-1].lower().replace('_', '-')

                        if 'giratina' == name_string or 'deoxys' == name_string:
                            continue
                        pokemon_id = slugify(self._next_clean_string(csv_object).replace('_', '-')[9:])

                        if name_string != pokemon_id:
                            if len(pokemon_id) > len(name_string):
                                name_string = pokemon_id

                        if 'deoxys' not in name_string:
                            name_string = name_string.replace('-normal', '')

                        data.append({'number': template_id})
                        data.append({'slug': slugify(name_string)})
                        self._next(csv_object)
                        # types
                        data.append({
                            'pokemon_types': (
                                self._next(csv_object, 30).replace('"', '').lower(),
                                self._next(csv_object, 31).replace('"', '').lower()
                            )
                        })

                        while 'stats' not in self._next(csv_object):
                            pass
                        # stats
                        data.append({
                            'stats': (
                                {'stamina': self._next_clean_numeric(csv_object)},
                                {'attack': self._next_clean_numeric(csv_object)},
                                {'defense': self._next_clean_numeric(csv_object)}
                            )
                        })
                        self._next(csv_object)

                        # moves
                        quick = []
                        cinematic = []
                        next_line = self._next_clean_string(csv_object)

                        while 'quickmoves' in next_line:
                            move = self._next_clean_string(csv_object)
                            if 'fast' in move:
                                quick.append(move.replace('_fast', '').replace(',', ''))
                            else:
                                next_line = self._next_clean_string(csv_object)

                        while 'cinematicmoves' in next_line:
                            move = self._next_clean_string(csv_object).replace(',', '')
                            if move:
                                cinematic.append(move)
                            else:
                                next_line = self._next_clean_string(csv_object)

                        moves = {
                            'quick': quick,
                            'cinematic': cinematic
                        }
                        data.append({'moves': moves})

                        while 'animation_time' in self._next(csv_object):
                            pass

                        pokemon_data[name_string] = data
                    else:
                        data = []
                        move_slug = slugify(self._next_clean_string(csv_object).replace('_', '-')[10:])
                        category = 'CC'
                        if 'blastoise' in move_slug:
                            continue

                        if 'fast' in move_slug:
                            category = 'QK'
                            move_slug = move_slug[:-5]
                        self._next(csv_object)

                        # name & category
                        data.append({'category': category})
                        # move type
                        data.append(
                            {'move_type': slugify(self._next_clean_string(csv_object)[24:])})
                        # power
                        if move_slug not in ['transform', 'splash', 'yawn']:
                            data.append({'power': self._next_clean_numeric(csv_object)})

                        while 'vfxName' not in self._next(csv_object):
                            pass

                        # durations & delta
                        data.append({
                            'duration': self._next_clean_numeric(csv_object)})
                        data.append({
                            'damage_window_start': self._next_clean_numeric(csv_object)})
                        data.append({
                            'damage_window_end': self._next_clean_numeric(csv_object)})

                        if move_slug not in ['transform', 'struggle']:
                            data.append({
                                'energy_delta': self._next_clean_numeric(csv_object)})
                        move_data[move_slug] = data

                pvp_move = []
                if '"templateId": "COMBAT_V' in row[0]:
                    next(csv_object)
                    next_line = self._next_clean_string(csv_object)
                    move_slug = next_line[8:].replace('_', '-').replace(',', '')
                    next(csv_object)

                    pvp_move.append(move_slug.replace('-fast', ''))
                    next_line = next(csv_object)

                    if 'power' in str(next_line):
                        power = self._clean_numeric(next_line)
                        pvp_move.append(power)

                        # skip vfx
                        next(csv_object)
                    else:
                        pvp_move.append(0)

                    next_line = next(csv_object)
                    if 'fast' in move_slug and 'energyDelta' in str(next_line):
                        pvp_move.append(1)

                        energy_delta = self._clean_numeric(next_line)
                        pvp_move.append(energy_delta)
                    else:
                        value = self._clean_numeric(next_line)
                        if int(value) < 0:
                            pvp_move.append(0)
                            pvp_move.append(value)
                        else:
                            duration_turns = self._clean_numeric(next_line)
                            pvp_move.append(int(duration_turns) + 1)
                            energy_delta = self._next_clean_numeric(csv_object)
                            pvp_move.append(energy_delta)
                    pvp_move_data.append(pvp_move)

        self._process_moves(move_data)
        print('moves processed')
        self._process_pvp_moves(pvp_move_data)
        print('pvp moves processed')
        self._process_pokemon(pokemon_data)
        print('pokemon processed')

        call_command('pgo_calculate_cp')
        print('cp processed')
        call_command('pgo_compound_weakness_resistance')
        print('weakness and resistance processed')
        call_command('pgo_calculate_move_stats')
        print('move stats processed')
        call_command('pgo_calculate_weave_damage')
        print('moveset weave processed')
        call_command('pgo_populate_pokemon_moves')
        print('move scores processed')

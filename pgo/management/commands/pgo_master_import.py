# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv
import re

from decimal import Decimal
from math import sqrt, pow

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from pgo.models import (
    CPM,
    Pokemon,
    PokemonMove,
    Move,
    Moveset,
    Type,
    TypeEffectivness,
    TypeEffectivnessScalar,
)
from pgo.utils import (
    SUPER_EFFECTIVE_SCALAR,
    NOT_VERY_EFFECTIVE_SCALAR,
    NEUTRAL_SCALAR,
    IMMUNE,
)
TYPE_EFFECTIVNESS = {
    'Super effective': SUPER_EFFECTIVE_SCALAR,
    'Not very effective': NOT_VERY_EFFECTIVE_SCALAR,
    'Immune': IMMUNE,
    'Neutral': NEUTRAL_SCALAR,
}
TYPE_IMPORT_ORDER = (
    'normal',
    'fighting',
    'flying',
    'poison',
    'ground',
    'rock',
    'bug',
    'ghost',
    'steel',
    'fire',
    'water',
    'grass',
    'electric',
    'psychic',
    'ice',
    'dragon',
    'dark',
    'fairy',
)


class Command(BaseCommand):
    help = '''
        Build the CPM, Pokemon, Move and Type models, parsed from the .csv source file.
    '''

    # def get_or_create_cpm(self, value, level):
    #     obj, created = CPM.gyms.get_or_create(
    #         level=level,
    #         defaults={'value': value}
    #     )

    def get_or_create_type(self, slug):
        if slug != '':
            obj, created = Type.objects.get_or_create(
                slug=slug,
                defaults={'name': slug.capitalize()}
            )
            return obj

    def get_or_create_type_effectivness_scalar(self, name, scalar):
        obj, created = TypeEffectivnessScalar.objects.get_or_create(
            slug=slugify(name),
            defaults={'scalar': Decimal(scalar), 'name': name}
        )

    def get_or_create_type_advantage(self, first_type, second_type, effectivness):
        relation = '{0}:{1}'.format(first_type.slug, second_type.slug)

        obj, created = TypeEffectivness.objects.get_or_create(
            relation=relation,
            defaults={
                'type_offense': first_type,
                'type_defense': second_type,
                'effectivness': effectivness,
            }
        )
        obj.effectivness = effectivness
        obj.save()

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

    # def _process_cpm(self, cpm):
    #     previous_value = None
    #     for cp_m in [(y, x + 1) for x, y in enumerate(cpm)]:
    #         value = cp_m[0]
    #         level = cp_m[1]
    #         self.get_or_create_cpm(value, level)

    #         if previous_value:
    #             halflevel_value = \
    #                 sqrt((pow(previous_value, 2) + pow(value, 2)) / 2.0)
    #             self.get_or_create_cpm(halflevel_value, level - 0.5)
    #             previous_value = None

    #         previous_value = value

    # def _process_type_advantages(self, type_and_scalar_data):
    #     for first_type_slug, type_data_and_scalars in type_and_scalar_data.items():

    #         first_type = Type.objects.get(slug=first_type_slug)

    #         for data in type_data_and_scalars:
    #             for second_type_slug, scalar in data.items():
    #                 second_type = Type.objects.get(slug=second_type_slug)
    #                 self.get_or_create_type_advantage(
    #                     first_type, second_type, TypeEffectivnessScalar.objects.get(scalar=scalar))

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

    # def _map_type_effectivness(self):
    #     types = Type.objects.all()
    #     se = TypeEffectivnessScalar.objects.get(slug='super-effective').scalar
    #     nve = TypeEffectivnessScalar.objects.get(slug='not-very-effective').scalar
    #     imn = TypeEffectivnessScalar.objects.get(slug='immune').scalar

    #     for _type in types:
    #         type_offense_strong = []
    #         type_offense_feeble = []
    #         type_offense_puny = []
    #         type_defense_resistant = []
    #         type_defense_weak = []
    #         type_defense_immune = []

    #         for type_e in _type.type_offense.all():
    #             scalar = type_e.effectivness.scalar
    #             if scalar == se:
    #                 type_offense_strong.append((type_e.type_defense, scalar))
    #             if scalar == nve:
    #                 type_offense_feeble.append((type_e.type_defense, scalar))
    #             if scalar == imn:
    #                 type_offense_puny.append((type_e.type_defense, scalar))
    #         for type_e in _type.type_defense.all():
    #             scalar = type_e.effectivness.scalar
    #             if scalar == nve:
    #                 type_defense_resistant.append((type_e.type_offense, scalar))
    #             if scalar == se:
    #                 type_defense_weak.append((type_e.type_offense, scalar))
    #             if scalar == imn:
    #                 type_defense_immune.append((type_e.type_offense, scalar))

    #         type_offense_strong.sort(key=lambda x: x[0].name)
    #         type_offense_feeble.sort(key=lambda x: x[0].name)
    #         type_defense_resistant.sort(key=lambda x: x[0].name)
    #         type_defense_weak.sort(key=lambda x: x[0].name)
    #         type_offense_puny.sort(key=lambda x: x[0].name)
    #         type_defense_immune.sort(key=lambda x: x[0].name)

    #         _type.strong = [(x[0].name, float(x[1])) for x in type_offense_strong]
    #         _type.feeble = [(x[0].name, float(x[1])) for x in type_offense_feeble]
    #         _type.puny = [(x[0].name, float(x[1])) for x in type_offense_puny]
    #         _type.resistant = [(x[0].name, float(x[1])) for x in type_defense_resistant]
    #         _type.weak = [(x[0].name, float(x[1])) for x in type_defense_weak]
    #         _type.immune = [(x[0].name, float(x[1])) for x in type_defense_immune]
    #         _type.save()

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

        Type.objects.get_or_create(slug='dark', defaults={'name': 'Dark'})
        for name, scalar in TYPE_EFFECTIVNESS.items():
            self.get_or_create_type_effectivness_scalar(name, scalar)

        # cpm_data = []
        # type_data = {}
        pokemon_data = {}
        move_data = {}
        pvp_move_data = []

        with open(file_path) as csvfile:
            csv_object = csv.reader(csvfile)

            for row in csv_object:
                # if 'templateId": "POKEMON_TYPE' in row[0]:
                #     key = slugify(row[0][32:].replace('"', ''))
                #     type_data[key] = ''
                #     self._next(csv_object)

                #     type_data_scalars = []
                #     effectivness_array = self._next(csv_object, 23).replace(']', '').split(',', 18)

                #     for n in range(1, 19):
                #         effectivness_scalar = effectivness_array[n - 1]

                #         type_data_scalars.append(
                #             {TYPE_IMPORT_ORDER[n - 1]: effectivness_scalar})
                #     type_data[key] = type_data_scalars

                if 'templateId": "V' in row[0]:
                    template_id = '#{0}'.format(row[0][21:24])

                    if 'pokemonSettings' in self._next(csv_object):
                        # name
                        data = []
                        name_string = row[0][33:-1].lower().replace('_', '-')
                        pokemon_id = slugify(self._next(csv_object, 16).replace('_', '-'))

                        if 'deoxys' == name_string:
                            continue

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
                                self._next(csv_object, 28).replace('",', ''),
                                self._next(csv_object, 29).replace('",', '')
                            )
                        })

                        while 'stats' not in self._next(csv_object):
                            pass
                        # stats
                        data.append({
                            'stats': (
                                {'stamina': self._next(csv_object, 23).replace(',', '')},
                                {'attack': self._next(csv_object, 22).replace(',', '')},
                                {'defense': self._next(csv_object, 23).replace(',', '')}
                            )
                        })
                        self._next(csv_object)

                        # moves
                        quick = []
                        cinematic = []
                        next_line = self._next_clean_string(csv_object)
                        while 'moves' in next_line:
                            if 'quickmoves' in next_line:
                                quick_moves = next_line[10:-1].split(',')

                                for qm in quick_moves:
                                    quick.append(qm.replace('_fast', ''))
                            if 'cinematicmoves' in next_line:
                                charge_moves = next_line[14:-1].split(',')

                                for cm in charge_moves:
                                    cinematic.append(cm)
                            next_line = self._next_clean_string(csv_object)

                        moves = {
                            'quick': quick,
                            'cinematic': cinematic
                        }
                        data.append({'moves': moves})

                        while 'animation_time' in self._next(csv_object):
                            pass

                        if 'rarity' in self._next(csv_object):
                            data.append({'legendary': True})
                        pokemon_data[name_string] = data
                    else:
                        data = []
                        move_slug = slugify(
                            self._next(csv_object, 17).replace('_', '-'))
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
                            {'move_type': slugify(self._next(csv_object, 35))})
                        # power

                        if move_slug not in ['transform', 'splash', 'yawn']:
                            data.append({'power': self._next(csv_object, 15).replace(',', '')})

                        while 'vfxName' not in self._next(csv_object):
                            pass

                        # durations & delta
                        data.append({
                            'duration': self._next(csv_object, 20).replace(',', '')})
                        data.append({
                            'damage_window_start': self._next(csv_object, 29).replace(',', '')})
                        data.append({
                            'damage_window_end': self._next(csv_object, 27).replace(',', '')})

                        if move_slug not in ['transform', 'struggle']:
                            data.append({
                                'energy_delta': self._next(csv_object, 21).replace(',', '')})
                        move_data[move_slug] = data

                # pvp moves
                # "templateId": "COMBAT_V0250_MOVE_VOLT_SWITCH_FAST",
                # "combatMove": {
                #   "uniqueId": "VOLT_SWITCH_FAST",
                #   "type": "POKEMON_TYPE_ELECTRIC",
                #   "power": 12.0,
                #   "vfxName": "volt_switch_fast",
                #   "durationTurns": 4,
                #   "energyDelta": 10

                # "templateId": "COMBAT_V0013_MOVE_WRAP",
                # "combatMove": {
                #   "uniqueId": "WRAP",
                #   "type": "POKEMON_TYPE_NORMAL",
                #   "power": 60.0,
                #   "vfxName": "wrap",
                #   "energyDelta": -45
                # }
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

        # self._process_type_advantages(type_data)
        # self._process_cpm(cpm_data)
        # self._map_type_effectivness()

        self._process_moves(move_data)
        self._process_pvp_moves(pvp_move_data)
        # self._process_pokemon(pokemon_data)

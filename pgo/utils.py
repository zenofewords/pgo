from __future__ import division

from math import floor

SUPER_EFFECTIVE_SCALAR = 1.4
NOT_VERY_EFFECTIVE_SCALAR = 0.714
NEUTRAL_SCALAR = 1.0
STAB_SCALAR = 1.2
TIMEOUT = 99000
RAID_TIER_POKEMON_GROUPS = {
    '5': ('lugia', 'articuno', 'moltres', 'zapdos', 'ho-oh', 'suicune', 'entei', 'raikou', 'mew', 'mewtwo', 'celebi'),
    '4': ('venusaur', 'charizard', 'blastoise', 'snorlax', 'lapras', 'tyranitar', 'rhydon'),
    '3': ('machamp', 'alakazam', 'gengar', 'jolteon', 'flareon', 'vaporeon', 'arcanine'),
    '2': ('weezing', 'muk', 'exeggutor', 'magmar', 'electabuzz'),
    '1': ('quilava', 'bayleef', 'croconaw', 'magikarp'),
}


def simulate_weave_damage(quick_move, cinematic_move, health):

    def _timeout(step, duration):
        return step + duration > TIMEOUT

    def _knockout(damage, health):
        return True if damage >= health else False

    step = 0
    energy = 0
    damage = 0

    while step < TIMEOUT:
        if not _timeout(step, cinematic_move.duration):
            if energy >= cinematic_move.energy_delta * - 1:
                damage += cinematic_move.damage_per_hit
                step += (cinematic_move.duration + 1000)

                if _knockout(damage, health):
                    return damage, step / 1000
                energy += cinematic_move.energy_delta

        if _timeout(step, quick_move.duration):
            step = 99000
            break

        damage += quick_move.damage_per_hit
        step += quick_move.duration

        if _knockout(damage, health):
            return damage, step / 1000
        energy += quick_move.energy_delta
    return damage, step / 1000


def calculate_weave_damage(qk_move, cc_move, health=None):
    if qk_move.energy_delta > 0:
        qk_moves_required = (cc_move.energy_delta * - 1) / qk_move.energy_delta
    else:
        qk_moves_required = 0
    cycle_dps = (
        qk_moves_required * qk_move.damage_per_hit + cc_move.damage_per_hit) / (
        (qk_moves_required * qk_move.duration + cc_move.duration) / 1000)

    if health:
        return health / cycle_dps
    return cycle_dps


def calculate_dph(power, attack_multiplier, stab, effectivness=1.0):

    def _get_stab(stab):
        return STAB_SCALAR if stab else NEUTRAL_SCALAR

    return int(floor(0.5 * power * float(attack_multiplier) *
        _get_stab(stab) * float(effectivness)) + 1)


def calculate_health(total_stamina, cpm):
    return int(floor(total_stamina * cpm))


def calculate_defender_health(total_stamina, cpm):
    return calculate_health(total_stamina, cpm) * 2


def calculate_defense(total_defense, cpm):
    return int(floor(total_defense * cpm))

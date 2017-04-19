from math import floor

TIMEOUT = 99000


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
                    return damage, step
                energy += cinematic_move.energy_delta

        if _timeout(step, quick_move.duration):
            break

        damage += quick_move.damage_per_hit
        step += quick_move.duration

        if _knockout(damage, health):
            return damage, step
        energy += quick_move.energy_delta
    return damage, step


def calculate_dph(power, attack_multiplier, stab, effectivness=1.0):

    def _get_stab(stab):
        return 1.25 if stab else 1.0

    return int(floor(
        0.5 * power * float(attack_multiplier) * _get_stab(stab) * float(effectivness)) + 1)


def calculate_health(total_stamina, cpm):
    return int(floor(total_stamina * cpm))


def calculate_defender_health(total_stamina, cpm):
    return calculate_health(total_stamina, cpm) * 2


def calculate_defense(total_defense, cpm):
    return int(floor(total_defense * cpm))

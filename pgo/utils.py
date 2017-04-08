from math import floor

LEVELS = (20.0, 25.0, 30.0, 35.0, 40.0)
TIMEOUT = 99000


def calculate_weave_damage(attack_multiplier, quick_move, cinematic_move, stab):
    def _timeout(step, duration):
        return step + duration > TIMEOUT

    weave_damage = {}
    for level in LEVELS:
        step = 0
        energy = 0
        damage = 0

        while step < TIMEOUT:
            if not _timeout(step, cinematic_move.duration):
                if energy >= cinematic_move.energy_delta * - 1:

                    damage += calculate_dph(
                        cinematic_move.power, attack_multiplier, stab[1])
                    step += (cinematic_move.duration + 1000)
                    energy += cinematic_move.energy_delta

            if _timeout(step, quick_move.duration):
                break

            damage += calculate_dph(
                quick_move.power, attack_multiplier, stab[0])
            step += quick_move.duration
            energy += quick_move.energy_delta

        weave_damage[level] = damage
    return weave_damage


def calculate_dph(power, attack_multiplier, stab, effectivness=1.0):
    def _get_stab(stab):
        return 1.25 if stab else 1.0

    return floor(
        0.5 * power * float(attack_multiplier) * _get_stab(stab) * float(effectivness)) + 1

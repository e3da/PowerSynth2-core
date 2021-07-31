"""
This code is used for defining material of MainCode
"""

import math


class MaterialProperties:
    def __init__(self, name=None, thermal_cond_so=None, thermal_cond_liq=None, spec_heat_cap_so=None, spec_heat_cap_liq=None,
                 density_so=None, density_liq=None, electrical_res=None, rel_permit=None, rel_permeab=None,
                 young_modulus=None, poisson_ratio=None, thermal_expansion_coefficient=None,
                 type=None, liquid_fraction=None, melting_temp=None):

        self.name = name
        self.thermal_cond_so = thermal_cond_so
        self.thermal_cond_liq = thermal_cond_liq
        self.spec_heat_cap_so = spec_heat_cap_so
        self.spec_heat_cap_liq = spec_heat_cap_liq
        self.density_so = density_so
        self.density_liq = density_liq
        self.electrical_res = electrical_res
        self.rel_permit = rel_permit
        self.rel_permeab = rel_permeab
        self.young_modulus = young_modulus
        self.poisson_ratio = poisson_ratio
        self.thermal_expansion_coefficient = thermal_expansion_coefficient
        self.type = type
        self.liquid_fraction = liquid_fraction
        self.melting_temp = melting_temp
##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
#
# Please see the files COPYRIGHT.txt and LICENSE.txt for full copyright and
# license information, respectively. Both files are also available online
# at the URL "https://github.com/IDAES/idaes".
##############################################################################
"""
Tests for CSTR unit model.
Authors: Andrew Lee, Vibhav Dabadghao
"""

import pytest
from pyomo.environ import ConcreteModel, SolverFactory
from idaes.core import FlowsheetBlock
from idaes.unit_models.cstr import CSTR
from idaes.property_models.examples.saponification_thermo import (
    PhysicalParameterBlock)
from idaes.property_models.examples.saponification_reactions import (
    ReactionParameterBlock)
from idaes.ui.report import degrees_of_freedom


# -----------------------------------------------------------------------------
# See if ipopt is available and set up solver
if SolverFactory('ipopt').available():
    solver = SolverFactory('ipopt')
    solver.options = {'tol': 1e-6,
                      'mu_init': 1e-8,
                      'bound_push': 1e-8}
else:
    solver = None


# -----------------------------------------------------------------------------
def test_build():
    m = ConcreteModel()
    m.fs = FlowsheetBlock(default={"dynamic": False})

    m.fs.properties = PhysicalParameterBlock()
    m.fs.reactions = ReactionParameterBlock(default={
                            "property_package": m.fs.properties})

    m.fs.cstr = CSTR(default={"property_package": m.fs.properties,
                              "reaction_package": m.fs.reactions,
                              "has_equilibrium_reactions": False,
                              "has_heat_transfer": True,
                              "has_pressure_change": False})

    assert hasattr(m.fs.cstr, "inlet")
    assert len(m.fs.cstr.inlet[0].vars) == 4
    assert hasattr(m.fs.cstr.inlet[0], "flow_vol")
    assert hasattr(m.fs.cstr.inlet[0], "conc_mol_comp")
    assert hasattr(m.fs.cstr.inlet[0], "temperature")
    assert hasattr(m.fs.cstr.inlet[0], "pressure")

    assert hasattr(m.fs.cstr, "outlet")
    assert len(m.fs.cstr.outlet[0].vars) == 4
    assert hasattr(m.fs.cstr.outlet[0], "flow_vol")
    assert hasattr(m.fs.cstr.outlet[0], "conc_mol_comp")
    assert hasattr(m.fs.cstr.outlet[0], "temperature")
    assert hasattr(m.fs.cstr.outlet[0], "pressure")

    assert hasattr(m.fs.cstr, "cstr_performance_eqn")
    assert hasattr(m.fs.cstr.control_volume, "heat")
    assert hasattr(m.fs.cstr, "heat_duty")


@pytest.mark.skipif(solver is None, reason="Solver not available")
def test_initialize():
    m = ConcreteModel()
    m.fs = FlowsheetBlock(default={"dynamic": False})

    m.fs.properties = PhysicalParameterBlock()
    m.fs.reactions = ReactionParameterBlock(default={
                            "property_package": m.fs.properties})

    m.fs.cstr = CSTR(default={"property_package": m.fs.properties,
                              "reaction_package": m.fs.reactions,
                              "has_equilibrium_reactions": False,
                              "has_heat_transfer": False,
                              "has_pressure_change": False})

    m.fs.cstr.inlet[:].flow_vol.fix(1.0e-03)
    m.fs.cstr.inlet[:].conc_mol_comp["H2O"].fix(55388.0)
    m.fs.cstr.inlet[:].conc_mol_comp["NaOH"].fix(100.0)
    m.fs.cstr.inlet[:].conc_mol_comp["EthylAcetate"].fix(100.0)
    m.fs.cstr.inlet[:].conc_mol_comp["SodiumAcetate"].fix(0.0)
    m.fs.cstr.inlet[:].conc_mol_comp["Ethanol"].fix(0.0)

    m.fs.cstr.inlet[:].temperature.fix(303.15)
    m.fs.cstr.inlet[:].pressure.fix(101325.0)

    m.fs.cstr.control_volume.volume.fix(1.5e-03)

    assert degrees_of_freedom(m) == 0

    m.fs.cstr.initialize(outlvl=5,
                         optarg={'tol': 1e-6})

    assert (pytest.approx(101325.0, abs=1e-2) ==
            m.fs.cstr.outlet[0].vars["pressure"].value)
    assert (pytest.approx(303.15, abs=1e-2) ==
            m.fs.cstr.outlet[0].vars["temperature"].value)
    # print(m.fs.cstr.outlet[0].conc_mol_comp["EthylAcetate"].value)
    assert (pytest.approx(20.80, abs=1e-2) ==
            m.fs.cstr.outlet[0].conc_mol_comp["EthylAcetate"].value)

# -*- coding: utf-8 -*-
#
#
# TheVirtualBrain-Framework Package. This package holds all Data Management, and 
# Web-UI helpful to run brain-simulations. To use it, you also need do download
# TheVirtualBrain-Scientific Package (for simulators). See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2013, Baycrest Centre for Geriatric Care ("Baycrest")
#
# This program is free software; you can redistribute it and/or modify it under 
# the terms of the GNU General Public License version 2 as published by the Free
# Software Foundation. This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details. You should have received a copy of the GNU General 
# Public License along with this program; if not, you can download it here
# http://www.gnu.org/licenses/old-licenses/gpl-2.0
#
#
# CITATION:
# When using The Virtual Brain for scientific publications, please cite it as follows:
#
#   Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
#   Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
#       The Virtual Brain: a simulator of primate brain network dynamics.
#   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#

"""
This module is an example of how to validate model parameters and models.
The idea is to pick some model parameters then run a short simulation and see if it fails.
If it failed then you know that the model is broken with those settings.
You will use this module to run high dimensional parameter space explorations and get a report of what worked and what not.

.. moduleauthor:: Mihai Andrei <mihai.andrei@codemart.ro>
"""

import itertools

from tvb.simulator.lab import *

# maybe a good idea given the high dimensionality of the model parameter space
# def sample_parameter_space_monte_carlo(some_distribution):
#     pass

def sample_parameter_space_cartesian(path_assignments):
    """
    Samples the parameter space systematically based on explicit values for each dimension (parameter).
    :param path_assignments: a list of (param_name, [param_values])
    >>> list(sample_parameter_space_cartesian([('a', [1, 2]), ('b', [3, 4])]))
    ... [{'a': 1, 'b': 3}, {'a': 1, 'b': 4}, {'a': 2, 'b': 3}, {'a': 2, 'b': 4}]
    """
    # 'transpose' path_assignments
    paths, values = zip(*path_assignments)
    # cartesian product of value assignments
    for value_assignment in itertools.product(*values):
        yield dict(zip(paths, value_assignment))


def _set_sim_values(sim, path_assignment):
    """
    :param sim: A Simulator instance that will be modified
    :param path_assignment: a dict Ex {'model.a': 12, 'param.subpar.s': 100}
    The string_accessor should access a field on sim. Ex: model.param.subparam
    """
    for pth, val in path_assignment.iteritems():
        code = 'sim.%s = val' % pth
        exec code in {'sim': sim, 'val': val}


def run_exploration(sim, simulation_length, parameters):
    """
    Runs a series of simulations and reports weather they completed successfully or failed with FloatingPointError
    :param sim: a Simulator()
    :param simulation_length:
    :param parameters: [ {'model.a': 2, 'prop.subprop.w: 3 ...} ... ]
    :return:
    """

    print 'starting model parameter space exploration'
    print '------------------------------------------'

    numpy.seterr(divide='raise', invalid='raise')

    for params in parameters:
        _set_sim_values(sim, params)
        sim.configure()
        print params,

        try:
            for traw in sim(simulation_length=simulation_length):
                traw = traw[0]
                state = traw[1]
                if not numpy.all(numpy.isfinite(state)):
                    raise FloatingPointError('infinities generated outside numpy')
            print 'ok'
        except FloatingPointError:
            print 'bad'


def example():
    model = models.Generic2dOscillator()
    white_matter = connectivity.Connectivity(load_default=True)
    det_int = integrators.HeunDeterministic(dt=2 ** -4)

    sim = simulator.Simulator(
        model=model,
        connectivity=white_matter,
        coupling=coupling.Linear(a=0.0126),
        integrator=det_int,
        monitors=[monitors.Raw()],
    )

    exploration_settings = [
        ('model.tau', [0.0, 1.0]),
        ('model.b', [-5.0, 15.0]),
        ('model.d', [0.0, 0.5, 1.0]),
        # ('coupling.a', [1,3])  # you can also use non-model parameter dimensions like this
    ]

    print 'cartesian sampling settings: '
    print exploration_settings
    print '------------------------------------------'


    run_exploration(
        sim,
        simulation_length=10,
        parameters=sample_parameter_space_cartesian(exploration_settings)
    )


if __name__ == '__main__':
    example()
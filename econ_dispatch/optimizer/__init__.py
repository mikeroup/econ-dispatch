# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:

# Copyright (c) 2017, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation
# are those of the authors and should not be interpreted as representing
# official policies, either expressed or implied, of the FreeBSD
# Project.
#
# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization that
# has cooperated in the development of these materials, makes any
# warranty, express or implied, or assumes any legal liability or
# responsibility for the accuracy, completeness, or usefulness or any
# information, apparatus, product, software, or process disclosed, or
# represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does not
# necessarily constitute or imply its endorsement, recommendation, or
# favoring by the United States Government or any agency thereof, or
# Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830
# }}}

import pulp
import logging
_log = logging.getLogger(__name__)
import os.path
import os

def get_optimization_function(config):
    name = config["name"]
    write_lp = config.get("write_lp", False)
    use_glpk = config.get("use_glpk", False)
    glpk_options = config.get("glpk_options", [])
    lp_out_dir = config.get("lp_out_dir", "lps")

    if write_lp:
        try:
            os.makedirs(lp_out_dir)
        except Exception:
            pass

    module = __import__(name, globals(), locals(), ['get_optimization_problem'], 1)
    get_optimization_problem = module.get_optimization_problem

    def optimize(now, forecast, parameters = {}):
        prob = get_optimization_problem(forecast, parameters)

        if write_lp:
            prob.writeLP(os.path.join(lp_out_dir, str(now).replace(":", "_")+".lp"))

        convergence_time = -1
        objective_value = -1

        try:
            if use_glpk:
                prob.solve(pulp.solvers.GLPK_CMD(options=glpk_options))
            else:
                prob.solve()
            #
        except Exception as e:
            _log.warning("PuLP failed: " + str(e))
        else:
            convergence_time = prob.solutionTime
            objective_value = pulp.value(prob.objective)

        status = pulp.LpStatus[prob.status]

        result = {}

        for var in prob.variables():
            result[var.name] = var.varValue

        result["Optimization Status"] = status

        result["Objective Value"] = objective_value
        result["Convergence Time"] = convergence_time

        return result

    return optimize
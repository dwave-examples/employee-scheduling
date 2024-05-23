# Copyright 2024 D-Wave Systems Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
from collections import defaultdict

from dimod import (
    Binary,
    BinaryQuadraticModel,
    ConstrainedQuadraticModel,
    quicksum,
)
from dwave.system import LeapHybridCQMSampler


def build_cqm(
    availability,
    shifts,
    min_shifts,
    max_shifts,
    shift_min,
    shift_max,
    manager,
    isolated,
    k,
):
    """Builds the ConstrainedQuadraticModel for the given scenario."""
    cqm = ConstrainedQuadraticModel()
    employees = list(availability.keys())

    # Create variables: one per employee per shift
    x = {(i, j): Binary(i + "_" + j) for j in shifts for i in employees}

    # Objective: give employees preferred schedules (val = 2)
    obj = BinaryQuadraticModel(vartype="BINARY")
    for e in employees:
        sched = availability[e]
        for s in range(len(shifts)):
            if sched[s] == 2:
                obj += -x[e, shifts[s]]

    # Objective: for infeasible solutions, focus on right number of shifts for employees
    num_s = (min_shifts + max_shifts) / 2
    for e in employees:
        obj += (
            quicksum(x[e, shifts[s]] for s in range(len(shifts))) - num_s
        ) ** 2
    cqm.set_objective(obj)

    # Only schedule employees when they're available
    for e in employees:
        sched = availability[e]
        for s in range(len(shifts)):
            if sched[s] == 0:
                cqm.add_constraint(x[e, shifts[s]] == 0, label=f"unavailable,{e},{s}")

    # Schedule employees for at most max_shifts
    for e in employees:
        cqm.add_constraint(
            quicksum(x[e, shifts[s]] for s in range(len(shifts)))
            <= max_shifts,
            label=f"overtime,{e},",
        )

    # Schedule employees for at least min_shifts
    for e in employees:
        cqm.add_constraint(
            quicksum(x[e, shifts[s]] for s in range(len(shifts)))
            >= min_shifts,
            label=f"insufficient,{e},",
        )

    # Every shift needs shift_min and shift_max employees working
    for s in range(len(shifts)):
        cqm.add_constraint(
            sum(x[e, shifts[s]] for e in employees) >= shift_min,
            label=f"understaffed,,{shifts[s]}",
        )
        cqm.add_constraint(
            sum(x[e, shifts[s]] for e in employees) <= shift_max,
            label=f"overstaffed,,{shifts[s]}",
        )

    # Days off are consecutive
    if not isolated:
        # middle range shifts - pattern 101 penalized
        for s in range(len(shifts) - 2):
            for e in employees:
                cqm.add_constraint(
                    -3 * x[e, shifts[s + 1]]
                    + x[e, shifts[s]] * x[e, shifts[s + 1]]
                    + x[e, shifts[s + 1]] * x[e, shifts[s + 2]]
                    + x[e, shifts[s]] * x[e, shifts[s + 2]]
                    <= 0,
                    label=f"isolated,{e},{shifts[s + 1]}",
                )
        # end shifts - patterns 01 at start and 10 at end penalized
        for e in employees:
            cqm.add_constraint(
                x[e, shifts[1]] - x[e, shifts[0]] <= 0,
                label=f"isolated,{e},{shifts[0]}",
            )
            cqm.add_constraint(
                x[e, shifts[-2]] - x[e, shifts[-1]] <= 0,
                label=f"isolated,{e},{shifts[-1]}",
            )

    # Require a manager on every shift
    if manager:
        mgr_list = [e for e in employees if e[-3:] == "Mgr"]
        for s in range(len(shifts)):
            cqm.add_constraint(
                quicksum(x[m, shifts[s]] for m in mgr_list) == 1,
                label=f"manager_issue,,{shifts[s]}",
            )

    # No k shifts consecutive
    for e in employees:
        for s in range(len(shifts) - k + 1):
            cqm.add_constraint(
                quicksum([x[e, shifts[s + i]] for i in range(k)]) <= k - 1,
                label=f"too_many_consecutive,{e},{shifts[s]}",
            )

    # Trainee must work on shifts with trainer
    tr_list = [e for e in employees if e[-2:] == "Tr"]
    for s in range(len(shifts)):
        cqm.add_constraint(
            x[tr_list[0], shifts[s]]
            - x[tr_list[0], shifts[s]] * x[tr_list[0][:-3], shifts[s]]
            == 0,
            label=f"trainee_issue,,{shifts[s]}",
        )

    return cqm


def run_cqm(cqm):
    """Run the provided CQM on the Leap Hybrid CQM Sampler."""
    sampler = LeapHybridCQMSampler()

    sampleset = sampler.sample_cqm(cqm)
    feasible_sampleset = sampleset.filter(lambda row: row.is_feasible)

    num_feasible = len(feasible_sampleset)
    if num_feasible == 0:
        errors = defaultdict(list)
        sat_array = sampleset.first.is_satisfied

        # if sampleset is all 0's, set at least one variable to 1
        # --> this is needed for "Solve CQM" button to function propertly
        s_vals = set(sampleset.first.sample.values())
        if s_vals == {0.0}:
            sampleset.first.sample[list(cqm.variables)[0]] = 1.0

        msgs = {
            "unavailable": (
                "Employees scheduled when unavailable",
                "{employee} on day {day}"
            ),
            "overtime": (
                "Employees with scheduled overtime",
                "{employee} has too many shifts"
            ),
            "insufficient": (
                "Employees with not enough scheduled time",
                "{employee} doesn't have enough shifts"
            ),
            "understaffed": (
                "Understaffed shifts",
                "Day {day} is understaffed"
            ),
            "overstaffed": (
                "Overstaffed shifts",
                "Day {day} is overstaffed"
            ),
            "isolated": (
                "Isolated shifts",
                "Day off {day} is isolated for {employee}"
            ),
            "manager_issue": (
                "Shifts with manager issues",
                "No manager scheduled on day {day}"
            ),
            "too_many_consecutive": (
                "Employees with too many consecutive shifts",
                "{employee} starting with day {day}"
            ),
            "trainee_issue": (
                "Shifts with trainee scheduling issues",
                "Trainee scheduling issue on day {day}"
            ),
        }
        for i, _ in enumerate(sat_array):
            if not sat_array[i]:
                key, *data = sampleset.info["constraint_labels"][i].split(",")
                try:
                    heading, error_msg = msgs[key]
                except KeyError:
                    # ignore any unknown constraint labels
                    continue

                # constraint label should be of form "key,employee,day"
                format_dict = dict(zip(["employee", "day"], data))
                errors[heading].append(error_msg.format(**format_dict))

        return sampleset, errors

    return feasible_sampleset, None

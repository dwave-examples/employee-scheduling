# Copyright 2024 D-Wave
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

from utils import DAYS, FULL_TIME_SHIFTS, SHIFTS


def build_cqm(
    availability,
    shifts,
    min_shifts,
    max_shifts,
    shift_forecast,
    allow_isolated_days_off,
    max_consecutive_shifts,
    num_full_time,
):
    """Builds the ConstrainedQuadraticModel for the given scenario."""
    cqm = ConstrainedQuadraticModel()
    employees = list(availability.keys())
    employees_ft = employees[:num_full_time]
    employees_pt = employees[num_full_time:]

    # Create variables: one per employee per shift
    x = {(employee, shift): Binary(employee + "_" + shift) for shift in shifts for employee in employees}

    # OBJECTIVES:
    # Objective: give employees preferred schedules (val = 2)
    obj = BinaryQuadraticModel(vartype="BINARY")
    for employee, schedule in availability.items():
        for i, shift in enumerate(shifts):
            if schedule[i] == 2:
                obj += -x[employee, shift]

    # Objective: for infeasible solutions, focus on right number of shifts for employees
    num_s = (min_shifts + max_shifts) / 2
    for employee in employees_pt:
        obj += (
            quicksum(x[employee, shift] for shift in shifts) - num_s
        ) ** 2
    for employee in employees_ft:
        obj += (
            quicksum(x[employee, shift] for shift in shifts) - FULL_TIME_SHIFTS
        ) ** 2
    cqm.set_objective(obj)


    # CONSTRAINTS:
    # Only schedule employees when they're available
    for employee, schedule in availability.items():
        for i, shift in enumerate(shifts):
            if schedule[i] == 0:
                cqm.add_constraint(x[employee, shift] == 0, label=f"unavailable,{employee},{shift}")

    for employee in employees_pt:
        # Schedule employees for at most max_shifts
        cqm.add_constraint(
            quicksum(x[employee, shift] for shift in shifts)
            <= max_shifts,
            label=f"overtime,{employee},",
        )

        # Schedule employees for at least min_shifts
        cqm.add_constraint(
            quicksum(x[employee, shift] for shift in shifts)
            >= min_shifts,
            label=f"insufficient,{employee},",
        )

    for employee in employees_ft:
        # Schedule employees for at most max_shifts
        cqm.add_constraint(
            quicksum(x[employee, shift] for shift in shifts)
            <= FULL_TIME_SHIFTS,
            label=f"overtime,{employee},",
        )

        cqm.add_constraint(
            quicksum(x[employee, shift] for shift in shifts)
            >= FULL_TIME_SHIFTS,
            label=f"insufficient,{employee},",
        )

    # Every shift needs shift_min and shift_max employees working
    for i, shift in enumerate(shifts):
        cqm.add_constraint(
            sum(x[employee, shift] for employee in employees) >= shift_forecast[i],
            label=f"understaffed,,{shift}",
        )
        cqm.add_constraint(
            sum(x[employee, shift] for employee in employees) <= shift_forecast[i],
            label=f"overstaffed,,{shift}",
        )

    # Days off must be consecutive
    if not allow_isolated_days_off:
        # middle range shifts - pattern 101 penalized
        for i, prev_shift in enumerate(shifts[:-2]):
            shift = shifts[i + 1]
            next_shift = shifts[i + 2]
            for employee in employees_pt:
                cqm.add_constraint(
                    -3 * x[employee, shift]
                    + x[employee, prev_shift] * x[employee, shift]
                    + x[employee, shift] * x[employee, next_shift]
                    + x[employee, prev_shift] * x[employee, next_shift]
                    <= 0,
                    label=f"isolated,{employee},{shift}",
                )

    # Require a manager on every shift
    managers = [employee for employee in employees if employee[-3:] == "Mgr"]
    for shift in shifts:
        cqm.add_constraint(
            quicksum(x[manager, shift] for manager in managers) >= 1,
            label=f"manager_issue,,{shift}",
        )

    # Don't exceed max_consecutive_shifts
    for employee in employees_pt:
        for s in range(len(shifts) - max_consecutive_shifts + 1):
            cqm.add_constraint(
                quicksum(
                    [x[employee, shifts[s + i]] for i in range(max_consecutive_shifts)]
                ) <= max_consecutive_shifts - 1,
                label=f"too_many_consecutive,{employee},{shifts[s]}",
            )

    # Trainee must work on shifts with trainer
    trainees = [employee for employee in employees if employee[-2:] == "Tr"]
    for shift in shifts:
        cqm.add_constraint(
            x[trainees[0], shift]
            - x[trainees[0], shift] * x[trainees[0][:-3], shift]
            == 0,
            label=f"trainee_issue,,{shift}",
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
                "{employee} on {day}"
            ),
            "overtime": (
                "Employees with scheduled overtime",
                "{employee}"
            ),
            "insufficient": (
                "Employees with not enough scheduled time",
                "{employee}"
            ),
            "understaffed": (
                "Understaffed shifts",
                "{day} is understaffed"
            ),
            "overstaffed": (
                "Overstaffed shifts",
                "{day} is overstaffed"
            ),
            "isolated": (
                "Isolated shifts",
                "{day} is an isolated day off for {employee}"
            ),
            "manager_issue": (
                "Shifts with no manager",
                "No manager scheduled on {day}"
            ),
            "too_many_consecutive": (
                "Employees with too many consecutive shifts",
                "{employee} starting with {day}"
            ),
            "trainee_issue": (
                "Shifts with trainee scheduling issues",
                "Trainee scheduling issue on {day}"
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

                # translate day index into day of week and date
                if format_dict["day"]:
                    index = int(format_dict["day"]) - 1
                    format_dict["day"] = f"{DAYS[index%7]} {SHIFTS[index]}"

                errors[heading].append(error_msg.format(**format_dict))

        return sampleset, errors

    return feasible_sampleset, None

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
from typing import Optional

from dimod import (
    Binary,
    BinaryQuadraticModel,
    ConstrainedQuadraticModel,
    quicksum,
)
from dwave.optimization.model import Model
from dwave.optimization.mathematical import add
from dwave.optimization.symbols import BinaryVariable
from dwave.system import LeapHybridCQMSampler, LeapHybridNLSampler

from utils import DAYS, SHIFTS, ModelParams, validate_nl_schedule


MSGS = {
    "unavailable": ("Employees scheduled when unavailable", "{employee} on {day}"),
    "overtime": ("Employees with scheduled overtime", "{employee}"),
    "insufficient": ("Employees with not enough scheduled time", "{employee}"),
    "understaffed": ("Understaffed shifts", "{day} is understaffed"),
    "overstaffed": ("Overstaffed shifts", "{day} is overstaffed"),
    "isolated": ("Isolated shifts", "{day} is an isolated day off for {employee}"),
    "manager_issue": ("Shifts with no manager", "No manager scheduled on {day}"),
    "too_many_consecutive": (
        "Employees with too many consecutive shifts",
        "{employee} starting with {day}",
    ),
    "trainee_issue": (
        "Shifts with trainee scheduling issues",
        "Trainee scheduling issue on {day}",
    ),
}


def build_cqm(params: ModelParams):
    """Builds the ConstrainedQuadraticModel for the given scenario."""
    cqm = ConstrainedQuadraticModel()
    employees = list(params.availability.keys())

    # Create variables: one per employee per shift
    x = {
        (employee, shift): Binary(employee + "_" + shift)
        for shift in params.shifts
        for employee in employees
    }

    # OBJECTIVES:
    # Objective: give employees preferred schedules (val = 2)
    obj = BinaryQuadraticModel(vartype="BINARY")
    for employee, schedule in params.availability.items():
        for i, shift in enumerate(params.shifts):
            if schedule[i] == 2:
                obj += -x[employee, shift]

    # Objective: for infeasible solutions, focus on right number of shifts for employees
    num_s = (params.min_shifts + params.max_shifts) / 2
    for employee in employees:
        obj += (quicksum(x[employee, shift] for shift in params.shifts) - num_s) ** 2
    cqm.set_objective(obj)

    # CONSTRAINTS:
    # Only schedule employees when they're available
    for employee, schedule in params.availability.items():
        for i, shift in enumerate(params.shifts):
            if schedule[i] == 0:
                cqm.add_constraint(
                    x[employee, shift] == 0, label=f"unavailable,{employee},{shift}"
                )

    for employee in employees:
        # Schedule employees for at most max_shifts
        cqm.add_constraint(
            quicksum(x[employee, shift] for shift in params.shifts)
            <= params.max_shifts,
            label=f"overtime,{employee},",
        )

        # Schedule employees for at least min_shifts
        cqm.add_constraint(
            quicksum(x[employee, shift] for shift in params.shifts)
            >= params.min_shifts,
            label=f"insufficient,{employee},",
        )

    # Every shift needs shift_min and shift_max employees working
    for shift in params.shifts:
        cqm.add_constraint(
            sum(x[employee, shift] for employee in employees) >= params.shift_min,
            label=f"understaffed,,{shift}",
        )
        cqm.add_constraint(
            sum(x[employee, shift] for employee in employees) <= params.shift_max,
            label=f"overstaffed,,{shift}",
        )

    # Days off must be consecutive
    if not params.allow_isolated_days_off:
        # middle range shifts - pattern 101 penalized
        for i, prev_shift in enumerate(params.shifts[:-2]):
            shift = params.shifts[i + 1]
            next_shift = params.shifts[i + 2]
            for employee in employees:
                cqm.add_constraint(
                    -3 * x[employee, shift]
                    + x[employee, prev_shift] * x[employee, shift]
                    + x[employee, shift] * x[employee, next_shift]
                    + x[employee, prev_shift] * x[employee, next_shift]
                    <= 0,
                    label=f"isolated,{employee},{shift}",
                )

    # Require a manager on every shift
    if params.requires_manager:
        managers = [employee for employee in employees if employee[-3:] == "Mgr"]
        for shift in params.shifts:
            cqm.add_constraint(
                quicksum(x[manager, shift] for manager in managers) == 1,
                label=f"manager_issue,,{shift}",
            )

    # Don't exceed max_consecutive_shifts
    for employee in employees:
        for s in range(len(params.shifts) - params.max_consecutive_shifts):
            cqm.add_constraint(
                quicksum(
                    [
                        x[employee, params.shifts[s + i]]
                        for i in range(params.max_consecutive_shifts + 1)
                    ]
                )
                <= params.max_consecutive_shifts,
                label=f"too_many_consecutive,{employee},{params.shifts[s]}",
            )

    # Trainee must work on shifts with trainer
    trainees = [employee for employee in employees if employee[-2:] == "Tr"]
    for shift in params.shifts:
        cqm.add_constraint(
            x[trainees[0], shift] - x[trainees[0], shift] * x[trainees[0][:-3], shift]
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

        for i, _ in enumerate(sat_array):
            if not sat_array[i]:
                key, *data = sampleset.info["constraint_labels"][i].split(",")
                try:
                    heading, error_msg = MSGS[key]
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


def build_nl(params: ModelParams) -> tuple[Model, BinaryVariable]:
    """Builds an employee scheduling nonlinear model.

    Args:
        params (ModelParams): model parameters

    Returns:
        tuple[Model, BinaryVariable]: the NL model and assignments decision variable
    """
    # Create list of employees
    employees = list(params.availability)
    model = Model()

    # Create a binary symbol representing the assignment of employees to shifts
    # i.e. assignments[employee][shift] = 1 if assigned, else 0
    num_employees = len(employees)
    num_shifts = len(params.shifts)
    assignments = model.binary((num_employees, num_shifts))

    # Create availability constant
    availability_list = [params.availability[employee] for employee in employees]
    for i, sublist in enumerate(availability_list):
        availability_list[i] = [a if a != 2 else 100 for a in sublist]
    availability_const = model.constant(availability_list)

    # Initialize model constants
    min_shifts_constant = model.constant(params.min_shifts)
    max_shifts_constant = model.constant(params.max_shifts)
    shift_min_constant = model.constant(params.shift_min)
    shift_max_constant = model.constant(params.shift_max)
    max_consecutive_shifts_c = model.constant(params.max_consecutive_shifts)
    one_c = model.constant(1)

    # OBJECTIVES:
    # Objective: give employees preferred schedules (val = 2)
    obj = (assignments * availability_const).sum()

    # Objective: for infeasible solutions, focus on right number of shifts for employees
    target_shifts = model.constant((params.min_shifts + params.max_shifts) / 2)
    shift_difference_list = [
        (assignments[e, :].sum() - target_shifts) ** 2 for e in range(num_employees)
    ]
    obj += add(*shift_difference_list)

    model.minimize(-obj)

    # CONSTRAINTS:
    # Only schedule employees when they're available
    model.add_constraint((availability_const >= assignments).all())

    for e in range(len(employees)):
        # Schedule employees for at most max_shifts
        model.add_constraint(assignments[e, :].sum() <= max_shifts_constant)

        # Schedule employees for at least min_shifts
        model.add_constraint(assignments[e, :].sum() >= min_shifts_constant)

    # Every shift needs shift_min and shift_max employees working
    for s in range(num_shifts):
        model.add_constraint(assignments[:, s].sum() <= shift_max_constant)
        model.add_constraint(assignments[:, s].sum() >= shift_min_constant)

    managers_c = model.constant(
        [employees.index(e) for e in employees if e[-3:] == "Mgr"]
    )
    trainees_c = model.constant(
        [employees.index(e) for e in employees if e[-2:] == "Tr"]
    )

    if not params.allow_isolated_days_off:
        negthree_c = model.constant(-3)
        zero_c = model.constant(0)
        # Adding many small constraints greatly improves feasibility
        for e in range(len(employees)):
            for s1 in range(len(params.shifts) - 2):
                s2, s3 = s1 + 1, s1 + 2
                model.add_constraint(
                    negthree_c * assignments[e, s2]
                    + assignments[e][s1] * assignments[e][s2]
                    + assignments[e][s1] * assignments[e][s3]
                    + assignments[e][s2] * assignments[e][s3]
                    <= zero_c
                )

    if params.requires_manager:
        for shift in range(len(params.shifts)):
            model.add_constraint(assignments[managers_c][:, shift].sum() == one_c)

    # Don't exceed max_consecutive_shifts
    for e in range(num_employees):
        for s in range(num_shifts - params.max_consecutive_shifts + 1):
            s_window = s + params.max_consecutive_shifts + 1
            model.add_constraint(
                assignments[e][s : s_window + 1].sum() <= max_consecutive_shifts_c
            )

    # Trainee must work on shifts with trainer
    trainers = []
    for i in trainees_c.state():
        trainer_name = employees[int(i)][:-3]
        trainers.append(employees.index(trainer_name))
    trainers_c = model.constant(trainers)

    model.add_constraint((assignments[trainees_c] <= assignments[trainers_c]).all())

    return model, assignments


def run_nl(
    model: Model,
    assignments: BinaryVariable,
    params: ModelParams,
    time_limit: int | None = None,
    msgs: dict[str, tuple[str, str]] = MSGS,
) -> Optional[defaultdict[str, list[str]]]:
    """Solves the NL scheduling model and detects any errors.

    Args:
        model (Model): NL model to solve
        assignments (BinaryVariable): decision variable for employee shifts
        time_limit (int | None, optional): time limit for sampling. Defaults to None.
    """
    if not model.is_locked():
        model.lock()

    sampler = LeapHybridNLSampler()
    sampler.sample(model, time_limit=time_limit)
    errors = validate_nl_schedule(assignments, params, msgs)

    # Return errors if any error message list is populated
    for error_list in errors.values():
        if len(error_list) > 0:
            return errors

    return None


if __name__ == "__main__":
    ...

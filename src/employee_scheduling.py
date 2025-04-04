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
from typing import Optional

from dimod import Binary, BinaryQuadraticModel, ConstrainedQuadraticModel, quicksum
from dwave.optimization.mathematical import add
from dwave.optimization.model import Model
from dwave.optimization.symbols import BinaryVariable
from dwave.system import LeapHybridCQMSampler, LeapHybridNLSampler

from src.utils import DAYS, FULL_TIME_SHIFTS, SHIFTS, validate_nl_schedule

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


def build_cqm(  # params: ModelParams
    availability: dict[str, list[int]],
    shifts: list[str],
    min_shifts: int,
    max_shifts: int,
    shift_forecast: list,
    allow_isolated_days_off: bool,
    max_consecutive_shifts: int,
    num_full_time: int,
) -> ConstrainedQuadraticModel:
    """Builds the ConstrainedQuadraticModel for the given scenario.

     Args:
        availability: A dictionary of employees and their availabilities.
        shifts: A list of shift keys.
        min_shifts: The minimum shifts each employee needs to work per schedule.
        max_shifts: The maximum shifts any employee can work per schedule.
        shift_forecast: A list of the number of expected employees needed per shift.
        allow_isolated_days_off: Whether on-off-on should be allowed in the schedule.
        max_consecutive_shifts: The maximum consectutive shifts to schedule a part-time employee for.
        num_full_time: The number of full-time employees.

    Returns:
        cqm: A Constrained Quadratic Model representing the problem.
    """
    cqm = ConstrainedQuadraticModel()
    employees = list(availability.keys())
    employees_ft = employees[:num_full_time]
    employees_pt = employees[num_full_time:]

    # Create variables: one per employee per shift
    x = {
        (employee, shift): Binary(employee + "_" + shift)
        for shift in shifts
        for employee in employees
    }

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
        obj += (quicksum(x[employee, shift] for shift in shifts) - num_s) ** 2
    for employee in employees_ft:
        obj += (quicksum(x[employee, shift] for shift in shifts) - FULL_TIME_SHIFTS) ** 2
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
            quicksum(x[employee, shift] for shift in shifts) <= max_shifts,
            label=f"overtime,{employee},",
        )

        # Schedule employees for at least min_shifts
        cqm.add_constraint(
            quicksum(x[employee, shift] for shift in shifts) >= min_shifts,
            label=f"insufficient,{employee},",
        )

    for employee in employees_ft:
        # Schedule full-time employees for all their shifts
        cqm.add_constraint(
            quicksum(x[employee, shift] for shift in shifts) <= FULL_TIME_SHIFTS,
            label=f"overtime,{employee},",
        )

        cqm.add_constraint(
            quicksum(x[employee, shift] for shift in shifts) >= FULL_TIME_SHIFTS,
            label=f"insufficient,{employee},",
        )

    # Every shift needs shift_forecast employees working
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
        for s in range(len(shifts) - max_consecutive_shifts):
            cqm.add_constraint(
                quicksum([x[employee, shifts[s + i]] for i in range(max_consecutive_shifts + 1)])
                <= max_consecutive_shifts,
                label=f"too_many_consecutive,{employee},{shifts[s]}",
            )

    # Trainee must work on shifts with trainer
    trainees = [employee for employee in employees if employee[-2:] == "Tr"]
    for shift in shifts:
        cqm.add_constraint(
            x[trainees[0], shift] - x[trainees[0], shift] * x[trainees[0][:-3], shift] == 0,
            label=f"trainee_issue,,{shift}",
        )

    return cqm


def run_cqm(cqm: ConstrainedQuadraticModel):
    """Run the provided CQM on the Leap Hybrid CQM Sampler.

    Args:
        cqm: A Constrained Quadratic Model representing the problem.

    Returns:
        sampleset: A set of feasible or infeasible solutions.
        errors: A dictionary of error types and the errors that occurred.
    """
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


def build_nl(  # params: ModelParams
    availability: dict[str, list[int]],
    shifts: list[str],
    min_shifts: int,
    max_shifts: int,
    shift_forecast: list,
    allow_isolated_days_off: bool,
    max_consecutive_shifts: int,
    num_full_time: int,
) -> tuple[Model, BinaryVariable]:
    """Builds an employee scheduling nonlinear model.

    Args:
        availability (dict[str, list[int]]): Employee availability.
        shifts (list[str]): Shift labels.
        min_shifts (int): Minimum shifts per employee.
        max_shifts (int): Maximum shifts per employee.
        shift_forecast (list[int]): A list of the number of expected employees needed per shift.
        allow_isolated_days_off (bool): Whether to allow isolated days off.
        max_consecutive_shifts (int): Maximum consecutive shifts per employee.
        num_full_time (int): The number of full-time employees.

    Returns:
        tuple[Model, BinaryVariable]: the NL model and assignments decision variable
    """
    # Create list of employees
    employees = list(availability)
    model = Model()

    # Create a binary symbol representing the assignment of employees to shifts
    # i.e. assignments[employee][shift] = 1 if assigned, else 0
    num_employees = len(employees)
    num_shifts = len(shifts)
    assignments = model.binary((num_employees, num_shifts))

    # Create availability constant
    availability_list = [availability[employee] for employee in employees]
    availability_const = model.constant(availability_list)

    # Initialize model constants
    min_shifts_constant = model.constant(min_shifts)
    max_shifts_constant = model.constant(max_shifts)
    full_time_shifts_constant = model.constant(FULL_TIME_SHIFTS)
    shift_forecast_constant = model.constant(shift_forecast)
    max_consecutive_shifts_c = model.constant(max_consecutive_shifts)
    one_c = model.constant(1)

    # OBJECTIVES:
    # Objective: give employees preferred schedules (val = 2)
    obj = -(assignments * availability_const).sum()

    # Objective: for infeasible solutions, focus on right number of shifts for employees
    target_shifts = model.constant((min_shifts + max_shifts) / 2)
    shift_difference_list_pt = [
        (assignments[e, :].sum() - target_shifts) ** 2 for e in range(num_full_time, num_employees)
    ]
    shift_difference_list_ft = [
        (assignments[e, :].sum() - full_time_shifts_constant) ** 2 for e in range(num_full_time)
    ]
    obj += add(*shift_difference_list_pt, *shift_difference_list_ft)

    model.minimize(obj)

    # CONSTRAINTS:
    # Only schedule employees when they're available
    model.add_constraint((availability_const >= assignments).all())

    # Schedule part-time employees for at most max_shifts
    model.add_constraint((assignments[num_full_time:, :].sum(axis=1) <= max_shifts_constant).all())

    # Schedule part-time employees for at least min_shifts
    model.add_constraint((assignments[num_full_time:, :].sum(axis=1) >= min_shifts_constant).all())

    if num_full_time:
        # Schedule full-time employees for all their shifts
        model.add_constraint(
            (assignments[:num_full_time, :].sum(axis=1) == full_time_shifts_constant).all()
        )

    # Schedule only forecast number of employees per day
    model.add_constraint((assignments.sum(axis=0) == shift_forecast_constant).all())

    managers_c = model.constant([employees.index(e) for e in employees if e[-3:] == "Mgr"])
    trainees_c = model.constant([employees.index(e) for e in employees if e[-2:] == "Tr"])

    if not allow_isolated_days_off:
        negthree_c = model.constant(-3)
        zero_c = model.constant(0)
        # Adding many small constraints greatly improves feasibility
        for e in range(num_full_time, num_employees):  # for part-time employees
            for s1 in range(len(shifts) - 2):
                s2, s3 = s1 + 1, s1 + 2
                model.add_constraint(
                    negthree_c * assignments[e, s2]
                    + assignments[e][s1] * assignments[e][s2]
                    + assignments[e][s1] * assignments[e][s3]
                    + assignments[e][s2] * assignments[e][s3]
                    <= zero_c
                )

    # At least 1 manager per shift
    model.add_constraint((assignments[managers_c].sum(axis=0) >= one_c).all())

    # Don't exceed max_consecutive_shifts for part-time employees
    for e in range(num_full_time, num_employees):
        for s in range(num_shifts - max_consecutive_shifts + 1):
            s_window = s + max_consecutive_shifts + 1
            model.add_constraint(assignments[e][s : s_window + 1].sum() <= max_consecutive_shifts_c)

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
    availability: dict[str, list[int]],
    shifts: list[str],
    min_shifts: int,
    max_shifts: int,
    shift_forecast: list[int],
    allow_isolated_days_off: bool,
    max_consecutive_shifts: int,
    num_full_time: int,
    time_limit: Optional[int] = None,
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
    errors = validate_nl_schedule(
        assignments,
        msgs,
        availability,
        shifts,
        min_shifts,
        max_shifts,
        shift_forecast,
        allow_isolated_days_off,
        max_consecutive_shifts,
    )

    # Return errors if any error message list is populated
    for error_list in errors.values():
        if len(error_list) > 0:
            return errors

    return None

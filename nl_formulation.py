from typing import Callable

import numpy as np
from dwave.optimization.mathematical import add
from dwave.optimization.model import Model
from dwave.optimization.symbols import BinaryVariable
from dwave.system import LeapHybridNLSampler
from tabulate import tabulate
from colorama import Fore, Style

availability = {
    "Marcus K-Mgr": [1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
    "Robert C-Mgr": [1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 2],
    "Jonathan B": [1, 1, 0, 0, 1, 1, 1, 1, 1, 2, 1, 1, 1, 2],
    "Thomas U": [1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 2, 0, 1, 1],
    "Herbert I": [1, 2, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1],
    "Donna Z": [1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1],
    "Karen T": [1, 1, 1, 1, 2, 1, 0, 1, 1, 1, 1, 2, 1, 1],
    "Seth F": [1, 2, 1, 1, 0, 2, 1, 1, 1, 1, 1, 1, 1, 1],
    "Stephanie F": [1, 1, 2, 2, 1, 1, 2, 1, 0, 1, 1, 1, 1, 1],
    "Casey B": [1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 2],
    "Mike P": [1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 2, 1],
    "Mike P-Tr": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
}

shifts = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14"]

min_shifts = 5
max_shifts = 7
shift_min = 3
shift_max = 6
requires_manager = True
allow_isolated_days_off = False
max_consecutive_shifts = 6


def build_nl(
    availability: dict[str, list[int]],
    shifts: list[str],
    min_shifts: int,
    max_shifts: int,
    shift_min: int,
    shift_max: int,
    requires_manager: bool,
    allow_isolated_days_off: bool,
    max_consecutive_shifts: int,
) -> tuple[Model, BinaryVariable]:
    # Create list of employees
    employees = list(availability.keys())
    model = Model()

    # Create a binary symbol representing the assignment of employees to shifts
    # i.e. assignments[employee][shift] = 1 if assigned, else 0
    num_employees = len(employees)
    num_shifts = len(shifts)
    assignments = model.binary((num_employees, num_shifts))

    # Create availability constant
    availability_list = [availability[employee] for employee in employees]
    for i, sublist in enumerate(availability_list):
        availability_list[i] = [a if a != 2 else 100 for a in sublist]
    availability_const = model.constant(availability_list)

    # Initialize model constants
    min_shifts_constant = model.constant(min_shifts)
    max_shifts_constant = model.constant(max_shifts)
    shift_min_constant = model.constant(shift_min)
    shift_max_constant = model.constant(shift_max)
    max_consecutive_shifts_c = model.constant(max_consecutive_shifts)
    one_c = model.constant(1)

    # OBJECTIVES:
    # Objective: give employees preferred schedules (val = 2)
    obj = (assignments * availability_const).sum()

    # Objective: for infeasible solutions, focus on right number of shifts for employees
    target_shifts = model.constant((min_shifts + max_shifts) / 2)
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

    if not allow_isolated_days_off:
        negthree_c = model.constant(-3)
        zero_c = model.constant(0)
        # Adding many small constraints greatly improves feasibility
        for e in range(len(employees)):
            for s1 in range(len(shifts) - 2):
                s2, s3 = s1 + 1, s1 + 2
                model.add_constraint(
                    negthree_c * assignments[e, s2]
                    + assignments[e][s1] * assignments[e][s2]
                    + assignments[e][s1] * assignments[e][s3]
                    + assignments[e][s2] * assignments[e][s3]
                    <= zero_c
                )

    if requires_manager:
        for shift in range(len(shifts)):
            model.add_constraint(assignments[managers_c][:, shift].sum() >= one_c)

    # Don't exceed max_consecutive_shifts
    for e in range(num_employees):
        for s in range(num_shifts - max_consecutive_shifts + 1):
            s_window = s + max_consecutive_shifts + 1
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
    sampler: LeapHybridNLSampler,
    time_limit: int = 15,
    solution_printer: Callable | None = None,
) -> None:
    if not model.is_locked():
        model.lock()

    sampler = LeapHybridNLSampler()
    sampler.sample(model, time_limit=time_limit)
    if solution_printer is not None:
        solution_printer(assignments)
    else:
        print(model.state_size())


def pretty_print_solution(assignments: BinaryVariable):
    result = assignments.state()
    employees = list(availability.keys())
    shift_availability = list(availability.values())
    unicode_check = "*"
    unicode_heart = Fore.LIGHTGREEN_EX + "@" + Style.RESET_ALL
    unicode_heartbreak = Fore.LIGHTRED_EX + "/" + Style.RESET_ALL
    unicode_sos = Fore.RED + "E" + Style.RESET_ALL
    header = ["Employee", *shifts]
    solution_table = []

    print(f"{unicode_check} = shift assigned")
    print(f"{unicode_heart} = preferred shift assigned")
    print(f"{unicode_heartbreak} = preferred shift not assigned")
    print(f"{unicode_sos} = unavailable shift assigned")
    for i, employee in enumerate(employees):
        employee_shifts = [employee]
        solution_table.append(employee_shifts)
        for j in range(len(shifts)):
            match result[i, j], shift_availability[i][j]:
                case 0, 0 | 1:
                    employee_shifts.append("")
                case 0, 2:
                    employee_shifts.append(unicode_heartbreak)
                case 1, 1:
                    employee_shifts.append(unicode_check)
                case 1, 2:
                    employee_shifts.append(unicode_heart)
                case 1, 0:
                    employee_shifts.append(unicode_sos)
                case _:
                    raise Exception(
                        f"Case result={result[i,j]}, available={shift_availability[i][j]} not a valid case"
                    )

    print(tabulate(solution_table, headers=header, tablefmt="grid"))


def validate_schedule(
    assignments: BinaryVariable,
    availability: dict[str, list[int]],
    shifts: list[str],
    min_shifts: int,
    max_shifts: int,
    shift_min: int,
    shift_max: int,
    requires_manager: bool,
    allow_isolated_days_off: bool,
    max_consecutive_shifts: int,
) -> list[str]:
    result = assignments.state()
    employees = list(availability.keys())
    errors = []
    errors.extend(
        [
            *validate_availability(result, availability, employees, shifts),
            *validate_shifts_per_employee(result, employees, min_shifts, max_shifts),
            *validate_employees_per_shift(result, shifts, shift_min, shift_max),
            *validate_max_consecutive_shifts(result, employees, max_consecutive_shifts),
            *validate_trainee_shifts(result, employees),
        ]
    )
    if requires_manager:
        errors.extend(validate_requires_manager(result, employees))
    if not allow_isolated_days_off:
        errors.extend(validate_isolated_days_off(result, employees, shifts))
    return errors


def validate_availability(
    results: np.ndarray,
    availability: dict[str, list[int]],
    employees: list[str],
    shifts: list[str],
) -> list[str]:
    errors = []
    for e, employee in enumerate(employees):
        for s, shift in enumerate(shifts):
            if results[e, s] > availability[employee][s]:
                msg = (
                    f"Employee {employee} scheduled for shift {shift} but not available"
                )
                errors.append(msg)
    return errors


def validate_shifts_per_employee(
    results: np.ndarray, employees: list[str], min_shifts: int, max_shifts: int
) -> list[str]:
    errors = []
    for e, employee in enumerate(employees):
        num_shifts = results[e, :].sum()
        msg = None
        if num_shifts < min_shifts:
            msg = f"Employee {employee} scheduled for {num_shifts} but requires at least {min_shifts}"
        elif num_shifts > max_shifts:
            msg = f"Employee {employee} scheduled for {num_shifts} but requires at most {max_shifts}"
        if msg:
            errors.append(msg)
    return errors


def validate_employees_per_shift(
    results: np.ndarray, shifts: list[str], shift_min: int, shift_max: int
) -> list[str]:
    errors = []
    for s, shift in enumerate(shifts):
        num_employees = results[:, s].sum()
        msg = None
        if num_employees < shift_min:
            msg = f"Shift {shift} scheduled for {num_employees} employees but requires at least {shift_min}"
        elif num_employees > shift_max:
            msg = f"Shift {shift} scheduled for {num_employees} employees but requires at most {shift_max}"
        if msg:
            errors.append(msg)
    return errors


def validate_requires_manager(
    results: np.ndarray,
    employees: list[str],
) -> list[str]:
    errors = []
    employee_arr = np.asarray(
        [employees.index(e) for e in employees if e[-3:] == "Mgr"]
    )
    managers_per_shift = results[employee_arr].sum(axis=0)
    for shift, num_managers in enumerate(managers_per_shift):
        if num_managers == 0:
            msg = f"Shift {shift + 1} requires at least 1 manager but 0 scheduled"
            errors.append(msg)

    return errors


def validate_isolated_days_off(
    results: np.ndarray,
    employees: list[str],
    shifts: list[str],
) -> list[str]:
    errors = []
    isolated_pattern = np.array([1, 0, 1])
    for e, employee in enumerate(employees):
        shift_triples = [results[e, i : i + 3] for i in range(results.shape[1] - 2)]
        for s, shift_set in enumerate(shift_triples):
            if np.equal(shift_set, isolated_pattern).all():
                msg = f"Employee {employee} has an isolated day off on shift {shifts[s+1]}"
                errors.append(msg)

    return errors


def validate_max_consecutive_shifts(
    results: np.ndarray, employees: list[str], max_consecutive_shifts: int
) -> list[str]:
    errors = []
    for e, employee in enumerate(employees):
        for shifts in [
            results[e, i : i + max_consecutive_shifts]
            for i in range(results.shape[1] - max_consecutive_shifts)
        ]:
            if shifts.sum() > max_consecutive_shifts:
                msg = f"Employee {employee} scheduled for more than {max_consecutive_shifts} max consecutive shifts"
                errors.append(msg)
                break

    return errors


def validate_trainee_shifts(results: np.ndarray, employees: list[str]) -> list[str]:
    errors = []
    trainees = {employees.index(e): e for e in employees if e[-2:] == "Tr"}
    trainers = {
        employees.index(e): e for e in employees if e + "-Tr" in trainees.values()
    }
    for (trainee_i, trainee), (trainer_i, trainer) in zip(
        trainees.items(), trainers.items()
    ):
        same_shifts = np.less_equal(results[trainee_i], results[trainer_i])
        for i, s in enumerate(same_shifts):
            if not s:
                msg = f"Trainee {trainee} scheduled on shift {i+1} without trainer {trainer}"
                errors.append(msg)

    return errors


if __name__ == "__main__":
    model, assignments = build_nl(
        availability,
        shifts,
        min_shifts,
        max_shifts,
        shift_min,
        shift_max,
        requires_manager,
        allow_isolated_days_off,
        max_consecutive_shifts,
    )

    model.lock()

    time_limit = max(len(availability), len(shifts))

    sampler: LeapHybridNLSampler = LeapHybridNLSampler()
    sampler.sample(model)

    print(model.objective.state())

    pretty_print_solution(assignments)

    errors = validate_schedule(
        assignments,
        availability,
        shifts,
        min_shifts,
        max_shifts,
        shift_min,
        shift_max,
        requires_manager,
        allow_isolated_days_off,
        max_consecutive_shifts,
    )

    for e in errors:
        print(e)

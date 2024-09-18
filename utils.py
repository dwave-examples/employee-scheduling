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

import datetime
import random
import string
from collections import defaultdict
from dataclasses import dataclass, field

from app_configs import REQUESTED_SHIFT_ICON, UNAVAILABLE_ICON
import numpy as np
import pandas as pd
from dash import dash_table
from faker import Faker
from dwave.optimization.symbols import BinaryVariable

NOW = datetime.datetime.now()
SCHEDULE_LENGTH = 14
# Determine how many days away Sunday is then get two Sundays from that Sunday
START_DATE = NOW + datetime.timedelta(6 - NOW.weekday() + 14)
COL_IDS = [str(i+1) for i in range(SCHEDULE_LENGTH)] # The ids for each column
# The shift dates
SHIFTS = [
    (START_DATE + datetime.timedelta(i)).strftime("%e").strip()
    for i in range(SCHEDULE_LENGTH)
]
DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
WEEKEND_IDS = ["1", "7", "8", "14"]

@dataclass
class ModelParams:
    """Convenience class for defining and passing model parameters.

    Attributes:
        availability (dict[str, list[int]]): Employee availability for each shift,
            structured as follows:
            ```
            availability = {
                'Employee Name': [
                    0, # 0 if unavailable for shift at index i
                    1, # 1 if availabile for shift at index i
                    2, # 2 if shift at index i is preferred
                    ...
                ]
            }
            ```
        shifts (list[str]): List of shift labels.
        min_shifts (int): Min shifts per employee.
        max_shifts (int): Max shifts per employee.
        shift_min (int): Min employees per shift.
        shift_max (int): Max employees per shift.
        requires_manager (bool): Whether a manager is required on every shift.
        allow_isolated_days_off (bool): Whether isolated shifts off are allowed
            (pattern of on-off-on).
        max_consecutive_shifts (int): Max consecutive shifts for each employee.
        shift_labels (list[str]): Day/date labels for shifts.
    """
    availability: dict[str, list[int]]
    shifts: list[str]
    min_shifts: int
    max_shifts: int
    shift_min: int
    shift_max: int
    requires_manager: bool
    allow_isolated_days_off: bool
    max_consecutive_shifts: int
    shift_labels: list[str] = field(init=False)

    def __post_init__(self):
        self.shift_labels = [f"{DAYS[i%7]} {SHIFTS[i]}" for i in range(len(self.shifts))]


def get_random_string(length):
    """Generate a random string of a given length."""
    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for _ in range(length))

    return result_str


def get_random_names(num_employees):
    """Generate a list of names for the employees to be scheduled."""
    fake = Faker()
    names = []
    letters = string.ascii_uppercase

    for i in range(num_employees):
        n = fake.first_name()
        li = random.choice(letters)

        full_name = n + " " + li
        while full_name in names:
            n = fake.first_name()
            li = random.choice(letters)
            full_name = n + " " + li

        names.append(full_name)

    return names


def build_random_sched(num_employees, rand_seed=None):
    """Builds a random availability schedule for employees."""

    if rand_seed:
        np.random.seed(rand_seed)

    data = pd.DataFrame(
        np.random.choice([UNAVAILABLE_ICON, " ", REQUESTED_SHIFT_ICON], size=(num_employees + 1, len(COL_IDS)), p=[0.1, 0.8, 0.1]),
        columns=COL_IDS,
    )

    num_managers = 2

    employees = get_random_names(num_employees)

    for i in range(num_managers):
        employees[i] += "-Mgr"
    employees.append(employees[-1] + "-Tr")

    data.insert(0, "Employee", employees)

    data.replace({COL_IDS[0]: {UNAVAILABLE_ICON, " "}})
    data.replace({COL_IDS[-1]: {UNAVAILABLE_ICON, " "}})

    data.loc[data.Employee == employees[-1], data.columns[1:]] = " "

    return data


def build_schedule_from_sample(sample, employees):
    """Builds a schedule from the sample returned."""
    data = pd.DataFrame(columns=COL_IDS)
    data.insert(0, "Employee", employees)

    for key, val in sample.items():
        row, col = key.split("_")
        if val == 1.0:
            data.loc[data["Employee"] == row, col] = " "
        else:
            data.loc[data["Employee"] == row, col] = UNAVAILABLE_ICON

    return data


def build_schedule_from_state(state: np.ndarray, employees: list[str], shifts: list[str]):
    """Builds a schedule from the state of a BinaryVariable."""
    data = pd.DataFrame(columns=COL_IDS)
    data.insert(0, "Employee", employees)

    for e, employee in enumerate(employees):
        for s, shift in enumerate(shifts):
            if state[e, s] == 1.0:
                data.loc[data["Employee"] == employee, shift] = " "
            else:
                data.loc[data["Employee"] == employee, shift] = UNAVAILABLE_ICON

    return data


def get_cols():
    """Gets information for column headers, including months and days."""
    start_month = START_DATE.strftime("%B %Y") # Get month and year
    end_month = (START_DATE + datetime.timedelta(SCHEDULE_LENGTH-1)).strftime("%B %Y") # Get month and year
    month_display = [start_month, end_month]

    return (
        [{"id": "Employee", "name": ["", "", "Employee"]}]
        + [{"id": str(i+1), "name": [
            month_display[0 if i < 7 else 1], DAYS[i%7], c
        ]} for i, c in enumerate(SHIFTS)]
    )


def get_cell_styling(cols):
    """Sets conditional cell styling."""
    return [
            {
                "if": {"column_id": cols[1:]},
                "minWidth": "45px",
                "width": "45px",
                "maxWidth": "45px",
            },
        ]


def display_availability(df):
    """Builds the visual display of employee availability."""

    datatable = dash_table.DataTable(
        data=df.to_dict("records"),
        columns=get_cols(),
        cell_selectable=False,
        editable=False,
        style_cell={"textAlign": "center"},
        style_cell_conditional=get_cell_styling(df.columns),
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#f5f5f5",
            },
        ]
        + [
            {
                "if": {"column_id": weekend_id},
                "backgroundColor": "#E5E5E5",
            } for weekend_id in WEEKEND_IDS
        ]
        + [
            {
                "if": {
                    "filter_query": f'{{{col_id}}} = {UNAVAILABLE_ICON}',
                    "column_id": col_id,
                },
                "backgroundColor": "#FF7006", # orange
                "color": "white",
            }
            for col_id in COL_IDS
        ]
        + [
            {
                "if": {
                    "filter_query": f'{{{col_id}}} = {REQUESTED_SHIFT_ICON}',
                    "column_id": col_id,
                },
                "backgroundColor": "#008c82", # teal
                "color": "white",
            }
            for col_id in COL_IDS
        ],
        merge_duplicate_headers=True,
    )

    return datatable


def display_schedule(df, availability):
    """Builds the visual schedule for display."""

    df[df.iloc[:, 1:] == UNAVAILABLE_ICON] = "\r" # mark all unscheduled days with an invisible character
    for employee_name, employee_availability in availability.items():
        for i, col_id in enumerate(COL_IDS):
            if employee_availability[i] == 0: # not available
                df.loc[df["Employee"] == employee_name, col_id] = UNAVAILABLE_ICON
            elif employee_availability[i] == 2: # available
                df.loc[df["Employee"] == employee_name, col_id] += REQUESTED_SHIFT_ICON

    datatable = dash_table.DataTable(
        data=df.to_dict("records"),
        columns=get_cols(),
        cell_selectable=False,
        editable=False,
        style_cell={"textAlign": "center"},
        style_cell_conditional=get_cell_styling(df.columns),
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#f5f5f5",
            },
        ]
        + [
            {
                "if": {"column_id": weekend_id},
                "backgroundColor": "#E5E5E5",
            } for weekend_id in WEEKEND_IDS
        ]
        + [
            {
                "if": {
                    "filter_query": f'{{{col_id}}} contains " "',
                    "column_id": col_id,
                },
                "backgroundColor": "#2a7de1", # blue
                "color": "white",
            }
            for col_id in COL_IDS
        ]
        + [
            {
                "if": {
                    "filter_query": f'{{{col_id}}} contains "\r" && {{{col_id}}} contains {REQUESTED_SHIFT_ICON}',
                    "column_id": col_id,
                },
                "backgroundImage": "linear-gradient(-45deg, #c7003860 10%, transparent 10%, transparent 20%,\
                #c7003860 20%, #c7003860 30%, transparent 30%, transparent 40%, #c7003860 40%, #c7003860 50%,\
                transparent 50%, transparent 60%, #c7003860 60%, #c7003860 70%, transparent 70%, transparent 80%,\
                #c7003860 80%, #c7003860 90%, transparent 90%, #fff)", # light red
            }
            for col_id in COL_IDS
        ],
        merge_duplicate_headers=True,
    )

    return datatable


def availability_to_dict(availability_list):
    """Converts employee availability to a dictionary."""
    availability_dict = {}

    for row in availability_list:
        availability_dict[row["Employee"]] = [
            0 if row[col_id] == UNAVAILABLE_ICON else 2 if row[col_id] == REQUESTED_SHIFT_ICON else 1 for col_id in COL_IDS
        ]

    return availability_dict


def validate_nl_schedule(
    assignments: BinaryVariable,
    params: ModelParams,
    msgs: dict[str, tuple[str, str]],
) -> defaultdict[str, list[str]]:
    """Detect any errors in a solved NL scheduling model.

    Since NL models do not currently support constraint labels, this function
    is required to detect any constraint violations and format them for display
    in the user interface.

    Args:
        assignments (BinaryVariable): Assignments generated from sampling the
            NL model.
        params (ModelParams): Model parameters.
        msgs (dict[str, tuple[str, str]]): Error message template dictionary.
            Must be formatted like:
            ```
            msgs = {
                'error_type': ('Error message', 'message template with {replacement fields}'),
                ...
            }
            ```

    Raises:
        ValueError: Raised if the `msgs` dictionary doesn't contain the required keys.

    Returns:
        errors (defaultdict[str, list[str]]): Error descriptions and messages.
    """
    # Required keys to match existing error messages in employee_scheduling.py
    required_msg_keys = [
        "unavailable",
        "overtime",
        "insufficient",
        "understaffed",
        "overstaffed",
        "isolated",
        "manager_issue",
        "too_many_consecutive",
        "trainee_issue",
    ]
    for key in required_msg_keys:
        if key not in msgs:
            raise ValueError(f"`msgs` dictionary missing required key `{key}`")

    # Pull solution state as ndarray, employees as list
    result = assignments.state()
    employees = list(params.availability.keys())

    errors = defaultdict(list)

    _validate_availability(params, result, employees, errors, msgs)
    _validate_shifts_per_employee(params, result, employees, errors, msgs)
    _validate_employees_per_shift(params, result, errors, msgs)
    _validate_max_consecutive_shifts(params, result, employees, errors, msgs)
    _validate_trainee_shifts(params, result, employees, errors, msgs)
    if params.requires_manager:
        _validate_requires_manager(params, result, employees, errors, msgs)
    if not params.allow_isolated_days_off:
        _validate_isolated_days_off(params, result, employees, errors, msgs)

    return errors


def _validate_availability(
    params: ModelParams,
    results: np.ndarray,
    employees: list[str],
    errors: defaultdict[str, list[str]],
    msgs: dict[str, tuple[str, str]],
) -> defaultdict[str, list[str]]:
    """Validates employee availability for the solution and updates the `errors`
    dictionary with any errors found. Requires the `msgs` dict to have the
    key `'unavailable'`."""
    msg_key, msg_template = msgs["unavailable"]
    for e, employee in enumerate(employees):
        for s, day in enumerate(params.shift_labels):
            if results[e, s] > params.availability[employee][s]:
                errors[msg_key].append(
                    msg_template.format(employee=employee, day=day)
                )
    return errors


def _validate_shifts_per_employee(
    params: ModelParams,
    results: np.ndarray,
    employees: list[str],
    errors: defaultdict[str, list[str]],
    msgs: dict[str, tuple[str, str]],
) -> defaultdict[str, list[str]]:
    """Validates the number of shifts per employee for the solution and updates
    the `errors` dictionary with any errors found. Requires the `msgs` dict
    to have the keys `'insufficient'` and `'overtime'`."""
    insufficient_key, insufficient_template = msgs["insufficient"]
    overtime_key, overtime_template = msgs["overtime"]
    for e, employee in enumerate(employees):
        num_shifts = results[e, :].sum()
        if num_shifts < params.min_shifts:
            errors[insufficient_key].append(
                insufficient_template.format(employee=employee)
            )
        elif num_shifts > params.max_shifts:
            errors[overtime_key].append(overtime_template.format(employee=employee))
    return errors


def _validate_employees_per_shift(
    params: ModelParams,
    results: np.ndarray,
    errors: defaultdict[str, list[str]],
    msgs: dict[str, tuple[str, str]],
) -> defaultdict[str, list[str]]:
    """Validates the number of employees per shift for the solution and updates
    the `errors` dictionary with any errors found. Requires the `msgs` dict
    to have the keys `'understaffed'` and `'overstaffed'`."""
    for s, day in enumerate(params.shift_labels):
        understaffed_key, understaffed_template = msgs["understaffed"]
        overstaffed_key, overstaffed_template = msgs["overstaffed"]
        num_employees = results[:, s].sum()
        if num_employees < params.shift_min:
            errors[understaffed_key].append(understaffed_template.format(day=day))
        elif num_employees > params.shift_max:
            errors[overstaffed_key].append(overstaffed_template.format(day=day))
    return errors


def _validate_requires_manager(
    params: ModelParams,
    results: np.ndarray,
    employees: list[str],
    errors: defaultdict[str, list[str]],
    msgs: dict[str, tuple[str, str]],
) -> defaultdict[str, list[str]]:
    """Validates the number of managers per shift for the solution and updates
    the `errors` dictionary with any errors found. Requires the `msgs` dict
    to have the key `'manager_issue'`."""
    key, template = msgs["manager_issue"]
    employee_arr = np.asarray(
        [employees.index(e) for e in employees if e[-3:] == "Mgr"]
    )
    managers_per_shift = results[employee_arr].sum(axis=0)
    for shift, num_managers in enumerate(managers_per_shift):
        if num_managers == 0:
            errors[key].append(template.format(day=params.shift_labels[shift]))
    return errors


def _validate_isolated_days_off(
    params: ModelParams,
    results: np.ndarray,
    employees: list[str],
    errors: defaultdict[str, list[str]],
    msgs: dict[str, tuple[str, str]],
) -> defaultdict[str, list[str]]:
    """Validates the number of managers per shift for the solution and updates
    the `errors` dictionary with any errors found. Requires the `msgs` dict
    to have the key `'isolated'`."""
    key, template = msgs["isolated"]
    isolated_pattern = np.array([1, 0, 1])
    for e, employee in enumerate(employees):
        shift_triples = [results[e, i : i + 3] for i in range(results.shape[1] - 2)]
        for s, shift_set in enumerate(shift_triples):
            if np.equal(shift_set, isolated_pattern).all():
                day = params.shift_labels[s + 1]
                errors[key].append(template.format(employee=employee, day=day))
    return errors


def _validate_max_consecutive_shifts(
    params: ModelParams,
    results: np.ndarray,
    employees: list[str],
    errors: defaultdict[str, list[str]],
    msgs: dict[str, tuple[str, str]],
) -> defaultdict[str, list[str]]:
    """Validates the max number of consecutive shifts for the solution and updates
    the `errors` dictionary with any errors found. Requires the `msgs` dict
    to have the key `'too_many_consecutive'`."""
    key, template = msgs["too_many_consecutive"]
    for e, employee in enumerate(employees):
        for shift, shift_arr in enumerate(
            [
                results[e, i : i + params.max_consecutive_shifts]
                for i in range(results.shape[1] - params.max_consecutive_shifts)
            ]
        ):
            if shift_arr.sum() > params.max_consecutive_shifts:
                errors[key].append(
                    template.format(employee=employee, day=params.shift_labels[shift])
                )
                break
    return errors


def _validate_trainee_shifts(
    params: ModelParams,
    results: np.ndarray,
    employees: list[str],
    errors: defaultdict[str, list[str]],
    msgs: dict[str, tuple[str, str]],
) -> defaultdict[str, list[str]]:
    """Validates that trainees are on-shift with their manager for the solution
    and updates the `errors` dictionary with any errors found. Requires the
    `msgs` dict to have the key `'trainee_issue'`."""
    key, template = msgs["trainee_issue"]
    trainees = {employees.index(e): e for e in employees if e[-2:] == "Tr"}
    trainers = {
        employees.index(e): e for e in employees if e + "-Tr" in trainees.values()
    }
    for (trainee_i), (trainer_i) in zip(trainees.keys(), trainers.keys()):
        same_shifts = np.less_equal(results[trainee_i], results[trainer_i])
        for i, s in enumerate(same_shifts):
            if not s:
                errors[key].append(template.format(day=params.shift_labels[i]))
    return errors

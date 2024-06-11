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

from app_configs import REQUESTED_SHIFT_ICON, UNAVAILABLE_ICON
import numpy as np
import pandas as pd
from dash import dash_table
from faker import Faker

NOW = datetime.datetime.now()
SCHEDULE_LENGTH = 14
# Determine how many days away Sunday is then get two Sundays from that Sunday
START_DATE = NOW + datetime.timedelta(6 - NOW.weekday() + 14)
COL_IDS = [str(i+1) for i in range(SCHEDULE_LENGTH)] # The ids for each column
# The shift dates
SHIFTS = [
    (START_DATE + datetime.timedelta(i)).strftime("%-d")
    for i in range(SCHEDULE_LENGTH)
]
DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
WEEKEND_IDS = ["1", "7", "8", "14"]


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

    data[COL_IDS[0]].replace(UNAVAILABLE_ICON, " ", inplace=True)
    data[COL_IDS[-1]].replace(UNAVAILABLE_ICON, " ", inplace=True)

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

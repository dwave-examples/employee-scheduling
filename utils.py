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
import calendar
import random
import string

import numpy as np
import pandas as pd
from dash import dash_table
from faker import Faker


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


def build_random_sched(num_employees, shifts, rand_seed=None):
    """Builds a random availability schedule for employees."""

    if rand_seed:
        np.random.seed(rand_seed)

    data = pd.DataFrame(
        np.random.choice(["X", " ", "P"], size=(num_employees + 1, len(shifts)), p=[0.1, 0.8, 0.1]),
        columns=shifts,
    )

    num_managers = 2

    employees = get_random_names(num_employees)

    for i in range(num_managers):
        employees[i] += "-Mgr"
    employees.append(employees[-1] + "-Tr")

    data.insert(0, "Employee", employees)

    data[shifts[0]].replace("X", " ", inplace=True)
    data[shifts[-1]].replace("X", " ", inplace=True)

    data.loc[data.Employee == employees[-1], data.columns[1:]] = " "

    return data


def build_schedule_from_sample(sample, shifts, employees):
    """Builds a schedule from the sample returned."""
    data = pd.DataFrame(columns=shifts)
    data.insert(0, "Employee", employees)

    for key, val in sample.items():
        row, col = key.split("_")
        if val == 1.0:
            data.loc[data["Employee"] == row, col] = " "
        else:
            data.loc[data["Employee"] == row, col] = "X"

    return data


def display_availability(df, month, year):
    """Builds the visual display of employee availability."""
    shifts = list(df.columns)
    shifts.remove("Employee")
    cols = (
        [{"id": "Employee", "name": [" ", "Employee"]}]
        + [{"id": c, "name": [f"{calendar.month_name[month]} {year}", c]} for c in shifts]
        + [{"id": "final-col", "name": [" "]}]
    )
    df.loc[len(df)] = (
        [" ", "P", "Preferred shifts"]
        + [" "] * 4
        + ["X", "Unavailable shifts"]
        + [" "] * (len(shifts) - 8)
    )

    datatable = dash_table.DataTable(
        data=df.to_dict("records"),
        columns=cols,
        cell_selectable=False,
        editable=False,
        style_cell={
            "textAlign": "center",
            "font-family": "verdana",
        },
        style_cell_conditional=[
            {
                "if": {"column_id": df.columns[1:]},
                "minWidth": "30px",
                "width": "30px",
                "maxWidth": "30px",
                "textAlign": "center",
            },
        ],
        style_data={"color": "black", "backgroundColor": "white"},
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#EEEEEE",
            },
            {"if": {"row_index": len(df) - 1}, "backgroundColor": "#DDDDDD", "border-left": "none", "border-right": "none"},
            {
                "if": {"column_id": "Employee"},
                "fontWeight": "bold",
                "backgroundColor": "#DDDDDD",
                "minWidth": "160px",
                "width": "220px",
            },
            {"if": {"column_id": "final-col"}, "backgroundColor": "#DDDDDD", "border-top": "none", "border-bottom": "none"},
        ]
        + [
            {
                "if": {
                    "filter_query": '{{{col}}} contains "X"'.format(col=col),
                    "column_id": col,
                },
                "backgroundColor": "#FF7006",
                "color": "white",
            }
            for col in df.columns[1:]
        ]
        + [
            {
                "if": {
                    "filter_query": '{{{col}}} = "P"'.format(col=col),
                    "column_id": col,
                },
                "backgroundColor": "#008c82",
                "color": "white",
            }
            for col in df.columns[1:]
        ]
        + [],
        style_header={
            "backgroundColor": "#DDDDDD",
            "color": "black",
            "fontWeight": "bold",
        },
        merge_duplicate_headers=True,
    )

    return datatable


def display_schedule(df, availability, month, year):
    """Builds the visual schedule for display."""
    prefs = []

    # drop the last row containing the legend
    df.drop(df.tail(1).index, inplace=True)
    df[df.iloc[:, 1:] == "X"] = "\r"
    for e, a in availability.items():
        shifts = df.columns[1:]
        for i in range(len(shifts)):
            if a[i] == 0:
                df.loc[df["Employee"] == e, shifts[i]] = "X"
            elif a[i] == 2:
                df.loc[df["Employee"] == e, shifts[i]] += "P"

                prefs.append((e, shifts[i]))

    shifts = list(df.columns)
    shifts.remove("Employee")
    cols = (
        [{"id": "Employee", "name": [" ", "Employee"]}]
        + [{"id": c, "name": [f"{calendar.month_name[month]} {year}", c]} for c in shifts]
        + [{"id": "final-col", "name": [" "]}]
    )
    df.loc[len(df)] = (
        [" ", "P", "Scheduled preferred shifts"]
        + [" "] * 7
        + ["P", "Unscheduled preferred shifts"]
        + [" "] * 7
        + ["X", "Unavailable shifts"]
        + [" "] * (len(shifts) - 20)
    )

    datatable = dash_table.DataTable(
        data=df.to_dict("records"),
        columns=cols,
        cell_selectable=False,
        editable=False,
        style_cell={"textAlign": "center", "font-family": "verdana"},
        style_cell_conditional=[
            {
                "if": {"column_id": df.columns[1:]},
                "minWidth": "30px",
                "width": "30px",
                "maxWidth": "30px",
                "textAlign": "center",
            },
        ],
        style_data={"color": "black", "backgroundColor": "white"},
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#EEEEEE",
            },
            {
                "if": {"column_id": "Employee"},
                "fontWeight": "bold",
                "backgroundColor": "#DDDDDD",
                "minWidth": "160px",
                "width": "220px",
            },
            {"if": {"column_id": "final-col"}, "backgroundColor": "#DDDDDD", "border-top": "none", "border-bottom": "none"},
        ]
        + [
            {
                "if": {
                    "filter_query": '{{{col}}} contains " "'.format(col=col),
                    "column_id": col,
                },
                "backgroundColor": "#2a7de1",
                "color": "white",
            }
            for col in df.columns[1:]
        ]
        + [
            {
                "if": {
                    "filter_query": '{{{col}}} contains "\r" && {{{col}}} contains "P"'.format(
                        col=col
                    ),
                    "column_id": col,
                },
                "backgroundColor": "#c7003888",
                "color": "white",
            }
            for col in df.columns[1:]
        ]
        + [
            {"if": {"row_index": len(df) - 1}, "backgroundColor": "#DDDDDD", "border-left": "none", "border-right": "none"},
            {
                "if": {"column_id": "1", "row_index": len(df) - 1},
                "backgroundColor": "#2a7de1",
                "color": "white",
            },
            {
                "if": {"column_id": "2", "row_index": len(df) - 1},
                "color": "black",
            },
            {
                "if": {"column_id": "10", "row_index": len(df) - 1},
                "backgroundColor": "#c7003888",
                "color": "white",
            },
            {
                "if": {"column_id": "11", "row_index": len(df) - 1},
                "color": "black",
            },
            {
                "if": {"column_id": "19", "row_index": len(df) - 1},
                "backgroundColor": "white",
                "color": "black",
            },
            {
                "if": {"column_id": "20", "row_index": len(df) - 1},
                "color": "black",
            },
        ],
        style_header={
            "backgroundColor": "#DDDDDD",
            "color": "black",
            "fontWeight": "bold",
        },
        merge_duplicate_headers=True,
    )

    return datatable


def availability_to_dict(input, shifts):
    """Converts employee availability to a dictionary."""
    availability = {}

    for i in input:
        availability[i["Employee"]] = [
            0 if i[j] == "X" else 2 if i[j] == "P" else 1 for j in shifts
        ]

    return availability

# Copyright 2024 D-Wave
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

import math
from typing import Any

import dash
from dash import Input, MATCH, Output, State, ctx, no_update
from dash.exceptions import PreventUpdate

import employee_scheduling as employee_scheduling
import utils as utils
from demo_configs import (LARGE_SCENARIO, MEDIUM_SCENARIO, MIN_MAX_EMPLOYEES, NUM_FULL_TIME,
                         SMALL_SCENARIO)
from demo_interface import errors_list
import pandas as pd


@dash.callback(
    Output({"type": "to-collapse-class", "index": MATCH}, "className", allow_duplicate=True),
    inputs=[
        Input({"type": "collapse-trigger", "index": MATCH}, "n_clicks"),
        State({"type": "to-collapse-class", "index": MATCH}, "className"),
    ],
    prevent_initial_call=True,
)
def toggle_left_column(collapse_trigger: int, to_collapse_class: str) -> str:
    """Toggles a 'collapsed' class that hides and shows some aspect of the UI.

    Args:
        collapse_trigger (int): The (total) number of times a collapse button has been clicked.
        to_collapse_class (str): Current class name of the thing to collapse, 'collapsed' if not visible, empty string if visible

    Returns:
        str: The new class name of the thing to collapse.
    """
    classes = to_collapse_class.split(" ") if to_collapse_class else []
    if "collapsed" in classes:
        classes.remove("collapsed")
        return " ".join(classes)
    return to_collapse_class + " collapsed" if to_collapse_class else "collapsed"


@dash.callback(
    Output("num-employees-select", "value"),
    Output("num-full-time-select", "value"),
    Output("consecutive-shifts-select", "value"),
    Output("shifts-per-employee-select", "value"),
    Output("employees-per-shift-select", "value"),
    Output("seed-select", "value"),
    Output("num-employees-select", "disabled"),
    Output("num-full-time-select", "disabled"),
    Output("consecutive-shifts-select", "disabled"),
    Output("shifts-per-employee-select", "disabled"),
    Output("employees-per-shift-select", "disabled"),
    inputs=[
        Input("example-scenario-select", "value"),
        State("custom-saved-data", "data"),
    ],
    prevent_initial_call=True,
)
def set_scenario(
    scenario: int,
    custom_saved_data: dict,
) -> tuple[int, int, list[int], list[int], int, bool, bool, bool, bool]:
    """Sets the correct scenario, reverting to the saved custom setting if chosen."""
    if scenario == 1:
        return *tuple(SMALL_SCENARIO.values()), True, True, True, True, True
    elif scenario == 2:
        return *tuple(MEDIUM_SCENARIO.values()), True, True, True, True, True
    elif scenario == 3:
        return *tuple(LARGE_SCENARIO.values()), True, True, True, True, True

    # else return custom stored selections
    return (
        *custom_saved_data.values(),
        False, False, False, False, False
    )


@dash.callback(
    Output("employees-per-shift-select", "max"),
    Output("employees-per-shift-select", "marks"),
    # required to refresh tooltip
    Output("employees-per-shift-select", "tooltip"),
    Output("num-full-time-select", "max"),
    Output("num-full-time-select", "marks"),
    inputs=[
        Input("num-employees-select", "value"),
        # passthrough input; required to refresh tooltip
        State("employees-per-shift-select", "tooltip"),
    ],
)
def update_employee_settings(num_employees: int, tooltip: dict[str, Any]) -> tuple[int, dict, dict]:
    """Update the employees-per-shift slider max if num-employees is changed."""
    per_shift_marks = {
        MIN_MAX_EMPLOYEES["min"]: str(MIN_MAX_EMPLOYEES["min"]),
        num_employees: str(num_employees),
    }
    new_full_time_max = math.floor(num_employees/2)
    full_time_marks = {
        NUM_FULL_TIME["min"]: str(NUM_FULL_TIME["min"]),
        new_full_time_max: str(new_full_time_max),
    }
    return num_employees, per_shift_marks, tooltip, new_full_time_max, full_time_marks


@dash.callback(
    Output("custom-saved-data", "data"),
    inputs=[
        Input("num-employees-select", "value"),
        Input("num-full-time-select", "value"),
        Input("consecutive-shifts-select", "value"),
        Input("shifts-per-employee-select", "value"),
        Input("employees-per-shift-select", "value"),
        Input("seed-select", "value"),
        State("example-scenario-select", "value"),
        State("custom-saved-data", "data"),
    ],
)
def custom_saved_data(
    num_employees: int,
    num_full_time: int,
    consecutive_shifts: int,
    shifts_per_employees: list[int],
    employees_per_shift: list[int],
    random_seed: int,
    scenario: int,
    custom_saved_data: dict,
) -> int:
    """Save custom data if changed under custom scenario."""
    if not ctx.triggered_id:
        return {
            "num-employees-select": num_employees,
            "num-full-time-select": num_full_time,
            "consecutive-shifts-select": consecutive_shifts,
            "shifts-per-employee-select": shifts_per_employees,
            "employees-per-shift-select": employees_per_shift,
            "seed-select": random_seed,
        }

    if scenario == 0:
        custom_saved_data.update({ctx.triggered_id: ctx.triggered[0]["value"]})
        return custom_saved_data

    raise PreventUpdate


@dash.callback(
    Output("availability-content", "children"),
    Output("schedule-content", "children", allow_duplicate=True),
    Output("schedule-tab", "disabled", allow_duplicate=True),
    Output("tabs", "value"),
    Output({"type": "to-collapse-class", "index": 1}, "style", allow_duplicate=True),
    inputs=[
        Input("num-employees-select", "value"),
        Input("num-full-time-select", "value"),
        Input("seed-select", "value"),
    ],
    prevent_initial_call='initial_duplicate',
)
def disp_initial_sched(
    num_employees: int, num_full_time: int, rand_seed: int
) -> tuple[pd.DataFrame, pd.DataFrame, bool, str, dict]:
    """Display initial availability schedule.

    Display initial schedule in, and switch to, the availability
    tab if number of employees or seed is changed.
    """
    df = utils.build_random_sched(num_employees, num_full_time, rand_seed)

    init_availability_table = utils.display_availability(df)
    return (
        init_availability_table,
        init_availability_table,
        True,  # disable the shedule tab when changing parameters
        "input-tab",  # jump back to the availability tab
        {"display": "none"},
    )


@dash.callback(
    Output({"type": "to-collapse-class", "index": 1}, "style"),
    Output({"type": "to-collapse-class", "index": 1}, "className"),
    inputs=[
        Input("run-button", "n_clicks"),
        State({"type": "to-collapse-class", "index": 1}, "className"),
    ],
    prevent_initial_call=True,
)
def update_error_sidebar(run_click: int, prev_classes) -> tuple[dict, str]:
    """Hides and collapses error sidebar on button click."""
    if run_click == 0 or ctx.triggered_id != "run-button":
        raise PreventUpdate

    classes = prev_classes.split(" ") if prev_classes else []

    if "collapsed" in classes:
        return no_update, no_update

    return (
        {"display": "none"},
        prev_classes + " collapsed"
    )


@dash.callback(
    Output("schedule-content", "children", allow_duplicate=True),
    Output("schedule-tab", "disabled", allow_duplicate=True),
    Output({"type": "to-collapse-class", "index": 1}, "style", allow_duplicate=True),
    Output("errors", "children"),
    background=True,
    inputs=[
        Input("run-button", "n_clicks"),
        State("shifts-per-employee-select", "value"),
        State("employees-per-shift-select", "value"),
        State("checklist-input", "value"),
        State("consecutive-shifts-select", "value"),
        State("num-full-time-select", "value"),
        State("availability-content", "children"),
    ],
    running=[
        # show cancel button and hide run button, and disable and animate results tab
        (Output("cancel-button", "className"), "", "display-none"),  # Show/hide cancel button.
        (Output("run-button", "className"), "display-none", ""),  # Hides run button while running.
        # switch to schedule tab while running
        (Output("schedule-tab", "disabled"), False, False),
        (Output("tabs", "value"), "schedule-tab", "schedule-tab"),
        (Output("control-card", "disabled"), False, False),
    ],
    cancel=[Input("cancel-button", "n_clicks")],
    prevent_initial_call=True,
)
def run_optimization(
    run_click: int,
    shifts_per_employee: list[int],
    employees_per_shift: list[int],
    checklist: list[int],
    consecutive_shifts: int,
    num_full_time: int,
    sched_df: pd.DataFrame,
) -> tuple[pd.DataFrame, bool, dict, list]:
    """Runs the optimization and updates UI accordingly.

    This is the main function which is called when the ``Run Optimization`` button is clicked.
    This function takes in all form values and runs the optimization, updates the run/cancel
    buttons, deactivates (and reactivates) the results tab, and updates all relevant HTML
    components.

    Args:
        run_click: The (total) number of times the run button has been clicked.
        shifts_per_employee: TODO
        employees_per_shift: TODO
        checklist: TODO
        consecutive_shifts: TODO
        sched_df: TODO

    Returns:
        A tuple containing all outputs to be used when updating the HTML
        template (in ``demo_interface.py``). These are:

            TODO
    """
    if run_click == 0 or ctx.triggered_id != "run-button":
        raise PreventUpdate

    shifts = list(sched_df["props"]["data"][0].keys())
    shifts.remove("Employee")

    availability = utils.availability_to_dict(sched_df["props"]["data"])
    employees = list(availability.keys())

    isolated_days_allowed = True if 0 in checklist else False
    manager_required = True if 1 in checklist else False

    cqm = employee_scheduling.build_cqm(
        availability,
        shifts,
        *shifts_per_employee,
        *employees_per_shift,
        manager_required,
        isolated_days_allowed,
        consecutive_shifts + 1,
        num_full_time,
    )

    feasible_sampleset, errors = employee_scheduling.run_cqm(cqm)
    sample = feasible_sampleset.first.sample

    sched = utils.build_schedule_from_sample(sample, employees)

    return (
        utils.display_schedule(sched, availability),
        False,
        {"display": "flex"} if errors else {"display": "none"},
        errors_list(errors) if errors else no_update,
    )

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

import dash
import pandas as pd
from dash import ALL, MATCH, Input, Output, State, ctx
from dash.exceptions import PreventUpdate

import src.employee_scheduling as employee_scheduling
import src.utils as utils
from demo_configs import (
    LARGE_SCENARIO,
    MEDIUM_SCENARIO,
    NUM_FULL_TIME,
    REQUESTED_SHIFT_ICON,
    SMALL_SCENARIO,
    UNAVAILABLE_ICON,
)
from demo_interface import errors_list, generate_forecast_table


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
    Output("num-full-time-select", "value", allow_duplicate=True),
    Output("consecutive-shifts-select", "value"),
    Output("shifts-per-employee-select", "value"),
    Output("num-employees-select", "disabled"),
    Output("num-full-time-select", "disabled"),
    Output("consecutive-shifts-select", "disabled"),
    Output("shifts-per-employee-select", "disabled"),
    inputs=[
        Input("example-scenario-select", "value"),
        State("custom-saved-data", "data"),
    ],
    prevent_initial_call=True,
)
def set_scenario(
    scenario: int,
    custom_saved_data: dict,
) -> tuple[int, int, int, list[int], bool, bool, bool, bool]:
    """Sets the correct scenario, reverting to the saved custom setting if chosen.

    Args:
        scenario: The scenario preset that is selected.
        custom_saved_data: The saved custom scenario data to update.

    Returns:
        num-employees-select: The number of employees.
        num-full-time-select: The number of full-time employees.
        consecutive-shifts-select: The max consecutive shifts to schedule for a part-time employee.
        shifts-per-employee-select: The min/max shifts to schedule for each part-time employee.
        num-employees-select-disabled: Whether to disable the number of employees setting.
        num-full-time-select-disabled: Whether to disable the full-time employees setting.
        consecutive-shifts-select-disabled: Whether to disable the max consecutive shifts setting.
        shifts-per-employee-select-disabled: Whether to disable the min/max shifts setting.
    """
    if scenario == 0:
        # return custom stored selections
        return *custom_saved_data.values(), False, False, False, False

    scenarios = [SMALL_SCENARIO, MEDIUM_SCENARIO, LARGE_SCENARIO]
    return *tuple(scenarios[scenario - 1].values()), True, True, True, True


@dash.callback(
    Output("custom-saved-data", "data"),
    inputs=[
        Input("num-employees-select", "value"),
        Input("num-full-time-select", "value"),
        Input("consecutive-shifts-select", "value"),
        Input("shifts-per-employee-select", "value"),
        State("example-scenario-select", "value"),
        State("custom-saved-data", "data"),
    ],
    prevent_initial_call=True,
)
def custom_saved_data(
    num_employees: int,
    num_full_time: int,
    consecutive_shifts: int,
    shifts_per_employees: list[int],
    scenario: int,
    custom_saved_data: dict,
) -> dict:
    """Save custom data if changed whilte custom scenario is selected.

    Args:
        num_employees: The number of employees.
        num_full_time: The number of full-time employees.
        consecutive_shifts: The max consecutive shifts a part-time employee should be scheduled for.
        shifts_per_employees: The min and max shifts each part-time employee should be scheduled for.
        scenario: The scenario preset that is selected.
        custom_saved_data: The saved custom scenario data to update.

    Returns:
        custom-saved-data: The saved custom scenario data to update.
    """
    if scenario == 0:
        custom_saved_data.update({ctx.triggered_id: ctx.triggered[0]["value"]})
        return custom_saved_data

    raise PreventUpdate


@dash.callback(
    Output("availability-content", "children"),
    Output("schedule-content", "children"),
    Output("schedule-tab", "disabled"),
    Output("tabs", "value"),
    Output({"type": "to-collapse-class", "index": 1}, "style"),
    Output({"type": "forecast", "index": ALL}, "value"),
    Output({"type": "forecast", "index": ALL}, "placeholder"),
    Output({"type": "forecast", "index": ALL}, "max"),
    Output("num-full-time-select", "max"),
    Output("num-full-time-select", "marks"),
    Output("num-full-time-select", "value"),
    inputs=[
        Input("num-employees-select", "value"),
        Input("num-full-time-select", "value"),
    ],
)
def display_initial_schedule(
    num_employees: int, num_full_time: int
) -> tuple[pd.DataFrame, pd.DataFrame, bool, str, dict, list[dict]]:
    """Display initial availability schedule.

    Display initial schedule in, and switch to, the availability
    tab if number of employees has changed.

    Args:
        num_employees: The number of employees.
        num_full_time: The number of full-time employees.

    Returns:
        availability-content: The availability tab content.
        schedule-content: The schedule tab content.
        schedule-tab-disabled: Whether the schedule tab should be disabled.
        tabs-value: The tab that should be selected.
        to-collapse-class-style: The style for the errors tab.
        forecast: The forecasted employees per shift requirements value.
        forecast: The forecasted employees per shift requirements placeholder.
        forecast: The forecasted employees per shift requirements max.
        num-full-time-select-max: The max to set the full-time select to.
        num-full-time-select-marks: The marks to set for the full-time select.
        num-full-time-select-value: The value to set for the full-time select.
    """
    new_full_time_max = math.floor(num_employees * 3 / 4)
    full_time_marks = {
        NUM_FULL_TIME["min"]: str(NUM_FULL_TIME["min"]),
        new_full_time_max: str(new_full_time_max),
    }
    num_full_time = min(num_full_time, new_full_time_max)

    df = utils.build_random_sched(num_employees, num_full_time)

    init_availability_table = utils.display_availability(df)

    # Prepare forecast defaults
    df_to_count = df.iloc[:num_full_time, :]
    count = df_to_count.applymap(lambda cell: cell.count(REQUESTED_SHIFT_ICON)).sum()[1:].to_dict()
    num_part_time = num_employees - num_full_time
    count = [value + math.ceil(num_part_time / 2) for value in count.values()]

    return (
        init_availability_table,
        init_availability_table,
        True,  # disable the shedule tab when changing parameters
        "input-tab",  # jump back to the availability tab
        {"display": "none"},
        count,
        count,
        [num_employees]*len(count),
        new_full_time_max,
        full_time_marks,
        num_full_time
    )


@dash.callback(
    Output({"type": "to-collapse-class", "index": 1}, "className"),
    Output("scheduled-forecast-output", "children"),
    inputs=[
        Input("run-button", "n_clicks"),
        State({"type": "to-collapse-class", "index": 1}, "className"),
    ],
    prevent_initial_call=True,
)
def update_ui_on_run(run_click: int, prev_classes: str) -> tuple[str, list]:
    """Hides and collapses error sidebar on button click.

    Args:
        run_click: The number of times the run button was clicked.
        prev_classes: A string containing all the previous classes of the error sidebar.

    Returns:
        to-collapse-class-className: The class names for the errors sidebar.
        scheduled-forecast-output: The forecasted and scheduled difference per shift.
    """
    classes = prev_classes.split(" ") if prev_classes else []

    if "collapsed" in classes:
        return dash.no_update, []

    return prev_classes + " collapsed", []


@dash.callback(
    Output("schedule-content", "children", allow_duplicate=True),
    Output({"type": "to-collapse-class", "index": 1}, "style", allow_duplicate=True),
    Output("errors", "children"),
    Output("scheduled-forecast-output", "children", allow_duplicate=True),
    background=True,
    inputs=[
        Input("run-button", "n_clicks"),
        State("shifts-per-employee-select", "value"),
        State("checklist-input", "value"),
        State("consecutive-shifts-select", "value"),
        State("num-full-time-select", "value"),
        State({"type": "forecast", "index": ALL}, "value"),
        State({"type": "forecast", "index": ALL}, "placeholder"),
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
    checklist: list[int],
    consecutive_shifts: int,
    num_full_time: int,
    forecast: list[int],
    forecast_placeholder: list[int],
    sched_df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict, list, list]:
    """Runs the optimization and updates UI accordingly.

    This is the main function which is called when the ``Run Optimization`` button is clicked.
    This function takes in all form values and runs the optimization, updates the run/cancel
    buttons, deactivates (and reactivates) the results tab, and updates all relevant HTML
    components.

    Args:
        run_click: The (total) number of times the run button has been clicked.
        shifts_per_employee: The min and max shifts each part-time employee should be scheduled for.
        checklist: Whether the checkbox ``Allow isolated days off`` is checked.
        consecutive_shifts: The max consecutive shifts a part-time employee should be scheduled for.
        num_full_time: The number of full-time employees.
        forecast: The forecasted employees per shift requirements.
        sched_df: The schedule dataframe.

    Returns:
        A tuple containing all outputs to be used when updating the HTML
        template (in ``demo_interface.py``). These are:

            schedule-content: The completed schedule.
            to-collapse-class-style: Whether to show the errors sidebar or not.
            errors: The errors to include in the sidebar.
            scheduled-forecast-output: The forecasted and scheduled difference per shift.
    """
    if run_click == 0 or ctx.triggered_id != "run-button":
        raise PreventUpdate

    shifts = list(sched_df["props"]["data"][0].keys())
    shifts.remove("Employee")

    availability = utils.availability_to_dict(sched_df["props"]["data"])
    employees = list(availability.keys())

    isolated_days_allowed = True if 0 in checklist else False

    forecast = [
        val if isinstance(val, int)
        else forecast_placeholder[i]
        for i, val in enumerate(forecast)
    ]

    cqm = employee_scheduling.build_cqm(
        availability,
        shifts,
        *shifts_per_employee,
        forecast,
        isolated_days_allowed,
        consecutive_shifts + 1,
        num_full_time,
    )

    feasible_sampleset, errors = employee_scheduling.run_cqm(cqm)
    sample = feasible_sampleset.first.sample

    sched = utils.build_schedule_from_sample(sample, employees)
    scheduled_count = sched.applymap(lambda cell: UNAVAILABLE_ICON not in cell).sum()[1:].to_dict()

    return (
        utils.display_schedule(sched, availability),
        {"display": "flex"} if errors else {"display": "none"},
        errors_list(errors) if errors else dash.no_update,
        generate_forecast_table(forecast, scheduled_count),
    )

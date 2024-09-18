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
from __future__ import annotations

import multiprocess
from typing import TYPE_CHECKING, Any

import diskcache
from dash import Dash, DiskcacheManager, Input, MATCH, Output, State, ctx, no_update
from dash.exceptions import PreventUpdate

import employee_scheduling
import utils
from app_configs import (
    APP_TITLE,
    DEBUG,
    LARGE_SCENARIO,
    MEDIUM_SCENARIO,
    MIN_MAX_EMPLOYEES,
    SMALL_SCENARIO,
)
from app_html import errors_list, set_html

if TYPE_CHECKING:
    from pandas import DataFrame

cache = diskcache.Cache("./cache")
background_callback_manager = DiskcacheManager(cache)

# Fix for Dash background callbacks crashing on macOS 10.13+ (https://bugs.python.org/issue33725)
# See https://github.com/dwave-examples/flow-shop-scheduling/pull/4 for more details.
if multiprocess.get_start_method(allow_none=True) is None:
    multiprocess.set_start_method("spawn")

app = Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    prevent_initial_callbacks="initial_duplicate",
    background_callback_manager=background_callback_manager,
)
app.title = APP_TITLE


@app.callback(
    Output(
        {"type": "to-collapse-class", "index": MATCH}, "className", allow_duplicate=True
    ),
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


@app.callback(
    Output("num-employees-select", "value"),
    Output("consecutive-shifts-select", "value"),
    Output("shifts-per-employee-select", "value"),
    Output("employees-per-shift-select", "value"),
    Output("seed-select", "value"),
    Output("num-employees-select", "disabled"),
    Output("consecutive-shifts-select", "disabled"),
    Output("shifts-per-employee-select", "disabled"),
    Output("employees-per-shift-select", "disabled"),
    inputs=[
        Input("example-scenario-select", "value"),
        State("custom-num-employees", "data"),
        State("custom-consecutive-shifts", "data"),
        State("custom-shifts-per-employees", "data"),
        State("custom-employees-per-shift", "data"),
        State("custom-random-seed", "data"),
    ],
    prevent_initial_call=True,
)
def set_scenario(
    scenario: int,
    num_employees: int,
    consecutive_shifts: int,
    shifts_per_employees: list[int],
    employees_per_shift: list[int],
    random_seed: int,
) -> tuple[int, int, list[int], list[int], int, bool, bool, bool, bool]:
    """Sets the correct scenario, reverting to the saved custom setting if chosen."""
    if scenario == 1:
        return *tuple(SMALL_SCENARIO.values()), True, True, True, True
    elif scenario == 2:
        return *tuple(MEDIUM_SCENARIO.values()), True, True, True, True
    elif scenario == 3:
        return *tuple(LARGE_SCENARIO.values()), True, True, True, True

    # else return custom stored selections
    return (
        num_employees,
        consecutive_shifts,
        shifts_per_employees,
        employees_per_shift,
        random_seed,
        False,
        False,
        False,
        False,
    )


@app.callback(
    Output("employees-per-shift-select", "max"),
    Output("employees-per-shift-select", "marks"),
    # required to refresh tooltip
    Output("employees-per-shift-select", "tooltip"),
    inputs=[
        Input("num-employees-select", "value"),
        # passthrough input; required to refresh tooltip
        State("employees-per-shift-select", "tooltip"),
    ],
)
def update_employees_per_shift(
    value: int, tooltip: dict[str, Any]
) -> tuple[int, dict, dict]:
    """Update the employees-per-shift slider max if num-employees is changed."""
    marks = {
        MIN_MAX_EMPLOYEES["min"]: str(MIN_MAX_EMPLOYEES["min"]),
        value: str(value),
    }
    return value, marks, tooltip


########
# following callbacks all store custom parameters if changed


@app.callback(
    Output("custom-num-employees", "data"),
    inputs=[
        Input("num-employees-select", "value"),
        State("example-scenario-select", "value"),
    ],
)
def custom_num_employees(value: int, scenario: int) -> int:
    """Save num-employers value if changed under custom scenario."""
    if scenario == 0:
        return value
    raise PreventUpdate


@app.callback(
    Output("custom-consecutive-shifts", "data"),
    inputs=[
        Input("consecutive-shifts-select", "value"),
        State("example-scenario-select", "value"),
    ],
)
def custom_consecutive_shifts(value: int, scenario: int) -> int:
    """Save consecutive-shifts value if changed under custom scenario."""
    if scenario == 0:
        return value
    raise PreventUpdate


@app.callback(
    Output("custom-shifts-per-employees", "data"),
    inputs=[
        Input("shifts-per-employee-select", "value"),
        State("example-scenario-select", "value"),
    ],
)
def custom_shifts_per_employee(value: list[int], scenario: int) -> int:
    """Save shift-per-employee value if changed under custom scenario."""
    if scenario == 0:
        return value
    raise PreventUpdate


@app.callback(
    Output("custom-employees-per-shift", "data"),
    inputs=[
        Input("employees-per-shift-select", "value"),
        State("example-scenario-select", "value"),
    ],
)
def custom_employees_per_shift(value: list[int], scenario: int) -> int:
    """Save employees-per-shift value if changed under custom scenario."""
    if scenario == 0:
        return value
    raise PreventUpdate


@app.callback(
    Output("custom-random-seed", "data"),
    inputs=[
        Input("seed-select", "value"),
        State("example-scenario-select", "value"),
    ],
)
def custom_random_seed(value: int, scenario: int) -> int:
    """Save random-seed value if changed under custom scenario."""
    if scenario == 0:
        return value
    raise PreventUpdate


# done storing custom parameters
########


@app.callback(
    Output("availability-content", "children"),
    Output("schedule-content", "children", allow_duplicate=True),
    Output("schedule-tab", "disabled", allow_duplicate=True),
    Output("tabs", "value"),
    Output({"type": "to-collapse-class", "index": 1}, "style", allow_duplicate=True),
    inputs=[Input("num-employees-select", "value"), Input("seed-select", "value")],
)
def disp_initial_sched(
    num_employees: int, rand_seed: int
) -> tuple[DataFrame, DataFrame, bool, str, dict]:
    """Display initial availability schedule.

    Display initial schedule in, and switch to, the availability
    tab if number of employees or seed is changed.
    """
    # one less to account for trainee
    num_employees -= 1

    df = utils.build_random_sched(num_employees, rand_seed)

    init_availability_table = utils.display_availability(df)
    return (
        init_availability_table,
        init_availability_table,
        True,  # disable the shedule tab when changing parameters
        "availability-tab",  # jump back to the availability tab
        {"display": "none"},
    )


@app.callback(
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

    return ({"display": "none"}, prev_classes + " collapsed")


@app.callback(
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
        State("availability-content", "children"),
        State("solver-select", "value"),
    ],
    running=[
        # show cancel button and hide run button, and disable and animate results tab
        (
            Output("cancel-button", "style"),
            {"display": "inline-block"},
            {"display": "none"},
        ),
        (
            Output("run-button", "style"),
            {"display": "none"},
            {"display": "inline-block"},
        ),
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
    sched_df: DataFrame,
    solver: str,
) -> tuple[DataFrame, bool, dict, list]:
    """Run a job on the hybrid solver when the run button is clicked."""
    if run_click == 0 or ctx.triggered_id != "run-button":
        raise PreventUpdate

    shifts = list(sched_df["props"]["data"][0].keys())
    shifts.remove("Employee")

    availability = utils.availability_to_dict(sched_df["props"]["data"])
    employees = list(availability.keys())

    isolated_days_allowed = True if 0 in checklist else False
    manager_required = True if 1 in checklist else False

    params = utils.ModelParams(
        availability=availability,
        shifts=shifts,
        min_shifts=min(shifts_per_employee),
        max_shifts=max(shifts_per_employee),
        shift_min=min(employees_per_shift),
        shift_max=max(employees_per_shift),
        requires_manager=manager_required,
        allow_isolated_days_off=isolated_days_allowed,
        max_consecutive_shifts=consecutive_shifts
    )

    if solver == "cqm":
        cqm = employee_scheduling.build_cqm(params)

        feasible_sampleset, errors = employee_scheduling.run_cqm(cqm)
        sample = feasible_sampleset.first.sample

        sched = utils.build_schedule_from_sample(sample, employees)

    elif solver == "nl":
        model, assignments = employee_scheduling.build_nl(params)
        errors = employee_scheduling.run_nl(model, assignments, params)
        sched = utils.build_schedule_from_state(assignments.state(), employees, shifts)

    else:
        raise ValueError(f"Solver value `{solver} is unhandled.")

    return (
        utils.display_schedule(sched, availability),
        False,
        {"display": "flex"} if errors else {"display": "none"},
        errors_list(errors) if errors else no_update,
    )


# import the html code and sets it in the app
# creates the visual layout and app (see `app_html.py`)
set_html(app)

if __name__ == "__main__":
    app.run_server(debug=DEBUG)

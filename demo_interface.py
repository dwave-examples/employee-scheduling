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

"""This file stores the Dash HTML layout for the app."""
from __future__ import annotations
from enum import EnumMeta

from dash import dash_table, dcc, html
import dash_mantine_components as dmc

from demo_configs import (
    DESCRIPTION,
    MAIN_HEADER,
    MAX_CONSECUTIVE_SHIFTS,
    MIN_MAX_SHIFTS,
    NUM_EMPLOYEES,
    NUM_FULL_TIME,
    REQUESTED_SHIFT_ICON,
    THUMBNAIL,
    UNAVAILABLE_ICON,
)
from src.demo_enums import ScenarioType
from src.utils import COL_IDS

THEME_COLOR = "#2d4376"


def slider(label: str, id: str, config: dict) -> html.Div:
    """Slider element for value selection.

    Args:
        label: The title that goes above the slider.
        id: A unique selector for this element.
        config: A dictionary of slider configurations, see dmc.Slider Dash Mantine docs.
    """
    return html.Div(
        className="slider-wrapper",
        children=[
            html.Label(label, htmlFor=id),
            dmc.Slider(
                id=id,
                className="slider",
                **config,
                marks=[
                    {"value": config["min"], "label": f'{config["min"]}'},
                    {"value": config["max"], "label": f'{config["max"]}'},
                ],
                labelAlwaysOn=True,
                thumbLabel=f"{label} slider",
                color=THEME_COLOR,
            ),
        ],
    )


def range_slider(label: str, id: str, config: dict) -> html.Div:
    """Range slider element for value selection.

    Args:
        label: The title that goes above the range slider.
        id: A unique selector for this element.
        config: A dictionary of range slider configurations, see dmc.RangeSlider Dash Mantine docs.
    """
    return html.Div(
        className="rangeslider-wrapper",
        children=[
            html.Label(label, htmlFor=id),
            dmc.RangeSlider(
                id=id,
                className="slider",
                **config,
                marks=[
                    {"value": config["min"], "label": f'{config["min"]}'},
                    {"value": config["max"], "label": f'{config["max"]}'},
                ],
                labelAlwaysOn=True,
                thumbFromLabel=f"{label} slider start",
                thumbToLabel=f"{label} slider end",
                color=THEME_COLOR,
            )
        ]
    )


def dropdown(label: str, id: str, options: list) -> html.Div:
    """Dropdown element for option selection.

    Args:
        label: The title that goes above the dropdown.
        id: A unique selector for this element.
        options: A list of dictionaries of labels and values.
    """
    return html.Div(
        className="dropdown-wrapper",
        children=[
            html.Label(label, htmlFor=id),
            dmc.Select(
                id=id,
                data=options,
                value=options[0]["value"],
                allowDeselect=False,
            ),
        ],
    )


def checkbox(label: str, id: str, checked: bool) -> html.Div:
    """Checkbox element.

    Args:
        label: The title that goes above the checkbox.
        id: A unique selector for this element.
        checked: Whether the checkbox is checked or not.
    """
    return html.Div(
        className="checkbox-wrapper",
        children=[
            dmc.Checkbox(
                id=id,
                label=label,
                checked=checked,
                color=THEME_COLOR,
            )
        ],
    )


def input(label: str, id: str, configs: dict, type: str="number") -> html.Div:
    """Input element for either text or number input.

    Args:
        label: The title that goes above the input.
        id: A unique selector for this element.
        configs: A dictionary of configurations for the input element.
        type: The type of input, either "number" or "text".
    """
    return html.Div(
        className="input-wrapper",
        children=[
            html.Label(label, htmlFor=str(id)),
            dmc.TextInput(
                id=id,
                **configs,
            ) if type == "text" else dmc.NumberInput(
                id=id,
                **configs,
            ),
        ],
    )


def generate_options(options: list | EnumMeta | dict) -> list[dict]:
    """Format options for dropdowns, checklists, radios, etc.

    Args:
        options: A list, EnumMeta, or dictionary of options to format.

    Returns:
        A list of dictionaries with "label" and "value" keys for each option.
    """
    if isinstance(options, EnumMeta):
        return [{"label": option.label, "value": f"{option.value}"} for option in options]

    if isinstance(options, dict):
        return [{"label": f"{key}", "value": f"{value}"} for key, value in options.items()]

    return [{"label": f"{option}", "value": f"{option}"} for option in options]


def generate_settings_form() -> html.Div:
    """This function generates settings for selecting the scenario, model, and solver.

    Returns:
        html.Div: A Div containing the settings for selecting the scenario, model, and solver.
    """
    example_scenario = generate_options(ScenarioType)

    return html.Div(
        className="settings",
        children=[
            html.Div(
                children=[
                    dropdown(
                        "Presets (sets sliders below)",
                        "scenario-select",
                        example_scenario,
                    )
                ]
            ),
            slider(
                "Employees",
                "num-employees-select",
                NUM_EMPLOYEES,
            ),
            slider(
                "Full-Time Employees",
                "num-full-time-select",
                NUM_FULL_TIME,
            ),
            html.Div(
                id={
                    "type": "to-collapse-class",
                    "index": 3,
                },
                className="details-collapse-wrapper collapsed",
                children=[
                    html.Button(
                        id={
                            "type": "collapse-trigger",
                            "index": 3,
                        },
                        className="details-collapse accordion",
                        children=[
                            html.H3("Advanced options"),
                            html.Div(className="collapse-arrow"),
                        ],
                        **{"aria-expanded": "false"},
                    ),
                    html.Div(
                        className="details-to-collapse part-time-collapse",
                        children=[
                            slider(
                                "Max Consecutive Part-Time Shifts",
                                "consecutive-shifts-select",
                                MAX_CONSECUTIVE_SHIFTS,
                            ),
                            range_slider(
                                "Shifts Per Part-Time Employee",
                                "shifts-per-employee-select",
                                MIN_MAX_SHIFTS,
                            ),
                            checkbox(
                                "Allow isolated days off",
                                "checklist-input",
                                False,
                            )
                        ],
                    ),
                ],
            ),
        ],
    )


def generate_run_buttons() -> html.Div:
    """Generate run and cancel buttons to run the optimization."""
    return html.Div(
        id="button-group",
        children=[
            html.Button("Run Optimization", id="run-button", className="button"),
            html.Button(
                "Cancel Optimization",
                id="cancel-button",
                className="button",
                style={"display": "none"},
            ),
        ],
    )


def generate_forecast_table(forecast: list, scheduled: dict) -> html.Div:
    """Generate the forecasted vs scheduled table"""
    forecast = {scheduled_key: forecast_value for scheduled_key, forecast_value in zip(scheduled.keys(), forecast)}
    return html.Div(
        className="schedule-forecast",
        children=[
            html.Div([html.Label("Forecasted Need:"), html.Label("Scheduled Employees:"), html.Label("Difference:")]),
            dash_table.DataTable(
                id="forecast-output",
                columns=([{"id": p, "name": p} for p in forecast.keys()]),
                data=[
                    forecast,
                    scheduled,
                    {key: scheduled[key] - value for key, value in forecast.items()},
                ],
                style_data_conditional=[
                    {
                        "if": {
                            "filter_query": f"{{{col_id}}} != 0",
                            "column_id": col_id,
                            "row_index": 2,
                        },
                        "backgroundColor": "#c7003860",
                    }
                    for col_id in forecast.keys()
                ],
            ),
        ],
    )


def errors_list(errors: dict) -> html.Div:
    """Creates html list of errors."""
    error_lists = []
    error_counter = 0
    for error_key, error_list in errors.items():
        error_lists.append(
            html.Div(
                id={
                    "type": "to-collapse-class",
                    "index": 4 + error_counter,
                },
                className="details-collapse-wrapper collapsed",
                children=[
                    html.Button(
                        id={
                            "type": "collapse-trigger",
                            "index": 4 + error_counter,
                        },
                        title="Collapse error sidebar",
                        className="details-collapse accordion",
                        children=[
                            html.H6(error_key),
                            html.Div(className="collapse-arrow"),
                        ],
                        **{"aria-expanded": "true"},
                    ),
                    html.Div(
                        className="details-to-collapse",
                        children=[html.Ul([html.Li(error) for error in error_list])],
                    ),
                ],
            )
        )
        error_counter += 1
    return html.Div([html.H4("The following constraints were not satisfied:"), *error_lists])


def create_interface() -> html.Div:
    """Create the main application interface."""
    return html.Div(
        id="app-container",
        children=[
            html.A(  # Skip link for accessibility
                "Skip to main content",
                href="#main-content",
                id="skip-to-main",
                className="skip-link",
                tabIndex=1,
            ),
            dcc.Store(
                id="custom-saved-data",
                data={
                    "num-employees-select": NUM_EMPLOYEES["value"],
                    "num-full-time-select": NUM_FULL_TIME["value"],
                    "consecutive-shifts-select": MAX_CONSECUTIVE_SHIFTS["value"],
                    "shifts-per-employee-select": MIN_MAX_SHIFTS["value"],
                }
            ),
            dcc.Store(id="submission_indicator"),
            # Settings and results columns
            html.Main(
                className="columns-main",
                id="main-content",
                children=[
                    # Left column
                    html.Div(
                        id={"type": "to-collapse-class", "index": 0},
                        className="left-column",
                        children=[
                            html.Div(
                                className="left-column-layer-1",  # Fixed width Div to collapse
                                children=[
                                    html.Div(
                                        className="left-column-layer-2",  # Padding and content wrapper
                                        children=[
                                            html.Div(
                                                [
                                                    html.H1(MAIN_HEADER),
                                                    html.P(DESCRIPTION),
                                                ],
                                                className="title-section",
                                            ),
                                            html.Div(
                                                [
                                                    html.Div(
                                                        html.Div(
                                                            [
                                                                generate_settings_form(),
                                                                generate_run_buttons(),
                                                            ],
                                                            className="settings-and-buttons",
                                                        ),
                                                        className="settings-and-buttons-wrapper",
                                                    ),
                                                    # Left column collapse button
                                                    html.Div(
                                                        html.Button(
                                                            id={
                                                                "type": "collapse-trigger",
                                                                "index": 0,
                                                            },
                                                            className="left-column-collapse",
                                                            title="Collapse sidebar",
                                                            children=[
                                                                html.Div(className="collapse-arrow")
                                                            ],
                                                            **{"aria-expanded": "true"},
                                                        ),
                                                    ),
                                                ],
                                                className="form-section",
                                            ),
                                        ],
                                    )
                                ],
                            ),
                        ],
                    ),
                    # Right column
                    html.Div(
                        className="right-column",
                        children=[
                            dmc.Tabs(
                                id="tabs",
                                value="input-tab",
                                color="white",
                                children=[
                                    html.Header(
                                        className="banner",
                                        children=[
                                            html.Nav(
                                                [
                                                    dmc.TabsList(
                                                        [
                                                            dmc.TabsTab("Availability", value="input-tab"),
                                                            dmc.TabsTab(
                                                                "Scheduled Shifts",
                                                                value="schedule-tab",
                                                                id="schedule-tab",
                                                                disabled=True,
                                                            ),
                                                        ]
                                                    ),
                                                ]
                                            ),
                                            html.Img(src=THUMBNAIL, alt="D-Wave logo"),
                                        ],
                                    ),
                                    dmc.TabsPanel(
                                        value="input-tab",
                                        tabIndex="12",
                                        children=[
                                            html.Div(
                                                className="tab-content-wrapper",
                                                children=[
                                                    html.Div(
                                                        className="schedule",
                                                        children=[
                                                            html.Div(
                                                                className="schedule-inner",
                                                                children=[
                                                                    html.Div(id="availability-content"),
                                                                    html.Div(
                                                                        className="schedule-forecast schedule-forecast-input",
                                                                        children=[
                                                                            html.Label("Staffing Requirements:"),
                                                                            html.Div(
                                                                                [
                                                                                    dcc.Input(
                                                                                        id={"index": param, "type": "forecast"},
                                                                                        type="number",
                                                                                        debounce=True,
                                                                                        value=0,
                                                                                        min=0,
                                                                                        max=100,
                                                                                        required=True,
                                                                                    ) for param in COL_IDS
                                                                                ],
                                                                                id="forecast-input"
                                                                            )
                                                                        ],
                                                                    ),
                                                                ],
                                                            ),
                                                            html.Div(
                                                                className="legend",
                                                                children=[
                                                                    html.Div([
                                                                        html.Div(
                                                                            className="requested-shifts",
                                                                            children=[REQUESTED_SHIFT_ICON],
                                                                        ),
                                                                        html.Label("Requested"),
                                                                    ]),
                                                                    html.Div([
                                                                        html.Div(
                                                                            className="unavailable-shifts",
                                                                            children=[UNAVAILABLE_ICON],
                                                                        ),
                                                                        html.Label("Unavailable"),
                                                                    ]),
                                                                ],
                                                            ),
                                                        ],
                                                    ),
                                                ]
                                            )
                                        ],
                                    ),
                                    dmc.TabsPanel(
                                        value="schedule-tab",
                                        tabIndex="13",
                                        children=[
                                            html.Div(
                                                className="tab-content-wrapper",
                                                children=[
                                                    html.Div(
                                                        className="schedule",
                                                        children=[
                                                            dcc.Loading(
                                                                id="loading",
                                                                type="circle",
                                                                color="#2A7DE1",
                                                                parent_className="schedule-loading",
                                                                children=html.Div(
                                                                    [
                                                                        html.Div(id="schedule-content"),
                                                                        html.Div(
                                                                            className="schedule-forecast",
                                                                            id="scheduled-forecast-output",
                                                                        ),
                                                                    ]
                                                                ),
                                                            ),
                                                            html.Div(
                                                                className="legend",
                                                                children=[
                                                                    html.Div([
                                                                        html.Div(className="scheduled-shifts"),
                                                                        html.Label("Scheduled"),
                                                                    ]),
                                                                    html.Div([
                                                                        html.Div(
                                                                            className="unscheduled-requested-shifts",
                                                                            children=[REQUESTED_SHIFT_ICON],
                                                                        ),
                                                                        html.Label("Unscheduled requested"),
                                                                    ]),
                                                                    html.Div([
                                                                        html.Div(UNAVAILABLE_ICON),
                                                                        html.Label("Unavailable"),
                                                                    ]),
                                                                ],
                                                            ),
                                                        ],
                                                    ),
                                                ]
                                            )
                                        ],
                                    ),
                                ],
                            )
                        ],
                    ),
                    # Log column
                    html.Div(
                        id={"type": "to-collapse-class", "index": 1},
                        className="log-column collapsed",
                        children=[
                            html.Button(
                                id={"type": "collapse-trigger", "index": 1},
                                className="log-column-collapse",
                                children=[html.Div(className="collapse-arrow")],
                                **{"aria-expanded": "false"},
                            ),
                            html.Div([html.Div(id="errors")]),
                        ],
                    ),
                ],
            ),
        ],
    )

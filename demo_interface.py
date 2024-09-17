# Copyright 2024 D-Wave Systems Inc.
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

from dash import dash_table, dcc, html

from demo_configs import (
    DESCRIPTION,
    EXAMPLE_SCENARIO,
    MAIN_HEADER,
    MAX_CONSECUTIVE_SHIFTS,
    MIN_MAX_SHIFTS,
    NUM_EMPLOYEES,
    NUM_FULL_TIME,
    REQUESTED_SHIFT_ICON,
    THUMBNAIL,
    UNAVAILABLE_ICON
)
from utils import COL_IDS


def slider(label: str, id: str, config: dict) -> html.Div:
    """Slider element for value selection.

    Args:
        label: The title that goes above the slider.
        id: A unique selector for this element.
        config: A dictionary of slider configerations, see dcc.Slider Dash docs.
    """
    return html.Div(
        className="slider-wrapper",
        children=[
            html.Label(label),
            dcc.Slider(
                id=id,
                className="slider",
                **config,
                marks={
                    config["min"]: str(config["min"]),
                    config["max"]: str(config["max"]),
                },
                tooltip={
                    "placement": "bottom",
                    "always_visible": True,
                },
            ),
        ],
    )


def range_slider(label: str, id: str, config: dict) -> html.Div:
    """Range slider element for value selection."""
    return html.Div(
        className="range-slider",
        children=[
            html.Label(label),
            dcc.RangeSlider(
                id=id,
                **config,
                marks={
                    config["min"]: str(config["min"]),
                    config["max"]: str(config["max"]),
                },
                tooltip={
                    "placement": "bottom",
                    "always_visible": True,
                },
            ),
        ],
    )


def generate_options(options_list: list) -> list[dict]:
    """Generates options for dropdowns, checklists, radios, etc."""
    return [{"label": label, "value": i} for i, label in enumerate(options_list)]


def generate_settings_form() -> html.Div:
    """This function generates settings for selecting the scenario, model, and solver.

    Returns:
        html.Div: A Div containing the settings for selecting the scenario, model, and solver.
    """
    example_scenario = generate_options(EXAMPLE_SCENARIO)

    return html.Div(
        className="settings",
        id="control-card",
        children=[
            html.Div(
                children=[
                    html.Label("Presets (sets sliders below)"),
                    dcc.Dropdown(
                        id="example-scenario-select",
                        options=example_scenario,
                        value=example_scenario[0]["value"],
                        clearable=False,
                        searchable=False,
                    ),
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
                        className="details-collapse part-time-settings",
                        children=[
                            html.Label("Advanced settings"),
                            html.Div(
                                className="collapse-arrow"
                            ),
                        ],
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
                            dcc.Checklist(
                                options=[
                                    {"label": "Allow isolated days off", "value": 0},
                                ],
                                value=[],
                                id="checklist-input",
                            ),
                        ]
                    )
                ]
            ),
        ],
    )


def generate_run_buttons() -> html.Div:
    """Run and cancel buttons to run the optimization."""
    return html.Div(
        id="button-group",
        children=[
            html.Button(id="run-button", children="Run Optimization", n_clicks=0, disabled=False),
            html.Button(
                id="cancel-button",
                children="Cancel Optimization",
                n_clicks=0,
                className="display-none",
            ),
        ],
    )


def generate_forecast_table(forecast: dict, scheduled: dict) -> html.Div:
    """Generate the forecasted vs scheduled table"""
    return html.Div(
        className="schedule-forecast",
        children=[
            html.Div([html.Label("Forecasted"), html.Label("Scheduled"), html.Label("Difference")]),
            dash_table.DataTable(
                id="forecast-output",
                columns=(
                    [{'id': p, 'name': p} for p in forecast.keys()]
                ),
                data=[
                    forecast,
                    scheduled,
                    {key: scheduled[key] - value for key, value in forecast.items()}
                ],
                style_data_conditional=[
                    {
                        'if': {
                            'filter_query': f'{{{col_id}}} != 0',
                            'column_id': col_id,
                            'row_index': 2,
                        },
                        'backgroundColor': '#c7003860',
                    } for col_id in forecast.keys()
                ]
            ),
        ]
    )


def create_interface():
    """Set the application HTML."""
    return html.Div(
        id="app-container",
        children=[
            dcc.Store(id="custom-saved-data"),
            dcc.Store(id="submission_indicator"),
            # Header brand banner
            html.Div(className="banner", children=[html.Img(src=THUMBNAIL)]),
            # Settings and results columns
            html.Div(
                className="columns-main",
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
                                            html.H1(MAIN_HEADER),
                                            html.P(DESCRIPTION),
                                            generate_settings_form(),
                                            generate_run_buttons(),
                                        ],
                                    )
                                ],
                            ),
                            # Left column collapse button
                            html.Div(
                                html.Button(
                                    id={"type": "collapse-trigger", "index": 0},
                                    className="left-column-collapse",
                                    children=[html.Div(className="collapse-arrow")],
                                ),
                            ),
                        ],
                    ),
                    # Right column
                    html.Div(
                        className="right-column",
                        children=[
                            dcc.Tabs(
                                id="tabs",
                                value="input-tab",
                                children=[
                                    dcc.Tab(
                                        label="Availability",
                                        id="input-tab",
                                        value="input-tab",  # used for switching to programatically
                                        className="tab",
                                        children=[
                                            html.Div(
                                                className="schedule",
                                                children=[
                                                    html.Div(
                                                        className="schedule-inner",
                                                        children=[
                                                            html.Div(id="availability-content"),
                                                            html.Div(
                                                                className="schedule-forecast",
                                                                children=[
                                                                    html.Label("Forecast"),
                                                                    dash_table.DataTable(
                                                                        id="forecast-input",
                                                                        columns=(
                                                                            [{'id': p, 'name': p} for p in COL_IDS]
                                                                        ),
                                                                        data=[
                                                                            dict({param: 0 for param in COL_IDS})
                                                                        ],
                                                                        editable=True
                                                                    ),
                                                                ]
                                                            ),
                                                        ]
                                                    ),
                                                    html.Div(
                                                        className="legend",
                                                        children=[
                                                            html.Div(className="requested-shifts", children=[REQUESTED_SHIFT_ICON]),
                                                            html.Label("Requested"),
                                                            html.Div(className="unavailable-shifts", children=[UNAVAILABLE_ICON]),
                                                            html.Label("Unavailable"),
                                                        ]
                                                    )
                                                ]
                                            ),
                                        ],
                                    ),
                                    dcc.Tab(
                                        label="Scheduled Shifts",
                                        id="schedule-tab",
                                        value="schedule-tab",  # used for switching to programatically
                                        className="tab",
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
                                                            html.Div(className="scheduled-shifts"),
                                                            html.Label("Scheduled"),
                                                            html.Div(className="unscheduled-requested-shifts", children=[REQUESTED_SHIFT_ICON]),
                                                            html.Label("Unscheduled requested"),
                                                            html.Div(UNAVAILABLE_ICON),
                                                            html.Label("Unavailable"),
                                                        ]
                                                    )
                                                ]
                                            )
                                        ],
                                        disabled=True,
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
                                children=[html.Div(className="collapse-arrow")]
                            ),
                            html.Div(
                                [
                                    html.Div(id="errors")
                                ]
                            ),
                        ],
                    ),
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
                        className="details-collapse",
                        children=[
                            html.H6(error_key),
                            html.Div(
                                className="collapse-arrow"
                            ),
                        ],
                    ),
                    html.Div(
                        className="details-to-collapse",
                        children=[
                            html.Ul(
                                [
                                    html.Li(error) for error in error_list
                                ]
                            )
                        ]
                    )
                ]
            )
        )
        error_counter += 1
    return html.Div([html.H4("The following constraints were not satisfied:"), *error_lists])

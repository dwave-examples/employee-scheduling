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

"""This file stores the HTML layout for the app (see ``employee_scheduling.css`` for CSS styling)."""
from __future__ import annotations

import html
from typing import Any

from dash import dcc, html

from app_configs import (DESCRIPTION, MAIN_HEADER, MAX_CONSECUTIVE_SHIFTS, MIN_MAX_EMPLOYEES,
                         MIN_MAX_SHIFTS, NUM_EMPLOYEES, THUMBNAIL)

map_width, map_height = 1000, 600

EXAMPLE_SCENARIO = ["Custom", "Small", "Medium", "Large"]


def description_card():
    """A Div containing dashboard title & descriptions."""
    return html.Div(
        id="description-card",
        children=[html.H1(MAIN_HEADER), html.P(DESCRIPTION)],
    )


def slider(name: str, id: str, config: dict) -> html.Div:
    """Slider element for value selection."""
    return html.Div(
        className="slider",
        children=[
            html.Label(name),
            dcc.Slider(
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


def range_slider(name: str, id: str, config: dict) -> html.Div:
    """Range slider element for value selection."""
    return html.Div(
        className="range-slider",
        children=[
            html.Label(name),
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


def generate_control_card() -> html.Div:
    """Generates the control card for the dashboard.

    Returns:
        html.Div: A Div containing the dropdowns for selecting the scenario,
        model, and solver.
    """
    example_scenario = [{"label": size, "value": i} for i, size in enumerate(EXAMPLE_SCENARIO)]

    return html.Div(
        id="control-card",
        children=[
            html.Div(
                children=[
                    html.Label("Example scenario"),
                    dcc.Dropdown(
                        id="example-scenario-select",
                        options=example_scenario,
                        value=example_scenario[0]["value"],
                        clearable=False,
                        searchable=False,
                    ),
                ]
            ),
            # add sliders for employees and shifts
            slider(
                "Number of employees",
                "num-employees-select",
                NUM_EMPLOYEES,
            ),
            slider(
                "Max consecutice shifts",
                "consecutive-shifts-select",
                MAX_CONSECUTIVE_SHIFTS,
            ),
            # add range sliders for min/max employees and shifts
            range_slider(
                "Min/max shifts per employee",
                "shifts-per-employee-select",
                MIN_MAX_SHIFTS,
            ),
            range_slider(
                "Min/max employees per shift",
                "employees-per-shift-select",
                MIN_MAX_EMPLOYEES,
            ),
            dcc.Checklist(
                options=[
                    {"label": "Allow isolated days off", "value": 0},
                    {"label": "Require exactly one manager on every shift", "value": 1},
                ],
                value=[1],
                id="checklist-input",
            ),
            html.Div(
                children=[
                    html.Label("Random seed (optional)"),
                    dcc.Input(id="seed-select", type="number", min=0),
                ]
            ),
            html.Div(
                id="button-group",
                children=[
                    html.Button(id="run-button", children="Solve", n_clicks=0),
                    html.Button(
                        id="cancel-button",
                        children="Cancel",
                        n_clicks=0,
                        style={"display": "none"},
                    ),
                ],
            ),
        ],
    )


def set_html(app):
    """Set the application HTML."""
    app.layout = html.Div(
        id="app-container",
        children=[
            html.Div(
                id="custom-parameters",
                children=[
                    dcc.Store(id="custom-num-employees"),
                    dcc.Store(id="custom-consecutive-shifts"),
                    dcc.Store(id="custom-shifts-per-employees"),
                    dcc.Store(id="custom-employees-per-shift"),
                    dcc.Store(id="custom-random-seed"),
                ],
            ),
            dcc.Store(id="submission_indicator"),
            # Banner
            html.Div(id="banner", children=[html.Img(src=THUMBNAIL)]),
            html.Div(
                id="columns",
                children=[
                    # Left column
                    html.Div(
                        id="left-column",
                        children=[
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            description_card(),
                                            generate_control_card(),
                                            html.Div(
                                                ["initial child"],
                                                id="output-clientside",
                                                style={"display": "none"},
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                            html.Div(
                                html.Button(id="left-column-collapse", children=[html.Div()]),
                            ),
                        ],
                    ),
                    # Right column
                    html.Div(
                        id="right-column",
                        children=[
                            dcc.Tabs(
                                id="tabs",
                                value="availability-tab",
                                children=[
                                    dcc.Tab(
                                        label="Availability",
                                        id="availability-tab",
                                        value="availability-tab",  # used for switching to programatically
                                        className="tab",
                                        children=[
                                            html.Div(id="availability-content"),
                                        ],
                                    ),
                                    dcc.Tab(
                                        label="Schedule",
                                        id="schedule-tab",
                                        value="schedule-tab",  # used for switching to programatically
                                        className="tab",
                                        children=[
                                            dcc.Loading(
                                                id="loading",
                                                type="circle",
                                                color="#2A7DE1",
                                                children=html.Div(id="schedule-content"),
                                            ),
                                        ],
                                        disabled=True,
                                    ),
                                ],
                            )
                        ],
                    ),
                ],
            ),
        ],
    )

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
from datetime import datetime

import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, State, dcc, html, callback_context, no_update

import employee_scheduling
import utils

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

ALLOWED_TYPES = (
    "text",
    "number",
    "range",
)


# style settings
col = "white"
ff = "verdana"

nav_bar = dbc.Card(
    [
        dbc.Navbar(
            [
                html.A(
                    dbc.Row(
                        [
                            dbc.Col(
                                html.Img(
                                    src="assets/dwave_logo.png", height="20px"
                                ),
                                style={"margin": "5px", "outline": False},
                            ),
                        ],
                        align="center",
                        className="g-0",
                    ),
                    href="https://dwavesys.com",
                    style={
                        "textDecoration": "none",
                    },
                )
            ],
            color="#074c91",
        )
    ]
)


title_card = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        html.H1(
                            children="Employee Scheduling",
                            style={
                                "textAlign": "center",
                                "font-family": ff,
                                "className": "border-0 bg-transparent",
                                "color": col,
                            },
                        )
                    ]
                )
            ]
        )
    ],
    className="border-0 bg-transparent",
)

input_card = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Tabs(
                    id="input_tabs",
                    active_tab="basic",
                    children=[
                        dbc.Tab(
                            tab_id="basic",
                            children=[

                                dbc.Row([
                                    dbc.Col([

                                        html.P(
                                            "Number of employees:  ",
                                            style={"font-family": ff, 
                                                   "color": col,
                                                   "marginTop": "20px"},
                                        ),
                                        dbc.Input(
                                            id="input_employees",
                                            type="number",
                                            placeholder="#",
                                            min=4,
                                            max=200,
                                            step=1,
                                            value=12,
                                            style={"marginBottom": "5px", "outline": False,},
                                            debounce = True
                                        ),
                                        html.P(
                                            "Example scenario: ",
                                            style={"font-family": ff, 
                                                   "color": col,
                                                   "marginTop": "20px"},
                                        ),
                                        dcc.Dropdown(
                                            ["Small", "Medium", "Large"],
                                            placeholder="Select a scenario",
                                            id="demo-dropdown",
                                            style={"marginBottom": "15px"}
                                        ),
                                        
                                    ], width=4),
                                ]),
                            ],
                            label="Basic Configuration",
                            active_label_style={"color": "black"},
                            label_style={"color": "white"},
                        ),
                        dbc.Tab(
                            tab_id="more",
                            children=[
                                dbc.Row([
                                    dbc.Col([
                                        html.P(
                                            "Optional random seed: ",
                                            style={"font-family": ff, 
                                                   "color": col,
                                                   "marginTop": "10px"},
                                        ),
                                        dbc.Input(
                                            id="seed",
                                            type="number",
                                            placeholder="(Optional)",
                                            min=1,
                                            style={"marginBottom": "5px", 
                                                   "max-width": "50%",
                                                   "outline": False},
                                            debounce = True,
                                            size = "sm"
                                        ),
                                        html.P(
                                            "Max consecutive shifts:",
                                            style={"font-family": ff, "color": col},
                                        ),
                                        dbc.Input(
                                            id="cons shifts",
                                            type="number",
                                            placeholder="Max consecutive shifts",
                                            min=1,
                                            value=5,
                                            style={
                                                "max-width": "50%",
                                                "marginBottom": "5px",
                                                "outline": False,
                                            },
                                        ),
                                        dbc.Checklist(
                                            options=[
                                                {
                                                    "label": "Allow isolated days off",
                                                    "value": 1,
                                                },
                                                {
                                                    "label": "Require exactly one manager on every shift",
                                                    "value": 2,
                                                },
                                            ],
                                            value=[2],
                                            id="checklist-input",
                                            style={
                                                "color": col,
                                                "font-family": ff,
                                            },
                                        ),
                                    ], width=5),
                                    dbc.Col([
                                        html.P(
                                            "Min/max shifts per employee:",
                                            style={"font-family": ff, 
                                                   "color": col,
                                                   "marginTop": "10px"},
                                        ),
                                        dcc.RangeSlider(min=1, max=20, step=1, marks=None, value=[5, 15], 
                                                        id='shifts-per-employee-slider', 
                                                        tooltip={"placement": "bottom", "always_visible": True},
                                                        allowCross=False),
                                        html.P(
                                            "Min/max employees per shift:",
                                            style={"font-family": ff, 
                                                   "color": col,
                                                   "marginTop": "15px"},
                                        ),
                                        dcc.RangeSlider(min=1, max=20, step=1, marks=None,  value=[5, 15], 
                                                        id='employees-per-shift-slider', 
                                                        tooltip={"placement": "bottom", "always_visible": True},
                                                        allowCross=False,
                                                        ),
                                    ]),
                                ]),    
                            ],
                            label="Advanced Configuration",
                            active_label_style={"color": "black"},
                            label_style={"color": "white"},
                        ),                
            ]
        )
    ],
    ),], 
    className="border-0 bg-transparent"
)

availability_card = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H2(
                    children="Employee Availability", style={"font-family": ff}
                ),
                html.Div(
                    id="initial-sched",
                    style={
                        "marginBottom": "5px",
                        "outline": False,
                    },
                ),
            ]
        )
    ]
)

ready_style = {
    "max-width": "50%",
    "marginBottom": "5px",
    "outline": False,
}
pending_style = {
    "max-width": "50%",
    "marginBottom": "5px",
    "outline": False,
    "background-color": "red",
}
solve_card = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row([
                        dbc.Button("Solve CQM", id="btn_solve_cqm", style=ready_style),
                        html.Div(id="trigger", children=0, style=dict(display="none")),]),
                dbc.Row([
                        dbc.FormText("Submission status:", style={"color": col},
                        ),
                        dcc.Textarea(id="submission_indicator", value="Ready to solve",
                            style={"width": "100%", "color": "white", "background-color": "rgba(0,0,0,0)", "border": "rgba(0,0,0,0)", "resize": "none"}, rows=2),
                        dcc.Interval(id="submission_timer", interval=None, n_intervals=0, disabled=True),
                ])
            ]
        )
    ],
    className="border-0 bg-transparent",
)

schedule_card = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H2(
                    children="Employee Schedule", style={"font-family": ff}
                ),
                html.Div(
                    id="built-sched",
                    style={
                        "marginBottom": "5px",
                        "outline": False,
                        "textAlign": "center",
                    },
                ),
            ]
        )
    ]
)

legend_card = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    dbc.FormText(
                        "[X] Employee unavailable",
                        style={
                            "color": col,
                            "backgroundColor": "#FF7006",
                            "padding": 10,
                        },
                    )
                ),
                dbc.Row(
                    dbc.FormText(
                        "[P] Preferred shift",
                        style={
                            "color": col,
                            "backgroundColor": "#008c82",
                            "padding": 10,
                        },
                    )
                ),
                dbc.Row(
                    dbc.FormText(
                        "Mgr = Manager; Tr - Trainee",
                        style={
                            "padding": 10,
                        },
                    )
                ),
            ]
        )
    ]
)

shift_legend_card = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    dbc.FormText(
                        "[ ] Employee shift scheduled",
                        style={
                            "color": col,
                            "backgroundColor": "#2a7de1",
                            "padding": 10,
                        },
                    )
                ),
                dbc.Row(
                    dbc.FormText(
                        "[P] Preferred shift",
                        style={
                            "padding": 10,
                        },
                    )
                ),
                dbc.Row(
                    dbc.FormText(
                        "[X] Employee unavailable",
                        style={
                            "padding": 10,
                        },
                    )
                ),
                dbc.Row(
                    dbc.FormText(
                        "[-] Employee not scheduled",
                        style={
                            "padding": 10,
                        },
                    )
                ),
            ]
        )
    ]
)

error_card = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H4(children=" ", style={"font-family": ff}),
            ],
            id="error_card_body",
        )
    ]
)

app.layout = html.Div(
    [
        nav_bar,
        dbc.Container(
            [dbc.Col([
                dbc.Row(
                    dbc.Col(
                        title_card,
                        style={
                            "paddingLeft": 150,
                            "paddingRight": 150,
                            "paddingTop": 25,
                            "paddingBottom": 25,
                            "outline": False,
                            "className": "border-0 bg-transparent",
                        },
                    )
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                input_card,
                            ],
                            style={
                                "padding": 10,
                            },
                            width=6,
                        ),
                        dbc.Col(
                            [
                                solve_card,
                            ],
                            style={
                                "padding": 10,
                            },
                            width={"size": 3, "offset": 1},
                        ),
                    ]),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Tabs(
                                id="tabs",
                                active_tab="avail",
                                children=[
                                    dbc.Tab(
                                        tab_id="avail",
                                        children=[
                                            availability_card,
                                            legend_card,
                                        ],
                                        label="Availability",
                                        active_label_style={"color": "black"},
                                        label_style={"color": "white"},
                                    ),
                                    dbc.Tab(
                                        tab_id="sched",
                                        children=[
                                            schedule_card,
                                            shift_legend_card,
                                        ],
                                        label="Schedule",
                                        active_label_style={"color": "black"},
                                        label_style={"color": "white"},
                                    ),
                                ],
                            ),
                            width="auto",
                            style={
                                "padding": 10,
                                "paddingLeft": 40,
                                "paddingBottom": 60,
                            },
                        ),
                    ],
                    style={
                        "outline": False,
                        "className": "border-0 bg-transparent",
                        "justify": "left",
                    }, justify="center"
                ),
                dbc.Row(error_card),
            ])],
            style={
                "backgroundColor": "black",
                "background-image": "url('assets/electric_squids.png')",
                "background-size": "100%",
                "paddingBottom": 50,
            },
            fluid=True,
        ),
    ]
)


@app.callback(
    Output("input_employees", "value"),
    Output("seed", "value"),
    Output("checklist-input", "value"),
    Output("shifts-per-employee-slider", "value"),
    Output("employees-per-shift-slider", "value"),
    Output("cons shifts", "value"),
    [Input("demo-dropdown", "value")],
)
def set_scenario(scenario_size):
    if scenario_size == "Small":
        return 12, 4, [2], [10, 20], [3, 6], 5
    elif scenario_size == "Medium":
        return 20, 4, [2], [8, 16], [6, 10], 5
    elif scenario_size == "Large":
        return 40, 4, [2], [4, 16], [6, 10], 5
    else:
        return 12, None, [2], [10, 20], [3, 6], 5


@app.callback(
        Output('shifts-per-employee-slider', "max"),
        Input("input_employees", "value"),
        )
def shift_range(val):
    now = datetime.now()
    month = now.month
    year = now.year
    num_days = calendar.monthrange(year, month)[1]
    return num_days

@app.callback(
        Output('employees-per-shift-slider', "max"),
        Input("input_employees", "value"),
        )
def employee_range(val):
    return val

@app.callback(
    Output("initial-sched", "children"),
    Output("built-sched", "children", allow_duplicate=True),
    [Input("input_employees", "value"), Input("seed", "value")],
    prevent_initial_call='initial_duplicate'
)
def disp_initial_sched(*vals):
    if vals:
        num_employees = vals[0] - 1
        rand_seed = vals[1]
    else:
        num_employees = 9  # one less to account for trainee

    now = datetime.now()
    month = now.month
    year = now.year
    num_days = calendar.monthrange(year, month)[1]

    shifts = [str(i + 1) for i in range(num_days)]
    df = utils.build_random_sched(num_employees, shifts, rand_seed)

    df.replace(False, " ", inplace=True)
    df.replace(True, "X", inplace=True)

    employees = list(df["Employee"])

    availability = {}

    for _, row in df.iterrows():
        e = row[0]
        i = list(row[1:])

        availability[e] = [
            0 if i[j] == "X" else 2 if i[j] == "P" else 1 for j in range(len(i))
        ]    

    sample = {str(e)+"_"+str(s): 0.0 for e in employees for s in shifts}
    temp = utils.build_schedule_from_sample(sample, shifts, employees)

    return utils.display_availability(df, month, year), utils.display_schedule(temp, availability, month, year)


@app.callback(
    Output("submission_indicator", "value"),
    Output("submission_timer", "interval"),
    Output("submission_timer", "disabled"),
    Output("tabs", "active_tab", allow_duplicate=True),
    Input("btn_solve_cqm", "n_clicks"),
    Input("submission_timer", "n_intervals"),
    State("submission_indicator", "value"),
    State("tabs", "active_tab"),
    State("built-sched", "children"),
    prevent_initial_call=True
)
def submission_mngr(
    n_clicks,
    n_intervals,
    submission_indicator_val,
    active_tab,
    built_sched
):
    trigger = callback_context.triggered
    trigger_id = trigger[0]["prop_id"].split(".")[0]

    if trigger_id == "btn_solve_cqm" and n_clicks:
        return "Submitting... please wait", 1000, False, "avail"     
        
    if trigger_id == "submission_timer" and submission_indicator_val == "Submitting... please wait":
        s = set( val[0] for dic in built_sched['props']['derived_virtual_data'] for val in dic.values())
        
        if " " not in s:
            return no_update, no_update, False, no_update
        else:
            return "Done", no_update, True, "sched"
        
    return no_update, no_update, True, no_update

   
@app.callback(
    Output("built-sched", "children", allow_duplicate=True),
    Output("error_card_body", "children"),
    Output("tabs", "active_tab"),
    Input("submission_indicator", "value"),
    State("shifts-per-employee-slider", "value"),
    State("employees-per-shift-slider", "value"),
    State("checklist-input", "value"),
    State("cons shifts", "value"),  # consecutive shifts allowed
    State("initial-sched", "children"),
    State("built-sched", "children"),
    State("error_card_body", "children"),
    prevent_initial_call=True
)
def submitter(
    submission_indicator_val,
    s_per_e_range,
    e_per_s_range,
    checklist_value,
    k,
    sched_df,
    built_sched,
    e_card,
):
    if submission_indicator_val == "Ready to solve":
        return (
            html.Label("Not constructed yet.", style={"max-width": "50%"}),
            None,
            "avail",
        )
    
    elif submission_indicator_val == "Done":
        return built_sched, e_card, "sched"
    
    elif submission_indicator_val == "Submitting... please wait":
        shifts = list(sched_df["props"]["data"][0].keys())
        shifts.remove("Employee")
        availability = utils.availability_to_dict(
            sched_df["props"]["data"], shifts
        )
        employees = list(availability.keys())

        if 1 in checklist_value:
            isolated = True
        else:
            isolated = False

        if 2 in checklist_value:
            manager = True
        else:
            manager = False

   
        
        print("\nBuilding CQM...\n")
        min_shifts = s_per_e_range[0]
        max_shifts = s_per_e_range[1]
        [shift_min, shift_max] = e_per_s_range
        cqm = employee_scheduling.build_cqm(
            availability,
            shifts,
            min_shifts,
            max_shifts,
            shift_min,
            shift_max,
            manager,
            isolated,
            k + 1,
        )

        print("\nSubmitting CQM...\n")
        feasible_sampleset, errors = employee_scheduling.run_cqm(cqm)

        sample = feasible_sampleset.first.sample

        sched = utils.build_schedule_from_sample(sample, shifts, employees)

        if errors is None:
            new_card_body = " "
        else:
            new_card_body = [
                html.H4(
                    children="Issues with Schedule", style={"font-family": ff}
                ),
                html.Div(errors, style={"whiteSpace": "pre-wrap"}),
            ]

        now = datetime.now()
        month = now.month
        year = now.year

        return (
            utils.display_schedule(sched, availability, month, year),
            new_card_body,
            "sched",
        )

    else:
        return no_update, no_update, no_update


if __name__ == "__main__":
    app.run_server(debug=True)

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
                                            style={"font-family": ff, "color": col},
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
                                            style={"font-family": ff, "color": col},
                                        ),
                                        dcc.Dropdown(
                                            ["Small", "Medium", "Large"],
                                            placeholder="Select a scenario",
                                            id="demo-dropdown",
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
                                            style={"font-family": ff, "color": col},
                                        ),
                                        dbc.Input(
                                            id="seed",
                                            type="number",
                                            placeholder="(Optional) Random Seed",
                                            min=1,
                                            style={"marginBottom": "5px", "outline": False},
                                            debounce = True
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
                                    ]),
                                    dbc.Col([
                                        dbc.FormText(
                                            "Min shifts per employee:",
                                            style={"color": col},
                                        ),
                                        dbc.Input(
                                            id="min shifts",
                                            type="number",
                                            placeholder="Min shifts per employee",
                                            min=0,
                                            value=10,
                                            style={
                                                "max-width": "50%",
                                                "marginBottom": "5px",
                                                "outline": False,
                                            },
                                            debounce = True
                                        ),
                                        dbc.FormText(
                                            "Max shifts per employee:",
                                            style={"color": col},
                                        ),
                                        dbc.Input(
                                            id="max shifts",
                                            type="number",
                                            placeholder="Max shifts per employee",
                                            min=0,
                                            value=20,
                                            style={
                                                "max-width": "50%",
                                                "marginBottom": "5px",
                                                "outline": False,
                                            },
                                            debounce = True
                                        ),
                                        dbc.FormText(
                                            "Max consecutive shifts:",
                                            style={"color": col},
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
                                            debounce = True
                                        ),
                                    ]),
                                    dbc.Col([
                                        dbc.FormText(
                                            "Min employees per shift:",
                                            style={"color": col},
                                        ),
                                        dbc.Input(
                                            id="shifts min",
                                            type="number",
                                            placeholder="Min employees per shift",
                                            min=0,
                                            value=1,
                                            style={
                                                "max-width": "50%",
                                                "marginBottom": "5px",
                                                "outline": False,
                                            },
                                            debounce = True
                                        ),
                                        dbc.FormText(
                                            "Max employees per shift:",
                                            style={"color": col},
                                        ),
                                        dbc.Input(
                                            id="shifts max",
                                            type="number",
                                            placeholder="Max employees per shift",
                                            min=1,
                                            value=6,
                                            style={
                                                "max-width": "50%",
                                                "marginBottom": "5px",
                                                "outline": False,
                                            },
                                            debounce = True
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
    Output("min shifts", "value"),
    Output("max shifts", "value"),
    Output("shifts min", "value"),
    Output("shifts max", "value"),
    Output("cons shifts", "value"),
    [Input("demo-dropdown", "value")],
)
def set_scenario(scenario_size):
    if scenario_size == "Small":
        return 12, 4, [2], 10, 20, 3, 6, 5
    elif scenario_size == "Medium":
        return 20, 4, [2], 8, 16, 6, 10, 5
    elif scenario_size == "Large":
        return 40, 4, [2], 4, 16, 6, 10, 5
    else:
        return 12, None, [2], 10, 20, 3, 6, 5


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


# Don't allow max shifts to be smaller than min shifts
@app.callback(Output("max shifts", "min"), Input("min shifts", "value"))
def set_min_shifts(min_s):
    return min_s


# Don't allow min shifts to be bigger than max shifts
@app.callback(Output("shifts min", "max"), Input("shifts max", "value"))
def set_max_shifts(max_s):
    return max_s


# Don't allow max employees to be smaller than min employees
@app.callback(Output("shifts max", "min"), Input("shifts min", "value"))
def set_shifts_min(min_e):
    return min_e


# Don't allow min employees to be bigger than max employees
@app.callback(Output("min shifts", "max"), Input("max shifts", "value"))
def set_shifts_max(max_e):
    return max_e


@app.callback(
    Output("submission_indicator", "value"),
    Output("submission_timer", "interval"),
    Output("submission_timer", "disabled"),
    Output("tabs", "active_tab", allow_duplicate=True),
    Input("btn_solve_cqm", "n_clicks"),
    Input("submission_timer", "n_intervals"),
    State("submission_indicator", "value"),
    State("tabs", "active_tab"),
    prevent_initial_call=True
)
def submission_mngr(
    n_clicks,
    n_intervals,
    submission_indicator_val,
    active_tab,
):
    trigger = callback_context.triggered
    trigger_id = trigger[0]["prop_id"].split(".")[0]

    if trigger_id == "btn_solve_cqm" and n_clicks:
        return "Submitting... please wait", 1000, False, "avail"     
        
    if trigger_id == "submission_timer" and submission_indicator_val == "Submitting... please wait":
        if active_tab == "avail":
            return no_update, no_update, False, no_update
        else:
            return "Done", no_update, True, no_update
        
    return no_update, no_update, no_update, no_update

   
@app.callback(
    Output("built-sched", "children", allow_duplicate=True),
    Output("error_card_body", "children"),
    Output("tabs", "active_tab"),
    Input("submission_indicator", "value"),
    State("checklist-input", "value"),
    State("min shifts", "value"),  # shifts per employee
    State("max shifts", "value"),
    State("shifts min", "value"),  # employees per shift
    State("shifts max", "value"),
    State("cons shifts", "value"),  # consecutive shifts allowed
    State("initial-sched", "children"),
    State("built-sched", "children"),
    State("error_card_body", "children"),
    prevent_initial_call=True
)
def submitter(
    submission_indicator_val,
    checklist_value,
    min_shifts,
    max_shifts,
    shift_min,
    shift_max,
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

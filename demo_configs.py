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

"""This file stores input parameters for the app."""

# THEME_COLOR is used for the button, text, and banner and should be dark
# and pass accessibility checks with white: https://webaim.org/resources/contrastchecker/
# THEME_COLOR_SECONDARY can be light or dark and is used for sliders, loading icon, and tabs
THEME_COLOR = "#074C91"  # D-Wave dark blue default #074C91
THEME_COLOR_SECONDARY = "#2A7DE1"  # D-Wave blue default #2A7DE1

THUMBNAIL = "static/dwave_logo.svg"

APP_TITLE = "Workforce Scheduling Demo"
MAIN_HEADER = "Workforce Scheduling"
DESCRIPTION = """\
Workforce scheduling is a common industry problem that often becomes complex
due to real-world constraints. This example demonstrates a scheduling
scenario with a variety of employees and rules.
"""

REQUESTED_SHIFT_ICON = "✓"
UNAVAILABLE_ICON = "x"


# Optional, None or an integer
RANDOM_SEED = None


#######################################
# Sliders, buttons and option entries #
#######################################

# min/max number of shifts per employee range slider (value means default)
MIN_MAX_SHIFTS = {
    "min": 1,
    "max": 14,
    "step": 1,
    "value": [5, 7],
}

# number of employees slider (value means default)
NUM_EMPLOYEES = {
    "min": 4,
    "max": 80,
    "step": 1,
    "value": 12,
}

# number of full time employees slider (value means default)
NUM_FULL_TIME = {
    "min": 0,
    "max": 9,
    "step": 1,
    "value": 8,
}

# max consecutive shifts slider (value means default)
MAX_CONSECUTIVE_SHIFTS = {
    "min": 1,
    "max": 14,
    "step": 1,
    "value": 5,
}

# example scenario labels (must have 4, first is custom scenario)
EXAMPLE_SCENARIO = ["Custom", "Small", "Medium", "Large"]

# default scenarios (don't change order of items)
SMALL_SCENARIO = {
    "num_employees": 12,
    "num_full_time": 8,
    "consecutive_shifts": 5,
    "shifts_per_employee": [5, 7],
}

MEDIUM_SCENARIO = {
    "num_employees": 20,
    "num_full_time": 14,
    "consecutive_shifts": 5,
    "shifts_per_employee": [5, 10],
}

LARGE_SCENARIO = {
    "num_employees": 40,
    "num_full_time": 25,
    "consecutive_shifts": 5,
    "shifts_per_employee": [5, 10],
}

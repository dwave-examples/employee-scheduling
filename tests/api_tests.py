import json
from api.app import generate_roster

employees = json.loads("""[
{
    "id": "pilot_1",
    "name": "Eddie",
    "job_function": "Captain",
    "qualifications": ["best", "great"],
    "availability": ["2024-05-01T08:00:00",
                    "2024-05-02T08:00:00",
                    "2024-05-03T08:00:00",
                    "2024-05-04T08:00:00",
                    "2024-05-05T08:00:00",
                    "2024-05-14T08:00:00",
                    "2024-05-15T08:00:00",
                    "2024-05-19T08:00:00",
                    "2024-05-20T08:00:00",
                    "2024-05-21T08:00:00",
                    "2024-05-22T08:00:00",
                    "2024-05-24T08:00:00",
                    "2024-05-25T08:00:00"],
    "non_availability": ["2024-05-29T08:00:00",
                    "2024-05-30T08:00:00",
                    "2024-05-31T08:00:00"],
    "experience_level": 5,
    "is_trainee": false,
    "must_pair_with": null
},
{
    "id": "pilot_2",
    "name": "Charlie",
    "job_function": "Pilot",
    "qualifications": ["best", "great"],
    "availability": ["2024-05-04T08:00:00",
                    "2024-05-19T08:00:00",
                    "2024-05-20T08:00:00",
                    "2024-05-21T08:00:00",
                    "2024-05-22T08:00:00",
                    "2024-05-24T08:00:00",
                    "2024-05-25T08:00:00"],
    "non_availability": ["2024-05-01T08:00:00",
                    "2024-05-02T08:00:00",
                    "2024-05-03T08:00:00"],
    "experience_level": 5,
    "is_trainee": false,
    "must_pair_with": null
},
{
    "id": "pilot_3",
    "name": "Robin",
    "job_function": "Pilot",
    "qualifications": ["best", "great"],
    "availability": [],
    "non_availability": ["2024-05-10T08:00:00"],
    "experience_level": 5,
    "is_trainee": false,
    "must_pair_with": null
},
{
    "id": "pilot_4",
    "name": "Alex",
    "job_function": "Pilot",
    "qualifications": ["best", "great"],
    "availability": [],
    "non_availability": [],
    "experience_level": 5,
    "is_trainee": false,
    "must_pair_with": null
},
{
    "id": "pilot_5",
    "name": "Kate",
    "job_function": "Pilot",
    "qualifications": ["best", "great"],
    "availability": [],
    "non_availability": [],
    "experience_level": 5,
    "is_trainee": false,
    "must_pair_with": null
},
{
    "id": "trainee_1",
    "name": "Rik",
    "job_function": "Trainee",
    "qualifications": ["best", "great"],
    "availability": ["2024-05-01T08:00:00",
                    "2024-05-02T08:00:00",
                    "2024-05-03T08:00:00",
                    "2024-05-04T08:00:00",
                    "2024-05-10T08:00:00",
                    "2024-05-11T08:00:00",
                    "2024-05-12T08:00:00",
                    "2024-05-13T08:00:00",
                    "2024-05-14T08:00:00",
                    "2024-05-15T08:00:00",
                    "2024-05-16T08:00:00",
                    "2024-05-19T08:00:00",
                    "2024-05-20T08:00:00",
                    "2024-05-21T08:00:00",
                    "2024-05-27T08:00:00",
                    "2024-05-28T08:00:00",
                    "2024-05-29T08:00:00",
                    "2024-05-30T08:00:00"],
    "non_availability": ["2024-05-05T08:00:00",
                        "2024-05-06T08:00:00"],
    "experience_level": 1,
    "is_trainee": true,
    "must_pair_with": "pilot_1"
    }
]""")

shift_templates = json.loads("""[{
    "id": "shift_1",
    "name": "day",
    "start_time": "07:00",
    "end_time": "20:59",
    "hours_to_count": 5,
    "number_required": 3,
    "job_function_required": "Captain",
    "qualification_required": "Requires Flying Licence",
    "experience_required": 2,
    "accept_trainee": true
}]
""")
#
# ,{
#     "id": "shift_2",
#     "name": "night",
#     "start_time": "21:00",
#     "end_time": "06:59",
#     "hours_to_count": 5,
#     "number_required": 2,
#     "job_function_required": "Captain",
#     "qualification_required": "Requires Flying Licence",
#     "experience_required": 2,
#     "accept_trainee": false
# }

generate_roster(employees, shift_templates, 5, 2024)
from datetime import datetime
import calendar
import pandas as pd

import utils
from api.endpoints.schedule import Employee
from employee_scheduling import build_cqm
from utils import MONTH

NOW = datetime.now()
NUM_DAYS_IN_MONTH = calendar.monthrange(NOW.year, MONTH or NOW.month)[1]


def build_sched(employees_list: [Employee], days_in_month):
    """Builds availability schedule for employees."""

    employees_names = []

    def get_avail_list(employees_list):
        avail = []
        for employee in employees_list:
            av_list = []
            for av_date in employee.availability:
                if av_date is not None:
                    av_list.append("")
            avail.append(av_list)

            if employee.is_trainee:
                employees_names.append(employee.name + "-Tr")
            else:
                employees_names.append(employee.name)

        return avail

    data = pd.DataFrame(
        get_avail_list(employees_list),
        columns=days_in_month,
    )

    data.insert(0, "Employee", employees_names)

    return data


def generate_roster(employees):
    days = [str(i + 1) for i in range(NUM_DAYS_IN_MONTH)]

    employees_list = []
    for employee in employees:
        employees_list.append(Employee.parse_obj(employee))

    sched_df = build_sched(employees_list, days).to_dict('records')

    rn = range(1, len(days) + 1)
    listOfNum = []
    for num in rn:
        listOfNum.append(str(num))
    print(listOfNum)

    shifts = listOfNum

    availability = utils.availability_to_dict(sched_df, shifts)
    print(availability)

    cqm = build_cqm(
        availability, shifts, 1, 6, 5, 16, True, False, 6
    )

    print(cqm.variables)

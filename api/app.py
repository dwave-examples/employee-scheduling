from datetime import datetime
import calendar
import pandas as pd

import utils
from api.endpoints.schedule import Employee, ShiftTemplate
from employee_scheduling import build_cqm

NOW = datetime.now()


def create_schedule_header(shift_names, days_in_month):
    header_names = []
    for day in days_in_month:
        for shift_name in shift_names:
            header_names.append(day + "-" + shift_name)
    return header_names


def build_sched(employees_list: [Employee], shift_names, days_in_month, full_sched_list):
    """Builds availability schedule for employees."""

    employees_names = []
    for employee in employees_list:
        if employee.is_trainee:
            employees_names.append(employee.name + "-Tr")
        elif employee.job_function == "Captain":
            employees_names.append(employee.name + "-Mgr")
        else:
            employees_names.append(employee.name)

    def get_avail_list(employees_list):
        avail = []
        for employee in employees_list:
            av_list = []
            for day in days_in_month:
                for shift_name in shift_names:
                    #TODO: Employee days_available may need to be adjusted for shifts_available.
                    # This part of the code could then ascertain whether the employee was available for a specific shift, not just the day and mark it accordingly
                    ticked = False
                    for av_date in employee.availability:
                        if int(day) == av_date.day:
                            av_list.append("P")
                            ticked = True
                    for non_av_date in employee.non_availability:
                        if int(day) == non_av_date.day:
                            av_list.append("X")
                            ticked = True
                    if not ticked:
                        av_list.append(None)
            avail.append(av_list)

        return avail

    data = pd.DataFrame(
        get_avail_list(employees_list),
        columns=full_sched_list,
    )

    data.insert(0, "Employee", employees_names)

    return data


def generate_roster(employees, shift_templates, month, year):

    NUM_DAYS_IN_MONTH = calendar.monthrange(year, month)[1]
    days = [str(i + 1) for i in range(NUM_DAYS_IN_MONTH)]
    manager = False

    employees_list = []
    for employee in employees:
        employees_list.append(Employee.parse_obj(employee))

    shifts_list = []
    for shift in shift_templates:
        shifts_list.append(ShiftTemplate.parse_obj(shift))
    shift_names = [shift.name for shift in shifts_list]

    # if "captain" in shifttemplate.job_function_required.lower():
    #     manager = True

    days_in_month = []
    for monthNum in range(1, len(days) + 1):
        days_in_month.append(str(monthNum))
    print("days in month:", days_in_month)

    full_sched_list = create_schedule_header(shift_names, days_in_month)

    sched_df = build_sched(employees_list, shift_names, days, full_sched_list).to_dict('records')

    availability = utils.availability_to_dict(sched_df, full_sched_list)
    print("availability:", availability)

    cqm = build_cqm(
        availability, full_sched_list, 1, 6,
        shift_min=shifts_list[0].number_required, shift_max=shifts_list[0].number_required,
        manager=manager, isolated=False, k=6
    )

    print("cqm vars:", cqm.constraint_labels)
    #run_cqm(cqm)
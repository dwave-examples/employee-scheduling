[![Open in GitHub Codespaces](
  https://img.shields.io/badge/Open%20in%20GitHub%20Codespaces-333?logo=github)](
  https://codespaces.new/dwave-examples/employee-scheduling?quickstart=1)
<!-- [![Linux/Mac/Windows build status](
  https://circleci.com/gh/dwave-examples/employee-scheduling.svg?style=shield)](
  https://circleci.com/gh/dwave-examples/employee-scheduling) -->

# Workforce Scheduling

Workforce scheduling is a common industry problem that often becomes complex
due to real-world constraints. This example demonstrates
a scheduling scenario with a variety of employees and rules.

![Screen Image](static/demo.png)

## Installation

You can run this example without installation in cloud-based IDEs that support the
[Development Containers specification](https://containers.dev/supporting) (aka "devcontainers")
such as GitHub Codespaces.

For development environments that do not support `devcontainers`, install requirements:

```bash
pip install -r requirements.txt
```

If you are cloning the repo to your local system, working in a
[virtual environment](https://docs.python.org/3/library/venv.html) is recommended.

## Usage

Your development environment should be configured to access the
[Leap&trade; Quantum Cloud Service](https://docs.ocean.dwavesys.com/en/stable/overview/sapi.html).
You can see information about supported IDEs and authorizing access to your Leap account
[here](https://docs.dwavesys.com/docs/latest/doc_leap_dev_env.html).

Run the following terminal command to start the Dash app:

```bash
python app.py
```

Access the user interface with your browser at http://127.0.0.1:8050/.

The demo program opens an interface where you can configure problems and submit these problems to
a solver.

Configuration options can be found in the [demo_configs.py](demo_configs.py) file.

> [!NOTE]\
> If you plan on editing any files while the app is running,
please run the app with the `--debug` command-line argument for live reloads and easier debugging:
`python app.py --debug`

## Problem Description

The employee availability chart shows employee shift preferences and unavailable
days (PTO). Requested shifts are in teal and marked with a '✓', while
unavailable shifts are in orange and marked with an 'x'.

In the chart, there are three different types of employees.

- Managers: These are employees with 'Mgr' at the end of their name.
- Employees: These are employees with no tag at the end of their name.
- Trainees: These are employees with 'Tr' at the end of their name. The trainee
  has the same name as their trainer. The trainee can **only** be scheduled to
  work on a shift that their trainer is also scheduled to work.

The chart displays employee preferences and availability over two weeks. It will
always display two weeks starting two Sundays from now, with one column for each day of the two week period.

A subset of the employees have requested full-time schedules which consists of 5 days on,
2 days off, and is one of three options: Monday-Friday, Tuesday-Saturday, Sunday-Wednesday.

### Inputs

The scenario preset auto-populates all settings with scenarios of varying
sizes. If 'Custom' is selected, the following settings become available:

- Number of employees: Schedules always include 2 managers and 1 trainee.
- Number of full-time employees: The subset of the employees that have requested a 5 days on,
2 days off schedule.
- Max consecutive shifts: The maximum number of consecutive shifts an employee
  can be scheduled before a day off must be scheduled.
- Min/max shifts per part-time employee: This range determines the number of shifts an
  employee can work.
- Forecast: This determines how many employees are needed per day.
- Allow isolated days off: If unchecked, employees must be
  scheduled for at least two consecutive days off between work days.

### Outputs

Once the problem has completed, the best solution returned is displayed in
the "Scheduled Shifts" tab.

The solution returned is either the best feasible solution (if a feasible
solution is found) or the best infeasible solution (if no feasible solution is
found). If an infeasible solution is found, a collapsible error bar will show
on the right side of the demo with more information about what makes the solution
infeasible.

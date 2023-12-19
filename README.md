[![Open in GitHub Codespaces](
  https://img.shields.io/badge/Open%20in%20GitHub%20Codespaces-333?logo=github)](
  https://codespaces.new/dwave-examples/employee-scheduling?quickstart=1)
<!-- [![Linux/Mac/Windows build status](
  https://circleci.com/gh/dwave-examples/employee-scheduling.svg?style=shield)](
  https://circleci.com/gh/dwave-examples/employee-scheduling) -->

# Employee Scheduling Demo

Employee scheduling is a common industry problem that can often become complex
due to real-world constraints and requirements. In this example, we demonstrate
a scheduling scenario with a variety of employees and rules.

## Running the Demo

To run the demo, open the terminal and run `python app.py`. Open a web browser
and copy the URL from the terminal to load the demo in the browser.

Once we have set all of the options to our satisfaction, click the "Solve CQM"
button on the left. In the terminal we see status updates for "Building CQM..."
and "Submitting CQM...".

Once the problem has completed, the best solution returned will be displayed in
place of "Employee Availability". Click back to the original availability using
the tabs at the top of the schedule card.

The solution returned will be either the best feasible solution (if a feasible
solution is found) or the best infeasible solution (if no feasible solution is
found). If an infeasible solution is found, scrolling down will show the list of
constraints that were violated.

## Introducing the Demo

When the demo opens in the web browser, there are a few options on the left and
a chart of employee availability in the center.

![Screen Image](assets/demo_image.png)

### Employee Availability

The employee availability chart shows employee shift preferences and unavailable
days (PTO). Preferred shifts are in teal and marked with a 'P', while
unavailable shifts are in organe and marked with an 'X'.

In the chart, there are three different types of employees.

- Managers: These are employees with 'Mgr' at the end of their name.
- Employees: These are employees with no tag at the end of their name.
- Trainees: These are employees with 'Tr' at the end of their name. The trainee
  has the same name as their trainer. The trainee can **only** be scheduled to
  work on a shift that their trainer is also scheduled to work.

The chart displays employee preferences and availability for this month. It will
always display the current month, with one column for each day in this current
month.

### Options

Always available are three options.

- Number of employees: Pretty self-explanatory. We will always have 2 managers
  and 1 trainee.
- Random seed: Optional; included for consistency when giving live demos.
- Autofill scenario: Auto-populates all settings to provide scenarios of varying
  sizes that will produce feasible solutions.

There is also a collapsible menu of additional options. These additional options
include:

- Allow isolated days off: Unchecked, this option means that no employee can
  have a stand-alone day off. Every day off must be at least two consecutive
  days.
- Require a manager on every shift: Checked, this option means that every shift
  must have exactly one manager on duty to supervise.
- Min/max shifts per employee: The range that determines the number of shifts an
  employee can work in the month.
- Min/max employees per shift: The range that determines how many employees need
  to be assigned to each shift.
- Max consecutive shifts: The maximum number of shifts in a row that an employee
  can be scheduled before they need to have a day off.

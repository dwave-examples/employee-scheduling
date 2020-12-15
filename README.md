[![Linux/Mac/Windows build status](
  https://circleci.com/gh/dwave-examples/employee-scheduling.svg?style=svg)](
  https://circleci.com/gh/dwave-examples/employee-scheduling)

# Building an Employee Schedule

Building a schedule for employees can be an extremely complex optimization
problem in which managers must balance employee preferences against schedule
requirements. In this example, we show how a discrete quadratic model (DQM) can
be used to model this problem and how the new hybrid DQM solver available in
Leap can optimize over these competing scheduling and preference needs.

## Usage

To run the demo, type the command:

```python scheduler.py```

A prompt will appear asking for the number of employees:

```Enter number of employees:```

Type the number of employees to be considered and hit `Enter`. Note that the
DQM solver can take up to 5000 variables, or employees for this problem.

A second prompt for the number of shifts will appear:

```Enter number of shifts:```

Type the number of shifts and hit `Enter`. Note that we should have at least as
many employees as there are shifts.

Once these values have been entered, the program will randomly generate employee
preferences for the N shifts from most preferred (0) to least preferred (N-1). A
DQM is constructed (see below for details) and the problem is run using
`LeapHybridDQMSampler`.

Once the problem has run, two images are created. First, `employee_schedule.png`
illustrates the employee preference matrix alongside the schedule built.
Second, `schedule_statistics.png` shows how many employees are scheduled for
each shift, alongside a bar chart showing the employees' average preferences
for the shifts for which they have been scheduled.

## Building the DQM

The employee scheduling problem consists of two components: a requirement that
employees are evenly distributed across all shifts, and a goal to satisfy
employees by scheduling them for their preferred shifts.

### Preferred Shifts

Since shift preferences are ranked from most preferred (smallest value) to
least preferred (largest value), the rankings can be used for the linear biases
in the DQM.  Since the DQM solver looks for minimum energy solutions, and
minimum rank corresponds to most preferred, these naturally align.

### Even Distribution

An even distribution of employees across shifts would have approximately
`num_employees/num_shifts` scheduled employees per shift. To enforce this
requirement, both linear and quadratic biases must be adjusted in a specific
manner.

To determine the linear and quadratic bias adjustments, we must consider the
underlying binary variables in our DQM. For a DQM with N shifts and M employees,
each employee has a single variable constructed with N cases or classes. These
are implemented as N binary variables per employee &mdash; one for each possible
shift.

For a specific shift `i`, we require that exactly `M/N` employees are scheduled.
This is equivalent to saying that `M/N` employee variables are assigned case
`i`, or, returning to our binary variables, that `M/N` of the binary variables
corresponding to case `i` take a value of 1. In other words, the sum of *all*
employee case `i` binary variables should equal `M/N`. An equality over a
summation of binary variables can be converted to a minimization expression by
moving from the equality:

```sum(shift i binary variables) = M/N```

to a minimization expression:

```min( ( sum(shift i binary variables) - M/N)**2 )```

Expanding and simplifying this expression of binary variables, it becomes:

```min( (-2*M/N+1)*sum(shift i linear biases) + 2*sum(shift i quadratic biases))```

When this constraint is built into our DQM object, it is added in with a
coefficient `gamma`.  This term gamma is known as a Lagrange parameter and can
be used to weight this constraint against the competing employee preferences.
You may wish to adjust this parameter depending on your problem requirements and
size. The value set here in this program was chosen to empirically work well as
a starting point for problems of a wide-variety of sizes. For more information
on setting this parameter, see D-Wave's [Problem Formulation Guide](https://www.dwavesys.com/practical-quantum-computing-developers).

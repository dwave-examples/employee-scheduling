# Building an Employee Schedule

Building a schedule for employees can be an extremely complex optimization problem in which managers must balance employee preferences against schedule requirements. In this example, we show how a discrete quadratic model (DQM) can be used to model this problem and how D-Wave's DQM solver can optimize over these competing requirements.

## Usage

To run the demo, type the command: 

```python scheduler.py```

A prompt will appear asking for the number of employees:

```Enter number of employees:```

Type the number of employees to be considered and hit `Enter`. A second prompt for the number of shifts will appear:

```Enter number of shifts:```

Type the number of shifts and hit `Enter`.

Once these values have been entered, the program will randomly generate employee preferences for the N shifts from most preferred (0) to least preferred (N). A DQM is constructed (see below for details) and the problem is run using `LeapHybridDQMSampler`. 

Once the problem has run, two images are created. First, `employee_schedule.png` illustrate the employee preference matrix alongside the schedule built.  Second, `schedule_statistics.png` shows how many employees are scheduled for each shift, alongside a bar chart showing the employees' preferences for the shifts for which they have been scheduled.

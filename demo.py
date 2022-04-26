# Copyright 2022 D-Wave Systems Inc.
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

from dimod import ConstrainedQuadraticModel, Binary, quicksum
from dwave.system import LeapHybridCQMSampler
import numpy as np
import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt

# Collect user input on size of problem
response_1 = input("\nEnter number of employees > ")
try:
    num_employees = int(response_1)
except ValueError:
    print("Must input an integer.")
    num_employees = int(input("\nEnter number of employees > "))

response_2 = input("\nEnter number of shifts > ")
try:
    num_shifts = int(response_2)
except ValueError:
    print("Must input an integer.")
    num_shifts = int(input("\nEnter number of shifts > "))

if num_employees < num_shifts:
    print("\n**Number of employees must be at least number of shifts.**")

    print("\nEnter number of employees:")
    num_employees = int(input())
    print("\nEnter number of shifts:")
    num_shifts = int(input())

print("\nScheduling", num_employees, "employees over", num_shifts, "shifts...\n")

# Generate random array of preferences over employees
preferences = np.tile(np.arange(num_shifts), (num_employees, 1))
rows = np.indices((num_employees,num_shifts))[0]
cols = [np.random.permutation(num_shifts) for _ in range(num_employees)]
preferences = preferences[rows, cols]

# Initialize the CQM object
cqm = ConstrainedQuadraticModel()

# Build the CQM starting by creating variables
vars = [[Binary(f'x_{name}_{i}') for i in range(num_shifts)] for name in range(num_employees)]

# Add constraint to make variables discrete
for v in range(len(vars)):
    cqm.add_discrete([f'x_{v}_{i}' for i in range(num_shifts)])

# Objective: maximize employee preference (choose shifts with lower preference numbers)
obj = quicksum([preferences[j,i]*vars[j][i] for j in range(num_employees) for i in range(num_shifts)])
cqm.set_objective(obj)

# Constraint: equal number of employees per shift
num_per_shift = int(num_employees/num_shifts)
for i in range(num_shifts):
    cst = quicksum([vars[j][i] for j in range(num_employees)])
    cqm.add_constraint(cst == num_per_shift, label=f'c_{i}')

# Initialize the CQM solver
sampler = LeapHybridCQMSampler()

# Solve the problem using the DQM solver
sampleset = sampler.sample_cqm(cqm, label='Example - Employee Scheduling')

# Get the first feasible solution
feasible_sampleset = sampleset.filter(lambda d: d.is_feasible)
if len(feasible_sampleset) == 0:
    print("\nNo feasible solution found. Returning best infeasible solution.")
    sample = sampleset.first.sample
    energy = sampleset.first.energy 
else:
    sample = feasible_sampleset.first.sample
    energy = feasible_sampleset.first.energy
print("\nSchedule score:", energy)

# Build schedule
schedule = np.ones((num_employees, num_shifts))*num_shifts
prefs = [0]*num_shifts
shifts = [0]*num_shifts
for key, val in sample.items():
    if val == 1:
        v = key.split("_")
        emp = int(v[1])
        shft = int(v[2])
        schedule[emp,shft]=preferences[emp,shft]
        prefs[preferences[emp,shft]] += 1
        shifts[shft] += 1

# Show heatmap of preferences
cmap = plt.get_cmap('seismic')
cmaplist = [cmap(i) for i in range(cmap.N)]
cmaplist[-1] = (1.0,1.0,1.0,1.0)
cmap = cmap.from_list('Custom cmap', cmaplist, cmap.N)

fig, (ax1, ax2) = plt.subplots(1, 2)
ax1.imshow(preferences, cmap='seismic', interpolation='nearest', vmin=0, vmax=num_shifts, aspect='auto')
ax1.xlabel = 'Shifts'
ax1.ylabel = 'Employees'
ax1.set_title("Employee Shift Preferences", color='Black', fontstyle='italic')

# Show heatmap of schedule
cax = ax2.imshow(schedule, cmap=cmap, interpolation='nearest', aspect='auto', vmin=0)
cbar = fig.colorbar(cax, ticks=[0, num_shifts])
cbar.set_ticklabels(['Best', 'Worst'])
ax2.xlabel = 'Shifts'
ax2.set_title("Employee Shift Schedule", color='Black', fontstyle='italic')
plt.savefig("employee_schedule.png")

# Compute/display schedule statistics
plt.clf()
plt.subplot(1, 2, 1)
plt.bar(np.arange(num_shifts), shifts)
plt.xlabel("Shift")
plt.ylabel("Number Scheduled")
plt.title("Employees Scheduled Per Shift")

mean_happiness = sum([i*prefs[i] for i in range(num_shifts)])/num_employees
print("\nAverage happiness:\t", mean_happiness)

plt.subplot(1, 2, 2)
plt.bar(np.arange(num_shifts), prefs)
plt.xlabel("Preference Rank")
plt.title("Average Preference per Shift")
plt.savefig("schedule_statistics.png")

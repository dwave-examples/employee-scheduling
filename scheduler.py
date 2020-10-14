# Copyright 2020 D-Wave Systems Inc.
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

from dimod import DiscreteQuadraticModel
from dwave.system import LeapHybridDQMSampler
import numpy as np
from matplotlib import pyplot as plt

# Collect user input on size of problem
print("\nEnter number of employees:")
num_employees = int(input())
print("\nEnter number of shifts:")
num_shifts = int(input())

if num_employees <= num_shifts:
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

# Initialize the DQM object
dqm = DiscreteQuadraticModel()

# Build the DQM starting by adding variables
for name in range(num_employees):
    dqm.add_variable(num_shifts, label=name)

# Distribute employees equally across shifts according to preferences
num_per_shift = int(num_employees/num_shifts)
gamma = 1/(num_employees*num_shifts)

for i in range(num_shifts):
    for j in range(num_employees):
        dqm.set_linear_case(j, i, dqm.get_linear_case(j, i) - gamma*(2*num_per_shift+1))
        for k in range(j+1, num_employees):
            dqm.set_quadratic_case(j, i, k, i, gamma*(dqm.get_quadratic_case(j, i, k, i) + 2))

# Initialize the DQM solver
sampler = LeapHybridDQMSampler()

# Solve the problem using the DQM solver
sampleset = sampler.sample_dqm(dqm)

# Get the first solution, and print it
sample = sampleset.first.sample
energy = sampleset.first.energy
print("\nSchedule score:", energy)

# Build schedule
schedule = np.ones((num_employees, num_shifts))*num_shifts
prefs = [0 for _ in range(num_shifts)]
shifts = [0 for _ in range(num_shifts)]
for key, val in sample.items():
    schedule[key,val]=preferences[key,val]
    prefs[preferences[key,val]] += 1
    shifts[val] += 1

# Show heatmap of preferences
cmap = plt.get_cmap('CMRmap')
cmaplist = [cmap(i) for i in range(cmap.N)]
cmaplist[-1] = (1.0,1.0,1.0,1.0)
cmap = cmap.from_list('Custom cmap', cmaplist, cmap.N)

fig, (ax1, ax2) = plt.subplots(1, 2)
ax1.imshow(preferences, cmap='CMRmap', interpolation='nearest', vmin=0, vmax=num_shifts, aspect='auto')
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
plt.title("Average Preference Scheduled")
plt.savefig("schedule_statistics.png")
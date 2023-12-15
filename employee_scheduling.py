from dimod import (
    Binary,
    BinaryQuadraticModel,
    ConstrainedQuadraticModel,
    quicksum,
)
from dwave.system import LeapHybridCQMSampler


def build_cqm(
    availability,
    shifts,
    min_shifts,
    max_shifts,
    shift_min,
    shift_max,
    manager,
    isolated,
    k,
):
    cqm = ConstrainedQuadraticModel()
    employees = [key for key in availability.keys()]

    # Create variables: one per employee per shift
    x = {(i, j): Binary(i + "_" + j) for j in shifts for i in employees}

    # Objective: give employees preferred schedules (val = 2)
    obj = BinaryQuadraticModel(vartype="BINARY")
    for e in employees:
        sched = availability[e]
        for s in range(len(shifts)):
            if sched[s] == 2:
                obj += -x[e, shifts[s]]

    # Objective: for infeasible solutions, focus on right number of shifts for employees
    num_s = (min_shifts + max_shifts) / 2
    for e in employees:
        obj += (
            quicksum(x[e, shifts[s]] for s in range(len(shifts))) - num_s
        ) ** 2
    cqm.set_objective(obj)

    # Only schedule employees when they're available
    for e in employees:
        sched = availability[e]
        for s in range(len(shifts)):
            if sched[s] == 0:
                cqm.add_constraint(x[e, shifts[s]] == 0, label=f"0{e} on {s}")

    # Schedule employees for at most max_shifts
    for e in employees:
        cqm.add_constraint(
            quicksum(x[e, shifts[s]] for s in range(len(shifts)))
            <= max_shifts,
            label=f"1{e} has too many shifts",
        )

    # Schedule employees for at least min_shifts
    for e in employees:
        cqm.add_constraint(
            quicksum(x[e, shifts[s]] for s in range(len(shifts)))
            >= min_shifts,
            label=f"2{e} doesn't have enough shifts",
        )

    # Every shift needs shift_min and shift_max employees working
    for s in range(len(shifts)):
        cqm.add_constraint(
            sum(x[e, shifts[s]] for e in employees) >= shift_min,
            label=f"3{shifts[s]} understaffed",
        )
        cqm.add_constraint(
            sum(x[e, shifts[s]] for e in employees) <= shift_max,
            label=f"4{shifts[s]} overstaffed",
        )

    # Days off are consecutive
    if not isolated:
        # middle range shifts - pattern 101 penalized
        for s in range(len(shifts) - 2):
            for e in employees:
                cqm.add_constraint(
                    -3 * x[e, shifts[s + 1]]
                    + x[e, shifts[s]] * x[e, shifts[s + 1]]
                    + x[e, shifts[s + 1]] * x[e, shifts[s + 2]]
                    + x[e, shifts[s]] * x[e, shifts[s + 2]]
                    <= 0,
                    label=f"5aDay off {shifts[s+1]} is isolated for {e}",
                )
        # end shifts - patterns 01 at start and 10 at end penalized
        for e in employees:
            cqm.add_constraint(
                x[e, shifts[1]] - x[e, shifts[0]] <= 0,
                label=f"5bDay off {shifts[0]} is isolated for {e}",
            )
            cqm.add_constraint(
                x[e, shifts[-2]] - x[e, shifts[-1]] <= 0,
                label=f"5cDay off {shifts[-1]} is isolated for {e}",
            )

    # Require a manager on every shift
    if manager:
        mgr_list = [e for e in employees if e[-3:] == "Mgr"]
        for s in range(len(shifts)):
            cqm.add_constraint(
                quicksum(x[m, shifts[s]] for m in mgr_list) == 1,
                label=f"6Issue on {shifts[s]}",
            )

    # No k shifts consecutive
    for e in employees:
        for s in range(len(shifts) - k + 1):
            cqm.add_constraint(
                quicksum([x[e, shifts[s + i]] for i in range(k)]) <= k - 1,
                label=f"7Employee {e} starting with {shifts[s]}",
            )

    # Trainee must work on shifts with trainer
    tr_list = [e for e in employees if e[-2:] == "Tr"]
    for s in range(len(shifts)):
        cqm.add_constraint(
            x[tr_list[0], shifts[s]]
            - x[tr_list[0], shifts[s]] * x[tr_list[0][:-3], shifts[s]]
            == 0,
            label=f"8Trainee scheduling issue on {shifts[s]}",
        )

    # print(cqm)

    return cqm


def run_cqm(cqm):
    sampler = LeapHybridCQMSampler()

    sampleset = sampler.sample_cqm(cqm)
    feasible_sampleset = sampleset.filter(lambda row: row.is_feasible)

    num_feasible = len(feasible_sampleset)
    errors = " "
    if num_feasible == 0:
        msg = "\nNo feasible solution found.\n"
        errors += msg
        print(msg)
        sat_array = sampleset.first.is_satisfied
        constraints = sampleset.info["constraint_labels"]
        for i in range(len(sat_array)):
            if sat_array[i] is False:
                c = constraints[i]
                if c[0] == "0":
                    msg = (
                        "\n- Employee scheduled when unavailable: "
                        + constraints[i][1:]
                    )
                    errors += msg
                    print(msg)
                elif c[0] == "1":
                    msg = (
                        "\n- Employee scheduled overtime: "
                        + constraints[i][1:]
                    )
                    errors += msg
                    print(msg)
                elif c[0] == "2":
                    msg = (
                        "\n- Employee scheduled undertime: "
                        + constraints[i][1:]
                    )
                    errors += msg
                    print(msg)
                elif c[0] == "3":
                    msg = "\n- Shift understaffed: " + constraints[i][1:]
                    errors += msg
                    print(msg)
                elif c[0] == "4":
                    msg = "\n- Shift overstaffed: " + constraints[i][1:]
                    errors += msg
                    print(msg)
                elif c[0] == "5":
                    msg = "\n- Isolated shift: " + constraints[i][2:]
                    errors += msg
                    print(msg)
                elif c[0] == "6":
                    msg = "\n- Shift manager issue: " + constraints[i][1:]
                    errors += msg
                    print(msg)
                elif c[0] == "7":
                    msg = (
                        "\n- Too many consecutive shifts: "
                        + constraints[i][1:]
                    )
                    errors += msg
                    print(msg)
                elif c[0] == "8":
                    msg = "\n- " + constraints[i][1:]
                    errors += msg
                    print(msg)
        return sampleset, errors

    print("\nFeasible solution found.\n")

    return feasible_sampleset, None

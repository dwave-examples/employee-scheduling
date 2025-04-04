# Copyright 2024 D-Wave
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
import unittest
from dataclasses import asdict

from dash import dash_table
from numpy import asarray

import src.employee_scheduling as employee_scheduling
import src.utils as utils
from demo_callbacks import display_initial_schedule


class TestDemo(unittest.TestCase):
    # Initialize shared data for tests
    def setUp(self):
        self.num_employees = 12
        self.sched_df = display_initial_schedule(self.num_employees, 6)[0].data
        self.shifts = list(self.sched_df[0].keys())
        self.shifts.remove("Employee")
        self.availability = utils.availability_to_dict(self.sched_df)
        self.test_params = utils.ModelParams(
            availability=self.availability,
            shifts=self.shifts,
            min_shifts=5,
            max_shifts=10,
            shift_forecast=[9, 8, 8, 8, 8, 8, 9, 9, 8, 8, 8, 8, 8, 9],
            allow_isolated_days_off=False,
            max_consecutive_shifts=6,
            num_full_time=6
        )

    # Check that initial schedule created is the right size
    def test_initial_sched(self):
        self.assertEqual(len(self.sched_df), self.num_employees)

    # Check that CQM created has the right number of variables
    def test_cqm(self):
        cqm = employee_scheduling.build_cqm(**asdict(self.test_params))

        self.assertEqual(len(cqm.variables), self.num_employees * len(self.shifts))

    # Check that NL assignments variable is the correct shape
    def test_nl(self):
        _, assignments = employee_scheduling.build_nl(**asdict(self.test_params))

        self.assertEqual(assignments.shape(), (self.num_employees, len(self.shifts)))

    def test_samples_cqm(self):
        shifts = [str(i + 1) for i in range(5)]
        shift_forecast = [5] * 14

        # Make every employee available for every shift
        availability = {
            "A-Mgr": [1] * 5,
            "B-Mgr": [1] * 5,
            "C": [1] * 5,
            "D": [1] * 5,
            "E": [1] * 5,
            "E-Tr": [1] * 5,
        }

        test_params = utils.ModelParams(
            availability=availability,
            shifts=shifts,
            min_shifts=1,
            max_shifts=6,
            shift_forecast=shift_forecast,
            allow_isolated_days_off=False,
            max_consecutive_shifts=6,
            num_full_time=0
        )

        cqm = employee_scheduling.build_cqm(**asdict(test_params))

        feasible_sample = {
            "A-Mgr_1": 0.0,
            "A-Mgr_2": 0.0,
            "A-Mgr_3": 1.0,
            "A-Mgr_4": 1.0,
            "A-Mgr_5": 1.0,
            "B-Mgr_1": 1.0,
            "B-Mgr_2": 1.0,
            "B-Mgr_3": 0.0,
            "B-Mgr_4": 0.0,
            "B-Mgr_5": 0.0,
            "C_1": 1.0,
            "C_2": 1.0,
            "C_3": 1.0,
            "C_4": 1.0,
            "C_5": 1.0,
            "D_1": 1.0,
            "D_2": 1.0,
            "D_3": 1.0,
            "D_4": 1.0,
            "D_5": 1.0,
            "E-Tr_1": 1.0,
            "E-Tr_2": 1.0,
            "E-Tr_3": 1.0,
            "E-Tr_4": 1.0,
            "E-Tr_5": 1.0,
            "E_1": 1.0,
            "E_2": 1.0,
            "E_3": 1.0,
            "E_4": 1.0,
            "E_5": 1.0,
        }

        infeasible_sample = {
            "A-Mgr_1": 1.0,
            "A-Mgr_2": 1.0,
            "A-Mgr_3": 1.0,
            "A-Mgr_4": 1.0,
            "A-Mgr_5": 1.0,
            "B-Mgr_1": 1.0,
            "B-Mgr_2": 1.0,
            "B-Mgr_3": 1.0,
            "B-Mgr_4": 1.0,
            "B-Mgr_5": 1.0,
            "C_1": 1.0,
            "C_2": 1.0,
            "C_3": 1.0,
            "C_4": 1.0,
            "C_5": 1.0,
            "D_1": 1.0,
            "D_2": 1.0,
            "D_3": 1.0,
            "D_4": 1.0,
            "D_5": 1.0,
            "E-Tr_1": 1.0,
            "E-Tr_2": 1.0,
            "E-Tr_3": 1.0,
            "E-Tr_4": 1.0,
            "E-Tr_5": 1.0,
            "E_1": 1.0,
            "E_2": 1.0,
            "E_3": 1.0,
            "E_4": 1.0,
            "E_5": 1.0,
        }

        self.assertTrue(cqm.check_feasible(feasible_sample))
        self.assertFalse(cqm.check_feasible(infeasible_sample))

    def test_states_nl(self):
        shifts = [str(i + 1) for i in range(5)]

        # Make every employee available for every shift
        availability = {
            "A-Mgr": [1] * 5,
            "B-Mgr": [1] * 5,
            "C": [1] * 5,
            "D": [1] * 5,
            "E": [1] * 5,
            "E-Tr": [1] * 5,
        }

        test_params = utils.ModelParams(
            availability=availability,
            shifts=shifts,
            min_shifts=1,
            max_shifts=6,
            shift_forecast=[5]*5,
            allow_isolated_days_off=False,
            max_consecutive_shifts=6,
            num_full_time=0
        )

        model, assignments = employee_scheduling.build_nl(**asdict(test_params))

        if not model.is_locked():
            model.lock()

        # Resize model states
        model.states.resize(2)

        feasible_state = [
            [0, 0, 1, 1, 1],  # A-Mgr
            [1, 1, 0, 0, 0],  # B-Mgr
            [1, 1, 1, 1, 1],  # C
            [1, 1, 1, 1, 1],  # D
            [1, 1, 1, 1, 1],  # E
            [1, 1, 1, 1, 1],  # E-Tr
        ]

        # Infeasible: multiple managers scheduled for the same shift
        infeasible_state = [
            [1, 1, 1, 1, 1],  # A-Mgr
            [1, 1, 1, 1, 1],  # B-Mgr
            [1, 1, 1, 1, 1],  # C
            [1, 1, 1, 1, 1],  # D
            [1, 1, 1, 1, 1],  # E
            [1, 1, 1, 1, 1],  # E-Tr
        ]

        # Assign feasible state to index 0
        assignments.set_state(0, feasible_state)
        # Assign infeasible state to index 1
        assignments.set_state(1, infeasible_state)

        constraints_0 = [int(c.state(0)) for c in model.iter_constraints()]
        constraints_1 = [int(c.state(1)) for c in model.iter_constraints()]

        self.assertEqual(len(constraints_0), sum(constraints_0))
        self.assertGreater(len(constraints_1), sum(constraints_1))

    def test_build_from_sample(self):
        employees = ["A-Mgr", "B-Mgr", "C", "D", "E", "E-Tr"]

        # Make every employee available for every shift
        availability = {
            "A-Mgr": [1] * 14,
            "B-Mgr": [1] * 14,
            "C": [1] * 14,
            "D": [1] * 14,
            "E": [1] * 14,
            "E-Tr": [1] * 14,
        }

        sample = {
            "A-Mgr_1": 0.0,
            "A-Mgr_2": 0.0,
            "A-Mgr_3": 1.0,
            "A-Mgr_4": 1.0,
            "A-Mgr_5": 1.0,
            "B-Mgr_1": 1.0,
            "B-Mgr_2": 1.0,
            "B-Mgr_3": 0.0,
            "B-Mgr_4": 0.0,
            "B-Mgr_5": 0.0,
            "C_1": 1.0,
            "C_2": 1.0,
            "C_3": 1.0,
            "C_4": 1.0,
            "C_5": 1.0,
            "D_1": 1.0,
            "D_2": 1.0,
            "D_3": 1.0,
            "D_4": 1.0,
            "D_5": 1.0,
            "E-Tr_1": 1.0,
            "E-Tr_2": 1.0,
            "E-Tr_3": 1.0,
            "E-Tr_4": 1.0,
            "E-Tr_5": 1.0,
            "E_1": 1.0,
            "E_2": 1.0,
            "E_3": 1.0,
            "E_4": 1.0,
            "E_5": 1.0,
        }

        disp_datatable = utils.display_schedule(
            utils.build_schedule_from_sample(sample, employees),
            availability,
        )

        # This should verify we don't have any issues in the object created for display from a sample
        self.assertEqual(type(disp_datatable), dash_table.DataTable)

    def test_build_from_state(self):
        employees = ["A-Mgr", "B-Mgr", "C", "D", "E", "E-Tr"]
        shifts = [str(i + 1) for i in range(14)]

        # Make every employee available for every shift
        availability = {
            "A-Mgr": [1] * 14,
            "B-Mgr": [1] * 14,
            "C": [1] * 14,
            "D": [1] * 14,
            "E": [1] * 14,
            "E-Tr": [1] * 14,
        }

        state = asarray(
            [
                # Give managers alternating shifts
                [i % 2 for i in range(14)],
                [(i + 1) % 2 for i in range(14)],
                [1 for _ in range(14)],
                [1 for _ in range(14)],
                [1 for _ in range(14)],
                [1 for _ in range(14)],
            ]
        )

        disp_datatable = utils.display_schedule(
            utils.build_schedule_from_state(state, employees, shifts), availability
        )

        self.assertIsInstance(disp_datatable, dash_table.DataTable)

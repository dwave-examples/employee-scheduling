from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()


class Employee(BaseModel):
    id: str
    name: str
    job_function: str
    qualifications: list[str]
    availability: list[datetime]
    non_availability: list[datetime]
    experience_level: int
    is_trainee: bool
    must_pair_with: str | None


class ShiftTemplate(BaseModel):
    id: str
    name: str
    start_time: datetime
    end_time: datetime
    hours_to_count: int
    number_required: int
    job_function_required: str
    qualification_required: str
    experience_required: int
    accept_trainee: bool


class ShiftPattern(BaseModel):
    name: str
    shifts: list[str]


class Fatigue(BaseModel):
    rule_id: str
    configuration: tuple[int, int]


class Pairing(BaseModel):
    acceptable_job_function_pairings: list[tuple[str, str]]
    acceptable_experience_level_minimum: int


@app.post("/employees")
async def employees(employees: list[Employee]):
    app.state.employees = employees
    return employees


@app.post("/shift_template")
async def shift_template(shift_template: ShiftTemplate):
    app.state.shift_template = shift_template
    return shift_template


@app.post("/shift_pattern")
async def shift_pattern(shift_pattern: ShiftPattern):
    app.state.shift_pattern = shift_pattern
    return shift_pattern


@app.post("/constraint/fatigue")
async def constraint_fatigue(fatigue: Fatigue):
    app.state.fatigue = fatigue
    return fatigue


@app.post("/constraint/pairing")
async def constraint_pairing(pairing: Pairing):
    app.state.pairing = pairing
    return pairing


# @app.post("/generate")
# async def generate():
#     print("Generating roster")
#     # employees (all, or list)
#     # target (from - to)
#     # desired_pattern (shift pattern id or null)
#     # only_return_feasilble_solutions (true or false)

# @app.post("/generate")
# async def generate():
#     print("Generating roster")
#     #return app.state.employees, app.state.shift_template, app.state.shift_pattern
#

@app.get("/employees")
async def get_employees():
    return app.state.employees


@app.get("/shift_template")
async def get_shift_template():
    return app.state.shift_template


@app.get("/shift_pattern")
async def get_shift_pattern():
    return app.state.shift_pattern
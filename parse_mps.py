# Another fun parsing session
# We're going to parse mp files to pyomo
from enum import Enum
from pyomo.kernel import *
from collections import defaultdict

# Note to future self, we're going to do this as ugly and fast as possible to start with
# Completely going for pure filth to just get this done asap.
# TODO[michaelr]: Come back at some point in the future and make this sane

file_name = r"/Users/michaelradigan/pyomosymmetry/mps/enlight9.mps"


class State(Enum):
    START = 1,
    NAME = 2
    ROWS = 3,
    COLUMNS = 4,
    RHS = 5,
    BOUNDS = 6,


class ConstraintType(Enum):
    E = 1,
    G = 2,
    L = 3,
    N = 4


# Dictionary from constraintname to a linear_constraint as defined by the the ROWS section
# If a constraint is not mentioned in the RHS section then it takes a RHS value of 0 so we will use that as our default
constraints = {}

# constraint_count is used to keep track of the index of each constraint
constraint_count = 0

# counts = Counts()

# dictionary from variable name to a variable. Note that variables in MPs are from 0 to +inf by default
variables = defaultdict(lambda: variable(lb=0, ub=None))


def parse_row(line):
    constrainttype, name = map(str.strip, line.split())

    # This is a bit shit, yes, but we'er just trying to get something to work quickly
    if constrainttype == "E":
        constraint = linear_constraint(
            variables=[], coefficients=[], terms=None, lb=0, ub=0)
        constraints[name] = (constraint, ConstraintType.E)
    elif constrainttype == "G":
        # TODO[michaelr]: We need a way of representing that the lower bound here is finite??
        # Or is it the case that a valid model will always provode the bound?
        # Similar question to answer for G
        constraint = linear_constraint(
            variables=[], coefficients=[], terms=None,  ub=None)
        constraints[name] = (constraint, ConstraintType.G)
    elif constrainttype == "L":
        constraint = linear_constraint(
            variables=[], coefficients=[], terms=None, lb=None)
        constraints[name] = (constraint, ConstraintType.L)
    elif constrainttype == "N":
        # Should we just save this as the objective?
        constraint = linear_constraint(
            variables=[], coefficients=[], terms=None, lb=None, ub=None)
        constraints[name] = (constraint, ConstraintType.N)
    else:
        raise Exception(
            f"Unknown contstraintType: {constrainttype} for constraint: {name}")


def parse_column(line):

    # For now, we're only going to consider the case that we have a single variabel per line
    var_name, constraint_name, coeff = map(str.strip, line.split())
    constraint, _ = constraints[constraint_name]

    var = variables[var_name]

    # TODO[michaelr]: Doing this is bad and I feel bad, obviously we can get around this by not constructing the constraint
    # until the end though so not the biggest worry for now
    # Obviously this is also really, really slow and will hamstring us when we get to large instances
    constraint._variables += (var,)
    # TODO[michaelr]: I'm implicitly assuming int here to get things going, this is not correct
    constraint._coefficients += (int(coeff),)


def parse_rhs(line):
    # Note that we definitely need to be careful here as the MPS definition of RHS amd the
    # pyomo definition of RHS do not necessarily agree exactly

    # TODO[michaelr]: implement me
    print(f"RHS: {line}")


def parse_bounds(line):
    # TODO[michaelr]: implement me
    print(f"BOUNDS: {line}")


parse = {
    State.ROWS: lambda line: parse_row(line),
    State.COLUMNS: lambda line: parse_column(line),
    State.RHS: lambda line: parse_rhs(line),
    State.BOUNDS: lambda line: parse_bounds(line)
}

current_state = State.START
with open(file_name) as f:
    for line in f:
        if "MARK0000" in line or "MARKER" in line:
            continue
        # Match on all of the special cases, otherwise parse using the respective state function
        # TODO[michaelr]: Lots of duplication here that should be cleaned up
        if line.startswith("NAME"):
            if current_state != State.START:
                raise Exception("NAME is only valid when in the state START")
            _, name = line.split()
            current_state = State.NAME
        elif line.startswith("ROWS"):
            if current_state != State.NAME:
                raise Exception("ROWS is only valid when in the state NAME")
            current_state = State.ROWS
        elif line.startswith("COLUMNS"):
            if current_state != State.ROWS:
                raise Exception("COLUMNS is only valid when in the state ROWS")
            current_state = State.COLUMNS
        elif line.startswith("RHS"):
            if current_state != State.COLUMNS:
                raise Exception(
                    "RHS is only valid after when in the state COLUMNS")
            current_state = State.RHS
        elif line.startswith("BOUNDS"):
            if current_state != State.RHS:
                raise Exception("Bounds is only valid when in the state RHS")
            current_state = State.BOUNDS
        elif line.startswith("ENDDATA"):
            # TODO[michaelr]: Not sure if we even want any checks here
            break
        else:
            constraint_count = parse[current_state](line)

print(variables)
print(constraints)

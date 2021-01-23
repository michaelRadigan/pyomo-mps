# Another fun parsing session
# We're going to parse mp files to pyomo
from enum import Enum
from pyomo.kernel import *
import pyomo.core.kernel as pck
from collections import defaultdict
import math

# Note to future self, we're going to do this as ugly and fast as possible to start with
# Completely going for pure filth to just get this done asap.
# TODO[michaelr]: Come back at some point in the future and make this sane

file_name = r"/Users/michaelradigan/pyomo-mps-parser/mps/enlight8.mps"


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
    N = 4,


class BoundType(Enum):
    FR = 1,
    FX = 2,
    LO = 3,
    MI = 4,
    PL = 5,
    UP = 6,
    BV = 7,
    LI = 8,
    UI = 9,


def to_expr(coefficients, variables):
    return sum([c*v for c, v in zip(coefficients, variables)])


# Dictionary from constraintname to a linear_constraint as defined by the the ROWS section
# If a constraint is not mentioned in the RHS section then it takes a RHS value of 0 so we will use that as our default
constraints = {}

# constraint_count is used to keep track of the index of each constraint
constraint_count = 0

# dictionary from variable name to a variable. Note that variables in MPs are from 0 to +inf by default
variables = defaultdict(lambda: variable(lb=0, ub=None, domain=Integers))

objective = None


def parse_row(line):
    constrainttype, name = map(str.strip, line.split())
    # This is a bit shit, yes, but we'er just trying to get something to work quickly
    if constrainttype == "E":
        constraint = linear_constraint(
            variables=[], coefficients=[], terms=None, rhs=0)
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

        #objective = pck.objective.objective()
        #constraints[name] = (objective, ConstraintType.N)
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
    # pyomo definition of RHS do not necessarily agree

    # We're just going to throw away the vector name, I'm not sure that we have any use for it...
    _, constraint_name, limit = line.split()

    constraint, constraint_type = constraints[constraint_name]

    # From my reading of the pyomo kernel docs, it seems like ub is <= and rhs is ==
    if constraint_type == ConstraintType.E:
        # TODO:michaelr]: limiting to int for now
        constraint.rhs = int(limit)
    elif constraint_type == ConstraintType.G:
        constraint.ub = limit
    elif constraint_tuple == ConstraintType.L:
        constraint.lb = limit
    else:
        raise Exception('unknown constraint type')


def parse_fr(variable):
    """ A free variable, set lower bound to -inf and upper bound to inf """
    variable.lb = None
    variable.ub = None


def parse_fx(variable, bound_limit):
    """ A fixed variable, set the lower and upper bounds to the bound_limit """
    variable.lb = bound_limit
    variable.ub = bound_limit


def parse_lo(variable, bound_limit):
    """ A lower bound, set the lower bound to bound_limit, the upper bound is unchanged"""
    variable.lb = bound_limit


def parse_mi(variable):
    """ Set the lower bound to -inf """
    variable.lb = None


def parse_pl(variable):
    """ Set the upper bound to inf"""
    variable.ub = None


def parse_up(variable, bound_limit):
    """ An upper bound, set the upper bound to bound_limit, the lower bound is unchanged"""
    variable.ub = bound_limit


def parse_bv(variable):
    """ Bounds the variable to be a binary variable"""
    # TODO[michaelr]: This makes the variable integer
    variable.lb = 0
    variable.ub = 1


def parse_li(variable, bound_limit):
    """ An integer lower bound, set the lower bound to ceil(bound_limit), the upper bound is unchanged"""
    variable.lb = math.ceil(bound_limit)


def parse_ui(variable, bound_limit):
    """ An integer upper bound, set the upper bound to floor(bound_limit), the lower bound is unchanged"""
    variable.ub = math.floor(bound_limit)


parse_bound_type = {
    BoundType.FR: lambda variable, bound_limit: parse_fr(variable),
    BoundType.FX: lambda variable, bound_limit: parse_fx(variable, bound_limit),
    BoundType.LO: lambda variable, bound_limit: parse_lo(variable, bound_limit),
    BoundType.MI: lambda variable, _: parse_mi(variable),
    BoundType.PL: lambda variable, _: parse_pl(variable),
    BoundType.UP: lambda variable, bound_limit: parse_up(variable, bound_limit),
    BoundType.BV: lambda variable, _: parse_bv(variable),
    BoundType.LI: lambda variable, bound_limit: parse_li(variable, bound_limit),
    BoundType.UI: lambda variable, bound_limit: parse_ui(variable, bound_limit),
}


def parse_bound(line):
    # TODO[michaelr]: Some kind of validation
    # We're throwing away the bound_name, I don't think that we have any use for it
    bound_key, _, variable_name, bound_limit = line.split()

    variable = variables[variable_name]
    bound_type = BoundType[bound_key]

    # TODO[michaelr] We're limitting to int here again
    parse_bound_type[bound_type](variable, int(bound_limit))


parse_line = {
    State.ROWS: lambda line: parse_row(line),
    State.COLUMNS: lambda line: parse_column(line),
    State.RHS: lambda line: parse_rhs(line),
    State.BOUNDS: lambda line: parse_bound(line)
}

current_state = State.START
with open(file_name) as f:
    for line in f:
        if "MARK0000" in line or "MARKER" in line:
            continue
        # Match on all of the special cases, otherwise parse using the respective state function
        # TODO[michaelr]: Lots of duplication here that should be cleaned up

        # TODO[michaelr]: We can clean a lot of this by just parsing the raw string into the enum?
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
        elif line.startswith("ENDATA"):
            # TODO[michaelr]: Not sure if we even want any checks here
            break
        else:
            constraint_count = parse_line[current_state](line)


# At this point, I think that we may have all of the things that we need, we should build the model!
model = block()
model.vd = variable_dict(dict(variables))

# We're doing a fair bit of extra work here
# There must be a much nicer and more efficient way to do this but it's not really very important for now
objective = [c for k, (c, t) in constraints.items()
             if t == ConstraintType.N][0]


obj_expr = sum(
    [c*v for c, v in zip(objective._coefficients, objective._variables)])
model.o = pck.objective.objective(obj_expr)


normal_constaints = {k: c for k, (c, t) in constraints.items()
                     if t != ConstraintType.N}

if len(normal_constaints) + 1 != len(constraints):
    raise Exception("We only support having a single objective function")
model.c = constraint_dict(normal_constaints)

opt = SolverFactory('cbc').solve(model)
opt.write()
print(model.o())

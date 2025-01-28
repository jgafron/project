import sys
import os
from typing import List, Any, Union, Tuple, TypeVar
from dataclasses import dataclass
import subprocess


# Define a type variable for generics
V = TypeVar('V')

@dataclass
class Command:
    program: str
    flags: List[str] = None
    arguments: List[str] = None

    def __str__(self) -> str:
        com = f"{self.program}"

        if self.flags:
            com += " Flags: " + " ".join(self.flags)
        
        if self.arguments:
            com += " Arguments: " + " ".join(self.arguments)
        
        return com

@dataclass
class Filename:
    name: str
    
    def __str__(self) -> str:
        return f"Filename: {self.name}"

# Replace `type` with `Union`
Literal = Union[int, Command, Filename]

# Replace `type Expr` with `Union`
Expr = Union['Add', 'Sub', 'Mul', 'Div', 'Neg', 'Lit', 'And', 'Or', 'Not', 'Name', 'Eq', 'Lt', 'If', 'Pipe', 'Redirect', 'Bg']

@dataclass
class Add:
    left: Expr
    right: Expr
    def __str__(self) -> str:
        return f"({self.left} + {self.right})"

@dataclass
class Sub:
    left: Expr
    right: Expr
    def __str__(self) -> str:
        return f"({self.left} - {self.right})"

@dataclass
class Mul:
    left: Expr
    right: Expr
    def __str__(self) -> str:
        return f"({self.left} * {self.right})"

@dataclass
class Div:
    left: Expr
    right: Expr
    def __str__(self) -> str:
            return f"({self.left} / {self.right})"

@dataclass
class Neg:
    subexpr: Expr
    def __str__(self) -> str:
        return f"(- {self.subexpr})"

@dataclass
class Lit:
    value: Literal
    def __str__(self) -> str:
        return f"{self.value}"

@dataclass
class And:
    left: Expr
    right: Expr
    def __str__(self) -> str:
        return f"{self.left} and {self.right}"

@dataclass
class Or:
    left: Expr
    right: Expr
    def __str__(self) -> str:
        return f"{self.left} or {self.right}"

@dataclass
class Not:
    subexpr: Expr
    def __str__(self) -> str:
        return f"(not {self.subexpr})"
    
@dataclass
class Name:
    name: str
    def __str__(self) -> str:
        return self.name
    
@dataclass
class Let:
    name: str
    defexpr: Expr
    bodyexpr: Expr
    def __str__(self) -> str:
        return f"(let {self.name} = {self.defexpr} in {self.bodyexpr})"
    
@dataclass
class Eq:
    left: Expr
    right: Expr
    def __str__(self) -> str:
        return f"({self.left} == {self.right})"

@dataclass
class Lt:
    left: Expr
    right: Expr
    def __str__(self) -> str:
        return f"{self.left} < {self.right}"

@dataclass
class If:
    condition: Expr
    thenBranch: Expr
    elseBranch: Expr
    def __str__(self) -> str:
        return f"If {self.condition} then {self.thenBranch} else {self.elseBranch}"
    
@dataclass
class Pipe:
    left: Command
    right: Command
    def __str__(self) -> str:
        return f"Command: {self.left} | Command: {self.right}"
    
@dataclass
class Redirect:
    left: Command
    right: Command
    def __str__(self) -> str:
        return f"Redirect from {self.left} > {self.right}"

@dataclass
class Append:
    left: Command
    right: Command
    def __str__(self) -> str:
        return f"Redirect from {self.left} >> {self.right}"

@dataclass
class Bg:
    program: Command
    def __str__(self) -> str:
        return f"Background {self.program}&"

@dataclass
class Sequence:
    left: Command
    right: Command
    def __str__(self) -> str:
        return f"Sequence {self.left};{self.right}"

# Use Union for the binding type
Binding = Tuple[str, Any]
# Define Env as a tuple of Bindings
Env = Tuple[Binding, ...]
emptyEnv: Env = ()

# Use `TypeVar` to define generics in functions
def extendEnv(name: str, value: V, env: Env[V]) -> Env[V]:
    return ((name, value),) + env

def lookupEnv(name: str, env: Env[V]) -> Union[V, None]:
    match env:
        case ((n, v), *rest):
            if n == name:
                return v
            else:
                return lookupEnv(name, rest)
        case _:
            return None

class EvalError(Exception):
    pass

# Use Union to define Value
Value = Union[int, bool, Command]

def evalInEnv(env: Env[Value], e: Expr) -> Value:
    match e:
        case Add(l, r):
            match (evalInEnv(env, l), evalInEnv(env, r)):
                case (int(lv), int(rv)):
                    return lv + rv
                case _:
                    raise EvalError("addition of non-integers")
        case Sub(l, r):
            match (evalInEnv(env, l), evalInEnv(env, r)):
                case (int(lv), int(rv)):
                    return lv - rv
                case _:
                    raise EvalError("subtraction of non-integers")
        case Mul(l, r):
            match (evalInEnv(env, l), evalInEnv(env, r)):
                case (int(lv), int(rv)):
                    return lv * rv
                case _:
                    raise EvalError("multiplication of non-integers")
        case Lt(l, r):
            match (evalInEnv(env, l), evalInEnv(env, r)):
                case (int(lv), int(rv)):
                    if lv < rv:
                        return True
                    elif lv > rv:
                        return False
                case _:
                    raise EvalError("Less than comparison of non-integers")
        case And(l, r):
            match (evalInEnv(env, l), evalInEnv(env, r)):
                case (bool(lv), bool(rv)):
                    return lv and rv
                case _:
                    raise EvalError("One of the operands is not a bool!")
        case Or(l, r):
            match (evalInEnv(env, l), evalInEnv(env, r)):
                case (bool(lv), bool(rv)):
                    return lv or rv
                case _:
                    raise EvalError("One of the operands is not a bool!")
        case Not(s):
            return Not(evalInEnv(env, s))
        case Eq(l, r):
            match (evalInEnv(env, l), evalInEnv(env, r)):
                case (bool(lv), bool(rv)):
                    return lv == rv
                case (int(lv), int(rv)):
                    return lv == rv
                case (Command(lv), Command(rv)):
                    return lv == rv
                case _:
                    raise EvalError("Invalid equality comparison!")
        case Div(l, r):
            match (evalInEnv(env, l), evalInEnv(env, r)):
                case (int(lv), int(rv)):
                    if rv == 0:
                        raise EvalError("division by zero")
                    return lv // rv
                case _:
                    raise EvalError("division of non-integers")
        case If(b, t, e):
            match evalInEnv(env, b):
                case bool(bv):
                    if bv:
                        return evalInEnv(env, t)
                    else:
                        return evalInEnv(env, e)
                case _:
                    raise EvalError("First operand in If statement is not a bool!")
        case Neg(s):
            match evalInEnv(env, s):
                case int(i):
                    return -i
                case _:
                    raise EvalError("negation of non-integer")
        case Lit(lit):
            match lit:
                case int(i):
                    return i
                case bool(b):
                    return b
                case Command(c):
                    return str(c)
                case _:
                    raise EvalError(f"Unsupported literal type: {lit}")
        case Name(n):
            v = lookupEnv(n, env)
            if v is None:
                raise EvalError(f"unbound name {n}")
            return v
        case Let(n, d, b):
            v = evalInEnv(env, d)
            newEnv = extendEnv(n, v, env)
            return evalInEnv(newEnv, b)
        case Command(line, flags, arguments):
            final_str = line
            if flags:
                final_str += " " + " ".join(flags)
            if arguments:
                final_str += " " + " ".join(arguments)
            return final_str
        case Pipe(lc, rc):
            return str(evalInEnv(env, lc)) + ' | ' + str(evalInEnv(env, rc))
        case Redirect(lc, rc):
            return str(evalInEnv(env, lc)) + ' > ' + str(evalInEnv(env, rc))
        case Append(lc, rc):
            return str(evalInEnv(env, lc)) + ' >> ' + str(evalInEnv(env, rc))
        case Bg(c):
            return str(evalInEnv(env, c)) + ' &'
        case Sequence(lc, rc):
            return str(evalInEnv(env, lc)) + ' ; ' + str(evalInEnv(env, rc))

def execute_command(cmd: str) -> str:
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True)
        if result.stderr:
            return result.stderr.decode()
        return result.stdout.decode()
    except Exception as e:
        raise EvalError(f"Error executing command: {str(e)}")

# Create test cases
ls_command = Command(program="ls", flags=["-l"], arguments=[])
grep_command = Command(program="grep", flags=[], arguments=["file"])
a: Expr = Let('x', Add(Lit(1), Lit(2)), Sub(Name('x'), Lit(3)))
pipe_command = Pipe(left=ls_command, right=grep_command)

# Print the AST representation
print(pipe_command)
print(a)

test_string = evalInEnv(emptyEnv, pipe_command)
execute_command(test_string)
print(evalInEnv(emptyEnv, a))
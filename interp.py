from typing import List, Any
from dataclasses import dataclass
import subprocess


@dataclass
class Command():
    program: str
    flags: List[str] = None
    arguments: List[str] = None

    def __str__(self) -> str:
        com = f"{self.program}"

        if self.flags:
            com += " " + " ".join(self.flags)
        
        if self.arguments:
            com += " " + " ".join(self.arguments)
        
        return com

@dataclass
class Filename():
    name: str
    
    def __str__(self) -> str:
        return f"Filename: {self.name}"
    

type Literal = int | Command | Filename
type Expr = Add | Sub | Mul | Div | Neg | Lit | And | Or | Not | Name | Eq | Lt | If | Pipe | RedirectOut | RedirectIn  | RedirectErrorIn | Bg 

@dataclass
class Add():
    left: Expr
    right: Expr
    def __str__(self) -> str:
        return f"({self.left} + {self.right})"

@dataclass
class Sub():
    left: Expr
    right: Expr
    def __str__(self) -> str:
        return f"({self.left} - {self.right})"

@dataclass
class Mul():
    left: Expr
    right: Expr
    def __str__(self) -> str:
        return f"({self.left} * {self.right})"

@dataclass
class Div():
    left: Expr
    right: Expr
    def __str__(self) -> str:
            return f"({self.left} / {self.right})"

@dataclass
class Neg():
    subexpr: Expr
    def __str__(self) -> str:
        return f"(- {self.subexpr})"

@dataclass
class Lit():
    value: Literal
    def __str__(self) -> str:
        return f"{self.value}"

@dataclass
class And():
    left: Expr
    right: Expr
    def __str__(self) -> str:
        return f"{self.left} and {self.right}"

@dataclass
class Or():
    left: Expr
    right: Expr
    def __str__(self) -> str:
        return f"{self.left} or {self.right}"

@dataclass
class Not():
    subexpr: Expr
    def __str__(self) -> str:
        return f"(not {self.subexpr})"
    
@dataclass
class Name():
    name: str
    def __str__(self) -> str:
        return self.name

@dataclass
class Let():
    name: str
    defexpr: Expr
    bodyexpr: Expr
    def __str__(self) -> str:
        return f"(let {self.name} = {self.defexpr} in {self.bodyexpr})"
    
@dataclass
class Eq():
    left: Expr
    right: Expr
    def __str__(self) -> str:
        return f"({self.left} == {self.right})"

@dataclass
class Lt():
    left: Expr
    right: Expr
    def __str__(self) -> str:
        return f"{self.left} < {self.right}"

@dataclass
class If():
    condition: Expr
    thenBranch: Expr
    elseBranch: Expr
    def __str__(self) -> str:
        return f"If {self.condition} then {self.thenBranch} else {self.elseBranch}"

@dataclass
class Letfun():
    name: str
    param: Name  # param is now a Name Expr
    bodyexpr: Expr
    inexpr: Expr
    def __str__(self) -> str:
        return f"letfun {self.name} ({self.param}) = {self.bodyexpr} in {self.inexpr} end"

@dataclass
class App():
    fun: Expr
    arg: Expr
    def __str__(self) -> str:
        return f"({self.fun} ({self.arg}))"
    
@dataclass
class Pipe():
    left: Command
    right: Command
    def __str__(self) -> str:
        return f"Command: {self.left} | Command: {self.right}"
    
@dataclass
class RedirectOut():
    left: Command
    right: Command
    def __str__(self) -> str:
        return f"Redirect from {self.left} > {self.right}"
    
@dataclass
class RedirectIn():
    left: Command
    right: Command
    def __str__(self) -> str:
        return f"Redirect to {self.left} < from {self.right}"
    
    
@dataclass
class RedirectErrorOut():
    left: Command
    right: Filename
    def __str__(self) -> str:
        return f"Redirect stderr from {self.left} 2> {self.right}"

@dataclass
class RedirectErrorIn():
    left: Command
    right: Filename
    def __str__(self) -> str:
        return f"Redirect stderr from {self.left} 2< {self.right}"

@dataclass
class Append():
    left: Command
    right: Command
    def __str__(self) -> str:
        return f"Redirect from {self.left} >> {self.right}"

@dataclass
class Bg():
    program: Command
    def __str__(self) -> str:
        return f"Background {self.program}&"

@dataclass
class Sequence():
    left: Command
    right: Command
    def __str__(self) -> str:
        return f"Sequence {self.left};{self.right}"
    
type Binding[V] = tuple[str,V]
type Env[V] = tuple[Binding[V],...]
emptyEnv : Env[Any] = ()

def extendEnv[V](name: str, value: V, env:Env[V]) -> Env[V]:
    return ((name,value),) + env

def lookupEnv[V](name: str, env: Env[V]) -> (V | None) :
    match env:
        case ((n,v), *rest) :
            if n == name:
                return v
            else:
                return lookupEnv(name, rest) # type:ignore
        case _ :
            return None  

class EvalError(Exception):
    pass

type Value = int | bool | Command | Closure

@dataclass
class Closure:
    param: str
    body: Expr
    env: Env[Value]

def eval(e: Expr, env: Env[Value] = emptyEnv) -> Value:
    match e:
        case Add(l, r):
            lv, rv = eval(l, env), eval(r, env)
            
            if isinstance(lv, bool) or isinstance(rv, bool):
                raise EvalError("One of the operands is a bool")
            match (lv, rv):
                case (int(lv), int(rv)):
                    return lv + rv
                case _:
                    raise EvalError("addition of non-integers")
                
        case Sub(l,r):
            lv = eval(l,env)
            rv = eval(r,env)

            if (type(lv) != int) or (type(rv) != int):
                raise EvalError("subtraction of non integers!")
            else:
                return lv - rv

        case Mul(l, r):
            lv = eval(l,env)
            rv = eval(r,env)

            if (type(lv) != type(rv)):
                raise EvalError("Less than operation on two variables that arent the same type@!")
            else:
                return (lv*rv)

        case Lt(l,r):
            lv = eval(l,env)
            rv = eval(r,env)
            
            if (type(lv) != type(rv)):
                raise EvalError("Less than operation on two variables that arent the same type@!")
            
            if(lv < rv):
                return True
            elif(lv > rv):
                return False
            elif(lv == rv):
                return False
                
        case And(l, r):
            lv = eval(l, env)
            if isinstance(lv, bool):
                if not lv:  # short-circuit
                    return False
            else:
                raise EvalError("Left operand is not a bool")
    
            rv = eval(r, env)
            if isinstance(rv, bool):
                return lv and rv
            else:
                raise EvalError("Right operand is not a bool!")
        case Or(l, r):
            lv = eval(l, env)
            if isinstance(lv, bool) and lv:
                return True
            if (type(lv) != bool):
                raise EvalError("LHS isnt bool!")
            rv = eval(r, env)
            if isinstance(rv, bool):
                return lv or rv
            else:
                raise EvalError("One of the operands is not a bool!")
        case Not(s):
            val = eval(s, env)
            if isinstance(val, bool):
                return not val  # Negate the boolean value
            else:
                raise EvalError("Not expects a boolean")
        case Eq(l,r):
            lv = eval(l, env)
            rv = eval(r, env)
            if (type(rv) != type(lv)):
                return False
            match (eval(l, env), eval(r, env)):
                case((bool(lv), bool(rv))):
                    if lv == rv:
                        return True
                    else:
                        return False
                case((int(lv), int(rv))):
                    if lv == rv:
                        return True
                    else:
                        return False
                case((str(lv), str(rv))):
                    if lv == rv:
                        return ("The strings are equal!")
                    else:
                        return ("The strings are not the same!")
                case _:
                    raise EvalError("Type is not bool, nor int, nor command!")
        case Div(l,r):
            lv = eval(l,env)
            rv = eval(r,env)
            
            if isinstance(lv, bool) or isinstance(rv, bool):
                raise EvalError("One of the operands is a bool")
            
            if isinstance(lv, int) and (rv == 0):
                raise EvalError("Division by zero!")
            
            else:
                return lv // rv
                
        case If(b,t,e):
            match(eval(b, env)):
                case bool(bv):
                    if bv:
                        return eval(t, env)
                    elif (bv == False):
                        return eval(e, env)
                case _:
                    raise EvalError("First operand in If statement is not a bool!")
                
        case Neg(s):
            val = eval(s, env)
            if (type(val)) is not int:
                raise EvalError
            else:
                return (-1 * val)

        case Lit(lit):
            match lit:  # two-level matching keeps type-checker happy
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
        case Let(n,d,b):
            v = eval(d, env)
            newEnv = extendEnv(n, v, env)
            return eval(b, newEnv)
        case Command(program, flags, arguments):
            cmd = [program] + (flags if flags else []) + (arguments if arguments else [])

            # 🛠 Debugging print statements
            print(f"DEBUG: Running command: {cmd}")

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return result.stdout.strip()
            except subprocess.CalledProcessError as e:
                print(f"DEBUG: Command failed: {e.stderr}")
                return f"Command failed: {e.stderr}"
        case Filename(s):
            return str('"' + s + '"')
        case Pipe(left, right):
            left_output = eval(left, env)
            if not isinstance(left_output, str):
                raise EvalError("Pipe left side must produce a string")
            
            right_cmd = eval(right, env) 

            process = subprocess.run(right_cmd, input=left_output, text=True, capture_output=True, shell=True)
            return process.stdout.strip()
        case RedirectOut(command, filename):
            output = eval(command, env)
            with open(filename.name, "w") as f:
                f.write(output)
            return f"Output written to {filename.name}"
        case RedirectIn(command, filename):
            with open(filename.name, "r") as f:
                input_data = f.read()
            return eval(command, extendEnv("STDIN", input_data, env))
        case RedirectErrorOut(command, filename):
            cmd = eval(command, env)
            if not isinstance(cmd, str):
                raise EvalError("Command must be a string")
            
            try:
                with open(filename.name, "w") as f:
                    subprocess.run(cmd, shell=True, stderr=f)
                return f"Error output written to {filename.name}"
            except Exception as e:
                raise EvalError(f"Failed to redirect stderr: {str(e)}")
        case Append(lc,rc):
            lcp = eval(lc,env)
            rcp = eval(rc,env)

            if(type(lcp) != str):
               raise EvalError("Left command isnt a command!")
            
            elif(type(rcp) != str):
               raise EvalError("Right side of append isnt a filename!")
            
            else:
                return str(lcp + ' >> ' + rcp)
        case Bg(command):
            cmd = eval(command, env)
            if not isinstance(cmd, str):
                raise EvalError("Command must be a string")
            
            subprocess.Popen(cmd, shell=True)
            return f"Running in background: {cmd}"
        case Sequence(lc,rc):
            lcp = eval(lc,env)
            rcp = eval(rc,env)

            if(type(lcp) != str):
               raise EvalError("Left command isnt a command!")
            
            elif(type(rcp) != str):
               raise EvalError("Right side of sequence isnt a command!")
            
            else:
                return str(lcp + ' ; ' + rcp)
        case App(f, a):
            fun = eval(f, env)
            arg = eval(a, env)
            match fun:
                case Closure(p, b, cenv):
                    newEnv = cenv  # Start with the closure's environment
                    newEnv = extendEnv(p, arg, newEnv)  # Create a *new* environment
                    return eval(b, newEnv)  # Evaluate in the *new* environment

        case Letfun(n, p, b, i):
            closure = Closure(p.name, b, env)  # Store param correctly
            newEnv = extendEnv(n, closure, env)
            return eval(i, newEnv)

#HELPER FUNCTION TO EXECUTE COMMANDS
def execute_command(cmd: str) -> str:
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        if result.stdout:
            return result.stdout
        else:
            return "No output from command"

    except subprocess.CalledProcessError as e:
        return f"Command failed with error: {e.stderr}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

#RUN FUNCTION LIKE TURTLE FOR REQUIREMENT
def run(e: Expr) -> None:
    print(f"Running: {e}")
    try:
        result = eval(e)
        print(f"Result = {result}")
    except EvalError as err:
        print(f"Evaluation error: {err}")
'''
#PROOF OF CONCEPT TESTS
command_stra = RedirectOut(Pipe(Command('ls', ['-l']), Command("grep", ["jgafron"])), Filename("output.txt"))
command_strb = RedirectOut(Command('cat', ['file1.txt']), Filename('output.log'))
command_strc = Bg(Pipe(Command('ps', ['-aux']), Command('grep', ['python'])))
command_strd = Sequence(Command('echo', ['Hello', '>', 'file.txt']),Command('ps', ['-aux']))
command_stre = RedirectErrorOut(Command('ls', ['nonexistent_directory']), Filename('error.log'))
command_strf = RedirectOut(Pipe(Command('ps', ['-aux']),Command('grep', ['jgafron'])),Filename('jgafron.txt')),RedirectErrorOut(Command('ls', ['-l']),Filename('stderr_log.txt'))



pure_a = And(Or(Eq(Lit(-37), Lit(-37)), Lit(False)), Lt(Lit(-75), Lit(43)))
pure_b = If(Lt(Add(Lit(30), Lit(-33)), Lit(31)),
                  And(Lit(True), Lit(False)),
                  Lit(True))
pure_c = If(Lit(True), If(Lit(False), Lit(-98), Lit(26)), Lit(-20))
pure_d = Eq(Lit(False), Lit(False))
pure_e = Let('x',
                   Lit(1),
                   Let('y',
                       Lit(2),
                       Sub(Name('y'),
                           Name('x')
                           )
                       )
                   )

run(command_stra)
run(command_strb)
run(command_strc)
run(command_strd)
run(command_stre)
run(command_strf)
run(pure_a)
run(pure_b)
run(pure_c)
run(pure_d)
run(pure_e)
#END OF PROOF OF CONCEPT TESTS

'''
'''
This Shell DSL part of the interpreter uses an Abstract Syntax Tree (AST) to represent shell commands and operations. 
Each shell command is broken down into distinct components—like the program name, flags, and arguments—captured as 
different data structures. Operations like piping (|), output redirection (>), and background execution (&) are also 
represented as specific AST nodes.

The interpreters eval function recursively evaluates these AST nodes. For commands, it constructs the corresponding 
shell command and executes it using Python subprocess module. Operations like redirection or piping are translated 
into system commands, and the output is handled accordingly. This structure allows the interpreter to execute complex 
shell command sequences while maintaining clarity and modularity in the evaluation process.
'''
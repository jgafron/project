from interp import Add, Sub, Mul, Div, Neg, Let, Lit, And, Or, Not, Name, Eq, Lt, If, Pipe, RedirectOut, RedirectIn, Command, Filename, RedirectErrorOut,RedirectErrorIn, Bg, Letfun, App, Expr, run
from lark import Lark, Token, ParseTree, Transformer, Tree
from lark.exceptions import VisitError
from pathlib import Path

parser = Lark(Path('expr.lark').read_text(),start='expr', parser='lalr', strict=True) #import lark grammar
class ParseError(Exception): #raise some error 
    pass

def parse(s:str) -> ParseTree: #output parsetree
    try:
        return parser.parse(s)
    except Exception as e:
        raise ParseError(e)

class AmbiguousParse(Exception): #raise error if expr is ambigous
    pass

class ToExpr(Transformer[Token,Expr]): #Class ToExpr that is a subclass of Transformer which will transform tokens into expressions
    '''Defines a transformation from5 a parse tree into an AST'''
    def flag(self, args):
        return "-" + args[0].value  # Convert flag token to string
    def command_base(self, args):
        program = args[1].value  # Extract command name (skip COM)
        flags = []
        arguments = []

        for arg in args[2:]:  # Process flags and arguments

            # Handle flags correctly even if they arrive as strings
            if isinstance(arg, str) and arg.startswith("-"):
                flags.append(arg)

            elif isinstance(arg, Tree) and arg.data == "flag":
                flag_value = "-" + arg.children[0].value  # Convert 'l' → '-l'
                flags.append(flag_value)

            elif isinstance(arg, Token):
                if arg.type == "ID":
                    arguments.append(arg.value)
                elif arg.type == "STRING":  
                    arguments.append(arg.value)  # Keep the quotes

        return Command(program, flags=flags, arguments=arguments)
    def pipe(self, args):
        left, right = args
        return Pipe(left, right)
    def redirect_out(self, args):
        return RedirectOut(args[0], Filename(args[1].value))
    def redirect_in(self, args):
        return RedirectIn(args[0], Filename(args[1].value))
    def redirect_err_out(self, args):
        return RedirectErrorOut(args[0], Filename(args[1].value))
    def redirect_err_in(self, args):
        return RedirectErrorIn(args[0], Filename(args[1].value))
    def background(self, args):
        return Bg(args[0])
    def true(self, args: tuple) -> Expr:
        return Lit(True)  # Represent 'true' as a boolean literal True
    def false(self, args: tuple) -> Expr:
        return Lit(False)  # Represent 'false' as a boolean literal False
    def plus(self, args:tuple[Expr,Expr]) -> Expr: #if you run across a plus, transform into an ADD ast node
        return Add(args[0],args[1])
    def times(self, args:tuple[Expr,Expr]) -> Expr:
        return Mul(args[0],args[1])
    def minus(self, args:tuple[Expr,Expr]) -> Expr:
        return Sub(args[0],args[1])
    def divide(self, args:tuple[Expr,Expr]) -> Expr:
        return Div(args[0],args[1])
    def and_exp(self, args:tuple[Expr, Expr]) -> Expr:
        return And(args[0],args[1])
    def or_exp(self, args:tuple[Expr, Expr]) -> Expr:
        return Or(args[0],args[1])
    def not_exp(self, args:tuple[Expr]) -> Expr:
        return Not(args[0])
    def comparison_expr(self, args: tuple) -> Expr:
        left = args[0]
        op_tree = args[1]  # This is a Tree, not a Token!
        right = args[2]

        op = op_tree.data # Access the data attribute of the tree, which is the operator name
        if op == "equalop":
            return Eq(left, right)
        elif op == "lessthan":
            return Lt(left, right)
        else:
            raise Exception("Unknown comparison operator")
    def neg(self, args:tuple[Expr]) -> Expr:
        return Neg(args[0])
    def let(self, args:tuple[Token,Expr,Expr]) -> Expr:
        return Let(args[0].value,args[1],args[2]) 
    def id(self, args: tuple[Token]) -> Expr:
        if args[0].value == "true":
            return Lit(True)
        elif args[0].value == "false":
            return Lit(False)
        return Name(args[0].value)
    def int(self,args:tuple[Token]) -> Expr:
        return Lit(int(args[0].value))
    def ifnz(self,args:tuple[Expr,Expr,Expr]) -> Expr:
        return If(args[0],args[1],args[2])
    def if_exp(self, args: tuple[Expr,Expr,Expr]) -> Expr:
        return If(args[0], args[1], args[2])
        
    def letfun(self, args: tuple[Token, Token, Expr, Expr]) -> Expr:
        name = args[0].value
        param = Name(args[1].value)  # Create a Name node for the parameter
        body = args[2]
        inexpr = args[3]
        return Letfun(name, param, body, inexpr)
    def app(self, args: tuple[Expr, Expr]) -> Expr:
        fun_expr = args[0]
        if isinstance(fun_expr, Token):  # Convert Token to Name if necessary
            fun_expr = Name(fun_expr.value)
        return App(fun_expr, args[1])
    
    def _ambig(self,_) -> Expr:    # ambiguity marker
        raise AmbiguousParse()


def parse_and_run(s: str):
    """Parses the input string, converts it into an AST, and executes it."""
    try:
        parse_tree = parser.parse(s)
        ast = ToExpr().transform(parse_tree)
        run(ast)
    except VisitError as e:
        if isinstance(e.orig_exc, AmbiguousParse):
            raise AmbiguousParse()
        else:
            raise e
    except Exception as e:
        raise ParseError(e)

test_arith1 = "1 + 2 * 3"  # Multiplication has higher precedence than addition → should evaluate to 1 + (2 * 3) = 7
test_arith2 = "(1 + 2) * 3"  # Parentheses override precedence → should evaluate to (1 + 2) * 3 = 9
test_arith3 = "-(5 + 3) * 2"  # Unary negation with parentheses → should evaluate to -8 * 2 = -16
test_arith4 = "let x = 10 in x * 2 + 5 end"  # `let-in-end` precedence → (x * 2) + 5 = 25
test_arith5 = "let x = 4 in let y = 2 in x / y + 3 end end"  # Nested let bindings → should evaluate to (4 / 2) + 3 = 5
test_arith6 = "letfun square(x) = x * x in square(3) + square(4) end"  
# Function application with precedence → should evaluate to (3*3) + (4*4) = 9 + 16 = 25
test_bool1 = "let x = 5 in x < 10 && x == 5 end"  
#  `x < 10` is `true`, `x == 5` is `true` → `true && true` → `true`
test_bool2 = "let a = 2 in let b = 4 in !(a == b) || a < b end end"  
#  `a == b` is `false`, `!(a == b)` is `true`, `a < b` is `true` → `true || true` → `true`
test_bool3 = "letfun isEven(n) = n == 0 || !(n == 1) in isEven(2) && isEven(3) end"  
#  `isEven(2)` → `2 == 0 || !(2 == 1)` → `false || true` → `true`
#  `isEven(3)` → `3 == 0 || !(3 == 1)` → `false || true` → `true`
#  `true && true` → `true`
test_bool_simple1 = "true && false"  
#  `true && false` → `false`
test_bool_simple2 = "!false || false"  
#  `!false` → `true`, `true || false` → `true`
test_bool_simple3 = "1 == 1 && 2 < 3"  
#  `1 == 1` → `true`, `2 < 3` → `true`
#  `true && true

test_dsl1 = "COM ls -la"
test_dsl2 = "COM echo 'Hello, world!'"
test_dsl3 = "COM grep 'error'"
test_dsl4 = "COM ls -la | grep"

parse_and_run(test_arith1)
parse_and_run(test_arith2)
parse_and_run(test_arith3)
parse_and_run(test_arith4)
parse_and_run(test_arith5)
parse_and_run(test_arith6)
parse_and_run(test_bool1)
parse_and_run(test_bool2)
parse_and_run(test_bool3)
parse_and_run(test_bool_simple1)
parse_and_run(test_bool_simple2)
parse_and_run(test_bool_simple3)
parse_and_run(test_dsl4)

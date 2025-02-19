from interp import Add, Sub, Mul, Div, Neg, Let, Lit, And, Or, Not, Name, Eq, Lt, If, Pipe, RedirectOut, RedirectIn, RedirectErrorOut,RedirectErrorIn, Bg, Letfun, App, Expr, run
from lark import Lark, Token, ParseTree, Transformer, Tree
from lark.exceptions import VisitError
from pathlib import Path

parser = Lark(Path('expr.lark').read_text(),start='expr', parser='earley', ambiguity='explicit') #import lark grammar
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


def genAST(t:ParseTree) -> Expr:
    '''Applies the transformer to convert a parse tree into an AST'''
    # boilerplate to catch potential ambiguity error raised by transformer
    try:
        return ToExpr().transform(t)               
    except VisitError as e:
        if isinstance(e.orig_exc,AmbiguousParse):
            raise AmbiguousParse()
        else:
            raise e

def driver():
    while True:
        try:
            s = input('expr: ')
            t = parse(s)
            print("raw:", t)    
            print("pretty:")
            print(t.pretty())
            ast = genAST(t)
            print("raw AST:", repr(ast))  # use repr() to avoid str() pretty-printing
            run(ast)                      # pretty-prints and executes the AST
        except AmbiguousParse:
            print("ambiguous parse")                
        except ParseError as e:
            print("parse error:")
            print(e)
        except EOFError:
            break

driver()
import sys
import os
from typing import List
from dataclasses import dataclass


@dataclass
class Command():
    program: str
    flags: List[str] = None
    arguments: List[str] = None

    def __str__(self) -> str:
        com = f"Command: {self.program}"

        if self.flags:
            com += " Flags: " + " ".join(self.flags)
        
        if self.arguments:
            com += " Arguments " + " ".join(self.arguments)
        
        return com

@dataclass
class Filename():
    name: str
    
    def __str__(self) -> str:
        return f"Filename: {self.name}"
    

type Literal = int | Command | Filename
type Expr = Add | Sub | Mul | Div | Neg | Lit | And | Or | Not | Name | Eq | Lt | If | Pipe | Redirect | Bg

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
class Pipe():
    left: Command
    right: Command
    def __str__(self) -> str:
        return f"Command: {self.left} | Command: {self.right}"
    
@dataclass
class Redirect():
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
    

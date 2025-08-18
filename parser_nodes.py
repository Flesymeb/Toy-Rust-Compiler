"""
Description  : 适用于单遍编译/语法制导翻译的Rust-like语法树节点定义
Author       : Hyoung
Date         : 2025-08-18 17:49:45
LastEditTime : 2025-08-18 17:49:47
FilePath     : \\课程设计\\rust-like-compiler\\parser_nodes.py
"""


class ASTNode:
    """基本AST节点类"""

    pass


# --- 程序结构 ---
class ProgramNode(ASTNode):
    def __init__(self, declarations):
        self.declarations = declarations  # list of FunctionDeclNode

    def __repr__(self):
        return f"ProgramNode({self.declarations})"


class FunctionDeclNode(ASTNode):
    def __init__(self, name_token, params, return_type, body):
        self.token = name_token  # 函数名 Token
        self.params = params  # 形参列表 (list of ParamNode)
        self.return_type = return_type  # 返回类型 (TypeNode or None)
        self.body = body  # 函数体 (BlockNode or FunctionExprNode)
        self.name = name_token.value  # 字符串形式的函数名

    def __repr__(self):
        return f"FunctionDeclNode(name={self.name}, params={self.params}, ret={self.return_type}, body={self.body})"


class ParamNode(ASTNode):
    def __init__(self, name_internal, param_type):
        self.name_internal = name_internal  # VariableInternalDeclNode
        self.param_type = param_type  # TypeNode

    def __repr__(self):
        return f"ParamNode({self.name_internal}, {self.param_type})"


class VariableInternalDeclNode(ASTNode):
    def __init__(self, mutable, name):
        self.mutable = mutable  # bool
        self.name = name  # Token(IDENTIFIER)

    def __repr__(self):
        mut_str = "mut " if self.mutable else ""
        return f"VarInternalDecl({mut_str}{self.name.value})"


class TypeNode(ASTNode):
    """类型节点 (支持基础类型, 数组, 元组, 引用)"""

    def __init__(
        self,
        type_token=None,
        array_type=None,
        array_size=None,
        tuple_types=None,
        ref_mutable=None,
        ref_type=None,
    ):
        self.type_token = type_token  # 基础类型Token (e.g., 'i32', 'bool')
        self.array_type = array_type  # 数组元素类型 (TypeNode)
        self.array_size = array_size  # 数组大小 (Token(NUMBER) or None)
        self.tuple_types = tuple_types  # 元组元素类型列表 (list of TypeNode)
        self.is_ref = ref_type is not None  # 是否是引用类型
        self.ref_mutable = ref_mutable  # 引用是否可变 (bool or None for immutable ref)
        self.ref_type = ref_type  # 引用的目标类型 (TypeNode or None)

    def __repr__(self):
        if self.is_ref:
            mut_str = "mut " if self.ref_mutable else ""
            return f"RefType(&{mut_str}{self.ref_type})"
        if self.type_token:
            return f"Type({self.type_token.value})"
        if self.array_type:
            return f"ArrayType(elem={self.array_type}, size={self.array_size.value if self.array_size else '?'})"  # Dyn size TBD
        if self.tuple_types is not None:
            return f"TupleType({self.tuple_types})"
        return "Type(Unknown)"


# --- 语句 ---
class BlockNode(ASTNode):
    def __init__(self, statements):
        self.statements = statements  # list of StatementNode

    def __repr__(self):
        return f"BlockNode({self.statements})"


class StatementNode(ASTNode):
    pass


class EmptyStatementNode(StatementNode):
    def __repr__(self):
        return "EmptyStmt"


class LetDeclNode(StatementNode):
    def __init__(self, var_internal_decl, var_type, init_expr=None):
        self.var_internal_decl = var_internal_decl  # VariableInternalDeclNode
        self.var_type = var_type  # TypeNode or None
        self.init_expr = init_expr  # ExpressionNode or None

    def __repr__(self):
        type_str = f": {self.var_type}" if self.var_type else ""
        init_str = f" = {self.init_expr}" if self.init_expr else ""
        return f"LetDeclNode({self.var_internal_decl}{type_str}{init_str})"


class AssignNode(StatementNode):
    def __init__(self, assignable_element, expr):
        self.assignable_element = assignable_element  # e.g., IdentifierNode, ArrayAccessNode, TupleAccessNode, UnaryOpNode(*)
        self.expr = expr  # ExpressionNode

    def __repr__(self):
        return f"AssignNode(to={self.assignable_element}, expr={self.expr})"


class ReturnNode(StatementNode):
    def __init__(self, expr=None):
        self.expr = expr  # ExpressionNode or None

    def __repr__(self):
        return f"ReturnNode(expr={self.expr})"


class IfNode(StatementNode):
    def __init__(self, condition, then_block, else_if_parts, else_block):
        self.condition = condition  # ExpressionNode
        self.then_block = then_block  # BlockNode
        self.else_if_parts = (
            else_if_parts  # List of {'condition': ExprNode, 'block': BlockNode}
        )
        self.else_block = else_block  # BlockNode or None

    def __repr__(self):
        return f"IfNode(cond={self.condition}, then={self.then_block}, else_if={self.else_if_parts}, else={self.else_block})"


class WhileNode(StatementNode):
    def __init__(self, condition, body):
        self.condition = condition  # ExpressionNode
        self.body = body  # BlockNode

    def __repr__(self):
        return f"WhileNode(cond={self.condition}, body={self.body})"


class ForNode(StatementNode):
    def __init__(self, var_internal_decl, iterable, body):
        self.var_internal_decl = var_internal_decl  # VariableInternalDeclNode
        self.iterable = iterable  # ExpressionNode (RangeNode or other)
        self.body = body  # BlockNode

    def __repr__(self):
        return f"ForNode(var={self.var_internal_decl}, in={self.iterable}, body={self.body})"


class LoopNode(StatementNode):
    def __init__(self, body):
        self.body = body  # BlockNode

    def __repr__(self):
        return f"LoopNode(body={self.body})"


class BreakNode(StatementNode):
    def __init__(self, expr=None):  # Rust's break can return a value from loop expr
        self.expr = expr

    def __repr__(self):
        return f"BreakNode(expr={self.expr})"


class ContinueNode(StatementNode):
    def __repr__(self):
        return "ContinueNode"


class ExprStatementNode(StatementNode):
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return f"ExprStmtNode({self.expr})"


# --- 表达式 ---
class ExpressionNode(ASTNode):
    pass


class NumberNode(ExpressionNode):
    def __init__(self, token):
        self.token = token
        self.value = token.value  # int or float

    def __repr__(self):
        return f"Number({self.value})"


class BooleanLiteralNode(ExpressionNode):
    def __init__(self, token, value):
        self.token = token  # The 'true' or 'false' keyword token
        self.value = value  # Python bool (True or False)

    def __repr__(self):
        return f"Boolean({self.value})"


class IdentifierNode(ExpressionNode):
    def __init__(self, token):
        self.token = token
        self.name = token.value  # string

    def __repr__(self):
        return f"Ident({self.name})"


class BinaryOpNode(ExpressionNode):
    def __init__(self, left, op_token, right):
        self.left = left  # ExpressionNode
        self.op_token = op_token  # Token (e.g., TT_PLUS, TT_EQ)
        self.right = right  # ExpressionNode

    def __repr__(self):
        # Special case for logical operators if needed
        return f"BinOp({self.left} {self.op_token.value} {self.right})"


class UnaryOpNode(ExpressionNode):
    """一元操作节点 (例如: -, *, !)"""

    def __init__(self, op_token, expr):
        self.op_token = op_token  # Token (e.g., TT_MINUS, TT_MUL for deref, TT_NOT?)
        self.expr = expr  # ExpressionNode

    def __repr__(self):
        op_val = self.op_token.value
        return f"UnaryOp(op={op_val}, expr={self.expr})"


# <<< --- 新增 BorrowNode --- >>>
class BorrowNode(ExpressionNode):
    """借用表达式节点 (&expr, &mut expr)"""

    def __init__(self, is_mutable, expr):
        self.is_mutable = is_mutable  # bool
        self.expr = expr  # ExpressionNode being borrowed

    def __repr__(self):
        mut_str = "mut " if self.is_mutable else ""
        return f"BorrowNode(&{mut_str}{self.expr})"


# <<< --- 结束新增 --- >>>


class FunctionCallNode(ExpressionNode):
    def __init__(self, func_expr, args):  # Changed func_name_token to func_expr
        self.func_expr = func_expr  # ExpressionNode (usually IdentifierNode)
        self.args = args  # list of ExpressionNode

    def __repr__(self):
        # Use token.value if it's an IdentifierNode
        if isinstance(self.func_expr, IdentifierNode):
            return f"FuncCall(name={self.func_expr.token.value}, args={self.args})"
        return f"FuncCall(expr={self.func_expr}, args={self.args})"


class ArrayLiteralNode(ExpressionNode):
    def __init__(self, elements):
        self.elements = elements  # list of ExpressionNode

    def __repr__(self):
        return f"ArrayLit({self.elements})"


class ArrayAccessNode(ExpressionNode):
    def __init__(self, array_expr, index_expr):
        self.array_expr = array_expr  # ExpressionNode
        self.index_expr = index_expr  # ExpressionNode

    def __repr__(self):
        return f"ArrayAccess(array={self.array_expr}, index={self.index_expr})"


class TupleLiteralNode(ExpressionNode):
    def __init__(self, elements):
        self.elements = elements  # list of ExpressionNode

    def __repr__(self):
        # Handle single-element tuple display correctly: (elem,)
        if len(self.elements) == 1:
            return f"TupleLit(({self.elements[0]},))"
        return f"TupleLit({self.elements})"


class TupleAccessNode(ExpressionNode):
    def __init__(self, tuple_expr, index_token):
        self.tuple_expr = tuple_expr  # ExpressionNode
        self.index_token = index_token  # Token(NUMBER)

    def __repr__(self):
        return f"TupleAccess(tuple={self.tuple_expr}, index={self.index_token.value})"


class RangeNode(ASTNode):  # Not strictly an expression itself, but used in ForNode
    def __init__(self, start_expr, end_expr):
        self.start_expr = start_expr  # ExpressionNode
        self.end_expr = end_expr  # ExpressionNode

    def __repr__(self):
        return f"Range({self.start_expr}..{self.end_expr})"


# --- 表达式块相关 (保持不变) ---
class FunctionExprNode(ExpressionNode):
    def __init__(self, items):
        self.items = items

    def __repr__(self):
        return f"FuncExprNode({self.items})"


class IfExprNode(ExpressionNode):
    def __init__(self, condition, then_expr_block, else_expr_block):
        self.condition = condition
        self.then_expr_block = then_expr_block  # BlockNode or similar
        self.else_expr_block = else_expr_block  # BlockNode or similar

    def __repr__(self):
        return f"IfExprNode(cond={self.condition}, then={self.then_expr_block}, else={self.else_expr_block})"


class LoopExprNode(ExpressionNode):
    def __init__(self, body):
        self.body = body  # BlockNode

    def __repr__(self):
        return f"LoopExprNode({self.body})"

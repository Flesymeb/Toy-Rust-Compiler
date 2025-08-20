"""
Description  : Rust-like语言语义分析器 - 集成符号表和错误检查
Author       : Hyoung
Date         : 2025-08-20 17:30:00
LastEditTime : 2025-08-20 17:30:00
FilePath     : \\课程设计\\rust-like-compiler\\semantic_analyzer.py
"""

from symbol_table import SymbolTable, Symbol, FunctionSymbol, CompilerError
from parser_nodes import *


class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.current_function_return_type = None
        self.in_loop = False

    def get_node_value(self, node):
        """安全地获取节点的值"""
        if node is None:
            return "unknown"
        if isinstance(node, str):
            return node
        if hasattr(node, "token") and hasattr(node.token, "value"):
            return node.token.value
        if hasattr(node, "value"):
            return node.value
        if hasattr(node, "name"):
            return self.get_node_value(node.name)
        return str(node)

    def get_node_line(self, node):
        """安全地获取节点的行号"""
        if hasattr(node, "token") and hasattr(node.token, "line"):
            return node.token.line
        if hasattr(node, "line"):
            return node.line
        return None

    def get_node_column(self, node):
        """安全地获取节点的列号"""
        if hasattr(node, "token") and hasattr(node.token, "column"):
            return node.token.column
        if hasattr(node, "column"):
            return node.column
        return None

    def get_type_name(self, type_node):
        """安全地获取类型名称"""
        if type_node is None:
            return "void"
        if isinstance(type_node, str):
            return type_node
        if hasattr(type_node, "type_name"):
            return type_node.type_name
        if hasattr(type_node, "name"):
            return self.get_node_value(type_node.name)
        return self.get_node_value(type_node)

    def analyze(self, ast):
        """分析AST并返回错误列表"""
        self.symbol_table.clear_errors()
        self.visit(ast)
        return self.symbol_table.errors

    def visit(self, node):
        """访问AST节点的通用方法"""
        method_name = f"visit_{node.__class__.__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        """通用访问方法"""
        for child in getattr(node, "children", []):
            if child:
                self.visit(child)

    def visit_ProgramNode(self, node):
        """访问程序根节点"""
        for decl in node.declarations:
            self.visit(decl)

    def visit_FunctionDeclNode(self, node):
        """访问函数声明节点"""
        # 添加函数到符号表
        param_types = []
        for param in node.params:
            param_types.append(self.get_type_name(param.param_type))

        # 获取函数名称 - 使用辅助函数
        func_name = self.get_node_value(node.name)

        func_symbol = FunctionSymbol(
            func_name,
            self.get_type_name(node.return_type),
            param_types,
            self.get_node_line(node),
            self.get_node_column(node),
        )

        self.symbol_table.define(func_symbol)

        # 进入函数作用域
        self.symbol_table.enter_scope()
        old_return_type = self.current_function_return_type
        self.current_function_return_type = self.get_type_name(node.return_type)

        # 添加参数到符号表
        for param in node.params:
            if param.name_internal and param.param_type:
                # 检查参数的可变性
                param_is_mutable = False
                if hasattr(param.name_internal, "mutable"):
                    param_is_mutable = param.name_internal.mutable

                param_symbol = Symbol(
                    self.get_node_value(param.name_internal),
                    self.get_type_name(param.param_type),
                    param_is_mutable,  # 使用参数的实际可变性
                    self.get_node_line(param.name_internal),
                    self.get_node_column(param.name_internal),
                )
                self.symbol_table.define(param_symbol)

        # 访问函数体
        if node.body:
            self.visit(node.body)

        # 退出函数作用域
        self.current_function_return_type = old_return_type
        self.symbol_table.exit_scope()

    def visit_LetDeclNode(self, node):
        """访问let声明节点"""
        var_name = None
        var_type = "unknown"
        is_mutable = False
        line = None
        col = None

        # 获取变量信息
        if node.var_internal_decl:
            if hasattr(node.var_internal_decl, "name") and node.var_internal_decl.name:
                var_name = self.get_node_value(node.var_internal_decl.name)
                line = self.get_node_line(node.var_internal_decl.name)
                col = self.get_node_column(node.var_internal_decl.name)

            if hasattr(node.var_internal_decl, "mutable"):
                is_mutable = node.var_internal_decl.mutable

            if (
                hasattr(node.var_internal_decl, "var_type")
                and node.var_internal_decl.var_type
            ):
                var_type = self.get_type_name(node.var_internal_decl.var_type)

        # 类型推断：如果没有显式类型，从初始化表达式推断
        if var_type == "unknown" and node.init_expr:
            init_type = self.get_expression_type(node.init_expr)
            if init_type != "unknown":
                var_type = init_type

        if var_name:
            symbol = Symbol(var_name, var_type, is_mutable, line, col)
            self.symbol_table.define(symbol)

        # 访问初始化表达式
        if node.init_expr:
            init_type = self.visit_expression(node.init_expr)
            # 检查类型兼容性
            if (
                var_type != "unknown"
                and init_type != "unknown"
                and var_type != init_type
            ):
                self.symbol_table.check_type_compatibility(
                    var_type,
                    init_type,
                    line,
                    col,
                    f" in variable '{var_name}' initialization",
                )

    def visit_AssignNode(self, node):
        """访问赋值节点"""
        if node.assignable_element:
            var_name = self.get_node_value(node.assignable_element)
            line = self.get_node_line(node.assignable_element)
            col = self.get_node_column(node.assignable_element)

            # 检查赋值合法性
            if not self.symbol_table.check_assignment(var_name, line, col):
                return

            # 检查类型兼容性
            if node.expr:
                value_type = self.visit_expression(node.expr)
                symbol = self.symbol_table.lookup(var_name, mark_used=False)
                if symbol and symbol.type != "unknown" and value_type != "unknown":
                    self.symbol_table.check_type_compatibility(
                        symbol.type,
                        value_type,
                        line,
                        col,
                        f" in assignment to '{var_name}'",
                    )

    def visit_IfNode(self, node):
        """访问if语句节点"""
        # 检查条件表达式类型
        if node.condition:
            cond_type = self.visit_expression(node.condition)
            if cond_type != "unknown" and cond_type != "bool":
                self.symbol_table.add_error(
                    "type_mismatch",
                    f"If condition must be of type 'bool', found '{cond_type}'",
                    suggestion="Use a boolean expression as the condition",
                )

        # 访问then和else块
        if node.then_block:
            self.symbol_table.enter_scope()
            self.visit(node.then_block)
            self.symbol_table.exit_scope()

        if node.else_block:
            self.symbol_table.enter_scope()
            self.visit(node.else_block)
            self.symbol_table.exit_scope()

    def visit_WhileNode(self, node):
        """访问while循环节点"""
        # 检查条件表达式类型
        if node.condition:
            cond_type = self.visit_expression(node.condition)
            if cond_type != "unknown" and cond_type != "bool":
                self.symbol_table.add_error(
                    "type_mismatch",
                    f"While condition must be of type 'bool', found '{cond_type}'",
                )

        # 访问循环体
        if node.body:
            old_in_loop = self.in_loop
            self.in_loop = True
            self.symbol_table.enter_scope()
            self.visit(node.body)
            self.symbol_table.exit_scope()
            self.in_loop = old_in_loop

    def visit_ReturnNode(self, node):
        """访问return语句节点"""
        if node.expr:
            return_type = self.visit_expression(node.expr)
            # 检查返回类型
            if (
                self.current_function_return_type
                and self.current_function_return_type != "void"
                and return_type != "unknown"
                and return_type != self.current_function_return_type
            ):
                self.symbol_table.check_type_compatibility(
                    self.current_function_return_type,
                    return_type,
                    context=" in return statement",
                )
        else:
            # 无返回值的return
            if (
                self.current_function_return_type
                and self.current_function_return_type != "void"
            ):
                self.symbol_table.add_error(
                    "type_mismatch",
                    f"Function expects return type '{self.current_function_return_type}', but no value returned",
                )

    def visit_BlockNode(self, node):
        """访问代码块节点"""
        for stmt in node.statements:
            self.visit(stmt)

    def visit_expression(self, node):
        """访问表达式并返回类型"""
        return self.get_expression_type(node)

    def get_expression_type(self, node):
        """获取表达式的类型"""
        if isinstance(node, NumberNode):
            return "i32"
        elif isinstance(node, BooleanLiteralNode):
            return "bool"
        elif isinstance(node, IdentifierNode):
            var_name = self.get_node_value(node)
            symbol = self.symbol_table.lookup(var_name)
            if symbol:
                return symbol.type
            else:
                self.symbol_table.add_error(
                    "undefined_variable",
                    f"Use of undeclared variable '{var_name}'",
                    self.get_node_line(node),
                    self.get_node_column(node),
                )
                return "unknown"
        elif isinstance(node, BinaryOpNode):
            return self.get_binary_op_type(node)
        elif isinstance(node, UnaryOpNode):
            return self.get_unary_op_type(node)
        elif isinstance(node, FunctionCallNode):
            return self.get_function_call_type(node)
        else:
            return "unknown"

    def get_binary_op_type(self, node):
        """获取二元操作的返回类型"""
        left_type = self.get_expression_type(node.left)
        right_type = self.get_expression_type(node.right)

        operator = (
            self.get_node_value(node.op_token)
            if hasattr(node, "op_token")
            else "unknown"
        )

        # 算术操作符
        if operator in ["+", "-", "*", "/", "%"]:
            if left_type == "i32" and right_type == "i32":
                return "i32"
            elif left_type != "unknown" and right_type != "unknown":
                self.symbol_table.add_error(
                    "type_mismatch",
                    f"Cannot apply operator '{operator}' to types '{left_type}' and '{right_type}'",
                )

        # 比较操作符
        elif operator in ["==", "!=", "<", "<=", ">", ">="]:
            if (
                left_type == right_type
                or left_type == "unknown"
                or right_type == "unknown"
            ):
                return "bool"
            else:
                self.symbol_table.add_error(
                    "type_mismatch",
                    f"Cannot compare types '{left_type}' and '{right_type}'",
                )

        # 逻辑操作符
        elif operator in ["&&", "||"]:
            if left_type == "bool" and right_type == "bool":
                return "bool"
            elif left_type != "unknown" and right_type != "unknown":
                self.symbol_table.add_error(
                    "type_mismatch",
                    f"Logical operator '{operator}' requires bool operands",
                )

        return "unknown"

    def get_unary_op_type(self, node):
        """获取一元操作的返回类型"""
        operand_type = self.get_expression_type(node.expr)
        operator = (
            self.get_node_value(node.op_token)
            if hasattr(node, "op_token")
            else "unknown"
        )

        if operator == "!" and operand_type == "bool":
            return "bool"
        elif operator == "-" and operand_type == "i32":
            return "i32"
        elif operator in ["&", "&mut"]:
            return f"&{operand_type}"
        elif operand_type != "unknown":
            self.symbol_table.add_error(
                "type_mismatch",
                f"Cannot apply operator '{operator}' to type '{operand_type}'",
            )

        return "unknown"

    def get_function_call_type(self, node):
        """获取函数调用的返回类型"""
        if node.callee:
            func_name = self.get_node_value(node.callee)
            symbol = self.symbol_table.lookup(func_name)

            if symbol and symbol.is_function:
                # 检查参数数量
                expected_args = len(symbol.param_types)
                actual_args = len(node.args) if node.args else 0

                if expected_args != actual_args:
                    self.symbol_table.add_error(
                        "function_args",
                        f"Function '{func_name}' expects {expected_args} arguments, found {actual_args}",
                    )

                return symbol.type
            else:
                self.symbol_table.add_error(
                    "undefined_function", f"Use of undeclared function '{func_name}'"
                )

        return "unknown"

"""
Description  : 递归下降语法分析器，支持单遍编译和语法制导翻译
Author       : Hyoung
Date         : 2025-08-18 18:56:41
LastEditTime : 2025-08-18 18:56:43
FilePath     : \\课程设计\\rust-like-compiler\\parser.py
"""

from lexer import (
    Lexer,
    Token,
    TT_EOF,
    TT_KEYWORD,
    TT_IDENTIFIER,
    TT_NUMBER,
    TT_ASSIGN,
    TT_PLUS,
    TT_MINUS,
    TT_MUL,
    TT_DIV,
    TT_EQ,
    TT_NE,
    TT_LT,
    TT_LTE,
    TT_GT,
    TT_GTE,
    TT_LPAREN,
    TT_RPAREN,
    TT_LBRACE,
    TT_RBRACE,
    TT_SEMICOLON,
    TT_COLON,
    TT_COMMA,
    TT_ARROW,
)
from parser_nodes import *
from ir_generator import IRGenerator


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, lexer: Lexer, irgen: IRGenerator = None):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()
        self.irgen = irgen

    def advance(self):
        self.current_token = self.lexer.get_next_token()

    def consume(self, expected_type, expected_value=None):
        token = self.current_token
        if token.type != expected_type:
            raise ParseError(
                f"期望 {expected_type}，但得到 {token.type} at L{token.line}C{token.column}"
            )
        if expected_value is not None and token.value != expected_value:
            raise ParseError(
                f"期望 {expected_value}，但得到 {token.value} at L{token.line}C{token.column}"
            )
        self.advance()
        return token

    def parse(self):
        program = self.parse_program()
        if self.irgen:
            self.irgen.generate(program)
        return program

    # --- 1.1 基础程序 ---
    def parse_program(self):
        declarations = []
        while (
            self.current_token.type == TT_KEYWORD and self.current_token.value == "fn"
        ):
            declarations.append(self.parse_function_decl())
        return ProgramNode(declarations)

    def parse_function_decl(self):
        self.consume(TT_KEYWORD, "fn")
        name_token = self.consume(TT_IDENTIFIER)
        self.consume(TT_LPAREN)
        params = self.parse_param_list()
        self.consume(TT_RPAREN)
        # 支持返回类型
        return_type = None
        if self.current_token.type == TT_ARROW:
            self.advance()
            return_type = self.parse_type()
        # 支持表达式块或语句块
        if self.current_token.type == TT_LBRACE:
            body = self.parse_block()
        else:
            raise ParseError("函数体必须是语句块")
        return FunctionDeclNode(name_token, params, return_type, body)

    def parse_param_list(self):
        params = []
        if self.current_token.type == TT_RPAREN:
            return params
        while True:
            is_mutable = False
            if (
                self.current_token.type == TT_KEYWORD
                and self.current_token.value == "mut"
            ):
                is_mutable = True
                self.advance()
            name_token = self.consume(TT_IDENTIFIER)
            # 类型
            if self.current_token.type == TT_COLON:
                self.advance()
                self.parse_type()  # 类型信息可选，暂不存储
            params.append(ParamNode(name_token, is_mutable))
            if self.current_token.type == TT_COMMA:
                self.advance()
            else:
                break
        return params

    def parse_type(self):
        # 只支持i32，后续可扩展
        if self.current_token.type == TT_KEYWORD and self.current_token.value == "i32":
            self.advance()
            return "i32"
        raise ParseError(f"暂不支持的类型 {self.current_token.value}")

    def parse_block(self):
        self.consume(TT_LBRACE)
        statements = []
        while (
            self.current_token.type != TT_RBRACE and self.current_token.type != TT_EOF
        ):
            statements.append(self.parse_statement())
        self.consume(TT_RBRACE)
        return BlockNode(statements)

    # --- 语句 ---
    def parse_statement(self):
        # ';' 空语句
        if self.current_token.type == TT_SEMICOLON:
            self.advance()
            return EmptyStatementNode()
        # if/else
        if self.current_token.type == TT_KEYWORD and self.current_token.value == "if":
            return self.parse_if_statement()
        # while
        if (
            self.current_token.type == TT_KEYWORD
            and self.current_token.value == "while"
        ):
            return self.parse_while_statement()
        # return
        if (
            self.current_token.type == TT_KEYWORD
            and self.current_token.value == "return"
        ):
            return self.parse_return_statement()
        # let 变量声明
        if self.current_token.type == TT_KEYWORD and self.current_token.value == "let":
            return self.parse_let_statement()
        # 赋值或表达式
        if self.current_token.type == TT_IDENTIFIER:
            # 赋值或表达式语句
            return self.parse_assign_or_expr_statement()
        # 表达式语句
        return self.parse_expr_statement()

    def parse_if_statement(self):
        self.consume(TT_KEYWORD, "if")
        condition = self.parse_expression()
        then_block = self.parse_block()
        else_if_parts = []
        else_block = None
        while (
            self.current_token.type == TT_KEYWORD and self.current_token.value == "else"
        ):
            self.advance()
            if (
                self.current_token.type == TT_KEYWORD
                and self.current_token.value == "if"
            ):
                self.advance()
                cond = self.parse_expression()
                blk = self.parse_block()
                else_if_parts.append({"condition": cond, "block": blk})
            else:
                else_block = self.parse_block()
                break
        return IfNode(condition, then_block, else_if_parts, else_block)

    def parse_while_statement(self):
        self.consume(TT_KEYWORD, "while")
        condition = self.parse_expression()
        body = self.parse_block()
        return WhileNode(condition, body)

    def parse_return_statement(self):
        self.consume(TT_KEYWORD, "return")
        # 支持 return; 或 return expr;
        if self.current_token.type == TT_SEMICOLON:
            self.advance()
            return ReturnNode()
        expr = self.parse_expression()
        self.consume(TT_SEMICOLON)
        return ReturnNode(expr)

    def parse_let_statement(self):
        self.consume(TT_KEYWORD, "let")
        is_mutable = False
        if self.current_token.type == TT_KEYWORD and self.current_token.value == "mut":
            is_mutable = True
            self.advance()
        name_token = self.consume(TT_IDENTIFIER)
        # 类型
        var_type = None
        if self.current_token.type == TT_COLON:
            self.advance()
            var_type = self.parse_type()
        # 初始化
        init_expr = None
        if self.current_token.type == TT_ASSIGN:
            self.advance()
            init_expr = self.parse_expression()
        self.consume(TT_SEMICOLON)
        var_internal = VariableInternalDeclNode(is_mutable, name_token)
        return LetDeclNode(var_internal, var_type, init_expr)

    def parse_assign_or_expr_statement(self):
        # 赋值或表达式
        name_token = self.consume(TT_IDENTIFIER)
        if self.current_token.type == TT_ASSIGN:
            self.advance()
            expr = self.parse_expression()
            self.consume(TT_SEMICOLON)
            return AssignNode(IdentifierNode(name_token), expr)
        # 函数调用 foo();
        if self.current_token.type == TT_LPAREN:
            self.advance()
            args = []
            if self.current_token.type != TT_RPAREN:
                args.append(self.parse_expression())
                while self.current_token.type == TT_COMMA:
                    self.advance()
                    args.append(self.parse_expression())
            self.consume(TT_RPAREN)
            self.consume(TT_SEMICOLON)
            return ExprStatementNode(FunctionCallNode(IdentifierNode(name_token), args))
        # 不是赋值或函数调用，就是其他表达式语句
        expr = self.parse_expression_rest(IdentifierNode(name_token))
        self.consume(TT_SEMICOLON)
        return ExprStatementNode(expr)

    def parse_expr_statement(self):
        expr = self.parse_expression()
        self.consume(TT_SEMICOLON)
        return ExprStatementNode(expr)

    # --- 表达式 ---
    def parse_expression(self):
        return self.parse_comparison()

    def parse_comparison(self):
        node = self.parse_additive()
        while self.current_token.type in (TT_EQ, TT_NE, TT_LT, TT_LTE, TT_GT, TT_GTE):
            op_token = self.current_token
            self.advance()
            right = self.parse_additive()
            node = BinaryOpNode(node, op_token, right)
        return node

    def parse_additive(self):
        node = self.parse_term()
        while self.current_token.type in (TT_PLUS, TT_MINUS):
            op_token = self.current_token
            self.advance()
            right = self.parse_term()
            node = BinaryOpNode(node, op_token, right)
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.current_token.type in (TT_MUL, TT_DIV):
            op_token = self.current_token
            self.advance()
            right = self.parse_factor()
            node = BinaryOpNode(node, op_token, right)
        return node

    def parse_factor(self):
        token = self.current_token
        if token.type == TT_NUMBER:
            self.advance()
            return NumberNode(token)
        if token.type == TT_IDENTIFIER:
            self.advance()
            # 函数调用
            if self.current_token.type == TT_LPAREN:
                self.advance()
                args = []
                if self.current_token.type != TT_RPAREN:
                    args.append(self.parse_expression())
                    while self.current_token.type == TT_COMMA:
                        self.advance()
                        args.append(self.parse_expression())
                self.consume(TT_RPAREN)
                return FunctionCallNode(IdentifierNode(token), args)
            return IdentifierNode(token)
        if token.type == TT_LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.consume(TT_RPAREN)
            return expr
        raise ParseError(f"无法识别的因子: {token}")

    def parse_expression_rest(self, left):
        # 用于处理赋值以外的表达式（如a+b等）
        node = left
        while self.current_token.type in (
            TT_PLUS,
            TT_MINUS,
            TT_MUL,
            TT_DIV,
            TT_EQ,
            TT_NE,
            TT_LT,
            TT_LTE,
            TT_GT,
            TT_GTE,
        ):
            op_token = self.current_token
            self.advance()
            right = self.parse_term()
            node = BinaryOpNode(node, op_token, right)
        return node

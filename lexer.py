"""
Description  : 适用于单遍编译的Rust-like语言词法分析器
Author       : Hyoung
Date         : 2025-08-18 17:36:25
LastEditTime : 2025-08-18 17:36:26
FilePath     : \\课程设计\\rust-like-compiler\\lexer.py
"""

import re


class Token:
    """Token 类表示词法分析器生成的单个 Token"""

    def __init__(self, type, value, line, column):
        """
        初始化 Token 实例
        :param type: Token 类型
        :param value: Token 值
        :param line: Token 所在行号
        :param column: Token 所在列号
        """
        # Token 的类型、值、行号和列号
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        """返回 Token 的字符串表示"""
        return f"Token({self.type}, {repr(self.value)}, L{self.line}C{self.column})"


# --- Token 类型常量 ---
TT_KEYWORD = "KEYWORD"
TT_IDENTIFIER = "IDENTIFIER"
TT_NUMBER = "NUMBER"
TT_STRING = "STRING"  # 添加字符串类型
TT_ASSIGN = "ASSIGN"  # =
TT_PLUS = "PLUS"  # +
TT_MINUS = "MINUS"  # -
TT_MUL = "MUL"  # *
TT_DIV = "DIV"  # /
TT_MOD = "MOD"  # %
TT_EQ = "EQ"  # ==
TT_GT = "GT"  # >
TT_GTE = "GTE"  # >=
TT_LT = "LT"  # <
TT_LTE = "LTE"  # <=
TT_NE = "NE"  # !=
TT_LPAREN = "LPAREN"  # (
TT_RPAREN = "RPAREN"  # )
TT_LBRACE = "LBRACE"  # {
TT_RBRACE = "RBRACE"  # }
TT_LBRACKET = "LBRACKET"  # [
TT_RBRACKET = "RBRACKET"  # ]
TT_SEMICOLON = "SEMICOLON"  # ;
TT_COLON = "COLON"  # :
TT_COMMA = "COMMA"  # ,
TT_ARROW = "ARROW"  # ->
TT_DOT = "DOT"  # .
TT_DOTDOT = "DOTDOT"  # ..
TT_AMPERSAND = "AMPERSAND"  # &
TT_COMMENT = "COMMENT"  # 注释
TT_EOF = "EOF"  # 文件结束

KEYWORDS = [
    "i32",
    "let",
    "if",
    "else",
    "while",
    "return",
    "mut",
    "fn",
    "for",
    "in",
    "loop",
    "break",
    "continue",
    "true",
    "false",
    "bool",
]


class Lexer:
    """Lexer 类用于将源代码转换为 Token 列表"""

    def __init__(self, text):

        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None
        self.line = 1
        self.column = 1

    def advance(self):
        """移动到下一个字符，并更新行号和列号"""
        if self.current_char == "\n":
            self.line += 1
            self.column = 0
        self.pos += 1
        self.column += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def peek(self, lookahead=1):
        """查看下一个字符，不移动指针"""
        peek_pos = self.pos + lookahead
        if peek_pos < len(self.text):
            return self.text[peek_pos]
        return None

    def skip_whitespace(self):
        """跳过空白字符"""
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def skip_comment(self):
        """跳过注释"""
        # 单行注释 //
        if self.current_char == "/" and self.peek() == "/":
            while self.current_char is not None and self.current_char != "\n":
                self.advance()
            return True
        # 块注释 /* ... */
        if self.current_char == "/" and self.peek() == "*":
            self.advance()  # /
            self.advance()  # *
            while self.current_char is not None:
                if self.current_char == "*" and self.peek() == "/":
                    self.advance()
                    self.advance()
                    break
                self.advance()
            return True
        return False

    def number(self):
        """处理数字 Token"""
        result = ""
        start_col = self.column
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return Token(TT_NUMBER, int(result), self.line, start_col)

    def identifier(self):
        """处理标识符或关键字 Token"""
        result = ""
        start_col = self.column
        while self.current_char is not None and (
            self.current_char.isalnum() or self.current_char == "_"
        ):
            result += self.current_char
            self.advance()
        if result in KEYWORDS:
            return Token(TT_KEYWORD, result, self.line, start_col)
        else:
            return Token(TT_IDENTIFIER, result, self.line, start_col)

    def string(self):
        """处理字符串字面量"""
        start_col = self.column
        self.advance()  # 跳过开头的引号
        string_value = ""
        while self.current_char is not None and self.current_char != '"':
            # 处理转义字符
            if self.current_char == "\\":
                self.advance()
                if self.current_char == "n":
                    string_value += "\n"
                elif self.current_char == "t":
                    string_value += "\t"
                elif self.current_char == "r":
                    string_value += "\r"
                elif self.current_char == "\\":
                    string_value += "\\"
                elif self.current_char == '"':
                    string_value += '"'
                else:
                    string_value += "\\" + self.current_char
            else:
                string_value += self.current_char
            self.advance()

        # 检查是否正常结束（遇到结束引号）
        if self.current_char != '"':
            raise Exception(f"Unterminated string at L{self.line}C{start_col}")

        self.advance()  # 跳过结束的引号
        return Token(TT_STRING, string_value, self.line, start_col)

    def get_next_token(self):
        """获取下一个 Token"""
        while self.current_char is not None:
            # 跳过空白
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            # 跳过注释
            if self.current_char == "/" and (self.peek() == "/" or self.peek() == "*"):
                self.skip_comment()
                continue
            start_col = self.column

            # 处理字符串字面量
            if self.current_char == '"':
                return self.string()

            # 多字符操作符优先
            if self.current_char == "=" and self.peek() == "=":
                self.advance()
                self.advance()
                return Token(TT_EQ, "==", self.line, start_col)
            if self.current_char == ">" and self.peek() == "=":
                self.advance()
                self.advance()
                return Token(TT_GTE, ">=", self.line, start_col)
            if self.current_char == "<" and self.peek() == "=":
                self.advance()
                self.advance()
                return Token(TT_LTE, "<=", self.line, start_col)
            if self.current_char == "!" and self.peek() == "=":
                self.advance()
                self.advance()
                return Token(TT_NE, "!=", self.line, start_col)
            if self.current_char == "-" and self.peek() == ">":
                self.advance()
                self.advance()
                return Token(TT_ARROW, "->", self.line, start_col)
            if self.current_char == "." and self.peek() == ".":
                self.advance()
                self.advance()
                return Token(TT_DOTDOT, "..", self.line, start_col)
            # 单字符操作符和分隔符
            if self.current_char == "=":
                self.advance()
                return Token(TT_ASSIGN, "=", self.line, start_col)
            if self.current_char == "+":
                self.advance()
                return Token(TT_PLUS, "+", self.line, start_col)
            if self.current_char == "-":
                self.advance()
                return Token(TT_MINUS, "-", self.line, start_col)
            if self.current_char == "*":
                self.advance()
                return Token(TT_MUL, "*", self.line, start_col)
            if self.current_char == "/":
                self.advance()
                return Token(TT_DIV, "/", self.line, start_col)
            if self.current_char == "%":
                self.advance()
                return Token(TT_MOD, "%", self.line, start_col)
            if self.current_char == ">":
                self.advance()
                return Token(TT_GT, ">", self.line, start_col)
            if self.current_char == "<":
                self.advance()
                return Token(TT_LT, "<", self.line, start_col)
            if self.current_char == "(":
                self.advance()
                return Token(TT_LPAREN, "(", self.line, start_col)
            if self.current_char == ")":
                self.advance()
                return Token(TT_RPAREN, ")", self.line, start_col)
            if self.current_char == "{":
                self.advance()
                return Token(TT_LBRACE, "{", self.line, start_col)
            if self.current_char == "}":
                self.advance()
                return Token(TT_RBRACE, "}", self.line, start_col)
            if self.current_char == "[":
                self.advance()
                return Token(TT_LBRACKET, "[", self.line, start_col)
            if self.current_char == "]":
                self.advance()
                return Token(TT_RBRACKET, "]", self.line, start_col)
            if self.current_char == ";":
                self.advance()
                return Token(TT_SEMICOLON, ";", self.line, start_col)
            if self.current_char == ":":
                self.advance()
                return Token(TT_COLON, ":", self.line, start_col)
            if self.current_char == ",":
                self.advance()
                return Token(TT_COMMA, ",", self.line, start_col)
            if self.current_char == ".":
                self.advance()
                return Token(TT_DOT, ".", self.line, start_col)
            if self.current_char == "&":
                self.advance()
                return Token(TT_AMPERSAND, "&", self.line, start_col)
            # 数字
            if self.current_char.isdigit():
                return self.number()
            # 标识符/关键字
            if self.current_char.isalpha() or self.current_char == "_":
                return self.identifier()
            # 未知字符
            raise Exception(
                f"Unknown character: {self.current_char} at L{self.line}C{self.column}"
            )
        # 文件结束
        return Token(TT_EOF, None, self.line, self.column)

    def tokenize(self):
        """将整个源代码转换为 Token 列表"""
        tokens = []
        token = self.get_next_token()
        while token.type != TT_EOF:
            tokens.append(token)
            token = self.get_next_token()
        tokens.append(token)  # EOF
        return tokens


# --- 测试入口 ---
if __name__ == "__main__":
    code = """
	fn main() {
		let mut x: i32 = 10;
		let y: &i32 = &x;
		if x > 5 {
			x = x - 1;
		}
	}
	"""
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    for t in tokens:
        print(t)

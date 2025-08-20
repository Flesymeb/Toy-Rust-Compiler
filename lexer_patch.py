"""
补丁文件，添加对..和%的支持
"""

from lexer import Token, TT_DOTDOT, TT_MOD


# 修改get_next_token方法中的.和%处理部分
def patch_lexer_get_next_token(lexer_instance):
    original_get_next_token = lexer_instance.get_next_token

    def patched_get_next_token(self):
        """获取下一个 Token，添加对..和%的支持"""
        while self.current_char is not None:
            # 跳过空白字符
            if self.current_char.isspace():
                self.advance()
                continue

            # 处理..运算符
            if self.current_char == "." and self.peek() == ".":
                start_col = self.column
                self.advance()  # 第一个.
                self.advance()  # 第二个.
                return Token(TT_DOTDOT, "..", self.line, start_col)

            # 处理%运算符
            if self.current_char == "%":
                start_col = self.column
                self.advance()
                return Token(TT_MOD, "%", self.line, start_col)

            # 调用原始方法处理其他情况
            return original_get_next_token()

        # 文件结束
        return Token(TT_EOF, None, self.line, self.column)

    # 将方法绑定到实例
    lexer_instance.get_next_token = patched_get_next_token.__get__(lexer_instance)
    return lexer_instance

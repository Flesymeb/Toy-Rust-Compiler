"""
Description  : 适用于单遍编译的Rust-like语言符号表实现
Author       : Hyoung
Date         : 2025-08-20 17:18:03
LastEditTime : 2025-08-20 17:18:03
FilePath     : \\课程设计\\rust-like-compiler\\symbol_table.py
"""

"""
Description  : 适用于单遍编译的Rust-like语言符号表实现
Author       : Hyoung
Date         : 2025-08-20 17:18:03
LastEditTime : 2025-08-20 17:18:03
FilePath     : \\课程设计\\rust-like-compiler\\symbol_table.py
"""

# symbol_table.py


class Symbol:
    def __init__(self, name, sym_type, is_mutable=False, line=None, col=None):
        self.name = name
        self.type = sym_type  # e.g., 'i32', 'bool', or a function type object
        self.is_mutable = is_mutable
        self.line = line  # 定义所在行
        self.col = col  # 定义所在列
        self.is_used = False  # 是否被使用过
        self.is_function = False  # 是否为函数


class FunctionSymbol(Symbol):
    def __init__(self, name, return_type, param_types, line=None, col=None):
        super().__init__(name, return_type, False, line, col)
        self.param_types = param_types  # 参数类型列表
        self.is_function = True


class CompilerError:
    def __init__(self, error_type, message, line=None, col=None, suggestion=None):
        self.error_type = error_type  # 'syntax', 'semantic', 'type', 'scope'
        self.message = message
        self.line = line
        self.col = col
        self.suggestion = suggestion  # 修复建议


class SymbolTable:
    def __init__(self):
        self.scopes = [{}]  # 全局作用域
        self.errors = []  # 错误列表
        self.scope_level = 0  # 当前作用域层级

    def enter_scope(self):
        self.scopes.append({})
        self.scope_level += 1

    def exit_scope(self):
        if len(self.scopes) > 1:
            # 检查未使用的变量
            current_scope = self.scopes[-1]
            for symbol in current_scope.values():
                if not symbol.is_used and not symbol.is_function:
                    self.add_warning(
                        "unused_variable",
                        f"Variable '{symbol.name}' is defined but never used",
                        symbol.line,
                        symbol.col,
                        f"Consider removing unused variable '{symbol.name}'",
                    )

            self.scopes.pop()
            self.scope_level -= 1

    def define(self, symbol):
        # 在Rust中，变量遮蔽是允许的，所以在同一作用域重定义变量是合法的
        current_scope = self.scopes[-1]

        if symbol.name in current_scope:
            # 在Rust中这是变量遮蔽，不是错误
            existing = current_scope[symbol.name]
            # 标记被遮蔽的变量为已使用，避免"未使用"警告
            existing.is_used = True

            # 给一个信息性的警告
            self.add_warning(
                "variable_shadowing",
                f"Variable '{symbol.name}' shadows a previous declaration",
                symbol.line,
                symbol.col,
                f"Previous declaration was at line {existing.line}",
            )

        current_scope[symbol.name] = symbol
        return True

    def lookup(self, name, mark_used=True):
        for scope in reversed(self.scopes):
            if name in scope:
                symbol = scope[name]
                if mark_used:
                    symbol.is_used = True
                return symbol
        return None

    def lookup_current_scope(self, name):
        """只在当前作用域查找"""
        if name in self.scopes[-1]:
            return self.scopes[-1][name]
        return None

    def add_error(self, error_type, message, line=None, col=None, suggestion=None):
        error = CompilerError(error_type, message, line, col, suggestion)
        self.errors.append(error)

    def add_warning(self, error_type, message, line=None, col=None, suggestion=None):
        # 警告也作为错误处理，但类型标记为warning
        error = CompilerError(f"warning_{error_type}", message, line, col, suggestion)
        self.errors.append(error)

    def check_assignment(self, var_name, line=None, col=None):
        """检查变量赋值是否合法"""
        symbol = self.lookup(var_name, mark_used=True)  # 赋值也算使用
        if not symbol:
            self.add_error(
                "undefined_variable",
                f"Use of undeclared variable '{var_name}'",
                line,
                col,
                f"Declare variable '{var_name}' before using it",
            )
            return False

        if not symbol.is_mutable:
            self.add_error(
                "immutable_assignment",
                f"Cannot assign to immutable variable '{var_name}'",
                line,
                col,
                f"Consider declaring '{var_name}' as 'mut {var_name}' to make it mutable",
            )
            return False

        return True

    def check_type_compatibility(
        self, expected_type, actual_type, line=None, col=None, context=""
    ):
        """检查类型兼容性"""
        if expected_type != actual_type:
            self.add_error(
                "type_mismatch",
                f"Type mismatch{context}: expected '{expected_type}', found '{actual_type}'",
                line,
                col,
                f"Convert the value to type '{expected_type}' or change the expected type",
            )
            return False
        return True

    def get_errors_by_type(self, error_type):
        """获取特定类型的错误"""
        return [error for error in self.errors if error.error_type == error_type]

    def has_errors(self):
        """检查是否有错误（不包括警告）"""
        return any(not error.error_type.startswith("warning_") for error in self.errors)

    def clear_errors(self):
        """清空错误列表"""
        self.errors.clear()

    def format_errors(self):
        """格式化错误信息用于显示"""
        if not self.errors:
            return "No errors found."

        formatted = []
        for error in self.errors:
            prefix = "Warning" if error.error_type.startswith("warning_") else "Error"
            location = (
                f" at line {error.line}, column {error.col}" if error.line else ""
            )
            message = f"{prefix}{location}: {error.message}"
            if error.suggestion:
                message += f"\n  Suggestion: {error.suggestion}"
            formatted.append(message)

        return "\n".join(formatted)

"""
Description  :
Author       : Hyoung
Date         : 2025-08-18 18:28:00
LastEditTime : 2025-08-18 18:28:01
FilePath     : \\课程设计\\rust-like-compiler\\ir_generator.py
"""

# ir_generator.py

import sys
from collections import namedtuple

# 确保你的 parser_nodes 和 lexer 文件在 Python 路径中
from parser_nodes import *
from lexer import *  # 导入 TT_* 常量

# 定义四元式结构
# op: 操作符 (字符串)
# arg1: 第一个操作数 (变量名, 常量, 临时变量名, 标签名, 或 None)
# arg2: 第二个操作数 (同上)
# result: 结果存放处 (变量名, 临时变量名, 标签名, 或 None)
Quadruple = namedtuple("Quadruple", ["op", "arg1", "arg2", "result"])


class IRGenerator:
    """
    通过访问 AST 节点生成四元式中间代码。
    """

    def __init__(self):
        self.quads = []  # 存储生成的四元式列表
        self.temp_count = 0  # 临时变量计数器 (t0, t1, ...)
        self.label_count = 0  # 标签计数器 (L0, L1, ...)
        # 循环标签栈，用于 break 和 continue 跳转
        # 每个元素是 (continue_label, break_label)
        self.loop_stack = []

    def new_temp(self):
        """生成一个新的唯一的临时变量名"""
        temp_name = f"t{self.temp_count}"
        self.temp_count += 1
        return temp_name

    def new_label(self):
        """生成一个新的唯一的标签名"""
        label_name = f"L{self.label_count}"
        self.label_count += 1
        return label_name

    def emit(self, op, arg1=None, arg2=None, result=None):
        """创建并添加一个新的四元式到列表中"""
        # 对字符串参数进行处理，避免与数字混淆（可选）
        arg1_repr = (
            f"'{arg1}'"
            if isinstance(arg1, str)
            and not arg1.startswith("t")
            and not arg1.startswith("L")
            else arg1
        )
        arg2_repr = (
            f"'{arg2}'"
            if isinstance(arg2, str)
            and not arg2.startswith("t")
            and not arg2.startswith("L")
            else arg2
        )
        result_repr = (
            f"'{result}'"
            if isinstance(result, str)
            and not result.startswith("t")
            and not result.startswith("L")
            else result
        )

        # 实际存储时不加引号，引号主要用于打印区分
        self.quads.append(Quadruple(op, arg1, arg2, result))
        # print(f"Emit: ({op}, {arg1}, {arg2}, {result})") # 用于调试

    def generate(self, node: ASTNode):
        """公共接口，开始生成整个程序的中间代码"""
        self.quads = []
        self.temp_count = 0
        self.label_count = 0
        self.loop_stack = []
        self.visit(node)
        return self.quads

    # --- 访问者方法 ---
    def visit(self, node):
        """调度到特定节点类型的访问方法 (Visitor Pattern)"""
        if node is None:
            return None
        method_name = "visit_" + type(node).__name__
        # 获取对应节点类型的 visit 方法，如果找不到，则使用 generic_visit
        visitor = getattr(self, method_name, self.generic_visit)
        # print(f"Visiting: {type(node).__name__} with {visitor.__name__}") # 调试信息
        return visitor(node)

    def generic_visit(self, node):
        """处理未明确实现 visit 方法的 AST 节点"""
        # print(f"警告: 没有为 {type(node).__name__} 节点类型实现特定的 visit 方法。")
        # 默认行为：递归访问子节点（如果它们是 ASTNode 或列表）
        if isinstance(node, ASTNode):
            for attr_name in vars(node):
                if attr_name.startswith("_"):
                    continue  # 跳过内部属性
                attr_value = getattr(node, attr_name)
                if isinstance(attr_value, list):
                    for item in attr_value:
                        if isinstance(item, ASTNode):
                            self.visit(item)
                elif isinstance(attr_value, ASTNode):
                    self.visit(attr_value)
        return None  # 通常，通用访问不返回 IR 值

    # --- 程序结构 ---
    def visit_ProgramNode(self, node: ProgramNode):
        for decl in node.declarations:
            self.visit(decl)

    def visit_FunctionDeclNode(self, node: FunctionDeclNode):
        func_name = node.name  # 使用修改后的 name 属性，它已经是字符串了
        param_count = len(node.params)
        self.emit(
            "FUNC_BEGIN", func_name, param_count, None
        )  # 操作符, 函数名, 参数个数, None

        # （可选）为参数生成 PARAM_DECL 四元式，如果后端需要
        # for param in node.params:
        #     param_name = param.name_internal.name.value
        #     self.emit('PARAM_DECL', param_name, None, None)

        # 访问函数体
        self.visit(node.body)

        # 确保函数有结束标记
        # （可选）如果函数声明了非 void 返回类型但没有显式 return，可能需要添加隐式 return 或报错
        # 简化处理：仅添加结束标记

        self.emit("FUNC_END", func_name, None, None)

    def visit_BlockNode(self, node: BlockNode):
        # 顺序访问块内的所有语句
        for stmt in node.statements:
            self.visit(stmt)
        # 如果要支持 Rust 风格的块表达式返回值：
        # 需要检查最后一条语句是否是表达式且无分号，
        # 如果是，则其结果是块的结果（需要解析器配合标记）
        # 此处简化为语句块不返回值

    # --- 语句 ---
    def visit_EmptyStatementNode(self, node: EmptyStatementNode):
        # 空语句不生成代码
        pass

    def visit_LetDeclNode(self, node: LetDeclNode):
        var_name = node.var_internal_decl.name.value
        # 可选：发出声明四元式，如果目标代码需要显式声明
        # self.emit('DECLARE', var_name, type_info, None)

        if node.init_expr:
            # 计算初始化表达式的值，结果可能是常量或临时变量
            init_value = self.visit(node.init_expr)
            # 将初始值赋给变量
            self.emit("ASSIGN", init_value, None, var_name)

    def visit_AssignNode(self, node: AssignNode):
        # 1. 计算右侧表达式的值
        rhs_value = self.visit(node.expr)

        # 2. 处理左侧可赋值元素
        if isinstance(node.assignable_element, IdentifierNode):
            # 简单变量赋值，通过token.value获取变量名
            lvalue_name = node.assignable_element.token.value
            self.emit("ASSIGN", rhs_value, None, lvalue_name)

        elif isinstance(node.assignable_element, ArrayAccessNode):
            # 数组元素赋值 a[i] = val
            array_ref = self.visit(
                node.assignable_element.array_expr
            )  # 数组名或基址临时变量
            index_val = self.visit(
                node.assignable_element.index_expr
            )  # 索引值或临时变量
            # 需要特定指令或地址计算
            self.emit(
                "ARR_STORE", rhs_value, index_val, array_ref
            )  # 操作符, 值, 索引, 数组

        elif isinstance(node.assignable_element, TupleAccessNode):
            # 元组元素赋值 t.0 = val
            tuple_ref = self.visit(
                node.assignable_element.tuple_expr
            )  # 元组名或基址临时变量
            index_val = int(node.assignable_element.index_token.value)  # 直接索引值
            # 需要特定指令或地址计算
            self.emit(
                "TUP_STORE", rhs_value, index_val, tuple_ref
            )  # 操作符, 值, 索引, 元组
        else:
            print(
                f"错误: 不支持的左值类型 {type(node.assignable_element).__name__} 在赋值语句中"
            )

    def visit_ReturnNode(self, node: ReturnNode):
        return_value = None
        if node.expr:
            # 计算返回值表达式
            return_value = self.visit(node.expr)
        # 发出返回四元式
        self.emit(
            "RETURN", return_value, None, None
        )  # 操作符, 返回值(或None), None, None

    def visit_ExprStatementNode(self, node: ExprStatementNode):
        # 计算表达式，但忽略其结果（例如，调用函数只为了副作用）
        self.visit(node.expr)

    # --- 表达式 ---
    def visit_NumberNode(self, node: NumberNode):
        # 数字常量直接返回其值
        return node.value

    def visit_BooleanLiteralNode(self, node: BooleanLiteralNode):
        # 布尔常量返回其值 (True/False) 或整数表示 (1/0)
        return 1 if node.value else 0  # 使用 1/0 便于条件跳转

    def visit_IdentifierNode(self, node: IdentifierNode):
        # 标识符（变量）返回其名称
        return node.token.value

    def visit_BinaryOpNode(self, node: BinaryOpNode):
        # 1. 计算左操作数
        left_operand = self.visit(node.left)
        # 2. 计算右操作数
        right_operand = self.visit(node.right)
        # 3. 创建一个新的临时变量来存储结果
        result_temp = self.new_temp()

        # 4. 映射词法单元类型到四元式操作符
        op_map = {
            TT_PLUS: "ADD",
            TT_MINUS: "SUB",
            TT_MUL: "MUL",
            TT_DIV: "DIV",
            TT_MOD: "MOD",  # 添加对模运算的支持
            TT_EQ: "EQ",
            TT_NE: "NE",
            TT_LT: "LT",
            TT_LTE: "LTE",
            TT_GT: "GT",
            TT_GTE: "GTE",
            # TODO: 添加逻辑运算符 (AND, OR) 的处理，可能涉及短路求值和跳转
        }
        ir_op = op_map.get(node.op_token.type)

        if ir_op:
            # 5. 发出计算四元式
            self.emit(ir_op, left_operand, right_operand, result_temp)
            # 6. 返回存储结果的临时变量名
            return result_temp
        else:
            print(f"错误: 未处理的二元运算符 {node.op_token.value}")
            return None  # 表示错误或未知结果

    def visit_UnaryOpNode(self, node: UnaryOpNode):
        # 1. 计算操作数
        operand = self.visit(node.expr)
        # 2. 创建临时变量存结果
        result_temp = self.new_temp()

        # 3. 根据操作符发出四元式
        if node.op_token.type == TT_MINUS:
            # 一元负号
            self.emit("NEG", operand, None, result_temp)  # NEG: 取负操作
        # elif node.op_token.type == TT_NOT: # 假设有逻辑非
        #     self.emit('NOT', operand, None, result_temp)
        else:
            print(f"错误: 未处理的一元运算符 {node.op_token.value}")
            return None

        # 4. 返回结果临时变量
        return result_temp

    def visit_FunctionCallNode(self, node: FunctionCallNode):
        # 从函数表达式获取函数名
        if isinstance(node.func_expr, IdentifierNode):
            func_name = node.func_expr.token.value
        else:
            func_name = str(node.func_expr)
        arg_values = [self.visit(arg) for arg in node.args]
        for arg_val in reversed(arg_values):
            self.emit("PARAM", arg_val, None, None)
        result_temp = self.new_temp()
        self.emit("CALL", func_name, len(arg_values), result_temp)
        return result_temp

    # --- 控制流 ---
    def visit_IfNode(self, node: IfNode):
        # --- 处理主 if ---
        # 1. 计算条件表达式
        condition_result = self.visit(node.condition)
        # 2. 创建标签
        label_after_then = self.new_label()  # if 为 false 时跳转的目标
        label_after_if_else = self.new_label()  # 整个 if-else 结构结束后的目标

        # 3. 发出条件跳转
        self.emit("IF_FALSE_GOTO", condition_result, None, label_after_then)
        # 4. 访问 then 块
        self.visit(node.then_block)
        # 5. then 块结束后无条件跳转到 if-else 结束处 (如果后面有 else/else if)
        if node.else_if_parts or node.else_block:
            self.emit("GOTO", None, None, label_after_if_else)

        # --- 处理 else if ---
        current_false_label = label_after_then  # 第一个 false 跳转目标
        for i, part in enumerate(node.else_if_parts):
            # 放置上一个 false 跳转的目标标签
            self.emit("LABEL", None, None, current_false_label)
            # 计算 else if 的条件
            elseif_cond_result = self.visit(part["condition"])
            # 创建下一个 false 跳转标签
            next_false_label = self.new_label()
            # 发出条件跳转
            self.emit("IF_FALSE_GOTO", elseif_cond_result, None, next_false_label)
            # 访问 else if 块
            self.visit(part["block"])
            # else if 块结束后无条件跳转到 if-else 结束处
            self.emit("GOTO", None, None, label_after_if_else)
            # 更新当前 false 跳转目标为下一个
            current_false_label = next_false_label

        # --- 处理 else ---
        # 放置最后一个 false 跳转的目标标签
        self.emit("LABEL", None, None, current_false_label)
        if node.else_block:
            # 访问 else 块
            self.visit(node.else_block)
            # else 块自然执行到 if-else 结束处，无需 GOTO

        # 放置整个 if-else 结构结束后的标签
        self.emit("LABEL", None, None, label_after_if_else)

    def visit_WhileNode(self, node: WhileNode):
        # 1. 创建循环开始（条件判断前）和循环结束的标签
        label_loop_start = self.new_label()
        label_loop_end = self.new_label()

        # 2. 将标签入栈，供 break/continue 使用
        # (continue 跳转到 label_loop_start, break 跳转到 label_loop_end)
        self.loop_stack.append((label_loop_start, label_loop_end))

        # 3. 放置循环开始标签
        self.emit("LABEL", None, None, label_loop_start)
        # 4. 计算循环条件
        condition_result = self.visit(node.condition)
        # 5. 如果条件为假，跳转到循环结束标签
        self.emit("IF_FALSE_GOTO", condition_result, None, label_loop_end)
        # 6. 访问循环体
        self.visit(node.body)
        # 7. 循环体结束后，无条件跳转回循环开始处进行下一次条件判断
        self.emit("GOTO", None, None, label_loop_start)
        # 8. 放置循环结束标签
        self.emit("LABEL", None, None, label_loop_end)

        # 9. 循环结束，将标签出栈
        self.loop_stack.pop()

    def visit_ForNode(self, node: ForNode):
        # 语法：for var in start..end { body }
        # desugar 成 while 循环:
        # let mut iter_var = start;
        # let end_val = end;
        # while iter_var < end_val {
        #     let var = iter_var; // shadowing or direct use
        #     { body }
        #     iter_var = iter_var + 1;
        # }

        # 1. 获取循环变量名 (内部用，不直接暴露给 body，除非 body 里重声明)
        loop_counter_temp = self.new_temp()  # 用作迭代计数器
        loop_var_name = node.var_internal_decl.name.value  # 用户指定的变量名

        # 2. 计算起始值和结束值
        start_val = self.visit(node.iterable.start_expr)
        end_val = self.visit(node.iterable.end_expr)

        # 3. 初始化计数器
        self.emit("ASSIGN", start_val, None, loop_counter_temp)

        # 4. 创建循环标签
        label_loop_start = self.new_label()
        label_loop_end = self.new_label()

        # 5. 循环标签入栈
        self.loop_stack.append(
            (label_loop_start, label_loop_end)
        )  # continue 回到增量前，break 跳出

        label_increment = self.new_label()  # continue 跳转到增量的地方
        self.loop_stack[-1] = (label_increment, label_loop_end)  # 更新 continue 目标

        # 6. 循环开始标签
        self.emit("LABEL", None, None, label_loop_start)

        # 7. 条件判断: iter_var < end_val
        condition_temp = self.new_temp()
        self.emit("LT", loop_counter_temp, end_val, condition_temp)  # t = counter < end
        self.emit(
            "IF_FALSE_GOTO", condition_temp, None, label_loop_end
        )  # if !t goto end

        # 8. 在循环体内 "声明" 循环变量 (实际是赋值)
        self.emit("ASSIGN", loop_counter_temp, None, loop_var_name)

        # 9. 访问循环体
        self.visit(node.body)

        # 10. continue 跳转点: 递增计数器
        self.emit("LABEL", None, None, label_increment)
        self.emit(
            "ADD", loop_counter_temp, 1, loop_counter_temp
        )  # counter = counter + 1

        # 11. 跳转回循环开始
        self.emit("GOTO", None, None, label_loop_start)

        # 12. 循环结束标签
        self.emit("LABEL", None, None, label_loop_end)

        # 13. 循环标签出栈
        self.loop_stack.pop()

    def visit_LoopNode(self, node: LoopNode):
        # 无条件循环 loop { body }
        label_loop_start = self.new_label()
        label_loop_end = self.new_label()  # break 跳转目标

        # continue 跳转目标是循环开始
        self.loop_stack.append((label_loop_start, label_loop_end))

        self.emit("LABEL", None, None, label_loop_start)
        self.visit(node.body)
        self.emit("GOTO", None, None, label_loop_start)  # 无条件跳回开始
        self.emit("LABEL", None, None, label_loop_end)

        self.loop_stack.pop()

    def visit_BreakNode(self, node: BreakNode):
        if not self.loop_stack:
            print("严重错误: Break 在循环外 (IR 生成阶段)")  # 语义分析应已捕获
            return
        # PDF 7.4: break <expr>; 允许带值跳出 loop 表达式
        # 当前简化：不处理 break 的返回值
        if node.expr:
            print("警告: 当前 IR 生成器忽略 break 表达式的值。")
            # 如果需要处理：
            # break_value = self.visit(node.expr)
            # self.emit('SET_LOOP_RETVAL', break_value, None, None) # 假设有指令

        break_label = self.loop_stack[-1][1]  # 获取 break 跳转目标 (end_label)
        self.emit("GOTO", None, None, break_label)

    def visit_ContinueNode(self, node: ContinueNode):
        if not self.loop_stack:
            print("严重错误: Continue 在循环外 (IR 生成阶段)")  # 语义分析应已捕获
            return
        continue_label = self.loop_stack[-1][
            0
        ]  # 获取 continue 跳转目标 (start_label 或 increment_label)
        self.emit("GOTO", None, None, continue_label)

    # --- 7.1 函数表达式块 ---
    def visit_FunctionExprNode(self, node: FunctionExprNode):
        # 处理函数表达式块内的所有语句
        for i, item in enumerate(node.items):
            # 最后一项是表达式，作为返回值
            if i == len(node.items) - 1 and isinstance(item, ExpressionNode):
                result = self.visit(item)
                return result
            else:
                self.visit(item)

        # 如果没有最后的表达式，则返回空
        return None

    # --- 7.3 选择表达式 ---
    def visit_IfExprNode(self, node: IfExprNode):
        # 生成条件判断的中间代码
        condition_temp = self.visit(node.condition)

        # 创建标签
        then_label = self.new_label()
        else_label = self.new_label()
        end_label = self.new_label()

        # 生成条件跳转代码
        self.emit("IF_FALSE_GOTO", condition_temp, None, else_label)

        # 生成then部分代码
        self.emit("LABEL", None, None, then_label)
        then_result = self.visit(node.then_expr_block)
        result_temp = self.new_temp()
        self.emit("ASSIGN", then_result, None, result_temp)
        self.emit("GOTO", None, None, end_label)

        # 生成else部分代码
        self.emit("LABEL", None, None, else_label)
        else_result = self.visit(node.else_expr_block)
        self.emit("ASSIGN", else_result, None, result_temp)

        # 结束标签
        self.emit("LABEL", None, None, end_label)

        return result_temp

    # --- 复合类型相关 (需要根据目标架构细化) ---

    def visit_ArrayLiteralNode(self, node: ArrayLiteralNode):
        # [1, 2, 3]
        element_values = [self.visit(elem) for elem in node.elements]
        array_size = len(element_values)
        # IR 需要表示数组的创建和初始化
        # 可能是分配内存 + 循环赋值，或者一个高级指令
        array_ref = self.new_temp()  # 假设这个 temp 代表数组引用或基地址
        # 简化：使用一个占位指令
        self.emit("ARR_INIT", element_values, array_size, array_ref)
        return array_ref

    def visit_ArrayAccessNode(self, node: ArrayAccessNode):
        # a[i] (作为右值读取)
        array_ref = self.visit(node.array_expr)
        index_val = self.visit(node.index_expr)
        result_temp = self.new_temp()
        # 简化：使用占位指令
        self.emit(
            "ARR_LOAD", array_ref, index_val, result_temp
        )  # 操作符, 数组, 索引, 结果存放处
        return result_temp

    def visit_TupleLiteralNode(self, node: TupleLiteralNode):
        # (1, true, c)
        element_values = [self.visit(elem) for elem in node.elements]
        tuple_size = len(element_values)
        tuple_ref = self.new_temp()
        # 简化：使用占位指令
        self.emit("TUP_INIT", element_values, tuple_size, tuple_ref)
        return tuple_ref

    def visit_TupleAccessNode(self, node: TupleAccessNode):
        # t.0 (作为右值读取)
        tuple_ref = self.visit(node.tuple_expr)
        index_val = int(node.index_token.value)  # 元组索引是字面量
        result_temp = self.new_temp()
        # 简化：使用占位指令
        self.emit(
            "TUP_LOAD", tuple_ref, index_val, result_temp
        )  # 操作符, 元组, 索引, 结果存放处
        return result_temp

    # --- 尚未处理或需要细化的节点 ---
    # FunctionExprNode, IfExprNode, LoopExprNode: 如果作为表达式返回值，需要特殊处理
    # TypeNode, ParamNode, VariableInternalDeclNode: 通常在声明节点中处理，自身不直接生成执行代码
    # RangeNode: 在 ForNode 中处理

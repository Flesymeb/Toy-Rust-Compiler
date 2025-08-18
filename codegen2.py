"""
Description  : 适用于单遍编译的Rust-like语言MIPS汇编代码生成器
Author       : Hyoung
Date         : 2025-08-19 17:44:49
LastEditTime : 2025-08-19 17:44:49
FilePath     : \\课程设计\\rust-like-compiler\\codegen2.py
"""

from collections import defaultdict

"""
寄存器分配与内存管理
"""


class RegManager:
    def __init__(self):
        self.RValue = defaultdict(set)  # 寄存器中存放的变量
        self.AValue = defaultdict(set)  # 变量存放的位置（寄存器或内存）
        self.num_registers = 8
        self.frame_size = 0  # 当前栈帧大小
        self.free_registers = []  # 当前空闲的寄存器
        self.memory = {}  # 记录变量在内存中临时存储的地址
        self.func_vars = {}  # 当前的局部变量
        self.data_vars = {}  # 全局变量（数据段）

    # 清空某变量所占用的寄存器
    def freeVarRegisters(self, var):
        # 全局变量不清空
        if var in self.data_vars - self.func_vars:
            return
        for pos in self.AValue[var]:
            if pos != "Memory":
                self.RValue[pos].remove(var)
                if len(self.RValue[pos]) == 0:
                    self.free_registers.append(pos)
        self.AValue[var].clear()

    # 清空所有寄存器（基本块开始前）
    def freeAllRegisters(self, in_set):
        self.RValue.clear()
        self.AValue.clear()
        for var in in_set:
            self.AValue[var].add("Memory")
        self.free_registers = [
            f"$s{self.num_registers - i - 1}" for i in range(self.num_registers)
        ]

    # 将变量存储到内存中
    def storeVariable(self, var, reg, codes):
        if var not in self.memory:
            self.memory[var] = self.frame_size
            self.frame_size += 4
        self.AValue[var].add("Memory")
        # 局部变量或中间变量
        if var in self.func_vars or var[0] == "T" or var[0] == "t":
            codes.append(f"sw {reg}, {self.memory[var]}($sp)")
        elif var in self.data_vars:
            codes.append(f"sw {reg}, {var}")

    # 将当前基本块的出口活跃变量存储到内存中
    def storeOutSet(self, out_set, codes):
        for var in out_set:
            reg = None
            for pos in self.AValue[var]:
                # 已经在memory中则不用再存储
                if pos == "Memory":
                    reg = None
                    break
                else:
                    reg = pos

            if reg:
                self.storeVariable(var, reg, codes)

    # 分配一个新的寄存器
    def allocateFreeRegister(self, quadruples, cur_quad_index, out_set, codes):
        free_reg = ""
        # 有寄存器空闲，则直接分配
        if len(self.free_registers):
            free_reg = self.free_registers.pop()
            return free_reg

        # 若无，则需要寻找最远引用的变量让渡寄存器
        farest_usepos = float("-inf")
        for reg, vars in self.RValue.items():
            cur_usepos = float("inf")
            # 看看存在这个reg中引用最近的那个var
            for var in vars:
                # 如果存在别的地方，则很好
                if len(self.AValue[var]) > 1:  # 不只在当前寄存器里
                    continue

                for idx in range(cur_quad_index, len(quadruples)):
                    quad = quadruples[idx]
                    if var in [quad[1], quad[2]]:
                        cur_usepos = min(cur_usepos, idx - cur_quad_index)
                        break
                    if var == quad[3]:
                        break

            if cur_usepos == float("inf"):
                free_reg = reg
                break
            elif cur_usepos > farest_usepos:
                farest_usepos = cur_usepos
                free_reg = reg

        # 释放寄存器，保存数据
        for var in list(self.RValue[free_reg]):
            self.AValue[var].remove(free_reg)
            # 若无其他地方存数据，才需要sw
            if len(self.AValue[var]) == 0:
                need_store = None
                for idx in range(cur_quad_index, len(quadruples)):
                    quad = quadruples[idx]
                    if var in [quad[1], quad[2]]:
                        need_store = True
                        break
                    if var == quad[3]:
                        break
                if need_store is None:  # 没有被引用、定值，检查是不是出口活跃
                    need_store = True if var in out_set else False
                if need_store:
                    self.storeVariable(var, free_reg, codes)

        self.RValue[free_reg].clear()

        return free_reg

    def _is_variable(self, name) -> bool:
        if name is None:
            return False
        return isinstance(name, str) and (
            name[0].isalpha() or (name[0] == "-" and name != "-")
        )

    # 为四元式的src获取寄存器
    def getSrcRegister(self, src, quadruples, cur_quad_index, out_set, codes):
        reg = ""
        # 先查AValue有无现成
        for pos in self.AValue[src]:
            if pos != "Memory":
                return pos

        # 没有则分配一个
        reg = self.allocateFreeRegister(quadruples, cur_quad_index, out_set, codes)

        if self._is_variable(src):
            # 局部变量或中间变量
            if src in self.func_vars or src[0] == "T" or src[0] == "t":
                codes.append(f"lw {reg}, {self.memory[src]}($sp)")
            elif src in self.data_vars:
                codes.append(f"lw {reg}, {src}")
            # 更新AValue RValue
            self.AValue[src].add(reg)
            self.RValue[reg].add(src)
        else:  # 立即数
            codes.append(f"li {reg}, {src}")

        return reg

    # 为四元式的tar获取寄存器
    def getTarRegister(self, tar, quadruples, cur_quad_index, out_set, codes):
        quad = quadruples[cur_quad_index]
        src1 = quad[1]
        # 看能否复用操作数的寄存器
        # 首先保证src1不是数字
        # 其次不抢占全局变量的寄存器
        if self._is_variable(src1) and src1 not in (self.data_vars - self.func_vars):
            for pos in self.AValue[src1]:
                if pos != "Memory" and len(self.RValue[pos]) == 1:
                    # 判断src1之后是否还会被使用（这里简化了，可以改进）
                    still_active = False
                    for idx in range(cur_quad_index + 1, len(quadruples)):
                        if quadruples[idx][1] == src1 or quadruples[idx][2] == src1:
                            still_active = True
                            break

                    if not still_active:
                        self.RValue[pos].remove(src1)
                        self.RValue[pos].add(tar)
                        self.AValue[src1].remove(pos)
                        self.AValue[tar].add(pos)
                        return pos

        # 重新分配
        reg = self.allocateFreeRegister(quadruples, cur_quad_index, out_set, codes)
        self.RValue[reg].add(tar)
        self.AValue[tar].add(reg)

        return reg


"""
MIPS目标代码生成器
"""


class MIPSCodeGenerator:
    def __init__(self, quadruples, variables=None, functions=None):
        self.quadruples = quadruples
        # 自动收集所有变量名（非立即数、非label、非函数名）
        all_vars = set()
        func_names = set()
        # 先收集所有函数名
        for quad in quadruples:
            if quad[0] == "FUNC_BEGIN" and isinstance(quad[1], str):
                func_names.add(quad[1])
        # 收集变量，排除所有函数名
        for quad in quadruples:
            op = quad[0]
            for v in quad[1:]:
                if (
                    isinstance(v, str)
                    and v != None
                    and v.isidentifier()
                    and not v.isupper()
                    and not v.startswith("L")
                    and op not in ("LABEL", "GOTO", "CALL")
                    and v not in func_names
                ):
                    all_vars.add(v)
        if variables:
            all_vars |= set(variables)
        self.variables = all_vars
        self.functions = functions or set()
        self.asm_lines = []
        self.param_list = []  # param传递的参数，每个基本块都要清空
        self.regManager = RegManager()
        self.regManager.data_vars = self.variables
        self.basic_blocks = []
        self.current_func = None
        self.build_basic_blocks()

    def build_basic_blocks(self):
        """构建基本块（简化版，仅用于寄存器分配）"""
        blocks = []
        current_block = []
        leader_indices = set([0])  # 第一条指令是leader

        # 找出所有leader指令的索引
        for i, quad in enumerate(self.quadruples):
            if quad[0] in ("GOTO", "IF_FALSE_GOTO"):
                # 跳转目标的下一条指令是leader
                for j, q in enumerate(self.quadruples):
                    if q[0] == "LABEL" and q[3] == quad[3]:
                        leader_indices.add(j)
                        break
                # 跳转指令的下一条指令是leader
                if i + 1 < len(self.quadruples):
                    leader_indices.add(i + 1)
            elif quad[0] == "FUNC_BEGIN":
                leader_indices.add(i)

        # 根据leader划分基本块
        leaders = sorted(list(leader_indices))
        for i in range(len(leaders)):
            start = leaders[i]
            end = leaders[i + 1] if i + 1 < len(leaders) else len(self.quadruples)
            block = self.quadruples[start:end]
            if block:
                blocks.append(
                    {
                        "quads": block,
                        "in_set": set(),  # 简化版，不做活跃变量分析
                        "out_set": set(),
                    }
                )

        self.basic_blocks = blocks
        return blocks

    def gen_data_section(self):
        self.asm_lines.append(".data")
        for var in sorted(self.variables):
            self.asm_lines.append(f"{var}: .word 0")
        self.asm_lines.append("")

    def gen_text_section(self):
        self.asm_lines.append(".text")
        self.asm_lines.append("lui $sp, 0x1004")
        self.asm_lines.append("j main")
        self.asm_lines.append("")

    def gen_func_prologue(self, func):
        self.asm_lines.append(f"{func}:")
        if func != "main":
            self.asm_lines.append("\tsw $ra, 4($sp)")  # 保存返回地址

        # 为局部变量预留空间
        self.regManager.frame_size = 8 if func != "main" else 0  # 初始栈帧大小
        self.regManager.memory.clear()

        # 预先为所有临时变量分配内存
        for var in self.variables:
            if var.startswith("t") or var == "n" or var == "a":
                self.regManager.memory[var] = self.regManager.frame_size
                self.regManager.frame_size += 4

        # 这里简化处理，可以根据实际情况扩展局部变量分析
        # 函数参数和临时变量都视为局部变量
        self.regManager.func_vars = set(
            [v for v in self.variables if v.startswith("t") or v == "n" or v == "a"]
        )

    def gen_func_epilogue(self, func):
        if func == "main":
            self.asm_lines.append("\tj end")
        else:
            self.asm_lines.append("\tlw $ra, 4($sp)")
            self.asm_lines.append("\tjr $ra")
        self.asm_lines.append("")

    def process_basic_block(self, block, in_func):
        # 清空寄存器使用情况
        self.regManager.freeAllRegisters(block["in_set"])
        self.param_list = []

        for i, quad in enumerate(block["quads"]):
            # 跳过函数开始和结束的四元式，它们在gen_asm中处理
            if quad[0] in ("FUNC_BEGIN", "FUNC_END"):
                continue

            # 处理标签
            if quad[0] == "LABEL":
                self.asm_lines.append(f"{quad[3]}:")
                continue

            # 处理跳转
            if quad[0] == "GOTO":
                self.asm_lines.append(f"\tj {quad[3]}")
                continue

            # 处理条件跳转
            if quad[0] == "IF_FALSE_GOTO":
                cond_reg = self.regManager.getSrcRegister(
                    quad[1], block["quads"], i, block["out_set"], self.asm_lines
                )
                self.asm_lines.append(f"\tbeq {cond_reg}, $zero, {quad[3]}")
                continue

            # 处理GT操作
            if quad[0] == "GT":
                src1, src2, dst = quad[1:]
                rs = self.regManager.getSrcRegister(
                    src1, block["quads"], i, block["out_set"], self.asm_lines
                )
                rt = self.regManager.getSrcRegister(
                    src2, block["quads"], i, block["out_set"], self.asm_lines
                )
                rd = self.regManager.getTarRegister(
                    dst, block["quads"], i, block["out_set"], self.asm_lines
                )
                self.asm_lines.append(
                    f"\tslt {rd}, {rt}, {rs}"
                )  # rd = (rt < rs) ? 1 : 0
                continue

            # 处理SUB操作
            if quad[0] == "SUB":
                src1, src2, dst = quad[1:]
                rs = self.regManager.getSrcRegister(
                    src1, block["quads"], i, block["out_set"], self.asm_lines
                )
                rt = self.regManager.getSrcRegister(
                    src2, block["quads"], i, block["out_set"], self.asm_lines
                )
                rd = self.regManager.getTarRegister(
                    dst, block["quads"], i, block["out_set"], self.asm_lines
                )
                self.asm_lines.append(f"\tsub {rd}, {rs}, {rt}")
                continue

            # 处理ASSIGN操作
            if quad[0] == "ASSIGN":
                src, _, dst = quad[1:]
                rs = self.regManager.getSrcRegister(
                    src, block["quads"], i, block["out_set"], self.asm_lines
                )
                # 如果dst是变量，直接存储到内存
                if dst in self.regManager.func_vars:
                    if dst not in self.regManager.memory:
                        self.regManager.memory[dst] = self.regManager.frame_size
                        self.regManager.frame_size += 4
                    self.asm_lines.append(
                        f"\tsw {rs}, {self.regManager.memory[dst]}($sp)"
                    )
                else:
                    self.asm_lines.append(f"\tsw {rs}, {dst}")
                continue

            if i == len(block["quads"]) - 1:
                # 基本块最后一条指令，需要保存活跃变量
                outset = block["out_set"] | self.regManager.data_vars
                if quad[0] in ("GOTO", "IF_FALSE_GOTO", "RETURN"):
                    self.regManager.storeOutSet(outset, self.asm_lines)
                    self.process_quad(quad, i, block, in_func)
                elif quad[0] == "CALL":
                    # 函数调用需要特殊处理返回值
                    self.regManager.storeOutSet(outset - {quad[3]}, self.asm_lines)
                    self.process_quad(quad, i, block, in_func)
                    self.regManager.storeOutSet({quad[3]}, self.asm_lines)
                else:
                    self.process_quad(quad, i, block, in_func)
                    self.regManager.storeOutSet(outset, self.asm_lines)
            else:
                self.process_quad(quad, i, block, in_func)

    def process_quad(self, quad, idx, block, func_name):
        op = quad[0]

        if op == "ASSIGN":
            # ('ASSIGN', src, None, dst)
            src, _, dst = quad[1:]
            if dst is None:  # 防止错误
                return

            reg = self.regManager.getSrcRegister(
                src, block["quads"], idx, block["out_set"], self.asm_lines
            )
            self.regManager.freeVarRegisters(dst)
            self.regManager.RValue[reg].add(dst)
            self.regManager.AValue[dst].add(reg)

        elif op == "ADD":
            # ('ADD', src1, src2, dst)
            src1, src2, dst = quad[1:]
            if dst is None:  # 防止错误
                return

            rs = self.regManager.getSrcRegister(
                src1, block["quads"], idx, block["out_set"], self.asm_lines
            )
            rt = self.regManager.getSrcRegister(
                src2, block["quads"], idx, block["out_set"], self.asm_lines
            )
            rd = self.regManager.getTarRegister(
                dst, block["quads"], idx, block["out_set"], self.asm_lines
            )
            self.asm_lines.append(f"\tadd {rd}, {rs}, {rt}")

            # 释放不再使用的寄存器
            if not self.regManager._is_variable(src1):
                if rs in self.regManager.RValue:
                    self.regManager.free_registers.append(rs)
            elif src1 != dst:
                # 检查src1之后是否还会被使用
                still_active = False
                for i in range(idx + 1, len(block["quads"])):
                    if src1 in [block["quads"][i][1], block["quads"][i][2]]:
                        still_active = True
                        break
                if not still_active:
                    self.regManager.freeVarRegisters(src1)

            if not self.regManager._is_variable(src2):
                if rt in self.regManager.RValue:
                    self.regManager.free_registers.append(rt)
            elif src2 != dst:
                # 检查src2之后是否还会被使用
                still_active = False
                for i in range(idx + 1, len(block["quads"])):
                    if src2 in [block["quads"][i][1], block["quads"][i][2]]:
                        still_active = True
                        break
                if not still_active:
                    self.regManager.freeVarRegisters(src2)

        elif op == "SUB":
            # ('SUB', src1, src2, dst)
            src1, src2, dst = quad[1:]
            if dst is None:  # 防止错误
                return

            rs = self.regManager.getSrcRegister(
                src1, block["quads"], idx, block["out_set"], self.asm_lines
            )
            rt = self.regManager.getSrcRegister(
                src2, block["quads"], idx, block["out_set"], self.asm_lines
            )
            rd = self.regManager.getTarRegister(
                dst, block["quads"], idx, block["out_set"], self.asm_lines
            )
            self.asm_lines.append(f"\tsub {rd}, {rs}, {rt}")

            # 释放不再使用的寄存器
            if not self.regManager._is_variable(src1):
                if rs in self.regManager.RValue:
                    self.regManager.free_registers.append(rs)
            elif src1 != dst:
                # 检查src1之后是否还会被使用
                still_active = False
                for i in range(idx + 1, len(block["quads"])):
                    if src1 in [block["quads"][i][1], block["quads"][i][2]]:
                        still_active = True
                        break
                if not still_active:
                    self.regManager.freeVarRegisters(src1)

            if not self.regManager._is_variable(src2):
                if rt in self.regManager.RValue:
                    self.regManager.free_registers.append(rt)
            elif src2 != dst:
                # 检查src2之后是否还会被使用
                still_active = False
                for i in range(idx + 1, len(block["quads"])):
                    if src2 in [block["quads"][i][1], block["quads"][i][2]]:
                        still_active = True
                        break
                if not still_active:
                    self.regManager.freeVarRegisters(src2)

        elif op == "MUL":
            # ('MUL', src1, src2, dst)
            src1, src2, dst = quad[1:]
            if dst is None:  # 防止错误
                return

            rs = self.regManager.getSrcRegister(
                src1, block["quads"], idx, block["out_set"], self.asm_lines
            )
            rt = self.regManager.getSrcRegister(
                src2, block["quads"], idx, block["out_set"], self.asm_lines
            )
            rd = self.regManager.getTarRegister(
                dst, block["quads"], idx, block["out_set"], self.asm_lines
            )
            self.asm_lines.append(f"\tmul {rd}, {rs}, {rt}")

            # 释放不再使用的寄存器
            if not self.regManager._is_variable(src1):
                if rs in self.regManager.RValue:
                    self.regManager.free_registers.append(rs)
            elif src1 != dst:
                # 检查src1之后是否还会被使用
                still_active = False
                for i in range(idx + 1, len(block["quads"])):
                    if src1 in [block["quads"][i][1], block["quads"][i][2]]:
                        still_active = True
                        break
                if not still_active:
                    self.regManager.freeVarRegisters(src1)

            if not self.regManager._is_variable(src2):
                if rt in self.regManager.RValue:
                    self.regManager.free_registers.append(rt)
            elif src2 != dst:
                # 检查src2之后是否还会被使用
                still_active = False
                for i in range(idx + 1, len(block["quads"])):
                    if src2 in [block["quads"][i][1], block["quads"][i][2]]:
                        still_active = True
                        break
                if not still_active:
                    self.regManager.freeVarRegisters(src2)

        elif op == "DIV":
            # ('DIV', src1, src2, dst)
            src1, src2, dst = quad[1:]
            if dst is None:  # 防止错误
                return

            rs = self.regManager.getSrcRegister(
                src1, block["quads"], idx, block["out_set"], self.asm_lines
            )
            rt = self.regManager.getSrcRegister(
                src2, block["quads"], idx, block["out_set"], self.asm_lines
            )
            rd = self.regManager.getTarRegister(
                dst, block["quads"], idx, block["out_set"], self.asm_lines
            )
            self.asm_lines.append(f"\tdiv {rs}, {rt}")
            self.asm_lines.append(f"\tmflo {rd}")

            # 释放不再使用的寄存器
            if not self.regManager._is_variable(src1):
                if rs in self.regManager.RValue:
                    self.regManager.free_registers.append(rs)
            elif src1 != dst:
                # 检查src1之后是否还会被使用
                still_active = False
                for i in range(idx + 1, len(block["quads"])):
                    if src1 in [block["quads"][i][1], block["quads"][i][2]]:
                        still_active = True
                        break
                if not still_active:
                    self.regManager.freeVarRegisters(src1)

            if not self.regManager._is_variable(src2):
                if rt in self.regManager.RValue:
                    self.regManager.free_registers.append(rt)
            elif src2 != dst:
                # 检查src2之后是否还会被使用
                still_active = False
                for i in range(idx + 1, len(block["quads"])):
                    if src2 in [block["quads"][i][1], block["quads"][i][2]]:
                        still_active = True
                        break
                if not still_active:
                    self.regManager.freeVarRegisters(src2)

        elif op == "RETURN":
            # ('RETURN', val, None, None)
            val = quad[1]
            if val is not None and val != "_":
                if self.regManager._is_variable(val):
                    reg = None
                    for pos in self.regManager.AValue[val]:
                        if pos != "Memory":
                            reg = pos
                            break
                    if reg:
                        self.asm_lines.append(f"\tadd $v0, {reg}, $zero")
                    else:
                        if val in self.regManager.memory:
                            self.asm_lines.append(
                                f"\tlw $v0, {self.regManager.memory[val]}($sp)"
                            )
                        else:
                            self.asm_lines.append(f"\tlw $v0, {val}")
                else:  # 立即数
                    self.asm_lines.append(f"\tli $v0, {val}")

            if func_name == "main":
                self.asm_lines.append("\tj end")
            else:
                self.asm_lines.append("\tlw $ra, 4($sp)")
                self.asm_lines.append("\tjr $ra")

        elif op == "CALL":
            # ('CALL', func, argc, ret)
            func, argc, ret = quad[1:]

            # 处理参数（简化版，可根据实际调用约定扩展）
            if hasattr(self, "param_list") and self.param_list:
                top = 0
                for param in self.param_list:
                    reg = self.regManager.getSrcRegister(
                        param["name"],
                        block["quads"],
                        idx,
                        block["out_set"],
                        self.asm_lines,
                    )
                    self.asm_lines.append(
                        f"\tsw {reg}, {8 + top + self.regManager.frame_size}($sp)"
                    )
                    top += 4
                    # 参数使用后释放
                    if not param.get("active", True):
                        self.regManager.freeVarRegisters(param["name"])

                # 保存SP并移动到新位置
                self.asm_lines.append(f"\tsw $sp, {self.regManager.frame_size}($sp)")
                self.asm_lines.append(f"\taddi $sp, $sp, {self.regManager.frame_size}")

            # 调用函数
            self.asm_lines.append(f"\tjal {func}")

            # 恢复SP
            if hasattr(self, "param_list") and self.param_list:
                self.asm_lines.append("\tlw $sp, 0($sp)")

            # 保存返回值
            if ret and ret != "_":
                rd = self.regManager.getTarRegister(
                    ret, block["quads"], idx, block["out_set"], self.asm_lines
                )
                self.asm_lines.append(f"\tadd {rd}, $v0, $zero")

            # 清空参数列表
            self.param_list = []

        elif op == "PARAM":
            # ('PARAM', arg, None, None)
            arg = quad[1]
            # 记录参数，为函数调用准备
            is_active = True  # 简化版，可以根据活跃变量分析改进
            self.param_list.append({"name": arg, "active": is_active})

        elif op == "LABEL":
            # ('LABEL', None, None, label)
            label = quad[3]
            self.asm_lines.append(f"{label}:")

        elif op == "GOTO":
            # ('GOTO', None, None, label)
            label = quad[3]
            self.asm_lines.append(f"\tj {label}")

        elif op == "IF_FALSE_GOTO":
            # ('IF_FALSE_GOTO', cond, None, label)
            cond, _, label = quad[1:]
            rs = self.regManager.getSrcRegister(
                cond, block["quads"], idx, block["out_set"], self.asm_lines
            )
            self.asm_lines.append(f"\tbeq {rs}, $zero, {label}")

            # 条件使用后释放
            if not self.regManager._is_variable(cond):
                if rs in self.regManager.RValue:
                    self.regManager.free_registers.append(rs)
            else:
                # 检查cond之后是否还会被使用
                still_active = False
                for i in range(idx + 1, len(block["quads"])):
                    if cond in [block["quads"][i][1], block["quads"][i][2]]:
                        still_active = True
                        break
                if not still_active:
                    self.regManager.freeVarRegisters(cond)

        elif op == "FUNC_BEGIN":
            # ('FUNC_BEGIN', name, None, None)
            name = quad[1]
            self.current_func = name
            self.gen_func_prologue(name)

        elif op == "FUNC_END":
            # ('FUNC_END', name, None, None)
            name = quad[1]
            self.gen_func_epilogue(name)
            self.current_func = None

        elif op == "LT":
            # ('LT', src1, src2, dst) - 处理小于操作
            src1, src2, dst = quad[1:]
            if dst is None:  # 防止错误
                return

            rs = self.regManager.getSrcRegister(
                src1, block["quads"], idx, block["out_set"], self.asm_lines
            )
            rt = self.regManager.getSrcRegister(
                src2, block["quads"], idx, block["out_set"], self.asm_lines
            )
            rd = self.regManager.getTarRegister(
                dst, block["quads"], idx, block["out_set"], self.asm_lines
            )

            # 直接使用slt指令
            self.asm_lines.append(f"\tslt {rd}, {rs}, {rt}")  # rd = (rs < rt) ? 1 : 0

            # 释放不再使用的寄存器
            if not self.regManager._is_variable(src1):
                if rs in self.regManager.RValue:
                    self.regManager.free_registers.append(rs)
            elif src1 != dst:
                # 检查src1之后是否还会被使用
                still_active = False
                for i in range(idx + 1, len(block["quads"])):
                    if src1 in [block["quads"][i][1], block["quads"][i][2]]:
                        still_active = True
                        break
                if not still_active:
                    self.regManager.freeVarRegisters(src1)

            if not self.regManager._is_variable(src2):
                if rt in self.regManager.RValue:
                    self.regManager.free_registers.append(rt)
            elif src2 != dst:
                # 检查src2之后是否还会被使用
                still_active = False
                for i in range(idx + 1, len(block["quads"])):
                    if src2 in [block["quads"][i][1], block["quads"][i][2]]:
                        still_active = True
                        break
                if not still_active:
                    self.regManager.freeVarRegisters(src2)

        elif op == "EQ":
            # ('EQ', src1, src2, dst) - 处理等于操作
            src1, src2, dst = quad[1:]
            if dst is None:  # 防止错误
                return

            rs = self.regManager.getSrcRegister(
                src1, block["quads"], idx, block["out_set"], self.asm_lines
            )
            rt = self.regManager.getSrcRegister(
                src2, block["quads"], idx, block["out_set"], self.asm_lines
            )
            rd = self.regManager.getTarRegister(
                dst, block["quads"], idx, block["out_set"], self.asm_lines
            )

            # MIPS中没有直接的等于指令，使用xor和sltiu实现
            self.asm_lines.append(f"\txor {rd}, {rs}, {rt}")  # rd = rs ^ rt
            self.asm_lines.append(
                f"\tsltiu {rd}, {rd}, 1"
            )  # rd = (rd < 1) ? 1 : 0，即rd = (rd == 0) ? 1 : 0

            # 释放不再使用的寄存器
            if not self.regManager._is_variable(src1):
                if rs in self.regManager.RValue:
                    self.regManager.free_registers.append(rs)
            elif src1 != dst:
                # 检查src1之后是否还会被使用
                still_active = False
                for i in range(idx + 1, len(block["quads"])):
                    if src1 in [block["quads"][i][1], block["quads"][i][2]]:
                        still_active = True
                        break
                if not still_active:
                    self.regManager.freeVarRegisters(src1)

            if not self.regManager._is_variable(src2):
                if rt in self.regManager.RValue:
                    self.regManager.free_registers.append(rt)
            elif src2 != dst:
                # 检查src2之后是否还会被使用
                still_active = False
                for i in range(idx + 1, len(block["quads"])):
                    if src2 in [block["quads"][i][1], block["quads"][i][2]]:
                        still_active = True
                        break
                if not still_active:
                    self.regManager.freeVarRegisters(src2)

        elif op == "NE":
            # ('NE', src1, src2, dst) - 处理不等于操作
            src1, src2, dst = quad[1:]
            if dst is None:  # 防止错误
                return

            rs = self.regManager.getSrcRegister(
                src1, block["quads"], idx, block["out_set"], self.asm_lines
            )
            rt = self.regManager.getSrcRegister(
                src2, block["quads"], idx, block["out_set"], self.asm_lines
            )
            rd = self.regManager.getTarRegister(
                dst, block["quads"], idx, block["out_set"], self.asm_lines
            )

            # MIPS中没有直接的不等于指令，使用xor和sltu实现
            self.asm_lines.append(f"\txor {rd}, {rs}, {rt}")  # rd = rs ^ rt
            self.asm_lines.append(
                f"\tsltu {rd}, $zero, {rd}"
            )  # rd = (0 < rd) ? 1 : 0，即rd = (rd != 0) ? 1 : 0

            # 释放不再使用的寄存器
            if not self.regManager._is_variable(src1):
                if rs in self.regManager.RValue:
                    self.regManager.free_registers.append(rs)
            elif src1 != dst:
                # 检查src1之后是否还会被使用
                still_active = False
                for i in range(idx + 1, len(block["quads"])):
                    if src1 in [block["quads"][i][1], block["quads"][i][2]]:
                        still_active = True
                        break
                if not still_active:
                    self.regManager.freeVarRegisters(src1)

            if not self.regManager._is_variable(src2):
                if rt in self.regManager.RValue:
                    self.regManager.free_registers.append(rt)
            elif src2 != dst:
                # 检查src2之后是否还会被使用
                still_active = False
                for i in range(idx + 1, len(block["quads"])):
                    if src2 in [block["quads"][i][1], block["quads"][i][2]]:
                        still_active = True
                        break
                if not still_active:
                    self.regManager.freeVarRegisters(src2)

        # 可以继续添加更多操作类型...

    def gen_asm(self):
        self.gen_data_section()
        self.gen_text_section()

        # 跟踪已处理的函数名，避免重复
        processed_funcs = set()

        # 处理所有基本块
        for block in self.basic_blocks:
            # 检查基本块所属函数
            in_func = None
            for quad in block["quads"]:
                if quad[0] == "FUNC_BEGIN":
                    in_func = quad[1]
                    break

            # 处理函数开始
            for quad in block["quads"]:
                if quad[0] == "FUNC_BEGIN" and quad[1] not in processed_funcs:
                    self.current_func = quad[1]
                    self.gen_func_prologue(quad[1])
                    processed_funcs.add(quad[1])

            # 处理这个基本块中的所有四元式
            self.process_basic_block(block, in_func or self.current_func)

            # 处理函数结束
            for quad in block["quads"]:
                if quad[0] == "FUNC_END" and quad[1] in processed_funcs:
                    self.gen_func_epilogue(quad[1])
                    self.current_func = None
                    processed_funcs.remove(quad[1])

        # 程序结束标记
        self.asm_lines.append("end:")
        self.asm_lines.append("\tli $v0, 10")  # SPIM系统调用退出
        self.asm_lines.append("\tsyscall")

        return "\n".join(self.asm_lines)

    def save(self, filename):
        with open(filename, "w") as f:
            f.write(self.gen_asm())

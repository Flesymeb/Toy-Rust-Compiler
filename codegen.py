from collections import defaultdict


class X86AsmGenerator:
    def __init__(self, quadruples, variables=None, functions=None):
        self.quadruples = quadruples
        # 自动收集所有用到的变量名（非立即数、非label、非函数名）
        all_vars = set()
        func_names = set()
        # 先收集所有函数名
        for quad in quadruples:
            if quad[0] == "FUNC_BEGIN" and isinstance(quad[1], str):
                func_names.add(quad[1])
        func_names.add("_start")
        # 收集变量，排除所有函数名和 _start
        for quad in quadruples:
            op = quad[0]
            for v in quad[1:]:
                if (
                    isinstance(v, str)
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
        self.var_offset = {}
        self.offset = 0
        self.temp_count = 0
        self.label_count = 0
        self.used_regs = set()
        self.reg_pool = ["eax", "ebx", "ecx", "edx"]
        self.func_stack = []

    def alloc_var(self, var):
        if var not in self.var_offset:
            self.var_offset[var] = self.offset
            self.offset += 4
        return self.var_offset[var]

    def get_reg(self):
        for reg in self.reg_pool:
            if reg not in self.used_regs:
                self.used_regs.add(reg)
                return reg
        # 若无空闲寄存器，简单溢出到栈
        return None

    def free_reg(self, reg):
        if reg in self.used_regs:
            self.used_regs.remove(reg)

    def gen_data_section(self):
        self.asm_lines.append("section .data")
        for var in sorted(self.variables):
            self.asm_lines.append(f"{var} dd 0")
        self.asm_lines.append("")

    def gen_text_section(self):
        self.asm_lines.append("section .text")
        self.asm_lines.append("global main")
        self.asm_lines.append("")

    def gen_func_prologue(self, func):
        self.asm_lines.append(f"{func}:")
        self.asm_lines.append("    push ebp")
        self.asm_lines.append("    mov ebp, esp")
        self.asm_lines.append("    sub esp, 256")  # 简单分配栈空间

    def gen_func_epilogue(self, func):
        self.asm_lines.append("    mov esp, ebp")
        self.asm_lines.append("    pop ebp")
        if func == "main":
            self.asm_lines.append("    ret")
        else:
            self.asm_lines.append("    ret")
        self.asm_lines.append("")

    def gen_asm(self):
        self.gen_data_section()
        self.gen_text_section()
        cur_func = None
        for quad in self.quadruples:
            op = quad[0]
            if op == "FUNC_BEGIN":
                cur_func = quad[1]
                self.gen_func_prologue(cur_func)
            elif op == "FUNC_END":
                self.gen_func_epilogue(cur_func)
                cur_func = None
            elif op == "ASSIGN":
                # ('ASSIGN', src, None, dst)
                src, _, dst = quad[1:]
                reg = self.get_reg() or "eax"
                if isinstance(src, int) or (isinstance(src, str) and src.isdigit()):
                    self.asm_lines.append(f"    mov {reg}, {src}")
                else:
                    self.asm_lines.append(f"    mov {reg}, [{src}]")
                self.asm_lines.append(f"    mov [{dst}], {reg}")
                self.free_reg(reg)
            elif op in ("ADD", "SUB", "MUL", "DIV"):
                # ('ADD', src1, src2, dst)
                src1, src2, dst = quad[1:]
                reg1 = self.get_reg() or "eax"
                reg2 = self.get_reg() or "ebx"
                # 加载操作数
                if isinstance(src1, int) or (isinstance(src1, str) and src1.isdigit()):
                    self.asm_lines.append(f"    mov {reg1}, {src1}")
                else:
                    self.asm_lines.append(f"    mov {reg1}, [{src1}]")
                if isinstance(src2, int) or (isinstance(src2, str) and src2.isdigit()):
                    self.asm_lines.append(f"    mov {reg2}, {src2}")
                else:
                    self.asm_lines.append(f"    mov {reg2}, [{src2}]")
                # 运算
                if op == "ADD":
                    self.asm_lines.append(f"    add {reg1}, {reg2}")
                elif op == "SUB":
                    self.asm_lines.append(f"    sub {reg1}, {reg2}")
                elif op == "MUL":
                    self.asm_lines.append(f"    imul {reg1}, {reg2}")
                elif op == "DIV":
                    self.asm_lines.append(f"    mov edx, 0")
                    self.asm_lines.append(f"    mov eax, {reg1}")
                    self.asm_lines.append(f"    idiv {reg2}")
                    self.asm_lines.append(f"    mov {reg1}, eax")
                self.asm_lines.append(f"    mov [{dst}], {reg1}")
                self.free_reg(reg1)
                self.free_reg(reg2)
            elif op == "RETURN":
                # ('RETURN', val, None, None)
                val = quad[1]
                reg = self.get_reg() or "eax"
                if isinstance(val, int) or (isinstance(val, str) and val.isdigit()):
                    self.asm_lines.append(f"    mov {reg}, {val}")
                else:
                    self.asm_lines.append(f"    mov {reg}, [{val}]")
                self.asm_lines.append(f"    mov eax, {reg}")
                self.asm_lines.append("    ; ret handled in epilogue")
                self.free_reg(reg)
            elif op == "CALL":
                # ('CALL', func, argc, ret)
                func, argc, ret = quad[1:]
                self.asm_lines.append(f"    call {func}")
                if ret and ret != "_":
                    self.asm_lines.append(f"    mov [{ret}], eax")
            elif op == "LABEL":
                # ('LABEL', None, None, label)
                label = quad[3]
                self.asm_lines.append(f"{label}:")
            elif op == "GOTO":
                # ('GOTO', None, None, label)
                label = quad[3]
                self.asm_lines.append(f"    jmp {label}")
            elif op == "IF_FALSE_GOTO":
                # ('IF_FALSE_GOTO', cond, None, label)
                cond, _, label = quad[1:]
                reg = self.get_reg() or "eax"
                if isinstance(cond, int) or (isinstance(cond, str) and cond.isdigit()):
                    self.asm_lines.append(f"    mov {reg}, {cond}")
                else:
                    self.asm_lines.append(f"    mov {reg}, [{cond}]")
                self.asm_lines.append(f"    cmp {reg}, 0")
                self.asm_lines.append(f"    je {label}")
                self.free_reg(reg)
            # 可扩展更多操作...
        return "\n".join(self.asm_lines)

    def save(self, filename):
        with open(filename, "w") as f:
            f.write(self.gen_asm())

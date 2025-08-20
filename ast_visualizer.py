"""
Description  : 修改后的AST可视化实现函数
"""


def get_node_color(node_type):
    """根据节点类型返回颜色"""
    # 根据节点类型设置不同的颜色
    colors = {
        "ProgramNode": "#008800",  # 深绿色
        "FunctionDeclNode": "#0066CC",  # 蓝色
        "BlockNode": "#666666",  # 灰色
        "LetDeclNode": "#993399",  # 紫色
        "IfNode": "#CC6600",  # 橙色
        "WhileNode": "#CC6600",  # 橙色
        "ForNode": "#CC6600",  # 橙色
        "ReturnNode": "#CC3300",  # 红色
        "AssignNode": "#993399",  # 紫色
        "BinaryOpNode": "#009999",  # 青色
        "UnaryOpNode": "#009999",  # 青色
        "NumberNode": "#999900",  # 黄色
        "StringLiteralNode": "#999900",  # 黄色
        "BooleanLiteralNode": "#999900",  # 黄色
        "IdentifierNode": "#000099",  # 深蓝色
        "FunctionCallNode": "#660066",  # 深紫色
    }

    # 从节点类型中提取名称（去掉前缀和后缀）
    node_name = node_type.replace("Node", "")

    # 返回颜色，如果没有特定颜色则返回黑色
    return colors.get(node_type, "#000000")


def build_ast_tree_improved(self, node, tree_widget, parent_item=None):
    """为语法树节点创建改进版的树形视图"""
    if node is None:
        return

    # 获取节点的类名
    node_class_name = node.__class__.__name__

    # 创建主要标签
    main_label = node_class_name.replace("Node", "")

    # 创建属性标签
    attrs = {}
    attrs_text = ""

    for key, value in node.__dict__.items():
        if (
            key != "children"
            and not key.startswith("_")
            and not isinstance(value, list)
        ):
            attrs[key] = value

    if attrs:
        # 收集属性
        attrs_parts = []
        for k, v in attrs.items():
            if isinstance(v, str) and v:
                attrs_parts.append(f'{k}: "{v}"')
            elif v is not None:
                attrs_parts.append(f"{k}: {v}")

        if attrs_parts:
            attrs_text = ", ".join(attrs_parts)

    # 创建树项
    if parent_item is None:
        # 创建根节点
        item = QTreeWidgetItem([main_label])
        tree_widget.addTopLevelItem(item)
    else:
        # 创建子节点
        item = QTreeWidgetItem(parent_item, [main_label])

    # 设置节点样式
    node_color = get_node_color(node_class_name)
    item.setForeground(0, QColor(node_color))

    # 设置字体 - 节点名称加粗
    font = QFont()
    font.setBold(True)
    item.setFont(0, font)

    # 如果有属性，添加为子节点
    if attrs_text:
        attrs_item = QTreeWidgetItem(item, [attrs_text])
        # 设置属性节点的样式 - 灰色，斜体
        attrs_item.setForeground(0, QColor("#555555"))
        font = QFont()
        font.setItalic(True)
        attrs_item.setFont(0, font)

    # 递归处理子节点
    if hasattr(node, "children") and node.children:
        # 添加子节点标签
        if len(node.children) > 0:
            stmts_item = QTreeWidgetItem(item, ["stmts:"])
            stmts_font = QFont()
            stmts_font.setItalic(True)
            stmts_item.setFont(0, stmts_font)
            stmts_item.setForeground(0, QColor("#777777"))

            # 添加子节点
            for child in node.children:
                self.build_ast_tree_improved(child, tree_widget, stmts_item)

    return item

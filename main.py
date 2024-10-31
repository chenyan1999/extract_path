from tree_sitter import Language, Parser
import os

# 定义函数 find_code_structure
def find_code_structure(file_path, line_number, language):
    # 初始化Tree-sitter解析器并设置语言
    LANGUAGES = Language('./build/my-languages.so', language)
    
    parser = Parser()
    parser.set_language(LANGUAGES)

    # 读取文件内容
    with open(file_path, 'r') as file:
        code = file.read()

    # 解析代码生成语法树
    tree = parser.parse(bytes(code, "utf8"))
    root_node = tree.root_node

    # 获取节点的完整声明内容
    def get_declaration_text_py(node):
        # 检查是否是类或函数声明
        if node.type == node_types['class']:
            declearation = ""
            # get child node of class, identifier, argument_list
            for child in node.children:
                if child.type == "class":
                    declearation += "class "
                elif child.type == "identifier":
                    declearation += child.text.decode("utf-8")
                elif child.type == "argument_list":
                    declearation += child.text.decode("utf-8")
                elif child.type == ":":
                    declearation += child.text.decode("utf-8")
            return declearation
        elif node.type == node_types['function']:
            declearation = ""
            # get child node of function, identifier, argument_list
            for child in node.children:
                if child.type == "def":
                    declearation += "def "
                elif child.type == "identifier":
                    declearation += child.text.decode("utf-8")
                elif child.type == "parameters":
                    declearation += child.text.decode("utf-8")
                elif child.type == ":":
                    declearation += child.text.decode("utf-8")
            return declearation
        return None
    
    def get_declaration_text_go(node):
        pass
    
    def get_declaration_text_java(node):
        pass
    
    def get_declaration_text_js(node):
        pass
    
    def get_declaration_text_ts(node):
        pass
    
    # 语言特定的节点类型（根据不同语言的语法树定义）
    language_nodes = {
        'python': {'class': 'class_definition', 'function': 'function_definition', "get_signature_fn": get_declaration_text_py},
        'go': {'class': 'type_declaration', 'function': 'function_declaration', "get_signature_fn": get_declaration_text_go},
        'java': {'class': 'class_declaration', 'function': 'method_declaration', "get_signature_fn": get_declaration_text_java},
        'javascript': {'class': 'class_declaration', 'function': 'function_declaration', "get_signature_fn": get_declaration_text_js},
        'typescript': {'class': 'class_declaration', 'function': 'function_declaration', "get_signature_fn": get_declaration_text_ts},
    }

    node_types = language_nodes[language]

    def print_node_structure(node, level=0):
        indent = '  ' * level  # 控制缩进显示层级
        print(f"{indent}Node Type: {node.type}, Text: {node.text if node.text else ''}, Start: {node.start_point}, End: {node.end_point}")

        # 递归打印子节点
        for child in node.children:
            print_node_structure(child, level + 1)
            
    # 查找行号对应的逻辑位置
    def traverse(node, current_structure=None):
        if not current_structure:
            current_structure = []

        # 检查行号是否在当前节点的范围内
        if node.start_point[0] <= line_number <= node.end_point[0]:
            # 如果是类定义，将整个类定义内容添加到当前结构路径中
            if node.type == node_types['class']:
                class_declaration = node_types["get_signature_fn"](node)
                current_structure.append(f"{class_declaration}")

            # 如果是函数定义，将整个函数定义内容添加到当前结构路径中
            elif node.type == node_types['function']:
                function_declaration = node_types["get_signature_fn"](node)
                current_structure.append(f"{function_declaration}")

            # 递归检查子节点
            for child in node.children:
                result = traverse(child, current_structure)
                if result:
                    return result

            # 返回当前结构路径
            return current_structure

        return None

    # 获取行号的结构路径
    structure_path = traverse(root_node)
    if structure_path:
        formatted_path = ""
        for level, node in enumerate(structure_path):
            if level > 1:
                indent = "    " * (level -1)  # 每层增加4个空格缩进
            else:
                indent = ""
            if level > 0:
                branch_symbol = "├-- " if level < len(structure_path) - 1 else "└-- "
                for i in range(level - 1):
                    branch_symbol = "│   " + branch_symbol
            else:
                branch_symbol = ""
            
            formatted_path += f"{branch_symbol}{node}\n"
        return formatted_path
    else:
        return None

# 示例调用
repo_path = "./transformers"
file_path = "src/transformers/commands/run.py" # path within the repository
line_number = 65
language_name = "python"
print(find_code_structure(os.path.join(repo_path, file_path), line_number, language_name))
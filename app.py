import streamlit as st
import re
from graphviz import Digraph

# ------------------------
# Node class for parse tree
# ------------------------
class Node:
    def __init__(self, name):
        self.name = name
        self.children = []

    def add_child(self, child):
        if isinstance(child, Node):
            self.children.append(child)
        else:
            self.children.append(Node(str(child)))

# ------------------------
# Lexical Analysis
# ------------------------
def tokenize(code):
    token_specification = [
        ('KEYWORD', r'int'),
        ('NUMBER', r'\d+'),
        ('ID', r'[a-zA-Z_][a-zA-Z0-9_]*'),
        ('OP', r'[+\-*/=]'),
        ('SEMI', r';'),
        ('SKIP', r'[ \t\n]+'),
    ]
    token_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
    tokens = []
    symbol_table = {}
    
    for match in re.finditer(token_regex, code):
        kind = match.lastgroup
        value = match.group()
        if kind != 'SKIP':
            tokens.append((kind, value))
        if kind == 'ID' and value not in symbol_table:
            symbol_table[value] = 'int'
    
    return tokens, symbol_table

# ------------------------
# Syntax Analysis
# ------------------------
def syntax_analysis(code):
    lines = code.strip().split("\n")
    result = []
    for line in lines:
        line = line.strip()
        if line.startswith("int") and line.endswith(";"):
            result.append((line, "Valid Declaration"))
        elif "=" in line and line.endswith(";"):
            result.append((line, "Valid Assignment"))
        else:
            result.append((line, "Syntax Error"))
    return result

# ------------------------
# Semantic Analysis
# ------------------------
def semantic_analysis(code):
    declared = set()
    errors = []
    lines = code.strip().split("\n")
    
    for line in lines:
        line = line.strip()
        if line.startswith("int"):
            var = line.split()[1].replace(";", "")
            if var in declared:
                errors.append(f"Semantic Error: Multiple declaration of '{var}'")
            else:
                declared.add(var)
        elif "=" in line:
            lhs, rhs = line.split("=", 1)
            lhs = lhs.strip()
            rhs = rhs.strip().replace(";", "")
            if lhs not in declared:
                errors.append(f"Semantic Error: Undeclared variable '{lhs}'")
            for token in re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', rhs):
                if token not in declared:
                    errors.append(f"Semantic Error: Undeclared variable '{token}'")
    return errors

# ------------------------
# Parser and Parse Tree
# ------------------------
def build_parse_tree(code):
    global tokens_list, index
    tokens_list = re.findall(r'int|[a-zA-Z_][a-zA-Z0-9_]*|[0-9]+|[=+*/-]|;', code)
    index = 0

    def match(expected):
        global index
        if index < len(tokens_list) and tokens_list[index] == expected:
            index += 1
            return Node(expected)
        else:
            raise SyntaxError(f"Expected '{expected}', found '{tokens_list[index]}'")

    def parse_program():
        global index
        node = Node("Program")
        while index < len(tokens_list):
            if tokens_list[index] == 'int':
                node.add_child(parse_declaration())
            else:
                node.add_child(parse_assignment())
        return node

    def parse_declaration():
        global index
        node = Node("Declaration")
        node.add_child(match('int'))
        node.add_child(Node(tokens_list[index]))  # variable name
        index += 1
        node.add_child(match(';'))
        return node

    def parse_assignment():
        global index
        node = Node("Assignment")
        node.add_child(Node(tokens_list[index]))  # LHS
        index += 1
        node.add_child(match('='))
        node.add_child(Node(tokens_list[index]))  # RHS first term
        index += 1
        if index < len(tokens_list) and tokens_list[index] == '+':
            node.add_child(match('+'))
            node.add_child(Node(tokens_list[index]))  # RHS second term
            index += 1
        node.add_child(match(';'))
        return node

    return parse_program()

def draw_tree(node, dot=None):
    if dot is None:
        dot = Digraph()
        dot.node(str(id(node)), node.name)
    for child in node.children:
        dot.node(str(id(child)), child.name)
        dot.edge(str(id(node)), str(id(child)))
        draw_tree(child, dot)
    return dot

# ------------------------
# Streamlit UI
# ------------------------
st.title("Simple Compiler Frontend")
st.write("Enter your code below:")

code_input = st.text_area("Code", value="""
int a;
int b;
a = 5;
b = a + 10;
""", height=200)

if st.button("Compile"):
    # Lexical Analysis
    tokens, symbol_table = tokenize(code_input)
    st.subheader("Tokens")
    st.table(tokens)
    
    # Symbol Table
    st.subheader("Symbol Table")
    st.table(symbol_table.items())
    
    # Syntax Analysis
    syntax_result = syntax_analysis(code_input)
    st.subheader("Syntax Analysis")
    st.table(syntax_result)
    
    # Semantic Analysis
    semantic_errors = semantic_analysis(code_input)
    st.subheader("Semantic Analysis")
    if semantic_errors:
        for err in semantic_errors:
            st.error(err)
    else:
        st.success("No semantic errors found!")
    
    # Parse Tree
    try:
        root = build_parse_tree(code_input)
        dot = draw_tree(root)
        st.subheader("Parse Tree")
        st.graphviz_chart(dot)
    except Exception as e:
        st.error(f"Parse Error: {e}")
import ast
from typing import Optional, List


def classify_dag_shape(prompt: str) -> str:
    has_code = any(w in prompt.lower() for w in ["api", "endpoint", "function", "class", "method", "route", "handler", "code", "program", "implement", "algorithm", "sort", "calculate", "compute", "script"])
    has_docs = any(w in prompt.lower() for w in ["doc", "documentation", "readme", "comment", "docstring"])
    has_tests = any(w in prompt.lower() for w in ["test", "unittest", "pytest", "spec"])
    is_sequential = any(w in prompt.lower() for w in ["sequential", "step by step", "linear"])
    parts = []
    if has_code:
        parts.append("code")
    if has_docs:
        parts.append("docs")
    if has_tests:
        parts.append("tests")
    if not parts:
        return "A"
    if is_sequential:
        return "C"
    if has_tests and (has_code or has_docs):
        return "B"
    return "A"


def extract_function_signature(code: str) -> Optional[dict]:
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                params = []
                for arg in node.args.args:
                    if arg.arg == "self":
                        continue
                    annotation = ast.unparse(arg.annotation) if arg.annotation else "Any"
                    params.append({"name": arg.arg, "type": annotation})
                returns = ast.unparse(node.returns) if node.returns else "None"
                return {"name": node.name, "params": params, "returns": returns}
    except SyntaxError:
        pass
    return None


def extract_code_blocks(text: str) -> List[str]:
    import re
    blocks = re.findall(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    if blocks:
        return [b.strip() for b in blocks]
    try:
        compile(text.strip(), "<string>", "exec")
        return [text.strip()]
    except SyntaxError:
        pass
    lines = text.strip().split("\n")
    code_lines = []
    in_code = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_code:
                code_lines.append(line)
            continue
        if any(kw in line for kw in ["def ", "class ", "import ", "from ", "@", "if __name__", "unittest."]):
            in_code = True
            code_lines.append(line)
        elif in_code:
            code_lines.append(line)
    if code_lines:
        return ["\n".join(code_lines)]
    return [text.strip()]


def _has_keywords(prompt: str) -> tuple:
    has_code = any(w in prompt.lower() for w in ["api", "endpoint", "function", "class", "method", "route", "handler", "code", "program", "implement", "algorithm", "sort", "calculate", "compute", "script"])
    has_docs = any(w in prompt.lower() for w in ["doc", "documentation", "readme", "comment", "docstring"])
    has_tests = any(w in prompt.lower() for w in ["test", "unittest", "pytest", "spec"])
    return has_code, has_docs, has_tests


def build_dag(prompt: str, shape: str) -> list[dict]:
    dag = []
    tid = 1
    has_code, has_docs, has_tests = _has_keywords(prompt)
    code_id, docs_id = None, None

    if shape == "C":
        prev_id = None
        if has_code:
            code_id = tid
            dag.append({
                "id": tid, "name": "Generate Code",
                "depends_on": [prev_id] if prev_id else [],
                "prompt_template": (
                    "Write only Python code for the following task. "
                    "Return ONLY valid Python code inside a ```python markdown block. "
                    "No explanation, no extra text.\n\n"
                    "Task: {prompt}\n\n```python\n"
                ),
            })
            prev_id = tid; tid += 1
        if has_docs:
            docs_id = tid
            dag.append({
                "id": tid, "name": "Generate Documentation",
                "depends_on": [prev_id] if prev_id else [],
                "prompt_template": (
                    "Generate documentation for the following request. "
                    "Respond in exactly this format:\n\n"
                    "## FUNCTION_NAME\none-line description\n\n"
                    "**Parameters:**\n- param_name (type): description\n\n"
                    "**Returns:**\n- type: description\n\n"
                    "**Example:**\none usage line\n\n"
                    "Request:\n{prompt}"
                ),
            })
            prev_id = tid; tid += 1
        if has_tests:
            dag.append({
                "id": tid, "name": "Generate Tests",
                "depends_on": [prev_id] if prev_id else [],
                "prompt_template": (
                    "Write Python unit tests using unittest for the code below. "
                    "Return only the test code, no explanation.\n\n"
                    "Code to test:\n{code_output}"
                ),
            })
            tid += 1
    else:
        if has_code:
            code_id = tid
            dag.append({
                "id": tid, "name": "Generate Code",
                "depends_on": [],
                "prompt_template": (
                    "Write only Python code for the following task. "
                    "Return ONLY valid Python code inside a ```python markdown block. "
                    "No explanation, no extra text.\n\n"
                    "Task: {prompt}\n\n```python\n"
                ),
            })
            tid += 1
        if has_docs:
            docs_id = tid
            dag.append({
                "id": tid, "name": "Generate Documentation",
                "depends_on": [],
                "prompt_template": (
                    "Generate documentation for the following request. "
                    "Respond in exactly this format:\n\n"
                    "## FUNCTION_NAME\none-line description\n\n"
                    "**Parameters:**\n- param_name (type): description\n\n"
                    "**Returns:**\n- type: description\n\n"
                    "**Example:**\none usage line\n\n"
                    "Request:\n{prompt}"
                ),
            })
            tid += 1
        if has_tests:
            depends = [code_id] if code_id else []
            dag.append({
                "id": tid, "name": "Generate Tests",
                "depends_on": depends,
                "prompt_template": (
                    "Write Python unit tests using unittest for the code below. "
                    "Return only the test code, no explanation.\n\n"
                    "Code to test:\n{code_output}"
                ),
            })
            tid += 1

    if not dag:
        dag.append({
            "id": 1, "name": "Generate Response",
            "depends_on": [],
            "prompt_template": "Respond to the following: {prompt}",
        })
    return dag

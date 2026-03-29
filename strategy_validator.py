"""
strategy_validator.py – Safety checks before executing user-uploaded strategies.
"""

import ast
import re

# Modules / builtins that uploaded strategies are not allowed to import or call.
BLOCKED_MODULES = {
    "os", "sys", "subprocess", "shutil", "socket", "threading", "multiprocessing",
    "importlib", "ctypes", "signal", "pty", "atexit", "gc", "inspect",
    "pickle", "shelve", "marshal", "code", "codeop", "compileall",
    "ftplib", "http", "urllib", "requests", "httpx", "aiohttp",
    "smtplib", "imaplib", "poplib", "telnetlib",
    "builtins",
}

BLOCKED_BUILTINS = {"exec", "eval", "compile", "__import__", "open", "input"}

# Allow only these top-level names to be defined by the strategy
ALLOWED_TOP_LEVEL = {"generate_signals", "STRATEGY_NAME"}


class StrategyValidationError(ValueError):
    """Raised when a strategy fails validation."""


def validate_strategy(source_code: str) -> None:
    """
    Parse and validate a strategy source file.

    Raises StrategyValidationError with a descriptive message on failure.
    """
    _check_syntax(source_code)
    tree = ast.parse(source_code)
    _check_imports(tree)
    _check_calls(tree)
    _check_required_function(tree)


# ---------------------------------------------------------------------------
# Internal checks
# ---------------------------------------------------------------------------

def _check_syntax(source: str) -> None:
    try:
        ast.parse(source)
    except SyntaxError as exc:
        raise StrategyValidationError(f"Syntax error in strategy: {exc}") from exc


def _check_imports(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            else:
                names = [node.module.split(".")[0]] if node.module else []
            for name in names:
                if name in BLOCKED_MODULES:
                    raise StrategyValidationError(
                        f"Import of '{name}' is not allowed in strategies."
                    )


def _check_calls(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_name = _get_call_name(node.func)
            if func_name in BLOCKED_BUILTINS:
                raise StrategyValidationError(
                    f"Call to '{func_name}' is not allowed in strategies."
                )


def _get_call_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _check_required_function(tree: ast.AST) -> None:
    function_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    if "generate_signals" not in function_names:
        raise StrategyValidationError(
            "Strategy must define a 'generate_signals(df)' function."
        )

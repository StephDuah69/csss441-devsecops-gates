"""Semgrep Rule Test Suite for CSSS 441 Custom Security Rules.

This file provides positive (must match) and negative (must not match)
test cases for automated Semgrep rule verification.
"""

import ast
import json
import pickle
import subprocess
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# ============================================================================
# Rule 1 Tests: csss441.python.sql-string-interpolation
# ============================================================================
def test_sql_injection_positive(cursor, user_id):
    # ruleid: csss441.python.sql-string-interpolation
    cursor.execute(f"SELECT * FROM accounts WHERE id = '{user_id}'")

    # ruleid: csss441.python.sql-string-interpolation
    cursor.execute("SELECT * FROM accounts WHERE id = '%s'" % user_id)

    # ruleid: csss441.python.sql-string-interpolation
    cursor.execute("SELECT * FROM accounts WHERE id = '{}'".format(user_id))


def test_sql_injection_negative(cursor, user_id):
    # ok: csss441.python.sql-string-interpolation
    cursor.execute("SELECT * FROM accounts WHERE id = %s", (user_id,))


# ============================================================================
# Rule 2 Tests: csss441.python.dangerous-subprocess-shell-true
# ============================================================================
def test_subprocess_shell_positive(command):
    # ruleid: csss441.python.dangerous-subprocess-shell-true
    subprocess.run(f"echo {command}", shell=True, check=True)

    # ruleid: csss441.python.dangerous-subprocess-shell-true
    subprocess.Popen(command, shell=True)


def test_subprocess_shell_negative(filename):
    # ok: csss441.python.dangerous-subprocess-shell-true
    subprocess.run(["ls", "-la", filename], shell=False, check=True)


# ============================================================================
# Rule 3 Tests: csss441.python.unsafe-dynamic-eval
# ============================================================================
def test_eval_positive(expression, statement):
    # ruleid: csss441.python.unsafe-dynamic-eval
    eval(expression)

    # ruleid: csss441.python.unsafe-dynamic-eval
    exec(statement)


def test_eval_negative(raw_data):
    # ok: csss441.python.unsafe-dynamic-eval
    return ast.literal_eval(raw_data)


# ============================================================================
# Rule 4 Tests: csss441.python.unsafe-pickle-deserialization
# ============================================================================
def test_pickle_positive(untrusted_payload):
    # ruleid: csss441.python.unsafe-pickle-deserialization
    pickle.loads(untrusted_payload)


def test_pickle_negative(untrusted_payload):
    # ok: csss441.python.unsafe-pickle-deserialization
    return json.loads(untrusted_payload)


# ============================================================================
# Rule 5 Tests: csss441.python.wildcard-cors-with-credentials
# ============================================================================
def test_cors_positive():
    app_vuln = FastAPI()
    # ruleid: csss441.python.wildcard-cors-with-credentials
    app_vuln.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def test_cors_negative():
    app_safe = FastAPI()
    # ok: csss441.python.wildcard-cors-with-credentials
    app_safe.add_middleware(
        CORSMiddleware,
        allow_origins=["https://secure.university.edu"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )

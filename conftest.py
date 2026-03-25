import os
import sys

import pytest
from common.observability import attach_json

# 在导入任何使用 config / os.getenv 的模块之前，根据 --env 加载对应 .env 文件，避免 config、ADMIN_EMAIL 等为 None
from utils.env_loader import load_env

_env = "uat"
for i, arg in enumerate(sys.argv):
    if arg == "--env" and i + 1 < len(sys.argv):
        _env = sys.argv[i + 1]
        break
if os.getenv("ENV"):
    _env = os.getenv("ENV")
load_env(_env)

from common.client import Client
from api.auth_api import AuthAPI
from common.config import config

pytest_plugins = ["fixtures.auth_fixture", "fixtures.resource_cleanup_fixture"]


def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default="uat",
        help="run env (e.g. uat, test); also load .env.{env} before config)",
    )


@pytest.fixture(scope="session", autouse=True)
def load_environment(request):
    """兼容：环境已在 conftest 顶部根据 --env 加载，此处可留空或再次确保加载。"""
    env = request.config.getoption("--env")
    load_env(env)


@pytest.fixture(autouse=True)
def attach_test_context(request):
    attach_json(
        "test context",
        {
            "nodeid": request.node.nodeid,
            "env": request.config.getoption("--env"),
        },
    )


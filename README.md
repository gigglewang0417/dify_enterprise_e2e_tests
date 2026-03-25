# Dify 企业版自动化测试

基于 **pytest** 的 Dify 企业版接口与端到端自动化测试工程。用例以 **HTTP API** 为主（`requests` + 会话 Cookie），通过 **Service** 封装业务流程，**API** 层描述各域 REST 路径；部分场景配合 **Allure** 步骤与报告。

---

## 技术栈

| 组件 | 说明 |
|------|------|
| Python 3 | 建议 3.10+ |
| pytest | 测试运行与断言 |
| requests | `common/client.Client` 会话请求 |
| python-dotenv | 按环境加载 `.env.{env}` |
| allure-pytest | 用例步骤与报告（可选） |
| pytest-html | HTML 报告（见 `pytest.ini`） |
| pytest-xdist / pytest-order / pytest-asyncio | 并行、顺序、异步（按需） |

> 仓库含 `pytest-playwright`，当前 `testcases/` 下用例未使用浏览器自动化；若后续补充 UI 用例，需执行 `playwright install`。

---

## 仓库结构

```
dify_enterprise_tests/
├── api/                    # 各域 REST 封装（路径拼接 + method）
│   ├── auth_api.py         # 登录、鉴权相关
│   ├── admin_api.py        # 管理端（如工作空间列表等）
│   ├── admin_user.py / admin_secret_key.py
│   ├── credentials_api.py  # 企业凭据、租户分配、策略等
│   ├── console_api.py      # Console：模型/内置工具凭据、model-providers 等
│   ├── apps_api.py         # 应用导入/发布、工作流草稿
│   ├── plugin_api.py       # 插件安装与任务
│   ├── member_api.py / workspace_api.py
│   ├── password_policy.py / system_user_setting.py / audit_log.py
│   └── ...
├── services/               # 业务流程（组合 API、登录等）
│   ├── auth_service.py     # Admin / Console / SAML SSO 登录
│   ├── credential_service.py
│   ├── plugin_service.py / member_service.py / ...
│   └── ...
├── testcases/              # 测试用例（实际收集目录）
│   ├── auth/               # 如登录、SSO
│   ├── workspace/          # 工作空间、成员
│   └── e2e/                # 凭据、插件、端到端场景（test_case*.py 等）
├── fixtures/               # pytest 插件模块
│   ├── auth_fixture.py     # admin_client、console_client
│   └── resource_cleanup_fixture.py  # 用例资源清理
├── common/                 # config、client、logger、request
├── utils/                  # env_loader、轮询、随机名等
├── test_data/              # YAML 等测试数据
├── config/                 # 包初始化等
├── conftest.py             # 环境加载、pytest 插件注册
├── pytest.ini
├── requirements.txt
├── allure.properties
└── reports/                # pytest-html、allure 报告输出（运行时生成）
```

---

## 环境配置

### 1. 安装依赖

```bash
cd dify_enterprise_tests
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 环境文件

项目通过 **`ENV` 环境变量** 或 **`--env` 命令行参数** 选择配置文件，对应文件为 **`.env.{环境名}`**（例如 `.env.uat`）。  
`conftest.py` 在导入配置前会调用 `utils.env_loader.load_env`，**必须存在对应文件**，否则会报错。

示例（按需复制并改名，勿提交真实密钥）：

```bash
cp .env.uat .env.local
# 编辑 .env.local，填入 BASE_URL、CONSOLE_URL、ADMIN_* 等
```

### 3. 常用环境变量（见 `common/config.py`）

| 变量 | 含义 |
|------|------|
| `BASE_URL` | 企业后台 API 根（如 `https://.../v1`） |
| `CONSOLE_URL` | Console 站点根，用于 `/console/api/...` |
| `ADMIN_API_BASE_URL` | 部分管理接口基址 |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | 管理端登录 |
| `PLUGIN_*` | 插件相关用例（keyword、plugin id、source 等） |

SAML SSO 等用例另需 `SAML_SSO_EMAIL` 或 `CONSOLE_EMAIL`（见 `testcases/auth/test_login.py`）。

---

## 运行测试

### 指定环境

默认 `conftest` 中默认 `--env` 为 **`uat`**；也可显式传入：

```bash
pytest testcases --env uat
```

或：

```bash
export ENV=uat
pytest testcases
```

### 常用命令

```bash
# 运行全部用例（建议显式指定 testcases）
pytest testcases

# 只跑某一目录或文件
pytest testcases/auth/test_login.py -v
pytest testcases/e2e/test_credentials.py

# 并行（需安装 pytest-xdist）
pytest testcases -n auto
```

> **说明**：`pytest.ini` 中 `testpaths = tests`，若项目根下无 `tests/` 目录，直接执行 `pytest` 可能不收集到用例。请使用 **`pytest testcases`**，或将 `testpaths` 改为 `testcases`。

---

## 测试夹具（Fixtures）

在 `fixtures/auth_fixture.py` 中：

- **`admin_client`**（session）：`AuthService.admin_login()`，已带 Cookie + `X-CSRF-Token`，用于企业后台 Dashboard API。
- **`console_client`**（session）：`AuthService.console_login()`，用于 Console API（如 `api/console_api.py`）。

`fixtures/resource_cleanup_fixture.py` 提供用例结束后的应用/凭据等清理，与 `resource_tracker` 配合使用。

---

## API 与 Service 分层

- **`api/`**：按路径封装 `get/post/delete`，入参为 `path` 或 `client` + 业务参数；**Console** 与 **Admin Dashboard** 基址不同（`CONSOLE_URL` vs `BASE_URL`）。
- **`services/`**：封装登录、凭据创建、插件安装等多步调用，供用例复用。

新增用例时：优先在 `api` 增加原子接口，在 `service` 组合步骤，在 `testcases` 写断言与 Allure 步骤。

---

## 报告

- **pytest-html**：由 `pytest.ini` 的 `addopts` 写入 `reports/report.html`（`--self-contained-html`）。
- **Allure**：结果目录见 `allure.properties`（默认 `reports/allure-results`）。生成 HTML 报告需本机安装 [Allure Commandline](https://github.com/allure-framework/allure2)：

```bash
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report
```

---

## 扩展与注意事项

1. **敏感信息**：勿将真实 `.env.*` 提交到版本库；测试数据放 `test_data/`，避免硬编码生产密钥。
2. **顺序依赖**：部分 e2e 用例使用 `pytest-order` 等，修改时注意执行顺序。
3. **401/CSRF**：`Client` 已对齐 Cookie 与 `X-CSRF-Token`；若接口变更，先检查 `common/client.py` 与登录响应。

---

## 许可证

MIT License

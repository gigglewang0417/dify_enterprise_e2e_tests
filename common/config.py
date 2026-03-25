import os
from dotenv import load_dotenv


class Config:

    def __init__(self):

        env = os.getenv("ENV", "test")

        dotenv_file = f".env.{env}"

        load_dotenv(dotenv_file)

        self.base_url = os.getenv("BASE_URL")

        self.admin_api_base_url = os.getenv("ADMIN_API_BASE_URL")

        self.admin_email = os.getenv("ADMIN_EMAIL")
        self.admin_password = os.getenv("ADMIN_PASSWORD")

        self.console_url = os.getenv("CONSOLE_URL")

        # 插件前置安装 fixture 用：list_plugin_ids 的 keyword；按 pluginId / pluginUniqueIdentifier 判断是否已安装；安装时 source
        self.plugin_keyword = os.getenv("PLUGIN_KEYWORD", "github")
        self.plugin_id = os.getenv("PLUGIN_ID", "")
        self.plugin_unique_identifier = os.getenv("PLUGIN_UNIQUE_IDENTIFIER", "")
        self.plugin_source = os.getenv("PLUGIN_SOURCE", "marketplace")


config = Config()
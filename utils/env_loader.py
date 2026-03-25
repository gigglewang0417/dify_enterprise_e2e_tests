import os
from dotenv import load_dotenv


def load_env(env):

    env_file = f".env.{env}"

    if not os.path.exists(env_file):
        raise FileNotFoundError(f"{env_file} not found")

    load_dotenv(env_file)
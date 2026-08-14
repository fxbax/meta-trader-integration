from dotenv import load_dotenv, dotenv_values


def getEnvValue(key):
    load_dotenv(dotenv_path="../.")
    config = dotenv_values(".env")
    return config.get(key)

from dotenv import load_dotenv,dotenv_values


config = dotenv_values(".env")

print(config["OPENAI_API_KEY"])
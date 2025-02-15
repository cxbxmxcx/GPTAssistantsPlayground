from dotenv import load_dotenv
import os

load_dotenv()


def get_llm_client():
    api_type = os.getenv("API_TYPE")

    if api_type:
        if api_type == "openai":
            from openai import OpenAI

            client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),                
            )
        elif api_type == "azure":
            from openai import AzureOpenAI

            client = AzureOpenAI(
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            )
    else:
        # no key revert back to openai
        from openai import OpenAI

        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    return client

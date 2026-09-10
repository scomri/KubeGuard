from LLMs.azure_openai_llm_communicator import AzureOpenAICommunicator
from LLMs.openai_api_llm_communicator import OpenAIAPICommunicator

from dotenv import load_dotenv

load_dotenv()


def create_openai_api(llm_name, record_conversation=False):
    if llm_name != "GPT-4o-2024-08-06":
        raise ValueError(
            f"Invalid LLM model '{llm_name}' for OpenAI API. "
            f"Supported models: {'GPT-4o-2024-08-06'}."
        )
    return OpenAIAPICommunicator(
        model=llm_name,
        record_conversation=record_conversation,
    )

def create_azure_openai(llm_name):
    if llm_name == 'GPT-4o-2024-08-06':
        return AzureOpenAICommunicator()
    else:
        raise ValueError(f"Invalid LLM model '{llm_name}' for Azure OpenAI. Only 'GPT-4o-2024-08-06' is supported.")


# Map communicator types to their factory functions
COMMUNICATOR_FACTORIES = {
    'openai_api': create_openai_api,
    'azure_openai': create_azure_openai
}

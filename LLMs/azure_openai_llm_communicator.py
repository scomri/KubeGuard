import os
from openai import AzureOpenAI
from LLMs.llm_communicator_ABC import LLMCommunicatorABC
from dotenv import load_dotenv

load_dotenv()


class AzureOpenAICommunicator(LLMCommunicatorABC):
    """
    Communicator class for interacting with Azure OpenAI service.
    Inherits from LLMCommunicatorABC.
    """

    def __init__(self, system_prompt=None):
        """
        Initializes the AzureOpenAICommunicator instance.

        Args:
            system_prompt (str, optional): The initial system prompt to set. Defaults to None.
        """
        super().__init__(system_prompt)

        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment_name = os.getenv("AZURE_DEPLOYMENT_NAME")

        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version="2024-02-01",
            azure_endpoint=self.azure_endpoint
        )

    def send_message(self, message):
        """
        Sends a message to the Azure OpenAI service and returns the response.

        Args:
            message (str): The message to send to the LLM.

        Returns:
            str: The response from the LLM.
        """
        if not self.deployment_name:
            raise ValueError("Deployment name not set.")
        self.conversation.append({"role": "user", "content": message})
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=self.conversation,
            temperature=0
        )
        self.conversation.append({"role": "assistant", "content": response.choices[0].message.content})
        return response.choices[0].message.content

    def set_api_key(self, api_key):
        """
        Sets the API key for the Azure OpenAI client.

        Args:
            api_key (str): The API key to set.
        """
        self.api_key = api_key
        self.client.api_key = api_key

    def set_endpoint(self, endpoint):
        """
        Sets the endpoint for the Azure OpenAI client.

        Args:
            endpoint (str): The endpoint to set.
        """
        self.azure_endpoint = endpoint
        self.client.azure_endpoint = endpoint

    def set_deployment_name(self, deployment_name):
        """
        Sets the deployment name for the Azure OpenAI client.

        Args:
            deployment_name (str): The deployment name to set.
        """
        self.deployment_name = deployment_name

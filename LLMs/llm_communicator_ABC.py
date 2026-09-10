import json
import os.path
from abc import ABC, abstractmethod
from datetime import datetime


class LLMCommunicatorABC(ABC):
    """
    Abstract base class for a Large Language Model (LLM) Communicator.
    This class defines the interface and common functionality for communicating with an LLM.
    """

    def __init__(self, system_prompt=None):
        """
        Initializes the LLMCommunicatorABC instance.

        Args:
            system_prompt (str, optional): The initial system prompt to set. Defaults to None.
        """
        self.conversation = []
        self.system_prompt = None
        if system_prompt:
            self.set_system_prompt(system_prompt)

    @abstractmethod
    def send_message(self, message):
        """
        Abstract method to send a message to the LLM.
        This method must be implemented by subclasses.

        Args:
            message (str): The message to send to the LLM.
        """
        pass

    def set_system_prompt(self, prompt):
        """
        Sets the system prompt for the conversation.

        Args:
            prompt (str): The system prompt to set.
        """
        self.system_prompt = prompt
        self.conversation.append({"role": "system", "content": prompt})

    def save_conversation(self, output_folder, service):
        """
        Saves the current conversation to a JSON file.

        Args:
            output_folder (str): The folder to save the conversation file in.
            service (str): The name of the service that the conversation memory is for.
        """
        if not os.path.exists(os.path.join(f'{output_folder}', 'conversation')):
            os.mkdir(os.path.join(f'{output_folder}', 'conversation'))
        path = os.path.join(f'{output_folder}', 'conversation', f'{service}_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.json')
        with open(path, 'w') as f:
            f.write(json.dumps(self.conversation, indent=4))
        os.chmod(path, 0o600)

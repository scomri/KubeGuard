import argparse
import os
from pathlib import Path

from LLMs.azure_openai_llm_communicator import AzureOpenAICommunicator
from LLMs.openai_api_llm_communicator import OpenAIAPICommunicator


PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_ROOT = PROJECT_ROOT / 'outputs'


def get_verbose_print(verbose):
    """
    Returns a print function that respects the verbosity flag.

    Args:
        verbose (bool): If True, the returned function will print messages. If False, it will do nothing.

    Returns:
        function: A print function if verbose is True, otherwise a no-op lambda function.
    """
    return print if verbose else lambda *args, **kwargs: None


def extract_last_json_pattern_from_response(communicator, json_pattern, response):
    """
    Extracts the appropriate JSON match (last one) from the response based on communicator type.

    :param communicator: The communicator instance (e.g., AzureOpenAICommunicator)
    :param json_pattern: The compiled regex pattern used for partial extraction (e.g.,
                         r'```json\\s*\\n(.*?)\\n```')
    :param response: The text response from which to extract
    :return: The extracted JSON string if found, otherwise None
    """

    # ----- OpenAI communicators -----
    if isinstance(communicator, AzureOpenAICommunicator) or isinstance(communicator, OpenAIAPICommunicator):
        match = json_pattern.search(response)
        return match.group(1) if match else None

    # Fallback if communicator type isn't recognized
    return None


def validate_output_folder(output_folder):
    folder = Path(output_folder).resolve()
    try:
        folder.relative_to(OUTPUT_ROOT.resolve())
    except ValueError as error:
        raise ValueError('Output folder must remain inside outputs/.') from error
    return str(folder)



def get_common_arg_parser(description):
    """
    Creates an ArgumentParser instance with common arguments for creation / refinement tasks.

    Args:
        description (str): Description of the script using the parser.

    Returns:
        argparse.ArgumentParser: Configured argument parser.
    """
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('--verbose', action='store_true',
                        help="Print verbose output.")
    parser.add_argument('--communicator', type=str,
                        default='azure_openai',
                        choices=['openai_api', 'azure_openai'],
                        help="Choose the LLM communicator type to use.")
    parser.add_argument('--LLM', type=str,
                        default='GPT-4o-2024-08-06',
                        help="Choose the LLM to use in the task-specific prompt chain.")
    parser.add_argument('--app_name', type=str,
                        required=True,
                        help="Application name.")
    parser.add_argument('--app_namespace', type=str,
                        help="Application namespace.")
    parser.add_argument('--service', type=str,
                        required=True,
                        help="Service name to process.")
    parser.add_argument('--output_folder', type=str,
                        help="Output folder for saving results.")


    return parser


def ensure_output_folder(output_folder):
    """
    Ensures the output folder exists, creates it if it doesn't.
    Also creates a 'conversation' subdirectory within the output folder.

    Args:
        output_folder (str): Path to the output folder

    Raises:
        SystemExit: If folder creation fails
    """
    try:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Create 'conversation' subdirectory
        conversation_folder = os.path.join(output_folder, 'conversation')
        if not os.path.exists(conversation_folder):
            os.makedirs(conversation_folder)

    except Exception as e:
        print(f"Error creating non-existent output folder: {e}")
        exit(1)

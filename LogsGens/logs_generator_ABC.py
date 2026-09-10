import os
from abc import ABC, abstractmethod


class LogGeneratorABC(ABC):
    """
    Abstract base class for a Log Generator.
    This class defines the interface and common functionality for generating logs.
    """

    def __init__(self, source):
        """
        Initializes the LogGeneratorABC instance.

        Args:
            source (str): The source from which to load logs.
        """
        self.load_logs(source)

    @abstractmethod
    def load_logs(self, source):
        """
        Abstract method to load logs from the given source.
        This method must be implemented by subclasses.

        Args:
            source (str): The source from which to load logs.
        """
        pass

    @abstractmethod
    def parse_logs(self, service):
        """
        Abstract method to parse raw logs into a structured format.
        This method must be implemented by subclasses.

        Args:
            service (str): The service to parse logs of.
        """
        pass

    @abstractmethod
    def run(self, service):
        """
        Abstract method to run the log generator.
        This method must be implemented by subclasses.

        Args:
            service (str): The service to run the log generator for.
        """
        pass

    @abstractmethod
    def generate_llm_text(self, service):
        """
        Abstract method to generate a report based on the analysis results.
        This method must be implemented by subclasses.

        Args:
            service (str): The service to generate the report of.
        """
        pass

    @abstractmethod
    def save_agg_logs_as_txt(self, service):
        """
        Abstract method to save the aggregated logs as a text file.
        This method must be implemented by subclasses.

        Args:
            service (str): The service to save the aggregated logs of.
        """
        pass

    @staticmethod
    def get_available_resources(data_source_files_dir):
        """
        Get the available resources from the specified directory.

        Args:
            data_source_files_dir (str): The directory to get available resources from.

        Returns:
            list: A list of available resources.
        """
        resources = []
        for d in os.listdir(data_source_files_dir):
            if os.path.isdir(os.path.join(data_source_files_dir, d)):
                resources.append('-'.join(d.split('-')[:-1]))
        return resources

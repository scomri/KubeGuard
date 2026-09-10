import yaml
import json
import os


class ManifestReader:
    """
    A class to read and convert manifest files in YAML and JSON formats.
    """

    def __init__(self, source):
        """
        Initializes the ManifestReader class.

        :param source: str: The path to the directory containing the manifest files.
        """
        self.manifests_path = source

    @staticmethod
    def read_manifest(path):
        """
        Reads the content of a manifest file.

        :param path: str: The path to the manifest file.

        :return: str: The content of the manifest file.
        """
        with open(path, 'r') as file:
            return file.read()

    @staticmethod
    def read_manifest_as_json(manifest_path):
        """
        Reads a manifest file and returns its content as a JSON string.

        :param manifest_path: str: The path to the manifest file.

        :return: str: The content of the manifest file in JSON format.

        :raises ValueError: If the file format is not YAML or JSON.
        """
        manifest_path = str(manifest_path)
        if manifest_path.endswith('.json'):
            with open(manifest_path, 'r') as json_file:
                return json_file.read()
        elif manifest_path.endswith('.yaml'):
            with open(manifest_path, 'r') as yaml_file:
                yaml_content = yaml.safe_load(yaml_file)
                json_content = json.dumps(yaml_content, indent=4)
                return json_content
        else:
            raise ValueError('Invalid manifest file format. Please provide a YAML or JSON file.')

    @staticmethod
    def save_manifest_as_json(manifest_path):
        """
        Converts a YAML manifest file to JSON format and saves it.

        :param manifest_path: str: The path to the YAML manifest file.
        """
        json_content = ManifestReader.read_manifest_as_json(manifest_path)
        with open(manifest_path.replace('.yaml', '.json'), 'w') as file:
            file.write(json_content)


    def get_available_resources_list(self, manifest_type):
        """
        Gets the list of available resources from the manifest files, based on the manifest type.

        :param manifest_type: str: The type of manifest file to read - 'deploy' if original, 'excessive' if excessive.

        :return: list: The list of available resources' names.
        """
        resource_list = []

        for root, dirs, files in os.walk(self.manifests_path):
            if manifest_type == 'logs':
                resource_list = [file.split(f'_logs_')[1] for file in files if file.endswith(f'.txt')]
                resource_list = [r.split('.txt')[0] for r in resource_list]
            else:
                resource_list = [file.split(f'-{manifest_type}.')[0] for file in files if file.endswith(f'-{manifest_type}.json')]
            break

        return resource_list

from LogsGens.logs_generator_ABC import LogGeneratorABC
import json
from collections import defaultdict
import pandas as pd
from pprint import pformat  # pprint
import os
import re
from manifest_reader import *


class NetworkLogsGenerator(LogGeneratorABC):
    """
    Class for generating network logs.
    Inherits from LogGeneratorABC.
    """

    def __init__(self, source, namespace):
        """
        Initializes the NetworkLogsGenerator instance.

        Args:
            source (str): The source from which to load logs.
            namespace (str): The Kubernetes namespace to filter logs by.
        """
        self.namespace = namespace
        self.source_path = source
        self.network_flows = []
        self.network_logs = defaultdict(dict)
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.agg_logs_text = None
        super().__init__(source)

    def load_logs(self, source=None):
        """
        Load network flow logs from the source.

        Args:
            source (str, optional): The source path to load logs from. Defaults to None.

        Returns:
            list: List of network flow logs.
        """
        source_path = source if source else self.source_path
        hubble_flows = []
        if isinstance(source, str):
            try:
                with open(source_path, 'r') as file:
                    for line in file:
                        data = json.loads(line)
                        hubble_flows.append(data)
            except FileNotFoundError:
                print(f"Hubble data file not found. Please check the path: {source_path}")
            except json.JSONDecodeError:
                print("Error decoding JSON. Please check the file format.")
        elif isinstance(source, list):
            for flow in source:
                try:
                    # If it's already a dictionary, use it directly
                    if isinstance(flow, dict):
                        hubble_flows.append(flow)
                    else:
                        # Otherwise try to parse as JSON
                        data = json.loads(flow)
                        hubble_flows.append(data)
                except json.JSONDecodeError:
                    print("Error decoding JSON. Please check the file format.")
        self.network_flows = hubble_flows
        return hubble_flows

    def clean_logs(self):
        """
        Clean network flow logs by removing specific keys.
        """
        for record in self.network_flows:
            try:
                record['flow'].pop('time')
                record['flow'].pop('uuid')
                record.pop('time')
            except KeyError:
                pass

    def parse_logs(self, service):
        """
        Parse network flow logs for a specific resource.

        Args:
            service (str): The resource to parse the logs for.

        Returns:
            dict: Parsed network logs for the specified resource.
        """
        network_agg_data = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
        exclude_list = ['time', 'uuid', 'interface']
        include_list = self.get_k8s_services_names(kubectl_svc_path=os.path.join(self.project_root, 'k8s_cluster_data', f'kubectl_get_svc_n_{self.namespace}.json'))

        for entry in self.network_flows:
            self.handle_entry(entry, network_agg_data, exclude_list=exclude_list, include_list=include_list)

        for k, v in network_agg_data.items():
            if service in k:
                self.network_logs[service][k] = v
        return self.network_logs[service]

    def handle_entry(self, entry, aggregated_data, exclude_list=None, include_list=None):
        """
        Handles the processing of a single flow entry, validating that the required keys are present,
        parsing the flow source and destination, and aggregating the relevant data. Filters are
        applied based on include and exclude lists.

        Args:
            entry (dict): The individual flow entry, expected to be a dictionary-like object containing
                information about the flow source, destination, and associated metadata.
                Must contain nested 'source' and 'destination' within 'flow' for meaningful processing.
            aggregated_data (dict): A dictionary-like structure that accumulates aggregated flow data.
                The key is typically derived from the source and destination identities, and the value
                holds aggregated metrics or properties.
            exclude_list (list, optional): Optional list of fields to exclude from aggregation. If supplied, these
                fields will not be included in the aggregated data. Defaults to None.
            include_list (list, optional): List of source and destination identifiers to include in processing.
                If the source or destination of the flow is not found in this list, the entry is skipped. Defaults to None.
        """
        if not entry:
            return

        if 'flow' not in entry or 'source' not in entry['flow'] or 'destination' not in entry['flow']:
            return

        if 'identity' not in entry['flow']['source'] or 'identity' not in entry['flow']['destination']:
            return

        try:
            if 'pod_name' not in entry['flow']['source'] and 'pod_name' not in entry['flow']['destination']:
                return
            # flow_source = entry['flow']['source']['pod_name'].split('-')[0] if 'pod_name' in entry['flow']['source'] \
            #     else entry['flow']['source']['identity']
            clean_pod_name_pattern = re.compile(r'-\d')
            flow_source = re.split(clean_pod_name_pattern, entry['flow']['source']['pod_name'])[0] if 'pod_name' in \
                                                                                                      entry['flow'][
                                                                                                          'source'] \
                else entry['flow']['source']['identity']
            # flow_destination = entry['flow']['destination']['pod_name'].split('-')[0] if 'pod_name' in entry['flow'][
            #     'destination'] else entry['flow']['destination']['identity']
            flow_destination = re.split(clean_pod_name_pattern, entry['flow']['destination']['pod_name'])[
                0] if 'pod_name' in entry['flow']['destination'] \
                else entry['flow']['destination']['identity']

            # if include_list is None:
            #     include_list = self.get_k8s_services_names()

            if flow_source not in include_list or flow_destination not in include_list:
                return
            # key = (flow_source, flow_destination)
            key = f'{flow_source}__{flow_destination}'
        except KeyError:
            print(f"*** KeyError in flow - no pod_name or identity in source or destination: \n{entry}")
            return

        for field, value in entry.items():
            self.aggregate_data(aggregated_data[key], field, value, exclude_list)

    def aggregate_data(self, agg_data, key, value, exclude_list=None):
        """
        Aggregate data for a specific key.

        Args:
            agg_data (dict): The aggregated data dictionary.
            key (str): The key to aggregate data for.
            value (any): The value to aggregate.
            exclude_list (list, optional): List of fields to exclude from aggregation. Defaults to None.
        """
        if exclude_list is None:
            exclude_list = ['time', 'uuid', 'interface']  #, 'destination_port', 'source_port']
        if isinstance(value, dict):
            if key not in agg_data:
                agg_data[key] = defaultdict(set)
            for sub_key, sub_value in value.items():
                if sub_key not in exclude_list:
                    self.aggregate_data(agg_data[key], sub_key, sub_value, exclude_list)
        elif isinstance(value, list):
            if all(isinstance(item, dict) for item in value):
                for item in value:
                    self.aggregate_data(agg_data, key, item, exclude_list)
            else:
                if key not in agg_data:
                    agg_data[key] = set()
                agg_data[key].update(value)
        else:
            if key not in agg_data:
                agg_data[key] = set()
            agg_data[key].add(value)

    def run(self, service):
        """
        Run the network logs generator.

        Args:
            service (str): The resource to run the log generator on.

        Returns:
            str: Cleaned text for LLM.
        """
        self.clean_logs()
        self.parse_logs(service)
        llm_text = self.generate_llm_text(service)
        # print(llm_text)
        return llm_text

    def generate_llm_text(self, service):
        """
        Generate LLM text for a specific resource.

        Args:
            service (str): The resource to generate text for.

        Returns:
            str: Generated LLM text.
        """
        special_identities_df = pd.read_csv(os.path.join(self.project_root, 'Network', 'hubble_special_identities.csv'))
        hubble_text = (f"Legend for Hubble Special Identities that exist in the network flow and traffic logs:\n"
                       f"{special_identities_df.to_string(index=False)}")
        self.agg_logs_text = self.pretty_print_dict_inline(self.network_logs[service])
        return hubble_text + "\n" + self.agg_logs_text

    def save_agg_logs_as_txt(self, service, save_dest=None):
        """
        Save aggregated logs as a text file.

        Args:
            service (str): The resource to save logs for.
            save_dest (str, optional): The destination path to save the logs. Defaults to None.
        """
        agg_logs_text = self.run(service)
        if save_dest is None:
            with open(os.path.join(self.project_root, 'Network', 'agg_network_logs', self.namespace, f'agg_network_logs_{service}.txt'), 'w') as f:
                f.write(agg_logs_text)
        else:
            with open(f'{save_dest}/agg_network_logs_{service}.txt', 'w') as f:
                f.write(agg_logs_text)
            return agg_logs_text

    @staticmethod
    def get_k8s_services_names(kubectl_svc_path):
        """
        Get the names of the k8s services from the kubectl services command output.

        Args:
            kubectl_svc_path (str): Path to the kubectl services command output file.

        Returns:
            list: List of k8s services names.
        """
        svc_names = []
        with open(kubectl_svc_path, 'r') as json_file:
            svc_data = json.load(json_file)
        for item in svc_data['items']:
            svc_names.append(item['metadata']['name'])
        return svc_names

    @staticmethod
    def pretty_print_dict_inline(d):
        """
        Pretty-print a dictionary with minimal spacing, only adding brackets and commas for readability.

        Args:
            d (dict): The dictionary to pretty-print.

        Returns:
            str: Pretty-printed dictionary as a string.
        """

        def format_item(item):
            # Handle nested dictionaries
            if isinstance(item, (defaultdict, dict)):
                return '{' + ', '.join(f'"{k}": {format_item(v)}' for k, v in item.items()) + '}'
            # Handle lists, sets, and tuples
            elif isinstance(item, (list, set, tuple)):
                return '[' + ', '.join(format_item(v) for v in item) + ']'
            # Handle string values, ensuring double quotes for JSON
            elif isinstance(item, str):
                return f'"{item}"'
            # Handle other types (use pformat for string representation)
            else:
                return pformat(item)

        # Format each top-level dictionary item with line breaks between items
        formatted_items = [f'"{key}": {format_item(value)}' for key, value in d.items()]
        formatted_dict = '{\n  ' + ',\n  '.join(formatted_items) + '\n}'

        # print(formatted_dict)
        return formatted_dict

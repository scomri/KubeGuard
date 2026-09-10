from manifest_reader import ManifestReader
from LogsGens.network_logs_generator import NetworkLogsGenerator
from LLMs.communicator_factory import *
from utils import *
from Prompts.network_policy_creation import *

import re
import time
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()


def create_network_policy(service, 
                            output_folder,
                            app_name, 
                            app_namespace,
                            network_source,
                            communicator_type, 
                            llm_name,
                            verbose=False
                          ):
    """
    Creates a network policy for a given service by analyzing manifests and network logs, and then generating
      the NetworkPolicy resource based on the analysis.

    Args:
        service (str): The name of the service for which the network policy is being created.
        output_folder (str): The folder where the results will be saved.
        app_name (str): The name of the application.
        app_namespace (str): The namespace of the application.
        network_source (str): The source of the network logs.
        communicator_type (str): The type of communicator to use.
        llm_name (str): The name of the LLM model to use.
        verbose (bool, optional): Whether to print verbose output. Defaults to False.

    Returns:
        str: The created NetworkPolicy resource in JSON format.
    """
    verbose_print = get_verbose_print(verbose)
    output_folder = validate_output_folder(output_folder)

    start_time = time.time()

    print(f"- Starting NetworkPolicy Creation for service: {service}")

    ########################################################
    #                LLM COMMUNICATOR SETUP                #
    ########################################################

    # Get communicator using the factory pattern
    try:
        communicator_factory = COMMUNICATOR_FACTORIES.get(communicator_type)
        if not communicator_factory:
            raise ValueError(f"Invalid communicator type. Choose from: {list(COMMUNICATOR_FACTORIES.keys())}")

        communicator = communicator_factory(llm_name)
        communicator.set_system_prompt(SYSTEM_PROMPT)
        verbose_print(f"    -- Set LLM {llm_name} with {communicator_type} communicator")
    except ValueError as e:
        raise e  # Re-raise with the specific error message from the factory

    ######################################################
    #                LOG GENERATORS SETUP                #
    ######################################################

    json_pattern = re.compile(r'```json\s*\n(.*?)\n```', re.DOTALL)

    network_logs_generator = NetworkLogsGenerator(network_source, app_namespace)
    network_logs_dict = {service: {}}

    # Resolve project root as the parent of this file (adjust parents\[n\] if needed)
    PROJECT_ROOT = Path(__file__).resolve().parent

    deployment_manifests_dict = {service: {}}
    deployment_manifest = ManifestReader.read_manifest_as_json(f'{PROJECT_ROOT}/Manifests/{app_name}/deployments/{service}-deploy.json')
    deployment_manifests_dict[service]['json_manifest'] = deployment_manifest

    verbose_print(f'Time taken for experiment initialization = Total time: {time.time() - start_time} sec')


    #################################################################
    #                1. Deployment Manifest Analysis                #
    #################################################################

    prompt_1_time = time.time()
    deployment_manifests_dict[service]['analysis_task'] = PROMPT_1_manifest_analysis.format(deployment_manifest=deployment_manifest)
    response = communicator.send_message(deployment_manifests_dict[service]['analysis_task'])
    deployment_manifests_dict[service]['manifest_analysis'] = extract_last_json_pattern_from_response(
        communicator,
        json_pattern,
        response
    )
    verbose_print(f"Time taken for Deployment manifest analysis: {time.time() - prompt_1_time} sec / Total time: {time.time() - start_time} sec\n")

    ##########################################################
    #                2. Network Logs Analysis                #
    ##########################################################

    prompt_2_time = time.time()
    network_logs_dict[service]['network_logs'] = network_logs_generator.run(service)
    network_logs_dict[service]['analysis_task'] = PROMPT_2_network_logs_analysis.format(agg_network_logs=network_logs_dict[service]['network_logs'])
    response = communicator.send_message(network_logs_dict[service]['analysis_task'])
    network_logs_dict[service]['network_analysis'] = extract_last_json_pattern_from_response(
        communicator,
        json_pattern,
        response
    )
    if network_logs_dict[service]['network_analysis'] is None:
        raise Exception(f"ANLs analysis `extract_last_json_pattern_from_response` failed for {service}.")
        # return None
    verbose_print(f"Time taken for network logs (ANL) analysis: {time.time() - prompt_2_time} sec / Total time: {time.time() - start_time} sec\n")

    ###########################################################
    #               3. NetworkPolicy Creation                 #
    ###########################################################

    prompt_3_time = time.time()
    network_policy_creation_task = PROMPT_3_network_policy_creation.format(manifest_analysis=deployment_manifests_dict[service]['manifest_analysis'],
                                                                           network_logs_analysis=network_logs_dict[service]['network_analysis']
                                                                           )
    response = communicator.send_message(network_policy_creation_task)
    network_policies = extract_last_json_pattern_from_response(
        communicator,
        json_pattern,
        response
    )
    verbose_print(f"Time taken for NetworkPolicies creation: {time.time() - prompt_3_time} sec / Total time: {time.time() - start_time} sec\n")

    ###############################################################
    #                SAVE CONVERSATION AND OUTPUTS                #
    ###############################################################

    # communicator.save_conversation(output_folder,
    #                                output_file=f'{service}_netpol_conversation_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.txt')
    communicator.save_conversation(output_folder, service)

    with open(os.path.join(output_folder, f'{service}_created_NetPol_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.json'), 'w') as json_file:
        json_file.write(network_policies)
        verbose_print(f"    * Saved NetworkPolicy for {service} to file")

    print(f"    -- NetworkPolicy Creation for service: {service} completed in {time.time() - start_time} sec\n")

    return network_policies


if __name__ == "__main__":

    parser = get_common_arg_parser("Create NetworkPolicies from manifests and network logs.")

    parser.add_argument('--network_source', type=str, help="Path to network logs")

    args = parser.parse_args()

    # Check the application name and set default values
    if args.app_name == 'aks-store-demo':
        args.output_folder = args.output_folder or os.path.join('outputs', f'{args.LLM}', 'netpol_creation', 'aks-store-demo')
        args.app_namespace = args.app_namespace or 'pets'
        args.network_source = args.network_source or "Network/hubble_data/hubble_out_ALL_2024-12-23_19-41.json"

    ensure_output_folder(args.output_folder)
    create_network_policy(
        service=args.service,
        output_folder=args.output_folder,
        app_name=args.app_name,
        app_namespace=args.app_namespace,
        network_source=args.network_source,
        communicator_type=args.communicator,
        llm_name=args.LLM,
        verbose=args.verbose
    )

# KubeGuard

KubeGuard is a research presented for applying LLMs to Kubernetes security tasks: [KubeGuard: LLM-Assisted Kubernetes Hardening via Configuration Files and Runtime Logs Analysis](https://arxiv.org/abs/2509.04191).

This KubeGuard repo is a focused code snapshot of an LLM prompt chain for Kubernetes network security:

- `network_policy_creation.py` analyzes a Deployment and Hubble network telemetry before producing a Kubernetes `NetworkPolicy`.

The repository ships one authentic `aks-store-demo` / `order-service` data snapshot used as the baseline task in the research paper. 

It intentionally excludes the other attack surface reduction workflows, evaluation code, paper artifacts, experiments, and model backends.
The prompt file in `Prompts/` is the exact network-policy prompt variant used by the runner.


## Setup

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and configure the credentials for the communicator you use.

For the Azure OpenAI communicator:
```text
`AZURE_OPENAI_API_KEY`=<your-key>
```

For the OpenAI API communicator:
```text
OPENAI_API_KEY=<your-key>
```


## Run

```bash
python network_policy_creation.py --app_name aks-store-demo --service order-service --communicator azure_openai
```

The default input files are the included Deployment and Hubble snapshots. 
Results are written beneath:

```text
outputs/<LLM>/netpol_creation/aks-store-demo/
```

Use `--LLM`, `--network_source`, `--output_folder`, or `--verbose` to override the defaults.


## Included baseline inputs

```text
Manifests/aks-store-demo/deployments/order-service-deploy.json
Network/hubble_data/hubble_out_ALL_2024-12-23_19-41.json
Network/hubble_special_identities.csv
k8s_cluster_data/kubectl_get_svc_n_pets.json
```
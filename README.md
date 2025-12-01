# Competitor Analysis using Red Hat OpenShift AI

This proof-of-concept solution demonstrates an approach to automate competitor analysis workflows using the Red Hat OpenShift AI platform. The solution is mainly focused on banks and financial services companies operating in the Indian subcontinent, but is generic enough to be customized to other industries and use-cases.

## Problem Statement

To identify competitor strengths, high-growth regions, and potential risks, banks follows a manual data collection and analysis process. Quarterly and half-yearly financial results of peer banks are downloaded from publicly available sources (RBI, NSE, BSE and more). The data is then consolidated into Excel, where analysts normalize classification differences. Once standardized, comparison reports are generated covering multiple parameters. **This process is currently fully manual, repetitive, resource intensive, and consumes significant skilled manpower.**

The solution explores possible ways to automate this workflow and increase the speed and quality of analysis that aids faster decision making, and reacting quickly to market conditions and trends.

> **NOTE**: The developers of this solution are not financial or banking experts. We have taken a simple approach of gathering publicly available documents and using simple, straightforward queries to analyze information contained in the input documents. It is expected that customers with **knowledgeable domain experts** can use the solution as a base and customize it to the organization's needs and policies. We propose an architecture that can be customized for many use-cases. We focus on the approach used to automate a manual, labor intensive task and do not make claims about the accuracy or validity of the output produced by the solution. 

## Acknowledgments

- Prasad Mukhedkar
- Varun Raste
- Ravi Srinivasan
- The Red Hat AI BU Team

## Technical Overview

This project provides an end-to-end solution for ingesting financial documents (PDFs), converting them to embeddings, storing them in a vector database, and enabling semantic search through Jupyter notebooks. The entire stack is deployed as a single Helm chart with automated setup and configuration.

### Architecture

![Solution Architecture](arch.png)

### Technology Stack

* Models as a Service (MaaS) for remote inference
* RHOAI 2.25 latest (To be updated to 3.0 at GA)
* Milvus Vector DB
* LlamaStack
* MinIO (for storing PDFs) S3 compatible storage
* OCP 4.18+, or whatever is LTS
* Docling for PDF parsing
* KubeFlow Pipelines (KFP) for automated data gathering
* Jupyter Notebooks for UI, hosted on RHOAI
* Python code for agents and RAG workflows
* IBM Granite 3.3 for Inference on MaaS
* IBM Granite 125M for embeddings

### Workflow

```
┌──────────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Upload PDFs │────▶│  Convert to │────▶│  Chunk &     │────▶│  Store in    │
│  to Minio    │     │  Markdown   │     │  Embed       │     │  Milvus      │
└──────────────┘     └─────────────┘     └──────────────┘     └──────────────┘
                                                                       │
                                                                       ▼
┌──────────────┐     ┌─────────────┐                          ┌──────────────┐
│  Present     │◀────│  RAG Query  │◀─────────────────────────│  Semantic    │
│  Results     │     │  Pipeline   │                          │  Search      │
└──────────────┘     └─────────────┘                          └──────────────┘
```

1. **Document Ingestion**: Upload PDF documents containing competitive intelligence (earnings reports, press releases, etc.)
2. **Data Processing**: Automatically convert PDFs to markdown, chunk content, and generate embeddings
3. **Vector Storage**: Store embeddings in Milvus for efficient similarity search
4. **Interactive Analysis**: Query and analyze documents using Jupyter notebooks with pre-built RAG workflows

## Prerequisites

Before you install the helm chart, ensure you have the following prerequisites in place:

### Provision RHOAI Cluster

Log in to the Red Hat Demo Platform (RHDP) and order this catalog item which contains a pre-installed RHOAI 2.22 on AWS - [RHOAI on OCP on AWS with NVIDIA GPUs](https://catalog.demo.redhat.com/catalog?item=babylon-catalog-prod/sandboxes-gpte.ocp4-demo-rhods-nvidia-gpu-aws.prod&utm_source=webapp&utm_medium=share-link)

* Select “Practice/Enablement” and “Trying out a technical solution”
* Ensure that “Enable Cert Manager” and “Enable OPEN Environment” are selected
* Leave the AWS Region at default value (It populates based on availability of GPUs)
* **IMPORTANT**: For “GPU Selection by Node Type” select `g6.4xlarge`
* Adjust the auto-stop and auto-destroy dates as per your needs, select the checkbox at the bottom of the instructions section, and click Order.
* It will take approximately 90-120 minutes for the cluster to fully provision. You will get an email once it is provisioned, with all the details needed to access the OpenShift cluster.

You can also use your own custom OpenShift cluster and install the RHOAI 2.25 operator and its pre-requisites by following the product documentation. You will need cluster admin rights to run the hands-on lab instructions. HW sizing recommended:

* 3 Control plane nodes (m6a.2xlarge)
	* CPU Cores - 8
	* Memory - 32GB
	* Disk - 100GB
* (Optional) 1 GPU worker node - GPU required for main inference LLM NVIDIA GPU with 24GiB vRAM (equivalent to g6.4xlarge on AWS)
* 2 worker nodes for non-GPU workloads (m6a.4xlarge)
	* CPU cores: 16
	* Memory: 64GB
	* Storage: 100Gi

> **NOTE**: GPU node is not mandatory. You only need it if you want to serve models within the RHOAI cluster. The solution uses Models as a Service (MaaS) by default, which provides a convienient remote inference end point (mimicking ChatGPT or Claude remote API access using API keys).

While the cluster is provisioning, we can go ahead and create an account at the MaaS portal to prepare our remote inference end point.

### Other Tools

* **OpenShift client** (`oc`):
	* The OpenShift oc command-line tool, configured to connect to your cluster.
* **Git CLI**:
	* To clone the GitHub repository containing the helm charts and notebooks.
* **jq tool**:
	* Install the jq tool for your platform to debug and test the responses from the LLM.
* **Web Terminal Operator**:
	* Install the web terminal operator from the OperatorHub. We will use it to do quick tests of the components deployed on OpenShift, as well as for general debugging.


### Create Models as a Service (MaaS) Account

Models as a Service (MaaS) is a free internally hosted service provided by the AI Business Unit that offers remote inference services to various LLMs. In scenarios where you cannot afford dedicated GPUs for your applications, MaaS provides a shared pool of GPUs that you can use to connect applications to LLMs.

MaaS offers OpenAI compatible end points, so your application code is not impacted. You can switch end points and test different models provided by MaaS.

* Navigate to [https://maas.apps.prod.rhoai.rh-aiservices-bu.com](https://maas.apps.prod.rhoai.rh-aiservices-bu.com) with a browser and click `Sign in`. Click `Authenticate with Red Hat Single Sign-On`. In the `MaaS on RHOAI` page, click the Google button to log in with your Red Hat ID.
* Click `Create an Application` and then select the `granite-3-3-8b-instruct model`.
* Enter `granite-3.3` as the name, provide a brief description and click Create Application
* Copy the `API Key value` and the `Model Name` and store it in a safe place. You will use this from applications and Jupyter Notebooks to send inference requests to the LLM. 
* Click on the `Usage Examples` tab. You will be provided with various options to test the inference end point. Run the curl commands for the Granite-3.3 model and replace the Authorization bearer token with your API key. You should receive a valid response back from the remote MaaS inference end point. 


## Installation

After the RHOAI cluster is provisioned and running, and assuming you have registered with MaaS to get the api key for remote inferencing, do the following:

### Upgrade the OpenShift Cluster to v2.25

> **NOTE**: You need to ensure your RHOAI version is at least 2.25. Ignore these steps if your installed RHOAI operator version is >=2.25.

* After provisioning your RHDP catalog item, you must have received an email with your credentials to access the OpenShift cluster as an administrator. This cluster comes with RHOAI 2.22 pre-installed.
* Navigate to the OpenShift web console URL and log in as the **admin** user.
* In the `Administrator` perspective, click on `Compute > Nodes`, and confirm that you have 3 control plane nodes, and three worker nodes (with one node having a GPU attached)
* Click on `Operators > Installed Operators` and verify that the RHOAI operator and its dependencies are installed and in Succeeded state.
* We need to ensure we are working with the latest stable version of RHOAI. Click the Red Hat OpenShift AI operator, and then click the `Subscription` tab.

![Upgrade RHOAI Operator](op-upgrade.png)

* Click the pencil icon below the `Update channel` label. You will see a pop-up listing all the available versions of the RHOAI operator. You need to select the **latest stable version** (which is 2.25 at the time of writing this article), and click `Save`.
* Click on **Operator > Installed Operators** and notice that the RHOAI operator is being updated. Wait until you see a `Succeeded` message in the `Status` column.
* Click on the Red Hat OpenShift AI operator and scroll to the bottom of the Details tab to see the messages from the update process. Verify that you can see the InstallSucceeded message with no errors.
* In the OpenShift web console, open the Red Hat OpenShift AI dashboard by clicking on the Red Hat Application icon (little squares in the top right corner), and log in as the **admin** user with the same credentials you used for logging into the OpenShift cluster.
* Once the RHOAI dashboard loads, click the question mark (?) icon in the top right navigation bar and verify that the latest stable version of RHOAI is displayed, along with the latest versions of the components in RHOAI.


### Get Your Cluster Domain

```bash
oc get routes -n openshift-console
# Look for: console-openshift-console.apps.<cluster-domain>
# Extract: apps.<cluster-domain>

# Example: apps.cluster-x5jfr.x5jfr.sandbox2053.opentlc.com
```

### Register and get an API key for Tavily search

We will use the Tavily search service to do a websearch from a Llamastack Agent. Register and create an API key for Tavily at https://app.tavily.com/home. Once you have the API key, store it in a safe place. You will need this key in the next step.

### Install the Helm Chart

```bash
# Clone this repository
git clone https://github.com/rsriniva/competitor-analysis.git
cd competitor-analysis

# Install with minimal configuration
helm install competitor-analysis ./helm \
  --namespace competitor-analysis \
  --create-namespace \
  --set llamastack.vllm.apiToken=<YOUR_MaaS_API_TOKEN> \
  --set llamastack.tavily.apiKey=<YOUR_TAVILY_API_KEY> \
  --set clusterDomainUrl=apps.<YOUR-CLUSTER-DOMAIN.com> \
  --wait \
  --timeout 20m
```

**Expected duration**: 10-15 minutes (with `--wait` flag)

The helm chart automates the following setup and configuration:

* Checks and enables the Llamastack components in the RHOAI operator (`DataScienceCluster` CR)
* Creates a namespace called `competitor-analysis` that contain all the components for the solution
* Deploys an instance of Minio to store various artifacts needed for the project
* Creates the required S3 compatible buckets in Minio to store input documents (PDF), converted documents (markdown), and pipeline runtime assets
* Deploys Llamastack server components and registers the models and vector database used in the solution
* Deploys an instance of Milvus vector database to store embeddings
* Deploys a pipeline server definition which manages pipeline runs for the project
* Deploys a Workbench (Notebook) which contains several notebooks used to test the solution

### Verify Installation

```
$ helm list
```

Ensure all the pods are in `Running` state

```bash
# Check all pods are running
oc get pods -n competitor-analysis

# Expected output:
# NAME                                  READY   STATUS    RESTARTS   AGE
# competitor-analysis-workbench-0       2/2     Running   0          5m
# etcd-...                              1/1     Running   0          12m
# llama-stack-dist-...                  1/1     Running   0          10m
# milvus-...                            1/1     Running   0          11m
# minio-...                             1/1     Running   0          12m
# pipelines-definition-ds-pipeline-...  2/2     Running   0          8m
...
```

## Usage Guide

### Step 1: Access the RHOAI Dashboard

```bash
# Get the dashboard URL
echo "https://rhods-dashboard-redhat-ods-applications.$(oc get route -n openshift-console console-openshift-console -o jsonpath='{.spec.host}' | cut -d'.' -f2-)"

# Or find it directly
oc get routes -n redhat-ods-applications rhods-dashboard
```

Login with your OpenShift credentials.

### Step 2: Upload Documents to Minio

```bash
# Get Minio Console URL
echo "https://minio-ui-competitor-analysis.$(oc get route -n competitor-analysis minio-ui -o jsonpath='{.spec.host}')"
```

1. Open the URL in your browser
2. Login with:
   - **Username**: `minio` (default)
   - **Password**: `minio123` (default)
3. Navigate to the `documents` bucket
4. Upload the PDF files in the `test-docs` folder of this repo (earnings reports, press releases, etc.) to the `documents` bucket

### Step 3: Import the Pipeline Definition

1. Open **RHOAI Dashboard** → **Data Science Projects** → `competitor-analysis`
2. Navigate to **Pipelines** → **Import pipeline**
3. Click **Upload file**
4. Select: `kfp/pipelines/pipeline.yaml` (from this repo)
5. Enter pipeline details:
   - **Name**: `document-ingestion-pipeline`
   - **Description**: `Document ingestion pipeline`
6. Click **Import pipeline**

### Step 4: Run the Pipeline

1. Navigate to **Pipelines** → **Runs** → **Create run**
2. Select pipeline: `document-ingestion-pipeline`
3. Fill in parameters:
   - `run_id`: `v1` (or any identifier for this run)
   - `minio_secret_name`: `minio-secret` (default)
   - `pipeline_configmap_name`: `pipeline-config` (default)
4. Click **Create** to start the pipeline

**Expected duration**: 5-15 minutes (depends on number of documents)

Monitor progress in the **Runs** page. Pipeline stages:
- Convert PDFs to markdown, chunk and embed documents
- Store embeddings in Milvus

### Step 5: Query Documents with Jupyter Notebooks

#### Access Your Workbench

1. Open **RHOAI Dashboard** → **Data Science Projects** → `competitor-analysis`
2. Navigate to **Workbenches**
3. Click **Open** next to `competitor-analysis-workbench`

Your workbench will open with the GitHub repository pre-cloned at:
`/opt/app-root/src/competitor-analysis/`

#### Run Query Notebooks

Open and run the pre-built notebooks:

1. **MaaS Test**: `1-maas-test.ipynb`
   - Simple test to validate inference using models hosted on MaaS
  
2. **Llamastack Test**: `2-llamastack-test-basic.ipynb`
   - Simple test to validate Llamastack setup. Llamastack sends the query to the remote inference end point running on MaaS
   
2. **Advanced Analysis**: `3-simple-rag.ipynb`
   - The main notebook demonstrating the solution

## Customization

The solution is made up of several building blocks, that can be further customized to adapt to the needs of your applications and workflows.

## Updating the Deployment

### Upgrade with New Values

You can customize the parameters in `values.yaml` and do a `helm upgrade`, or override the values using CLI flags to helm

```bash
helm upgrade competitor-analysis ./helm \
  -n competitor-analysis \
  --reuse-values \
  --set key=value
```

### Updating Notebooks

Clone the GitHub repo containing the notebooks (https://github.com/rsriniva/competitor-analysis-notebooks), and customize it if needed.

Change the `notebook.gitRepo.repository` value in `helm/values.yaml` to point to the newly cloned repo with your custom notebooks.

Run `helm upgrade`. The git-clone hook automatically runs when upgrading:

```bash
helm upgrade competitor-analysis ./helm \
  -n competitor-analysis \
  --reuse-values
```

Your workbench will have the latest code from GitHub!

### Modify Pipeline

The pipeline is currently implemented using Kubeflow Pipelines (KFP) v2. The pipeline code is written in Python, and the definition is compiled into YAML, which is then imported into RHOAI.

The pipeline consists of `components`, modular pieces (currently 2 python files) implementing a specific stage in your pipeline, which are then composed by an orchestrator (`pipeline.py`).

You can inspect and modify the pipeline. Currently, the input PDF documents are converted and embedded in sequential fashion. You can refer to the KFP documentation and explore ways to parallelize the pipeline, as well as make other enhancements.

```bash
# 1. Update pipeline code and components
cd kfp
vim pipeline.py

# 2. Recompile the Python code to YAML
./compile-all.sh

# 3. Re-import via RHOAI UI
# Dashboard → Pipelines → Import pipeline → Upload pipeline.yaml
```

## Troubleshooting and Clean up

### Uninstall Everything

If components fail, and you want to reset to original cluster status before running the helm chart:

```bash
# Uninstall Helm release
helm uninstall competitor-analysis -n competitor-analysis

# Delete namespace (WARNING: Deletes all data!)
oc delete project competitor-analysis
```

### Pods Not Starting

```bash
# Check pod status
oc get pods -n competitor-analysis

# Describe problematic pod
oc describe pod <pod-name> -n competitor-analysis

# Check logs
oc logs <pod-name> -n competitor-analysis --tail=100
```

### Pipeline Fails to Run

```bash
# Check DSPA status
oc get dspa pipelines-definition -n competitor-analysis -o yaml

# Check pipeline server logs
oc logs -n competitor-analysis -l app=ds-pipeline-pipelines-definition --tail=100

# Verify ConfigMap and Secret exist
oc get configmap pipeline-config -n competitor-analysis
oc get secret minio-secret -n competitor-analysis
```

### Milvus Connection Issues

```bash
# Check Milvus is running
oc get pods -n competitor-analysis -l app=milvus
```

### Workbench Git Clone Failed

```bash
# Check git clone job logs
oc logs -n competitor-analysis -l job-name=competitor-analysis-workbench-clone-repo

# Manually clone
oc exec -n competitor-analysis \
  $(oc get pods -l notebook-name=competitor-analysis-workbench -o name) \
  -c competitor-analysis-workbench -- \
  git clone https://github.com/rsriniva/competitor-analysis.git /opt/app-root/src/competitor-analysis
```

### Helm Install Timeout

```bash
# Increase timeout
helm install competitor-analysis ./helm \
  --timeout 30m \
  ...other flags...

# Or install without --wait and monitor manually
helm install competitor-analysis ./helm \
  ...flags...

oc get pods -n competitor-analysis -w
```

---

**Questions or Issues?** Open an issue on GitHub


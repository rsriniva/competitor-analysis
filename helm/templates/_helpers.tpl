{{/*
==============================================================================
Template Helpers for Competitor Analysis Chart
==============================================================================
This file contains reusable template functions used across all manifests.
*/}}

{{/*
Expand the name of the chart.
*/}}
{{- define "competitor-analysis.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "competitor-analysis.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "competitor-analysis.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "competitor-analysis.labels" -}}
helm.sh/chart: {{ include "competitor-analysis.chart" . }}
{{ include "competitor-analysis.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.commonLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "competitor-analysis.selectorLabels" -}}
app.kubernetes.io/name: {{ include "competitor-analysis.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Namespace
*/}}
{{- define "competitor-analysis.namespace" -}}
{{- .Values.namespace | default "competitor-analysis" }}
{{- end }}

{{/*
Minio labels
*/}}
{{- define "competitor-analysis.minio.labels" -}}
{{ include "competitor-analysis.labels" . }}
app.kubernetes.io/component: minio
{{- end }}

{{/*
Minio selector labels
*/}}
{{- define "competitor-analysis.minio.selectorLabels" -}}
{{ include "competitor-analysis.selectorLabels" . }}
app.kubernetes.io/component: minio
{{- end }}

{{/*
Milvus labels
*/}}
{{- define "competitor-analysis.milvus.labels" -}}
{{ include "competitor-analysis.labels" . }}
app.kubernetes.io/component: milvus
{{- end }}

{{/*
Milvus selector labels
*/}}
{{- define "competitor-analysis.milvus.selectorLabels" -}}
{{ include "competitor-analysis.selectorLabels" . }}
app.kubernetes.io/component: milvus
{{- end }}

{{/*
LlamaStack labels
*/}}
{{- define "competitor-analysis.llamastack.labels" -}}
{{ include "competitor-analysis.labels" . }}
app.kubernetes.io/component: llamastack
{{- end }}

{{/*
LlamaStack selector labels
*/}}
{{- define "competitor-analysis.llamastack.selectorLabels" -}}
{{ include "competitor-analysis.selectorLabels" . }}
app.kubernetes.io/component: llamastack
{{- end }}

{{/*
Minio service name
*/}}
{{- define "competitor-analysis.minio.serviceName" -}}
{{- printf "minio-service" }}
{{- end }}

{{/*
Milvus service name
*/}}
{{- define "competitor-analysis.milvus.serviceName" -}}
{{- printf "milvus-service" }}
{{- end }}

{{/*
LlamaStack service name
*/}}
{{- define "competitor-analysis.llamastack.serviceName" -}}
{{- printf "llama-stack-dist-service" }}
{{- end }}

{{/*
Minio endpoint (in-cluster DNS)
*/}}
{{- define "competitor-analysis.minio.endpoint" -}}
{{- printf "http://%s.%s.svc.cluster.local:%d" (include "competitor-analysis.minio.serviceName" .) (include "competitor-analysis.namespace" .) (int .Values.minio.service.apiPort) }}
{{- end }}

{{/*
Milvus endpoint (in-cluster DNS)
*/}}
{{- define "competitor-analysis.milvus.endpoint" -}}
{{- printf "http://%s.%s.svc.cluster.local:%d" (include "competitor-analysis.milvus.serviceName" .) (include "competitor-analysis.namespace" .) (int .Values.milvus.service.grpcPort) }}
{{- end }}

{{/*
LlamaStack endpoint (in-cluster DNS)
*/}}
{{- define "competitor-analysis.llamastack.endpoint" -}}
{{- printf "http://%s.%s.svc.cluster.local:%d" (include "competitor-analysis.llamastack.serviceName" .) (include "competitor-analysis.namespace" .) (int .Values.llamastack.service.port) }}
{{- end }}

{{/*
Milvus token (format: root:<password>)
*/}}
{{- define "competitor-analysis.milvus.token" -}}
{{- printf "root:%s" .Values.milvus.credentials.rootPassword }}
{{- end }}

{{/*
Etcd service name
*/}}
{{- define "competitor-analysis.etcd.serviceName" -}}
{{- printf "etcd-service" }}
{{- end }}

{{/*
Etcd endpoint
*/}}
{{- define "competitor-analysis.etcd.endpoint" -}}
{{- printf "%s:%d" (include "competitor-analysis.etcd.serviceName" .) (int .Values.milvus.etcd.service.port) }}
{{- end }}

{{/*
Secret key names for Minio
*/}}
{{- define "competitor-analysis.minio.secretUserKey" -}}
{{- printf "minio_root_user" }}
{{- end }}

{{- define "competitor-analysis.minio.secretPasswordKey" -}}
{{- printf "minio_root_password" }}
{{- end }}


{{- define "lungo-ui.mergedRuntimeEnv" -}}
{{- $out := dict -}}
{{- range $k, $v := .Values.configs.env.data -}}
{{- if $v }}{{- $_ := set $out $k $v -}}{{- end -}}
{{- end -}}
{{- $out | toJson -}}
{{- end -}}

{{- define "lungo-ui.envConfigJs" -}}
window.__ENV__ = {{ include "lungo-ui.mergedRuntimeEnv" . }};
{{- end -}}

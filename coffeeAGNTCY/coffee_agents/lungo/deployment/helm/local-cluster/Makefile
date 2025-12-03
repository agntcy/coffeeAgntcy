ENV_FILE ?= ../../../.env

create-cluster: kind create cluster --name lungo --config kind-config.yaml

apply:
	@set -a; source $(ENV_FILE); set +a; helm dependency update .; helmfile apply --skip-diff-on-install; \
	echo "✅ Installed lungo to local kind cluster"; \
	
# 	echo "Exporting Lungo-Local-Root-CA.crt..."; \
# 	kubectl -n cert-manager get secret local-root-ca -o jsonpath='{.data.ca\.crt}' | base64 -d > Lungo-Local-Root-CA.crt; \
# 	echo "✅ Lungo-Local-Root-CA.crt exported"; \
#   echo "Installing Lungo-Local-Root-CA.crt to system trust store...";
# 	sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain Lungo-Local-Root-CA.crt; \
# 	echo "✅ Lungo-Local-Root-CA.crt installed to system trust store"; \
# 	echo "127.0.0.1 lungo-ui.demo.com lungo-exchange.demo.com logistic-supervisor.demo.com logistic-helpdesk.demo.com" | sudo tee -a /etc/hosts > /dev/null; \

destroy:
	@echo ">> Uninstalling helm releases (best-effort, no wait)"
	-helmfile destroy --concurrency 4 --skip-diff-on-install || true

	@echo ">> Deleting cert-manager custom resources cluster-wide (fast, parallel)"
	- kubectl get certificaterequests.cert-manager.io -A -o name | xargs -r -P6 kubectl delete --wait=false --timeout=10s || true
	- kubectl get certificates.cert-manager.io       -A -o name | xargs -r -P6 kubectl delete --wait=false --timeout=10s || true
	- kubectl get challenges.acme.cert-manager.io    -A -o name | xargs -r -P6 kubectl delete --wait=false --timeout=10s || true
	- kubectl get orders.acme.cert-manager.io        -A -o name | xargs -r -P6 kubectl delete --wait=false --timeout=10s || true
	- kubectl get issuers.cert-manager.io            -A -o name | xargs -r -P6 kubectl delete --wait=false --timeout=10s || true
	- kubectl get clusterissuers.cert-manager.io     -A -o name | xargs -r -P6 kubectl delete --wait=false --timeout=10s || true

	@echo ">> Deleting webhooks & apiservices (don’t wait)"
	- kubectl get validatingwebhookconfigurations -o name | grep -E 'cert-manager' | xargs -r -P4 kubectl delete --wait=false --timeout=10s || true
	- kubectl get mutatingwebhookconfigurations   -o name | grep -E 'cert-manager' | xargs -r -P4 kubectl delete --wait=false --timeout=10s || true
	- kubectl get apiservices                     -o name | grep -E 'cert-manager' | xargs -r -P4 kubectl delete --wait=false --timeout=10s || true

	@echo ">> NOW delete CRDs (only after CRs are gone)"
	- kubectl get crd -o name | grep -E '(cert-manager\.io|acme\.cert-manager\.io)$$' | xargs -r -P4 kubectl delete --wait=false --timeout=10s || true

	@echo ">> Drop namespace (don’t wait)"
	- kubectl delete ns cert-manager --ignore-not-found --wait=false --timeout=10s || true

	@echo ">> If anything still terminating, run: make destroy-finalizers"

	helmfile destroy

diff:
	@set -a; source $(ENV_FILE); set +a; helmfile diff

install-helm-diff:
	@helm plugin install https://github.com/databus23/helm-diff
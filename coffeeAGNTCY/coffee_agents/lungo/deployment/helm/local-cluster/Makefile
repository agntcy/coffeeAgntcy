ENV_FILE ?= ../../../.env

apply:
	@set -a; source $(ENV_FILE); set +a; helm dependency update .; helmfile apply --skip-diff-on-install; \
	echo "Updating /etc/hosts..."; \
	IP=$$(kubectl -n ingress-nginx get svc ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}'); \
	if [ -z "$$IP" ]; then echo "❌ No LoadBalancer IP found"; exit 1; fi; \
	sudo awk '!/lungo-.*\.demo\.com/ {print}' /etc/hosts > /tmp/hosts.$$ && sudo mv /tmp/hosts.$$ /etc/hosts; \
	echo "$$IP  lungo-exchange.demo.com logistic-supervisor.demo.com logistic-helpdesk.demo.com lungo-ui.demo.com" | sudo tee -a /etc/hosts >/dev/null; \
	echo "✅ /etc/hosts updated with $$IP"

.PHONY: destroy-fast

KIND_SUBNET := $(shell docker network inspect kind -f '{{json .IPAM.Config}}' | jq -r '.[] | select(.Subnet | test(":") | not) | .Subnet')
METALLB_RANGE := $(shell python3 -c "import ipaddress; net=ipaddress.ip_network('$(KIND_SUBNET)', strict=False); start=list(net.hosts())[-51]; end=list(net.hosts())[-1]; print(f'{start}-{end}')")

print-range:
	@echo "Kind subnet: $(KIND_SUBNET)"
	@echo "Suggested MetalLB range: $(METALLB_RANGE)"

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
Issue 1: "path / is not a shared mount" (Node Exporter)

**Cause**: WSL doesn’t support shared mount propagation.  
**Solution**: Disable node-exporter in Helm values:
```yaml
# monitoring/prometheus-values.yaml
nodeExporter:
  enabled: false

Apply with:
helm upgrade prometheus ... -f monitoring/prometheus-values.yaml

Issue 2: Grafana Shows "No Data"
Diagnosis Checklist:

ServiceMonitors exist?
kubectl -n monitoring get servicemonitor

Prometheus targets UP?
kubectl -n monitoring port-forward svc/prometheus... 9090

Service port named "metrics"?
Worker service must have:
ports:
  - name: metrics
    port: 8001

FastAPI exposes metrics?
Ensure Instrumentator().instrument(app).expose(app) is in main.py.


Issue 3: Worker "Connection Refused to Queue"
Root Causes:

Incorrect NATS credentials in secret
NetworkPolicy blocking egress
NATS service not ready

Debug Commands:
# Verify secret
kubectl -n cuegrowth get secret app-secrets -o jsonpath='{.data.nats-worker-password}' | base64 -d

# Test connectivity
kubectl -n cuegrowth run -it --rm debug --image=busybox -- telnet nats 4222

# Check NetworkPolicy
kubectl -n cuegrowth describe netpol allow-worker-to-nats-valkey


Issue 4: ArgoCD "OutOfSync"
Fix:

Confirm repoURL in infra/argocd-app.yaml matches your GitHub repo
Ensure infra/kustomization.yaml exists and references charts correctly
In ArgoCD UI: Refresh → Sync


Issue 5: JWT Validation Fails
Validation Steps:

Secret must be 32+ bytes
kubectl -n cuegrowth get secret app-secrets -o jsonpath='{.data.jwt-secret}' | base64 -d

Token payload must include
{ "aud": "cuegrowth-api", "iss": "cuegrowth" }

Header format
curl -H "Authorization: Bearer <token>" ...

Issue 6: Helm PVC Conflicts
Symptom: "persistentvolumeclaims already exists"
Solution (dev only):

kubectl -n cuegrowth delete pvc -l app.kubernetes.io/name=valkey
helm upgrade valkey ...




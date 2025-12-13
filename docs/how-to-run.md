# CueGrowth DevOps Assessment  
## How to Run Locally  

**Candidate**: Uthayakumaran Uthayaragavan  
**Environment**: WSL Ubuntu 24.04 + MicroK8s  

---

### 1. Prerequisites

Install required tools:
```bash
sudo snap install microk8s --classic
sudo snap install helm --classic
sudo snap install kubectl --classic
sudo usermod -a -G microk8s $USER
newgrp microk8s
microk8s enable dns rbac helm3 ingress metrics-server registry

Verify cluster:
microk8s status --wait-ready
kubectl get nodes

Deployment Steps
Step 1: Clone Repository

git clone https://github.com/UthayakumarRakav/cuegrowth-devops-assessment.git
cd cuegrowth-devops-assessment

Step 2: Create Secrets
kubectl create namespace cuegrowth
kubectl label namespace cuegrowth pod-security.kubernetes.io/enforce=baseline

kubectl -n cuegrowth create secret generic app-secrets \
  --from-literal=valkey-password='secure_valkey_password_123!' \
  --from-literal=nats-api-user='api' \
  --from-literal=nats-api-password='nats_api_pass_789!' \
  --from-literal=nats-worker-user='worker' \
  --from-literal=nats-worker-password='nats_worker_pass_456!' \
  --from-literal=jwt-secret='your-super-secret-jwt-key-32bytes!'


Step 3: Deploy Monitoring
kubectl create namespace monitoring
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring -f monitoring/prometheus-values.yaml
kubectl apply -f monitoring/servicemonitors.yaml


Step 4: Deploy ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl apply -f infra/argocd-ingress.yaml
echo "127.0.0.1 argocd.local" | sudo tee -a /etc/hosts

Step 5: Deploy Application
# Update infra/argocd-app.yaml with your GitHub repo URL
kubectl apply -f infra/argocd-app.yaml

Step 6: Access Applications
ArgoCD UI: https://argocd.local (admin + auto-generated password)
API: curl http://api.local/stats (after adding to /etc/hosts)
Grafana: kubectl -n monitoring port-forward svc/prometheus-grafana 3000:80 → http://localhost:3000

Step 7: Generate Test Traffic
TOKEN="your-jwt-token"
for i in {1..5}; do
  curl -X POST http://api.local/task \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"input":"test"}'
done


Cleanup
kubectl delete -f infra/argocd-app.yaml
kubectl delete ns cuegrowth monitoring argocd
helm uninstall prometheus -n monitoring



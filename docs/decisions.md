
---
# CueGrowth DevOps Assessment  
## Architectural Decisions  


---

 1. MicroK8s on WSL

**Why Not Minikube/Kind?**  
- MicroK8s is **production-aligned** (uses containerd, not Docker)
- Native **snap installation** on Ubuntu
- Better **resource efficiency** for long-running services
- Supports all required addons: `ingress`, `registry`, `metrics-server`

Ideal balance of **local simplicity** and **production fidelity**.

---

2. NATS over Kafka/RabbitMQ

| Criteria        | NATS       | Kafka      | RabbitMQ   |
|-----------------|------------|------------|------------|
| Setup Complexity| Minimal    | ❌ High    | Medium  |
| Resource Usage  | <100MB     | ❌ >1GB    | ~500MB  |
| Persistence     | JetStream  | ✅         |  (plugin)|
| Metrics         | Built-in   | ✅         | ⚠️Plugin  |

**Decision**: NATS JetStream provides **replayable, persistent messaging** with **zero operational overhead** — perfect for this scope.

---

3. JWT for API Authentication

**Requirements Met**:
- Stateless validation
- Audience/issuer checks
- No external dependencies

**Why Not OAuth2?**  
- Overkill for internal service-to-service auth
- JWT is **simpler**, **faster**, and **sufficiently secure** when signed with strong secrets


---

4. ArgoCD + GitHub Actions (GitOps)

**CI/CD Separation**:
- **GitHub Actions**: Immutable image builds + vulnerability scanning
- **ArgoCD**: Declarative, self-healing deployments from Git

**Benefits**:
- Every change is **auditable** (Git commit)
- **Automatic drift correction**
- **One-click rollbacks**
- **No CI credentials in cluster**


---

5. Prometheus + Grafana

**Why Not SaaS?**  
- Requirement: **run locally**
- Requirement: **open-source**

**Advantages**:
- `kube-prometheus-stack` deploys full observability stack in 1 Helm command
- `ServiceMonitor` CRD enables **declarative metric discovery**
- Grafana dashboards are **versionable** and **portable**


---

6. Zero-Downtime Schema Migration

**Strategy**: Backward-compatible JSON with version field:
```json
{ "schema_version": 2, "result": "...", "processed_at": "..." }

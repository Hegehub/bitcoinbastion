````md
# Bitcoin Bastion

> **Bitcoin-first суверенный backend для evidence-driven market intelligence, операционной устойчивости и production-grade self-hosted развёртывания.**

![Status](https://img.shields.io/badge/status-RC--ready%20pending%20environment%20evidence-orange)
![Bitcoin First](https://img.shields.io/badge/bitcoin-first-f7931a)
![No Custody](https://img.shields.io/badge/no--custody-enforced-brightgreen)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688)
![Kubernetes](https://img.shields.io/badge/kubernetes-supported-326ce5)
![License](https://img.shields.io/badge/license-TBD-lightgrey)

---

## 1. Что такое Bitcoin Bastion?

**Bitcoin Bastion** — это Bitcoin-first backend-платформа для операторов, разработчиков, аналитиков и будущих Bitcoin-native систем, которым нужны:

- рыночная и новостная аналитика;
- проверяемое состояние внешних провайдеров;
- evidence-driven production readiness;
- наблюдаемость runtime-состояния;
- контролируемое Kubernetes-развёртывание;
- no-custody архитектура;
- суверенный self-hosted подход.

Проект создаётся не как обычный backend, а как **суверенная инфраструктурная основа** для Bitcoin-ориентированных систем, где важны:

- прозрачность;
- воспроизводимость;
- контроль оператора;
- отсутствие скрытого доверия к внешним провайдерам;
- проверяемость релиза;
- audit trail;
- отказоустойчивость;
- честное отображение degraded/fallback/synthetic состояний.

Bitcoin Bastion — это не кошелёк, не кастодиальный сервис и не автоматический торговый исполнитель.

---

## 2. Главная идея проекта

Главная идея Bitcoin Bastion:

> Не доверять молча работающим системам.  
> Делать runtime, риски, провайдеров, deployment и readiness видимыми, проверяемыми и управляемыми оператором.

Проект должен стать backend-ядром для Bitcoin-native инфраструктуры, где любое важное состояние подтверждается evidence-артефактами, а не просто словами в документации.

---

## 3. Философия Bitcoin Bastion

| Принцип | Значение |
|---|---|
| **Bitcoin-first** | Bitcoin является основной точкой проектирования. Всё остальное — вторично и изолировано. |
| **No-custody** | Система не хранит, не запрашивает и не передаёт seed-фразы или private keys. |
| **Operator control** | Рискованные действия должны быть видимы оператору и требовать осознанного подтверждения. |
| **Evidence over claims** | Готовность, состояние runtime и качество провайдеров должны подтверждаться артефактами. |
| **Self-hosted capable** | Проект должен запускаться на VPS, bare metal, homelab или приватном Kubernetes-кластере. |
| **No black-box trust** | Внешние провайдеры считаются потенциально ненадёжными и должны проверяться. |
| **Explicit limitations** | Synthetic, advisory, degraded, fallback и baseline состояния не скрываются. |
| **Rollback discipline** | Любой production-релиз должен иметь понятный rollback-путь. |
| **Auditability** | Release decision должен быть объяснимым и подтверждённым evidence. |

---

## 4. Чем Bitcoin Bastion не является

Bitcoin Bastion **не является**:

- custodial wallet;
- seed phrase manager;
- private key storage;
- сервисом хранения средств;
- полностью автоматическим торговым ботом;
- финансовым советником;
- заменой Bitcoin consensus;
- mining/Stratum системой;
- централизованным SaaS-сервисом;
- системой, которая скрывает degraded или fallback состояние.

Если в будущем будут добавляться функции, связанные с транзакциями, wallet-интеграцией или signing-flow, они должны сохранять no-custody модель:

- watch-only режим;
- PSBT-first workflow;
- external signing;
- explicit human confirmation;
- audit log;
- policy engine;
- запрет доступа к seed/private keys.

---

## 5. Архитектура высокого уровня

```text
Bitcoin Bastion
│
├── FastAPI Backend
│   ├── API routes
│   ├── health/readiness endpoints
│   ├── admin/status endpoints
│   ├── observability endpoints
│   └── metrics endpoint
│
├── Core Services
│   ├── provider health
│   ├── market/news intelligence
│   ├── delivery logic
│   ├── recovery checks
│   ├── protocol advisory layer
│   └── Citadel risk/evidence layer
│
├── Data Layer
│   ├── PostgreSQL
│   ├── SQLAlchemy
│   ├── Alembic migrations
│   └── schema parity validation
│
├── Background Runtime
│   ├── Celery worker
│   ├── Celery beat
│   ├── Redis broker/cache
│   └── scheduled jobs
│
├── Evidence Layer
│   ├── release evidence
│   ├── migration smoke evidence
│   ├── schema parity evidence
│   ├── provider evidence
│   ├── observability snapshot
│   └── deployment evidence pack
│
└── Kubernetes Runtime Layer
    ├── API deployment
    ├── worker deployment
    ├── beat deployment
    ├── migration jobs
    ├── evidence jobs
    ├── provider-health CronJobs
    ├── recovery drill CronJobs
    ├── NetworkPolicy
    ├── ServiceMonitor
    ├── GitOps templates
    ├── security policies
    └── production runbooks
````

---

## 6. Основные компоненты

### 6.1 FastAPI Backend

FastAPI backend отвечает за:

* API endpoints;
* health checks;
* readiness checks;
* admin status;
* observability snapshot;
* metrics endpoint;
* координацию сервисного слоя;
* участие в release evidence flow.

Backend должен быть строго типизирован, проверяем и пригоден для production-развёртывания.

---

### 6.2 PostgreSQL

PostgreSQL используется как production-grade persistence layer.

В проекте должны быть предусмотрены:

* Alembic migrations;
* migration smoke checks;
* schema parity validation;
* PostgreSQL staging validation;
* evidence artifacts.

Ключевые evidence-файлы:

```text
artifacts/postgres_migration_smoke.json
artifacts/postgres_schema_parity.json
```

---

### 6.3 Redis + Celery

Redis и Celery используются для background runtime.

Типовые задачи:

* provider health collection;
* scheduled recovery checks;
* delivery jobs;
* evidence-related jobs;
* operational checks;
* future drill execution.

Celery worker и Celery beat должны запускаться отдельно от API.

---

### 6.4 Provider Health Layer

Внешние провайдеры не считаются абсолютно надёжными.

Provider Health Layer отвечает за:

* проверку доступности провайдеров;
* оценку provider confidence;
* фиксацию fallback/mock состояния;
* provider evidence;
* degraded mode visibility;
* передачу состояния в observability и release evidence.

Система не должна молча доверять одному источнику данных.

---

### 6.5 Citadel Layer

**Citadel** — это advisory risk/evidence layer.

Он может включать:

* runtime risk assessment;
* recovery readiness indicators;
* synthetic/baseline labeling;
* confidence penalties;
* provider evidence correlation;
* operator guidance;
* limitations и warning surfaces.

Важно:

> Citadel — это advisory слой.
> Он не является Bitcoin consensus и не должен описываться как источник окончательной истины.

---

### 6.6 Protocol Advisory Layer

Bitcoin protocol-related аналитика является advisory.

Слой может анализировать:

* chain-state related signals;
* provider corroboration;
* finality/reorg-related risk indicators;
* protocol warnings;
* external provider consistency.

Важно:

> Protocol analytics не являются consensus proof.
> Bitcoin consensus остаётся за Bitcoin nodes и самим Bitcoin protocol.

---

## 7. Evidence Layer

Bitcoin Bastion строится вокруг evidence-based readiness.

Ожидаемые evidence artifacts:

```text
artifacts/release_evidence.json
artifacts/postgres_migration_smoke.json
artifacts/postgres_schema_parity.json
artifacts/sbom.spdx.json
artifacts/sbom.cyclonedx.json
artifacts/vulnerability_report.json
artifacts/provenance.json
```

Evidence может включать:

* git SHA;
* image digest;
* environment;
* timestamp;
* health status;
* readiness status;
* migration result;
* schema parity result;
* observability snapshot;
* provider health summary;
* known limitations;
* operator acknowledgement.

Цель evidence layer — не просто “запустить код”, а доказуемо подтвердить, что система готова к следующему этапу.

---

## 8. Kubernetes Runtime Control Plane

Bitcoin Bastion поддерживает Kubernetes как **суверенный runtime control plane**.

Kubernetes используется для:

* воспроизводимого deployment;
* runtime isolation;
* health/readiness enforcement;
* migration jobs;
* evidence jobs;
* provider-health CronJobs;
* recovery drill CronJobs;
* observability;
* NetworkPolicy;
* GitOps promotion;
* rollback discipline;
* production runbooks.

Kubernetes здесь не является cloud lock-in.
Он должен усиливать Bastion-философию:

* больше контроля;
* больше изоляции;
* больше наблюдаемости;
* больше воспроизводимости;
* больше evidence;
* меньше ручного хаоса.

Проект должен оставаться совместимым с:

* VPS;
* bare metal;
* homelab;
* private Kubernetes cluster;
* self-hosted infrastructure.

---

## 9. Kubernetes-возможности

| Возможность                 | Назначение                                       |
| --------------------------- | ------------------------------------------------ |
| `Deployment`                | API, worker, beat runtime                        |
| `Job`                       | migrations, evidence generation, validation      |
| `CronJob`                   | provider-health checks, recovery drills, backups |
| `ConfigMap`                 | non-secret configuration                         |
| `Secret` / `ExternalSecret` | secret injection без хранения credentials в Git  |
| `NetworkPolicy`             | уменьшение blast radius                          |
| `ServiceMonitor`            | Prometheus scraping                              |
| `HPA` / KEDA                | масштабирование API/workers                      |
| GitOps                      | controlled promotion dev → staging → production  |
| Kyverno / OPA examples      | policy-as-code guardrails                        |
| Grafana dashboards          | operational visibility                           |
| Alertmanager routing        | incident notification                            |
| Backup/restore jobs         | operational recovery                             |
| DR drills                   | failure simulation                               |
| Evidence archive            | release auditability                             |

---

## 10. Структура репозитория

Примерная структура проекта:

```text
.
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   └── tasks/
│
├── scripts/
│   ├── collect_release_evidence.py
│   ├── run_postgres_migration_smoke.py
│   └── check_postgres_schema_parity.py
│
├── deploy/
│   └── kubernetes/
│       ├── base/
│       ├── overlays/
│       ├── gitops/
│       ├── security/
│       ├── observability/
│       ├── autoscaling/
│       ├── evidence/
│       ├── rollout/
│       ├── backup/
│       ├── drills/
│       └── operations/
│
├── docs/
│   ├── STATUS.md
│   ├── PRODUCTION_READINESS.md
│   ├── FINAL_PRODUCTION_GAP_AUDIT.md
│   ├── DEPLOYMENT_EVIDENCE_PACK.md
│   ├── OPERATIONS_RUNBOOK.md
│   └── ...
│
├── tests/
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── README.md
```

---

## 11. Текущий статус проекта

Текущий целевой статус:

```text
RC-ready pending environment evidence
```

Это означает:

* кодовые проверки могут проходить;
* Kubernetes manifests могут быть добавлены;
* evidence jobs могут существовать;
* production-oriented документация может быть готова;
* но финальный RC-статус требует реальных environment evidence artifacts.

Полный статус **Production Release Candidate** можно объявлять только после прохождения локальных gates и получения evidence из целевой/staging среды.

---

## 12. Локальный запуск

### 12.1 Клонирование

```bash
git clone https://github.com/Hegehub/bitcoinbastion.git
cd bitcoinbastion
```

### 12.2 Установка

```bash
make install-dev
```

Если такой Makefile target отсутствует, используй актуальный способ установки зависимостей из репозитория.

### 12.3 Настройка окружения

```bash
cp .env.example .env
```

После этого нужно заполнить `.env`.

Важно:

> Никогда не коммить реальные secrets, tokens, private keys, seed phrases или production credentials.

### 12.4 Миграции

```bash
make migrate
```

### 12.5 Запуск приложения

```bash
make run
```

---

## 13. Локальная проверка

Стандартные verification gates:

```bash
make lint
python -m pytest -q
make migration-smoke
make docs-truthfulness
make ci-release-gates
```

Ожидаемое состояние для production-grade readiness:

* lint проходит;
* mypy проходит;
* tests проходят;
* migration smoke проходит;
* docs truthfulness проходит;
* CI release gates проходят.

Если хотя бы один gate падает, проект нельзя честно переводить в RC.

---

## 14. Docker / Docker Compose

Для локального контейнерного запуска:

```bash
docker compose up -d --build
```

Проверка состояния:

```bash
docker compose ps
```

Если endpoints доступны:

```bash
curl http://localhost:8000/api/v1/health/live
curl http://localhost:8000/api/v1/health/ready
curl http://localhost:8000/metrics
```

---

## 15. Kubernetes Deployment

### 15.1 Render manifests

```bash
make k8s-render-dev
make k8s-render-staging
make k8s-render-production
```

Или напрямую:

```bash
kubectl kustomize deploy/kubernetes/overlays/dev
kubectl kustomize deploy/kubernetes/overlays/staging
kubectl kustomize deploy/kubernetes/overlays/production
```

### 15.2 Apply staging

```bash
make k8s-apply-staging
make k8s-status
```

### 15.3 Migration и evidence jobs

```bash
make k8s-run-migration
make k8s-run-postgres-migration-smoke
make k8s-run-postgres-schema-parity
make k8s-run-release-evidence
make k8s-collect-evidence-artifacts
```

Ожидаемые артефакты:

```text
artifacts/release_evidence.json
artifacts/postgres_migration_smoke.json
artifacts/postgres_schema_parity.json
```

### 15.4 Production promotion

Перед production promotion:

```bash
make k8s-promotion-checklist
make k8s-production-approval-template
```

Production apply только после evidence и approval:

```bash
make k8s-apply-production
make k8s-status
```

---

## 16. Production Readiness Gates

Для Production Release Candidate нужны:

| Gate                          | Требование             |
| ----------------------------- | ---------------------- |
| Lint                          | PASS                   |
| Mypy                          | PASS                   |
| Tests                         | PASS                   |
| Migration smoke               | PASS                   |
| Docs truthfulness             | PASS                   |
| CI release gates              | PASS                   |
| Kubernetes render             | PASS                   |
| PostgreSQL staging validation | PASS                   |
| Release evidence              | PRESENT                |
| Schema parity evidence        | PRESENT                |
| Observability validation      | PASS                   |
| Backup strategy               | DOCUMENTED / VALIDATED |
| Rollback plan                 | DOCUMENTED             |
| Operator sign-off             | PRESENT                |
| No-custody posture            | PRESERVED              |

---

## 17. Evidence Artifacts

Ключевые артефакты:

```text
artifacts/release_evidence.json
artifacts/postgres_migration_smoke.json
artifacts/postgres_schema_parity.json
artifacts/sbom.spdx.json
artifacts/sbom.cyclonedx.json
artifacts/vulnerability_report.json
artifacts/provenance.json
```

Они нужны для:

* release auditability;
* deployment reproducibility;
* production readiness decision;
* incident review;
* rollback analysis;
* operator sign-off.

---

## 18. Security Model

Bitcoin Bastion security posture:

* no custody;
* no seed phrase handling;
* no private key handling;
* no silent provider trust;
* explicit fallback/degraded states;
* strict environment configuration;
* Kubernetes NetworkPolicy;
* non-root containers;
* resource limits;
* secret separation;
* optional External Secrets integration;
* optional Kyverno/OPA policy-as-code;
* optional image signing and SBOM generation;
* evidence-based release process.

---

## 19. No-Custody Rules

Следующие правила обязательны:

* не запрашивать seed phrases;
* не хранить seed phrases;
* не передавать seed phrases;
* не запрашивать private keys;
* не хранить private keys;
* не подписывать Bitcoin-транзакции автоматически;
* не выполнять финансовые действия без явного подтверждения оператора;
* не скрывать risk state от оператора.

Если в будущем появится wallet/transaction functionality, она должна строиться вокруг:

* watch-only mode;
* PSBT-first workflows;
* external signing;
* explicit human confirmation;
* audit logs;
* policy enforcement.

---

## 20. Observability

Проект поддерживает или планирует observability через:

* `/metrics`;
* health endpoints;
* readiness endpoints;
* observability snapshots;
* provider-health evidence;
* recovery checks;
* Kubernetes ServiceMonitor;
* Prometheus rules;
* Grafana dashboards;
* Alertmanager routing;
* incident automation notes.

Production observability должна отслеживать:

* API availability;
* readiness stability;
* degraded mode;
* provider fallback;
* provider confidence;
* Citadel runtime health;
* recovery findings;
* worker queue health;
* delivery failures;
* migration/evidence job status;
* backup status.

---

## 21. Backup, Restore и DR

Production operations должны включать:

* PostgreSQL backup strategy;
* restore validation;
* PITR strategy, если применимо;
* Redis recovery strategy;
* provider outage drill;
* delivery outage drill;
* recovery SLO drill;
* disaster recovery runbook;
* evidence retention policy.

Production restore должен быть явным и operator-controlled.

> Никакой destructive restore не должен запускаться автоматически.

---

## 22. GitOps и Release Governance

Рекомендуемый production flow:

```text
dev → staging → evidence → approval → production
```

Promotion должен основываться на:

* immutable image digest;
* rendered Kubernetes manifests;
* passing local gates;
* passing staging deployment;
* migration evidence;
* schema parity evidence;
* release evidence;
* observability validation;
* operator approval.

Production не должен использовать mutable `latest` images.

---

## 23. Supply Chain Security

Рекомендуемые controls:

* SBOM generation;
* vulnerability scanning;
* image signing;
* provenance;
* immutable image digests;
* admission policy examples;
* no unsigned production image без accepted exception;
* no hidden vulnerability exceptions.

Возможные инструменты:

* Syft;
* Trivy;
* Grype;
* pip-audit;
* Cosign;
* Kyverno;
* OPA Gatekeeper.

---

## 24. Runtime Security

Рекомендуемые Kubernetes runtime controls:

* least-privilege RBAC;
* restricted Pod Security;
* default-deny NetworkPolicy;
* controlled egress;
* emergency lockdown policy;
* secret leakage scanning;
* runtime detection examples;
* kube-bench;
* kube-score;
* Polaris;
* Falco rules.

Emergency lockdown должен по возможности сохранять observability, но блокировать небезопасные внешние коммуникации.

---

## 25. Known Limitations

Bitcoin Bastion должен честно отображать ограничения.

Возможные ограничения:

* Citadel может включать synthetic/baseline components.
* Protocol analytics являются advisory, а не consensus proof.
* Provider data может быть stale, unavailable или inconsistent.
* Telegram/delivery providers могут отказать.
* Kubernetes evidence требует реального выполнения в кластере.
* Production SLOs требуют burn-in evidence.
* Backup/restore claims требуют реальной restore validation.
* Security policy examples не равны enforced cluster policy.
* GitOps templates не являются доказательством production deployment.

---

## 26. Roadmap

### Phase 1 — Backend hardening

* typed service/repository boundaries;
* stable schema models;
* migration smoke tests;
* docs truthfulness;
* release gates.

### Phase 2 — Evidence layer

* release evidence;
* PostgreSQL evidence;
* schema parity evidence;
* observability snapshot;
* provider-health evidence.

### Phase 3 — Kubernetes foundation

* API/worker/beat deployments;
* migration jobs;
* evidence jobs;
* NetworkPolicy;
* ServiceMonitor;
* staging/production overlays.

### Phase 4 — Kubernetes production hardening

* GitOps;
* External Secrets;
* Kyverno/OPA;
* Grafana dashboards;
* Alertmanager;
* KEDA;
* backup/restore;
* DR drills.

### Phase 5 — Supply chain security

* SBOM;
* vulnerability scanning;
* image signing;
* provenance;
* immutable image digest promotion.

### Phase 6 — Production RC

* staging deployment;
* evidence generation;
* operator sign-off;
* production cutover;
* burn-in;
* post-RC hardening.

---

## 27. Quick Command Reference

```bash
# Local checks
make lint
python -m pytest -q
make migration-smoke
make docs-truthfulness
make ci-release-gates

# Docker
docker compose up -d --build

# Kubernetes render
make k8s-render-dev
make k8s-render-staging
make k8s-render-production

# Kubernetes staging
make k8s-apply-staging
make k8s-status

# Evidence jobs
make k8s-run-migration
make k8s-run-postgres-migration-smoke
make k8s-run-postgres-schema-parity
make k8s-run-release-evidence
make k8s-collect-evidence-artifacts

# Production promotion
make k8s-promotion-checklist
make k8s-production-approval-template
make k8s-apply-production

# Security / operations
make k8s-security-check
make k8s-secret-scan
make supply-chain-check
make k8s-operations-check
```

Некоторые targets могут зависеть от optional local tools. Если target недоступен, смотри соответствующую документацию в `docs/` и `deploy/kubernetes/`.

---

## 28. Contribution Rules

Перед внесением изменений:

1. Сохранять no-custody posture.
2. Не добавлять seed/private-key handling.
3. Не скрывать degraded/fallback/synthetic states.
4. Не ослаблять lint/tests/CI gates.
5. Не коммитить secrets.
6. Не заявлять production readiness без evidence.
7. Синхронизировать docs с реальным кодом.
8. Предпочитать explicit operator control вместо silent automation.
9. Сохранять Bitcoin-first design.
10. Делать deployment воспроизводимым.

---

## 29. Final Production Decision Model

Release decision должен быть evidence-based.

Возможные состояния:

```text
NOT READY
PRE-RC / PRODUCTION-ORIENTED BETA
RC-ready pending environment evidence
PRODUCTION RELEASE CANDIDATE
```

Проект можно назвать **Production Release Candidate** только если:

* local gates проходят;
* Kubernetes render проходит;
* staging evidence существует;
* PostgreSQL evidence существует;
* release evidence существует;
* security evidence reviewed;
* operator sign-off существует;
* P0 blockers отсутствуют.

---

## 30. License

License status: **TBD**.

Перед production или публичным commercial use нужно определить и добавить явную лицензию.

---

## 31. Summary

Bitcoin Bastion — это Bitcoin-first, no-custody, evidence-driven backend-платформа для суверенной операционной аналитики и production-grade deployment control.

Сильнейшая идея проекта:

> Не доверять молча работающим системам.
> Делать runtime, risk, deployment и readiness видимыми, проверяемыми и operator-controlled.

Bitcoin Bastion создаётся как основа для серьёзной Bitcoin-native инфраструктуры, где sovereignty, evidence и operational discipline имеют значение.

```
```


## Bastion Trace
Bastion Trace status: INITIAL BASELINE / NOT PRODUCTION-COMPLETE
Advisory only; baseline scoring placeholder; no trusted external risk sources; no legal verdict; no consensus proof; no seed/private key intake; no Stratum/mining introduced.


## Core documentation
- docs/ARCHITECTURE.md
- docs/API_CONTRACTS.md
- docs/DOMAIN_MODELS.md
- docs/PRODUCTION_READINESS.md
- docs/STATUS.md
- docs/BASTION_TRACE.md


Bastion Trace: BASELINE SCORING IMPLEMENTED / NOT PRODUCTION-CALIBRATED
Weights are deterministic baseline defaults and not production-calibrated. Confidence measures evidence reliability, not safety. Provider disagreement reduces confidence. Privacy risk is separate from illicit-risk claims.


Bastion Trace: BASELINE SCORING + EVIDENCE RECEIPTS + ORIGIN/SOURCE BASELINE IMPLEMENTED / NOT PRODUCTION-CALIBRATED


Bastion Trace: BASELINE SCORING + EVIDENCE RECEIPTS + ORIGIN/SOURCE BASELINE + PRIVACY SHIELD BASELINE IMPLEMENTED / NOT PRODUCTION-CALIBRATED


Bastion Trace: BASELINE SCORING + EVIDENCE RECEIPTS + ORIGIN/SOURCE BASELINE + PRIVACY SHIELD + COUNTERPARTY/PAYMENT CONTEXT BASELINE IMPLEMENTED / NOT PRODUCTION-CALIBRATED


Bastion Trace: LITE PUBLIC ADDRESS CHECK BASELINE IMPLEMENTED / NOT PRODUCTION-CALIBRATED

Business Tier is a capability profile, not billing enforcement. Business policy actions are operational recommendations, not legal verdicts. Business policy actions do not execute payments. Batch screening accepts only public Bitcoin addresses. Sensitive wallet material is rejected and not stored. Review Desk is for operator review, not automated enforcement. Proof packets are evidence bundles, not legal certificates. API-key scopes are placeholders unless auth infrastructure exists. Bastion Trace: BUSINESS TIER BASELINE IMPLEMENTED / NOT PRODUCTION-CALIBRATED

Enterprise Tier is a capability profile, not billing enforcement. RBAC/SSO are placeholders unless connected to production auth/IdP. Legal Hold is operational metadata and not legal advice. Immutable Audit Log is append-only at application level unless WORM is configured. SIEM hooks are placeholders unless delivery infrastructure is configured. Retention auto-delete is disabled by default. Legal hold overrides retention. Enterprise proof packets are evidence bundles, not legal certificates. Bastion Trace: ENTERPRISE TIER GOVERNANCE BASELINE IMPLEMENTED / NOT PRODUCTION-CALIBRATED

Bastion Trace is a module inside Bitcoin Bastion, not the whole platform. Citadel consumes Trace as a separate advisory contribution. Policy Bridge does not execute payments. Treasury Bridge does not sign or broadcast transactions. Register Bridge is advisory and does not auto-reject payments. Cross-domain evidence refs preserve auditability. Trace production calibration is still pending. Bastion Trace: PLATFORM INTEGRATION BASELINE IMPLEMENTED / NOT PRODUCTION-CALIBRATED
Bastion Trace metrics use bounded labels only. Bitcoin addresses are never used as Prometheus labels. Trace status is operational and not a production calibration claim. Telegram commands are advisory and never request seed/private keys. Trace alerts are placeholders unless delivery infrastructure exists. Production alert delivery requires environment configuration. trace_production_calibrated remains false until real calibration evidence exists.


## Bastion Trace (module)

Bastion Trace is a backend module inside Bitcoin Bastion for advisory public Bitcoin address analysis (risk/origin/privacy/context) with Lite/Pro/Business/Enterprise capability profiles.

Safety posture:
- no custody
- no seed phrase/private key/wallet-file handling
- no transaction signing or broadcasting
- advisory only (not a legal verdict, not Bitcoin consensus proof)

Reference docs:
- `docs/BASTION_TRACE.md`
- `docs/BASTION_TRACE_API.md`
- `docs/BASTION_TRACE_DOMAIN_MODEL.md`
- `docs/BASTION_TRACE_TIERS.md`
- `docs/BASTION_TRACE_INTEGRATIONS.md`
- `docs/BASTION_TRACE_OBSERVABILITY.md`
- `docs/BASTION_TRACE_LIMITATIONS.md`


## Public Website Backend Foundation

Public-safe website backend APIs are available under `/api/v1/public/*` for landing, status, roadmap, feature catalog, stats, and Trace summary presentation. These APIs are advisory-only and do not expose internal evidence chains by default.


## Frontend Foundation

Frontend architecture/design-system foundation is baseline implemented under `frontend/` using presentation-safe APIs. No transaction signing and no seed/private-key handling exists in frontend. Placeholder sections are intentionally marked.


Public website foundation implemented. Public pages are informational baseline and interactive workflows are still pending.


Trace Lite frontend workflow is advisory-only, accepts only public Bitcoin addresses, rejects seed/private key material, and is baseline (not production-calibrated).

Detailed Trace reports are advisory-only. Proof packets are evidence bundles and not legal certificates.

Business UI is baseline.
Enterprise UI is baseline/placeholder.
Business decisions are not legal verdicts.
Proof packets are not legal certificates.
No payment is executed from Review Desk actions.
Enterprise RBAC/SSO/SIEM require production configuration.

Platform dashboard is informational and operational. Citadel outputs are advisory-only. Operations UI does not manage infrastructure directly. Kubernetes/GitOps panels are informational baseline. Deployment evidence may be incomplete or placeholder. Production calibration is still pending.

Frontend hardening baseline completed.

Security hardening baseline implemented. Rate limiting is baseline and should also exist at infrastructure level. Frontend does not accept seed phrases/private keys. CSP and security headers may require tuning in production. Production penetration testing not yet completed.

Deployment manifests are baseline and require environment adaptation. Observability stack is baseline and requires tuning.

Calibration framework baseline implemented. Production calibration evidence is still pending. Release gates are baseline governance controls. Deployment evidence registry may contain placeholders until staging validation occurs. Operational validation remains incomplete until real deployments are exercised.

Repository stabilization baseline completed. Technical debt remains and is documented. Production validation is still pending.

Repository: Release Candidate Baseline. Frontend: baseline stabilized. Backend: baseline hardened. Deployment: baseline prepared. Calibration: pending production validation. Security: hardened baseline, validation pending. Production readiness: NOT COMPLETE.

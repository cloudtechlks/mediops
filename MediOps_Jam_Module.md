# LKS CITY-LEVEL MODULE — CLOUD COMPUTING

## MediOps Cloud Jam — Incident Response & Troubleshooting

**LKS 2027 · Cloud Computing · City Level · Module 4**

| Duration | Difficulty | Platform | Focus | Format |
|----------|-----------|----------|-------|--------|
| **4 Hours** | **Medium–Hard** | **AWS Academy** | **Troubleshooting / Incident Response** | **AWS Jam** |

---

## 1. PROJECT DESCRIPTION

### 1.1 Background

Over the weekend the MediOps clinic portal was redeployed from a new CloudFormation template.
Since then **everything has been falling apart**: the site returns 502, the compliance scanner is
screaming about public data, credentials leaked into Parameter Store, private instances cannot
reach the internet, the service crash-loops, jobs disappear after failures, and the 40-minute
outage went completely unnoticed.

You are the on-call cloud engineer. **The environment already exists and is broken.**
Your job is **not** to build from scratch — it is to **diagnose and repair** it in place.

> **Do not delete and redeploy the stack to "fix" things.** Each issue must be repaired on the
> live resources. Validators check that a specific defect is GONE.

### 1.2 Four tracks, twelve incidents

This module is split into **4 tracks**, each covering a different troubleshooting domain.

| Track | Domain | Incidents | Points |
|-------|--------|-----------|:------:|
| **A** | **Security Hardening (Cyber Security)** | SEC-1042, SEC-1043, SEC-1044 | **25** |
| **B** | **Network & Connectivity** | NET-2011, NET-2012, NET-2013 | **25** |
| **C** | **Application & Service Health** | APP-3007, APP-3008, APP-3009 | **25** |
| **D** | **Reliability & Observability** | REL-4001, REL-4002, REL-4003 | **25** |
| | **Total** | 12 incidents | **100** |

| # | Track | Incident ticket | Difficulty | Points |
|---|-------|-----------------|------------|:------:|
| 1 | A | SEC-1042 · Data Exposure Report | Medium | 7 |
| 2 | A | SEC-1043 · Inbound Traffic Anomaly | Hard | 8 |
| 3 | A | SEC-1044 · Credential Leak | Hard | 10 |
| 4 | B | NET-2011 · Private Tier Has No Egress | Medium | 8 |
| 5 | B | NET-2012 · 502 Bad Gateway | Hard | 10 |
| 6 | B | NET-2013 · Connection Timed Out to Database | Medium | 7 |
| 7 | C | APP-3007 · Service Never Stabilises | Hard | 10 |
| 8 | C | APP-3008 · Boot-Time Configuration Failure | Hard | 8 |
| 9 | C | APP-3009 · Stale Release / Capacity Shortfall | Medium | 7 |
| 10 | D | REL-4001 · Silent Outage | Hard | 8 |
| 11 | D | REL-4002 · Disappearing Jobs | Medium | 8 |
| 12 | D | REL-4003 · Capacity Did Not Scale | Hard | 9 |
| | | **Total** | | **100** |

> **The incident tickets describe SYMPTOMS only.** The Jam dashboard will not tell
> you which resource is broken or what to change — that is the exercise. Several
> tickets have more than one contributing cause; fixing only one of them leaves the
> symptom in place. There is also some noise in the account that looks like a
> finding but is not covered by any ticket.

Challenges unlock **in order** — the next one opens once the previous has **at least one
submission**. Each allows **at most 2 submissions**. Opening a clue permanently reduces that
task's maximum score (capped at 50%).

### 1.3 Technical Details

1. **Region:** `us-east-1`
2. **Resource prefix:** `mediops-`
3. **IAM:** existing `LabRole` / `LabInstanceProfile`
4. **Environment:** created by `cloudformation/mediops-incident.yaml` (deploy it first)
5. **Student ID:** replace `<studentid>` with your ID (lowercase)
6. **Learner Lab session:** 4 hours

---

## 2. GETTING STARTED — create the broken environment

Deploy `cloudformation/mediops-incident.yaml` in `us-east-1` with stack name `mediops-incident`. Supply `StudentId`, `LatestAmi` (a current Amazon Linux AMI ID from the organizer), and `IncidentDbPassword` (a unique disposable lab password; NoEcho). Use the existing LabRole. Enter the password through the CloudFormation parameter form; never commit it or place it in shell history.

Wait until the stack is `CREATE_COMPLETE`, then start investigating. The stack output
`IncidentSummary` lists the ticket IDs you have to close.

> **Important:** this template is intentionally broken. Deploying it *is* the starting state.
> Never edit the template to "fix" things — fix the live resources in AWS so that
> a re-run of the validators reports SOLVED.

---

## 3. ARCHITECTURE

The topology below is what the environment is *supposed* to look like. It is
shown so you can reason about the intended traffic paths — it deliberately does
**not** mark which parts are broken.

```
                          Internet
                              │  http://<alb-dns>/
                     ┌────────▼─────────┐
                     │ ALB mediops-alb  │  public subnets (2 AZ)
                     │ :80              │  SG mediops-alb-sg
                     └────────┬─────────┘
                              │ target group mediops-tg :3000
                     ┌────────▼──────────────────────────┐
                     │ ECS Fargate  mediops-service        │  private subnets (2 AZ)
                     │ task: web :3000                     │  SG mediops-app-sg
                     └────┬───────────────────┬───────────┘
                          │ 5432              │ egress
                 ┌────────▼────────┐  ┌───────▼────────┐
                 │ RDS mediops-db  │  │ NAT mediops-nat│
                 │ (private)       │  │ (public subnet)│
                 │ SG mediops-db-sg│  └─────────────────┘
                 └─────────────────┘
                          ▲
                Secrets Manager mediops-db-secret
                SSM /mediops/* (non-secret config)

   S3 mediops-docs-<studentid>-<accountid>  SQS mediops-jobs-queue → mediops-jobs-dlq
   SNS mediops-alerts                CloudWatch mediops-dashboard + alarm
   ASG mediops-asg (worker pool, not on the load balancer)
```

### 3.1 Incident brief (what was reported)



This is exactly what the on-call team handed you. Nothing more.

| Ticket | Reported symptom |
|--------|------------------|
| SEC-1042 | Compliance scan: *"Sensitive patient documents are reachable from the public internet."* Flags exposure, missing integrity protection and missing confidentiality on the same asset. |
| SEC-1043 | SOC: repeated inbound connection attempts to management and data-tier ports from arbitrary public IPs. Stated policy is a strict tiered path internet → LB → app → data. |
| SEC-1044 | Secrets scanner: *"A database credential is stored in plaintext configuration."* Two non-sensitve parameters in the same area are legitimate. |
| NET-2011 | Private-tier instances cannot reach the internet (`yum update` times out, outbound API calls fail). In-cidr traffic works. Public/private separation must be preserved. |
| NET-2012 | Public URL returns 502 Bad Gateway. All targets in the target group report `unhealthy`. More than one contributing cause. |
| NET-2013 | App logs: `connection timed out` opening a DB connection. Instance is `available`, endpoint resolves, routing is fine. Current rule set is both too permissive and wrong. |
| APP-3007 | Container service is in a crash-loop: tasks start, fail health check, get killed. Desired count never reached. Several values disagree with the rest of the platform. |
| APP-3008 | App boots then fails with `secret not found` / `invalid endpoint`. Code unchanged — values point at nothing or at placeholders. |
| APP-3009 | After a release the portal still serves the previous version and falls over under modest load. |
| REL-4001 | A 40-minute outage was discovered only because a customer complained. Nothing paged, nothing charted. The alerting pipeline is broken end to end. |
| REL-4002 | Background jobs vanish after a few failed attempts. No record of what failed, no way to re-run. |
| REL-4003 | During a traffic spike the site fell over; capacity never increased. Two independent defects in the scaling configuration produce the same symptom. |

### 3.2 How this module differs from 1–3

| | M1 MediTrack | M2 CareHost | M3 MediFlow | **M4 MediOps** |
|---|---|---|---|---|
| Task | Deploy | Deploy (IaC) | Deploy serverless | **Repair an existing broken stack** |
| Skill | Build | Build + IaC | Orchestration | **Diagnose & troubleshoot** |
| Domains | 1 (containers) | 1 (traditional) | 1 (serverless) | **4 (security/network/app/reliability)** |

---

## 4. TRACK DETAIL

Each track is 25 points. The tickets below are grouped by domain; the Jam
platform shows the same text and unlocks them in order.

### Track A — Security Hardening (Cyber Security) · 25 pts

**SEC-1042 (7)** · Data Exposure Report — a compliance finding about patient
documents being reachable publicly, with integrity and confidentiality also
flagged on the same asset.

**SEC-1043 (8)** · Inbound Traffic Anomaly — SOC sees connection attempts to
management and datastore ports from the internet. The tiered path must be
restored *and* the application must remain reachable from the load balancer.

**SEC-1044 (10)** · Credential Leak — a database password sits in plaintext
configuration. It must end up in a secrets service as structured data and the
leak must be gone; neighbouring non-sensitive parameters must survive.

### Track B — Network & Connectivity · 25 pts

**NET-2011 (8)** · Private Tier Has No Egress — outbound from private subnets
fails while in-cidr traffic works. The public/private separation must hold.

**NET-2012 (10)** · 502 Bad Gateway — public URL fails, all targets unhealthy.
Several contributing causes; fixing one leaves the symptom in place.

**NET-2013 (7)** · Connection Timed Out to Database — connectivity to the data
tier is blocked, while the current rule set is also too permissive.

### Track C — Application & Service Health · 25 pts

**APP-3007 (10)** · Service Never Stabilises — crash-loop; tasks are killed on
health check. Multiple contract violations between the workload and the platform.

**APP-3008 (8)** · Boot-Time Configuration Failure — the app reads values that
point at nothing or at placeholders. Every setting must be cross-checked.

**APP-3009 (7)** · Stale Release / Capacity Shortfall — old version still served
and the site falls over under load.

### Track D — Reliability & Observability · 25 pts

**REL-4001 (8)** · Silent Outage — nobody was paged. The alerting pipeline is
broken end to end; all three legs have missing pieces.

**REL-4002 (8)** · Disappearing Jobs — failed messages are dropped with no
recovery path. The failure-handling half of the design is missing.

**REL-4003 (9)** · Capacity Did Not Scale — the group cannot scale out by
construction, and self-healing is impaired.

---

## 5. HOW THE JAM WORKS

1. Register / log in, select **Module 4 — MediOps**, enter the shared access code + AWS keys.
2. Deploy `mediops-incident.yaml` to create the broken environment (see §2).
3. Work through the incidents **in order**. Read the symptom, find the cause, fix it in AWS.
4. Click **Verify** — the platform checks that the defect is gone.
5. Stuck? Reveal a **Clue** (penalty, capped at 50% of that task's points).

Your score is **not shown** during the event; the organizers see the live leaderboard.

---

## 6. TESTING & VERIFICATION

- **SEC:** `aws s3api get-public-access-block` returns all true; no SSM parameter
  `/mediops/db_password`; `aws secretsmanager describe-secret --secret-id mediops-db-secret` works.
- **NET:** `aws ec2 describe-route-tables` shows private `0.0.0.0/0 → nat-...`; target group health
  check path is `/health`; `curl http://<alb-dns>/health` returns 200.
- **APP:** `aws ecs describe-services` shows `runningCount: 2`; task definition containerPort 3000
  and env vars populated.
- **REL:** `aws cloudwatch list-dashboards` shows `mediops-dashboard`; SQS attributes show a
  `RedrivePolicy`; ASG shows `MinSize 2 / MaxSize 4 / HealthCheckType ELB` plus a scaling policy.

All of the above are scored automatically through the **Verify** button.

---

*LKS 2027 · Cloud Computing · City Level · MediOps Cloud Jam (Module 4)*

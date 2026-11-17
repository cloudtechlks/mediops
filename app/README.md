# MediOps Recovery Console

The original Jam access code, Start button and AI pre-check are unchanged.
Questions and submission/scoring remain in Jam. The application restoration key
is generated and used entirely inside this application, never in the Jam UI.

## Deployment contract

Build the supplied app/ Dockerfile for linux/amd64 and publish to ECR. Pass its URI
as AppImageUri to the incident template. Use existing LabRole for ECS execution/task
roles. No organizer signing key or RecoveryPublicKey parameter is needed.

Runtime environment: APP_PORT=3000, AWS_REGION=us-east-1, DB_HOST (actual PostgreSQL
endpoint), DB_SECRET_ARN (JSON username/password/dbname), DOCS_BUCKET (your documents
bucket), MEDIOPS_RECOVERY_MODE=local. Do not rewrite supplied application logic.

Restore the supplied infrastructure according to the incidents; do not substitute
a completed solution over participant work. The initial idle service and wrong
configuration are intentional starting conditions, not a deployment failure to skip.
GET /health is liveness only, so load balancing can recover before data wiring.

## Application unlock flow

1. Repair/deploy the workload and open CloudFormation output AlbUrl.
2. In the locked application select **Check restoration and obtain application key**.
3. The backend checks AWS configuration and real PostgreSQL/S3 connectivity. Any
   failed check or API permission error keeps the app locked. It does not reveal
   which incident to fix and does not contact Jam.
4. When ready, the app returns a random key in the input box. Select **Unlock operations**.
5. Demonstrate database-backed requests, SQS processing and private S3 documents.

Only key hashes are stored in PostgreSQL, shared by all ECS replicas. Keys expire
in four hours and protected API operations recheck readiness. A failed deployment
cannot be unlocked with an arbitrary key. No plaintext key is logged or persisted
in browser storage. This is a synthetic lab, not per-user patient authentication.
The AWS task role must support read access to the relevant EC2, RDS, ECS, ELB,
SSM, Secrets Manager, S3, SNS, CloudWatch, SQS and Auto Scaling APIs as well as the
application's actual data operations. Organizer must test Learner Lab permissions.

Use trusted HTTPS supplied by the organizer before entering keys. Baseline HTTP
is only for isolated troubleshooting. Never use real patient data or AWS browser
credentials. Supplied code is visible to participants, who control their own AWS
resources; the app gate is functional feedback, not anti-cheating security. Jam
validators and judge acceptance remain the independent assessment.

## Local preview

Install requirements, then run `flask --app app run --port 3000` from app/.
The locked page and /health work locally without AWS. Successful readiness/data
operations require an actual configured AWS lab, not fabricated local statuses.

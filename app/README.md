# MediOps Recovery Console — supplied application

Questions appear in Jam after Start and the AI pre-check. Do not change application
business logic. Restore the existing incident environment; do not replace it with
a completed solution stack. This folder is application source, not an answer key.

## Runtime contract

| Variable | Requirement |
|---|---|
| APP_PORT | 3000 |
| AWS_REGION | us-east-1 |
| DB_HOST | Actual PostgreSQL endpoint |
| DB_SECRET_ARN | Secrets Manager JSON: username, password, dbname |
| DOCS_BUCKET | Your deployment's private documents bucket |
| RECOVERY_PUBLIC_KEY | Organizer-supplied base64url Ed25519 public verification key |

Use existing LabRole as ECS task and execution role. Build the supplied Dockerfile
for linux/amd64 and publish to your own ECR repository. The incident template takes
AppImageUri and RecoveryPublicKey as deployment inputs. The organizer supplies the
public key before deployment. The private signing key is never supplied to participants.

The app uses the existing SQS queue named mediops-jobs-queue. Database tables are
initialized on first dashboard access; use synthetic references/text only.
GET /health is liveness only, independent of database configuration. This allows
network/load-balancer incidents to be repaired before data configuration incidents.
The root page is a locked recovery console, not an operational dashboard yet.

## Completion flow

1. Resolve and submit all twelve incidents in Jam.
2. On the Jam task board select **Request Recovery Token**. Jam rechecks all twelve
   incidents against your AWS account; this does not award points or consume attempts.
3. Once all checks pass, copy the signed token. It is account-bound and expires
   after four hours. Request it before your module working time ends.
4. Open the CloudFormation stack output **AlbUrl**, paste the token and unlock.
5. Demonstrate a queued request, job processing, private S3 document storage and
   actual database/storage/queue status. Failed jobs are retried and can reach the DLQ.

The token is completion evidence at issuance, not continuous posture certification.
It is not a patient identity system: all holders of an account's valid token share
that lab's synthetic workspace. For a real event, supply HTTPS at the ALB before
entering tokens. The baseline incident listener is HTTP; do not use real data or
credentials there. Never put AWS keys in the browser, image or repository.

## Local UI inspection

Install requirements and run `flask --app app run --port 3000` from this directory.
The locked page and /health can be viewed without AWS credentials. Unlock and data
operations require the organizer public key, a valid Jam token and a real AWS lab
deployment; the application does not fabricate connection results in local mode.

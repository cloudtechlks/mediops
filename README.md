# MediOps — Participant Starter

LKS 2027 · Cloud Computing · City Level

The module questions and challenges are available in the Jam platform after you press Start and pass the AI pre-check; they are not included in this repository. Read `app/README.md` if this module contains an application.

AWS Academy Learner Lab · us-east-1 · existing LabRole · 240 minutes · 100 points.
Submit verification through the competition Jam platform, not GitHub.

## Your task

Deploy cloudformation/mediops-incident.yaml as the starting state, using your own unique disposable IncidentDbPassword (NoEcho). This template deliberately creates an insecure lab, including a plaintext configuration incident; never use real credentials or production accounts. Repair live resources; do not replace this with a solution stack. Ask the organizer for the current Amazon Linux AMI ID.

This repository contains supplied application source/contracts (where applicable), and incident starting templates only where required. It contains no judge validators, clues, answer keys, solve scripts, or completed infrastructure solutions.

## Safety

Use synthetic data only. Never commit AWS credentials, passwords, Terraform state, plans, generated artifacts, or your completed competition solution to this starter repository. Keep participant infrastructure work in your own private workspace. Follow organizer instructions for cleanup.

## Application restoration

The original code for entering/starting the Jam module is unchanged. No application
restoration token is issued or entered in Jam. Jam remains questions/submissions/scoring.

Read app/README.md. Build/publish app/ and restore the existing incident environment.
At stack output AlbUrl, the application itself checks readiness. If the environment
is ready, it generates an application key there. Use it on the same page to unlock
all dashboard functions. Failed readiness keeps operations locked, including with
an old key. Keys are hashed in PostgreSQL and expire after four hours.

No organizer signing key, public key parameter or Jam recovery endpoint is needed.
Use trusted HTTPS and synthetic data only. Existing lab deployments need an in-place
image rollout; do not replace participant stacks or reset recorded scores. Live AWS
permissions/browser acceptance must be tested before competition use.

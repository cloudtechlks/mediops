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

## Recovery Console

The supplied app/ now contains a real token-gated operational dashboard. Read
app/README.md for its runtime contract. Build/publish the application image to ECR
(or use an organizer-provided release); supply AppImageUri and RecoveryPublicKey
when creating the incident starting state. The public key is available on the Jam
task board after Start and the AI pre-check. Never include a private signing key.

Resolve and submit twelve incidents, then request a Recovery Token in Jam before
your timer ends. Jam checks the live environment again; the signed token unlocks
the application at the stack output AlbUrl. It does not add points or consume
attempts. Use organizer-provided trusted HTTPS for token entry and synthetic data only.

This is a new starting-state version, not a reason to replace an existing stack.
For labs already in progress, ask the organizer for an in-place migration before
changing workload configuration. The source and templates have offline tests;
live AWS deployment and browser acceptance remain required before competition use.

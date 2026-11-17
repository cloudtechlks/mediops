"""Supplied MediOps recovery application. Never contains incident answers."""
import functools
import json
import os
import uuid

import boto3
import psycopg2
from flask import Flask, jsonify, render_template, request
from psycopg2.extras import RealDictCursor
from recovery_token import verify_token

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32768


def client(service):
    return boto3.client(service, region_name=os.environ.get("AWS_REGION", "us-east-1"))


@functools.lru_cache(maxsize=1)
def account_id():
    return client("sts").get_caller_identity()["Account"]


def authorized(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer ") or not header[7:].strip():
            return jsonify(error="A valid Jam Recovery Token is required."), 401
        try:
            verify_token(header.removeprefix("Bearer ") if header.startswith("Bearer ") else "",
                         os.environ.get("RECOVERY_PUBLIC_KEY", ""), account_id())
        except ValueError:
            return jsonify(error="A valid Jam Recovery Token is required."), 401
        return view(*args, **kwargs)
    return wrapped


def connection():
    secret = json.loads(client("secretsmanager").get_secret_value(
        SecretId=os.environ.get("DB_SECRET_ARN", ""))["SecretString"])
    return psycopg2.connect(host=os.environ.get("DB_HOST", ""), port=5432,
        dbname=secret.get("dbname", "mediops"), user=secret["username"],
        password=secret["password"], connect_timeout=5)


def database(operation, params=(), fetch=False):
    conn = connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("CREATE TABLE IF NOT EXISTS mediops_cases "
                               "(id VARCHAR(36) PRIMARY KEY, reference VARCHAR(80) NOT NULL, "
                               "status VARCHAR(20) NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW())")
                cursor.execute(operation, params)
                return [dict(row) for row in cursor.fetchall()] if fetch else None
    finally:
        conn.close()


def queue_url():
    return client("sqs").get_queue_url(QueueName="mediops-jobs-queue")["QueueUrl"]


@app.after_request
def security(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.errorhandler(Exception)
def failed(exc):
    from werkzeug.exceptions import HTTPException
    if isinstance(exc, HTTPException):
        return jsonify(error=exc.name), exc.code
    # Do not log secret values, uploaded text, tokens or connection strings.
    app.logger.error("dependency_failure type=%s", type(exc).__name__)
    return jsonify(error="An application dependency is unavailable. Check the deployment and service logs."), 503


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    # Liveness deliberately independent of data dependencies: network/ALB
    # incidents must be repairable before database configuration incidents.
    return jsonify(status="alive", service="MediOps", version="2.0")


@app.post("/api/unlock")
@authorized
def unlock():
    return jsonify(unlocked=True, account=account_id())


@app.get("/api/dashboard")
@authorized
def dashboard():
    cases = database("SELECT id, reference, status, created_at FROM mediops_cases ORDER BY created_at DESC LIMIT 50", fetch=True)
    bucket = os.environ.get("DOCS_BUCKET", "")
    objects = client("s3").list_objects_v2(Bucket=bucket, Prefix="documents/", MaxKeys=50)
    sqs = client("sqs")
    attributes = sqs.get_queue_attributes(QueueUrl=queue_url(), AttributeNames=["ApproximateNumberOfMessages", "RedrivePolicy"])["Attributes"]
    return jsonify(cases=cases, documents=[{"key": o["Key"], "bytes": o["Size"]} for o in objects.get("Contents", [])],
                   queued=int(attributes.get("ApproximateNumberOfMessages", 0)),
                   redrive_configured=bool(attributes.get("RedrivePolicy")),
                   services={"database": "CONNECTED", "storage": "CONNECTED", "queue": "CONNECTED"})


@app.post("/api/cases")
@authorized
def create_case():
    data = request.get_json(silent=True)
    reference = data.get("reference") if isinstance(data, dict) else None
    if not isinstance(reference, str) or not 1 <= len(reference.strip()) <= 80:
        return jsonify(error="Provide a synthetic reference of 1-80 characters."), 400
    case_id = str(uuid.uuid4())
    database("INSERT INTO mediops_cases (id, reference, status) VALUES (%s,%s,%s)", (case_id, reference.strip(), "PENDING"))
    # Pending records remain visible if enqueue fails; never claim completion.
    client("sqs").send_message(QueueUrl=queue_url(), MessageBody=json.dumps({"case_id": case_id}))
    database("UPDATE mediops_cases SET status=%s WHERE id=%s AND status='PENDING'", ("QUEUED", case_id))
    return jsonify(id=case_id, status="QUEUED"), 202


@app.post("/api/documents")
@authorized
def document():
    data = request.get_json(silent=True)
    text = data.get("text") if isinstance(data, dict) else None
    if not isinstance(text, str) or not 1 <= len(text.encode("utf-8")) <= 20000:
        return jsonify(error="Provide synthetic text of 1-20,000 UTF-8 bytes."), 400
    key = "documents/" + str(uuid.uuid4()) + ".txt"
    client("s3").put_object(Bucket=os.environ.get("DOCS_BUCKET", ""), Key=key,
                            Body=text.encode("utf-8"), ContentType="text/plain; charset=utf-8")
    return jsonify(key=key), 201


@app.post("/api/jobs/process")
@authorized
def process():
    sqs = client("sqs")
    url = queue_url()
    messages = sqs.receive_message(QueueUrl=url, MaxNumberOfMessages=5, WaitTimeSeconds=1).get("Messages", [])
    completed = failed_count = 0
    for message in messages:
        try:
            case_id = json.loads(message["Body"])["case_id"]
            if not isinstance(case_id, str) or len(case_id) != 36:
                raise ValueError("Invalid job")
            database("UPDATE mediops_cases SET status=%s WHERE id=%s", ("COMPLETED", case_id))
            sqs.delete_message(QueueUrl=url, ReceiptHandle=message["ReceiptHandle"])
            completed += 1
        except Exception:
            failed_count += 1  # Leave the message for retry and eventual DLQ.
    return jsonify(completed=completed, retrying=failed_count)
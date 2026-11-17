"""Live application recovery checks. No fixes or incident answers are performed."""
import json
import os


def is_ready(client):
    """Fail closed on missing resources, failed checks or denied AWS API access.

    The application owns this gate; it never calls the Jam platform. Resource
    identity is fixed to this lab and its configured documents bucket.
    """
    try:
        bucket = os.environ.get("DOCS_BUCKET", "")
        s3 = client("s3")
        blocks = s3.get_public_access_block(Bucket=bucket)["PublicAccessBlockConfiguration"]
        if not all(blocks.get(k) for k in ("BlockPublicAcls", "BlockPublicPolicy", "IgnorePublicAcls", "RestrictPublicBuckets")):
            return False
        if s3.get_bucket_versioning(Bucket=bucket).get("Status") != "Enabled":
            return False
        if not s3.get_bucket_encryption(Bucket=bucket)["ServerSideEncryptionConfiguration"]["Rules"]:
            return False
        if client("ssm").get_parameters(Names=["/mediops/db_password"], WithDecryption=False).get("Parameters"):
            return False

        rds = client("rds").describe_db_instances(DBInstanceIdentifier="mediops-db")["DBInstances"][0]
        if (rds.get("DBInstanceStatus") != "available" or rds.get("PubliclyAccessible")
                or rds["Endpoint"]["Address"] != os.environ.get("DB_HOST")):
            return False
        secret = json.loads(client("secretsmanager").get_secret_value(SecretId=os.environ.get("DB_SECRET_ARN", ""))["SecretString"])
        if (not secret.get("password") or secret.get("username") != rds.get("MasterUsername")
                or secret.get("dbname") != rds.get("DBName", "mediops")):
            return False

        ec2 = client("ec2")
        groups = ec2.describe_security_groups(Filters=[{"Name": "tag:Name", "Values": ["mediops-app-sg", "mediops-db-sg", "mediops-alb-sg"]}])["SecurityGroups"]
        by_name = {tag["Value"]: g for g in groups for tag in g.get("Tags", []) if tag["Key"] == "Name"}
        app, db, alb = (by_name[n] for n in ("mediops-app-sg", "mediops-db-sg", "mediops-alb-sg"))
        for group in (app, db):
            for rule in group.get("IpPermissions", []):
                if any(r.get("CidrIp") == "0.0.0.0/0" for r in rule.get("IpRanges", [])) or any(r.get("CidrIpv6") == "::/0" for r in rule.get("Ipv6Ranges", [])):
                    return False
        def linked(group, port, source):
            return any(r.get("IpProtocol") == "tcp" and r.get("FromPort") == port and r.get("ToPort") == port
                       and any(p.get("GroupId") == source for p in r.get("UserIdGroupPairs", []))
                       for r in group.get("IpPermissions", []))
        if not linked(app, 3000, alb["GroupId"]) or not linked(db, 5432, app["GroupId"]):
            return False
        routes = ec2.describe_route_tables(Filters=[{"Name": "tag:Name", "Values": ["mediops-private-rt"]}])["RouteTables"]
        defaults = [r for rt in routes for r in rt["Routes"] if r.get("DestinationCidrBlock") == "0.0.0.0/0"]
        if not defaults or any(r.get("State") != "active" or not r.get("NatGatewayId") for r in defaults):
            return False
        nat_ids = list({r["NatGatewayId"] for r in defaults})
        if any(n["State"] != "available" for n in ec2.describe_nat_gateways(NatGatewayIds=nat_ids)["NatGateways"]):
            return False

        elb = client("elbv2")
        load_balancer = next(a for a in elb.describe_load_balancers()["LoadBalancers"] if a["LoadBalancerName"] == "mediops-alb")
        targets = elb.describe_target_groups(LoadBalancerArn=load_balancer["LoadBalancerArn"])["TargetGroups"]
        if not any(t.get("HealthCheckPath") == "/health" and t.get("Port") == 3000
                   and any(h["TargetHealth"]["State"] == "healthy" for h in elb.describe_target_health(TargetGroupArn=t["TargetGroupArn"])["TargetHealthDescriptions"])
                   for t in targets):
            return False
        ecs = client("ecs")
        service = ecs.describe_services(cluster="mediops-cluster", services=["mediops-service"])["services"][0]
        if service.get("runningCount", 0) < 2 or service.get("desiredCount", 0) < 2:
            return False
        task = ecs.describe_task_definition(taskDefinition=service["taskDefinition"])["taskDefinition"]
        web = next(d for d in task["containerDefinitions"] if d["name"] == "web")
        env = {e["name"]: e["value"] for e in web.get("environment", [])}
        if (not any(p.get("containerPort") == 3000 for p in web.get("portMappings", []))
                or env.get("APP_PORT") != "3000"
                or any(env.get(k) != os.environ.get(k) for k in ("DB_HOST", "DB_SECRET_ARN", "DOCS_BUCKET"))):
            return False

        sns = client("sns")
        topic = next(t["TopicArn"] for t in sns.list_topics()["Topics"] if t["TopicArn"].endswith(":mediops-alerts"))
        if not sns.list_subscriptions_by_topic(TopicArn=topic)["Subscriptions"]:
            return False
        cw = client("cloudwatch")
        cw.get_dashboard(DashboardName="mediops-dashboard")
        if not any(topic in a.get("AlarmActions", []) for a in cw.describe_alarms(AlarmNamePrefix="mediops-")["MetricAlarms"]):
            return False
        sqs = client("sqs")
        main = sqs.get_queue_url(QueueName="mediops-jobs-queue")["QueueUrl"]
        dead = sqs.get_queue_url(QueueName="mediops-jobs-dlq")["QueueUrl"]
        policy = json.loads(sqs.get_queue_attributes(QueueUrl=main, AttributeNames=["RedrivePolicy"])["Attributes"]["RedrivePolicy"])
        arn = sqs.get_queue_attributes(QueueUrl=dead, AttributeNames=["QueueArn"])["Attributes"]["QueueArn"]
        if policy.get("deadLetterTargetArn") != arn or not 1 <= int(policy.get("maxReceiveCount", 0)) <= 10:
            return False
        scaling = client("autoscaling")
        group = scaling.describe_auto_scaling_groups(AutoScalingGroupNames=["mediops-asg"])["AutoScalingGroups"][0]
        if group["MinSize"] < 2 or group["MaxSize"] < 4 or group["DesiredCapacity"] < 2 or group["HealthCheckType"] not in ("EC2", "ELB"):
            return False
        if not any(p.get("PolicyType") == "TargetTrackingScaling" for p in scaling.describe_policies(AutoScalingGroupName="mediops-asg")["ScalingPolicies"]):
            return False
        return True
    except Exception:
        return False

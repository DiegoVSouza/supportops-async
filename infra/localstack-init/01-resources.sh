#!/bin/sh
set -eu

awslocal sqs create-queue --queue-name supportops-tasks-dlq >/dev/null
DLQ_ARN="$(awslocal sqs get-queue-attributes --queue-url http://localhost:4566/queue/us-east-1/000000000000/supportops-tasks-dlq --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)"
export DLQ_ARN
python -c 'import json, os; json.dump({"RedrivePolicy": json.dumps({"deadLetterTargetArn": os.environ["DLQ_ARN"], "maxReceiveCount": "3"})}, open("/tmp/supportops-sqs-attributes.json", "w"))'
awslocal sqs create-queue --queue-name supportops-tasks --attributes file:///tmp/supportops-sqs-attributes.json >/dev/null
awslocal sns create-topic --name task-created >/dev/null
awslocal sns create-topic --name task-completed >/dev/null
awslocal sns create-topic --name task-failed >/dev/null

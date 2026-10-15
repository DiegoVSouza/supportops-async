#!/bin/sh
set -eu

awslocal sqs create-queue --queue-name supportops-tasks-dlq >/dev/null
DLQ_ARN="$(awslocal sqs get-queue-attributes --queue-url http://localhost:4566/queue/us-east-1/000000000000/supportops-tasks-dlq --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)"
REDRIVE="$(printf '{"deadLetterTargetArn":"%s","maxReceiveCount":"3"}' "$DLQ_ARN")"
awslocal sqs create-queue --queue-name supportops-tasks --attributes "RedrivePolicy=$REDRIVE" >/dev/null
awslocal sns create-topic --name task-created >/dev/null
awslocal sns create-topic --name task-completed >/dev/null
awslocal sns create-topic --name task-failed >/dev/null

resource "aws_sqs_queue" "dlq" {
  name                      = "${var.name_prefix}-tasks-dlq"
  message_retention_seconds = 1209600
}

resource "aws_sqs_queue" "tasks" {
  name                       = "${var.name_prefix}-tasks"
  visibility_timeout_seconds = 30
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
}

resource "aws_sns_topic" "created" {
  name = "task-created"
}

resource "aws_sns_topic" "completed" {
  name = "task-completed"
}

resource "aws_sns_topic" "failed" {
  name = "task-failed"
}

resource "aws_iam_policy" "worker" {
  name = "${var.name_prefix}-worker-minimum"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:ChangeMessageVisibility", "sqs:GetQueueUrl", "sqs:SendMessage"]
      Resource = [aws_sqs_queue.tasks.arn, aws_sqs_queue.dlq.arn]
    }, {
      Effect = "Allow"
      Action = ["sns:Publish"]
      Resource = [aws_sns_topic.created.arn, aws_sns_topic.completed.arn, aws_sns_topic.failed.arn]
    }]
  })
}

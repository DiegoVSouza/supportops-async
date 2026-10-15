output "queue_url" {
  value = aws_sqs_queue.tasks.url
}

output "dead_letter_queue_url" {
  value = aws_sqs_queue.dlq.url
}

output "topic_arns" {
  value = {
    created   = aws_sns_topic.created.arn
    completed = aws_sns_topic.completed.arn
    failed    = aws_sns_topic.failed.arn
  }
}

resource "aws_sns_topic" "podcastify_tasks" {
  name         = "podcastify_tasks"
  display_name = "Podcastify Tasks"
}

resource "aws_sns_topic_subscription" "checker_trigger" {
  topic_arn = aws_sns_topic.podcastify_tasks.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.checker.arn
}

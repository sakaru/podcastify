resource "aws_cloudwatch_event_rule" "podcastify_ingest_schedule" {
  name                = "PodcastifyIngest-${var.name}"
  description         = "Trigger Podcastify Ingestor"
  schedule_expression = "cron(${var.schedule})"
}

resource "aws_cloudwatch_event_rule" "podcastify_creator_schedule" {
  name                = "PodcastifyCreate-${var.name}"
  description         = "Trigger Podcastify Creator"
  schedule_expression = "cron(${var.schedule})"
}

resource "aws_cloudwatch_event_target" "podcastify_ingest_trigger" {
  arn  = "${aws_lambda_function.ingestor.arn}"
  rule = "${aws_cloudwatch_event_rule.podcastify_ingest_schedule.name}"
}

resource "aws_cloudwatch_event_target" "podcastify_creator_trigger" {
  arn  = "${aws_lambda_function.creator.arn}"
  rule = "${aws_cloudwatch_event_rule.podcastify_creator_schedule.name}"
}

resource "aws_lambda_function" "ingestor" {
  filename                       = "${path.root}/../builds/app.zip"
  function_name                  = "podcastify-ingestor-${var.name}"
  role                           = "${aws_iam_role.podcastify.arn}"
  handler                        = "main.ingestor"
  source_code_hash               = "${base64sha256(file("../builds/app.zip"))}"
  runtime                        = "python3.7"
  timeout                        = 120
  description                    = "Reads text, schedules Text-to-speach tasks"
  reserved_concurrent_executions = 1                                                     # No need to ever run more than one at a time

  environment {
    variables = {
      source_name    = "${var.name}"
      bucket         = "${var.s3_bucket_prefix}-${var.name}"
      sns_topic      = "${aws_sns_topic.podcastify_tasks.arn}"
      output_format  = "${var.polly_audio_format}"
      text_type      = "${var.polly_texttype}"
      voice_id       = "${var.polly_voice}"
      language_code  = "${var.polly_language}"
      dynamodb_table = "${aws_dynamodb_table.podcast_polly_tasks.name}"
      domain_name    = "${aws_cloudfront_distribution.podcast_distribution.domain_name}"
    }
  }

  tags = "${var.aws_tags}"
}

resource "aws_lambda_function" "checker" {
  filename         = "${path.root}/../builds/app.zip"
  function_name    = "podcastify-checker-${var.name}"
  role             = "${aws_iam_role.podcastify.arn}"
  handler          = "main.checker"
  source_code_hash = "${base64sha256(file("${path.root}/../builds/app.zip"))}"
  runtime          = "python3.7"
  timeout          = 120
  description      = "Check the output of the Polly tasks"
  layers           = ["${aws_lambda_layer_version.mutagen.id}"]

  environment {
    variables = {
      source_name    = "${var.name}"
      bucket         = "${var.s3_bucket_prefix}-${var.name}"
      sns_topic      = "${aws_sns_topic.podcastify_tasks.arn}"
      output_format  = "${var.polly_audio_format}"
      text_type      = "${var.polly_texttype}"
      voice_id       = "${var.polly_voice}"
      language_code  = "${var.polly_language}"
      dynamodb_table = "${aws_dynamodb_table.podcast_polly_tasks.name}"
      domain_name    = "${aws_cloudfront_distribution.podcast_distribution.domain_name}"
    }
  }

  tags = "${var.aws_tags}"
}

resource "aws_lambda_function" "creator" {
  filename                       = "${path.root}/../builds/app.zip"
  function_name                  = "podcastify-creator-${var.name}"
  role                           = "${aws_iam_role.podcastify.arn}"
  handler                        = "main.creator"
  source_code_hash               = "${base64sha256(file("${path.root}/../builds/app.zip"))}"
  runtime                        = "python3.7"
  timeout                        = 120
  description                    = "Creates the final podcast RSS"
  reserved_concurrent_executions = 1                                                                  # No need to ever run more than one at a time

  environment {
    variables = {
      source_name    = "${var.name}"
      bucket         = "${var.s3_bucket_prefix}-${var.name}"
      sns_topic      = "${aws_sns_topic.podcastify_tasks.arn}"
      output_format  = "${var.polly_audio_format}"
      text_type      = "${var.polly_texttype}"
      voice_id       = "${var.polly_voice}"
      language_code  = "${var.polly_language}"
      dynamodb_table = "${aws_dynamodb_table.podcast_polly_tasks.name}"
      domain_name    = "${aws_cloudfront_distribution.podcast_distribution.domain_name}"
    }
  }

  tags = "${var.aws_tags}"
}

resource "aws_lambda_permission" "ingestor_allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.ingestor.function_name}"
  principal     = "events.amazonaws.com"
  source_arn    = "${aws_cloudwatch_event_rule.podcastify_ingest_schedule.arn}"
}

resource "aws_lambda_permission" "checker_allow_sns" {
  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.checker.arn}"
  principal     = "sns.amazonaws.com"
  source_arn    = "${aws_sns_topic.podcastify_tasks.arn}"
}

resource "aws_lambda_permission" "creator_allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.creator.function_name}"
  principal     = "events.amazonaws.com"
  source_arn    = "${aws_cloudwatch_event_rule.podcastify_creator_schedule.arn}"
}

resource "aws_lambda_layer_version" "mutagen" {
  filename            = "${path.root}/../builds/mutagen-${var.mutagen_version}.zip"
  source_code_hash    = "${base64sha256(file("${path.root}/../builds/mutagen-${var.mutagen_version}.zip"))}"
  layer_name          = "python3-mutagen-${replace(var.mutagen_version, ".", "-")}"
  license_info        = "GPL-2.0-or-later"
  description         = "Mutagen is a Python module to handle audio metadata"
  compatible_runtimes = ["python3.6", "python3.7"]
}

resource "aws_cloudwatch_log_group" "ingestor" {
   name              = "/aws/lambda/${aws_lambda_function.ingestor.function_name}"
   retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "checker" {
   name              = "/aws/lambda/${aws_lambda_function.checker.function_name}"
   retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "creator" {
    name              = "/aws/lambda/${aws_lambda_function.creator.function_name}"
    retention_in_days = 14
}

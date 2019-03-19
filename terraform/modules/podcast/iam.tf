resource "aws_iam_role" "podcastify" {
  name = "podcastify-${var.name}"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF

  tags = "${var.aws_tags}"
}

resource "aws_iam_role_policy_attachment" "attach" {
  role       = "${aws_iam_role.podcastify.name}"
  policy_arn = "${aws_iam_policy.podcastify.arn}"
}

resource "aws_iam_policy" "podcastify" {
  name        = "podcastify-${var.name}"
  description = "Grants StartSpeechSynthesisTask"

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "polly:*"
            ],
            "Effect": "Allow",
            "Resource": "*"
        },
        {
            "Action": [
                "s3:*"
            ],
            "Effect": "Allow",
            "Resource": "arn:aws:s3:::${var.s3_bucket_prefix}-${var.name}/*"
        },
        {
            "Action": [
                "sns:*"
            ],
            "Effect": "Allow",
            "Resource": "${aws_sns_topic.podcastify_tasks.arn}"
        },
        {
            "Action": [
                "dynamodb:Query",
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:DeleteItem",
                "dynamodb:Scan"
            ],
            "Effect": "Allow",
            "Resource": [
              "${aws_dynamodb_table.podcast_polly_tasks.arn}/*",
              "${aws_dynamodb_table.podcast_polly_tasks.arn}"
            ]
        },
        {
            "Action": [
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:${var.aws_region}:*:*",
            "Effect": "Allow"
        }
    ]
}
EOF
}

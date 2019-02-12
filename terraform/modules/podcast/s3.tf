resource "aws_s3_bucket" "podcast" {
  bucket = "${var.s3_bucket_prefix}-${var.name}"
  region = "${var.aws_region}"
  acl    = "private"
  tags   = "${var.aws_tags}"
}

resource "aws_s3_bucket" "logs" {
  bucket = "${var.s3_bucket_prefix}-${var.name}-logs"
  region = "${var.aws_region}"
  acl    = "private"
  tags   = "${var.aws_tags}"
}

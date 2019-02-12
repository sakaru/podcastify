variable "aws_region" {
  type = "string"
  description = "AWS region to create infrastructure in"
  default = "ap-southeast-1"
}

variable "aws_profile" {
  type = "string"
  description = "AWS profile to use"
  default = "default"
}

variable "s3_bucket_prefix" {
  type = "string"
  description = "S3 bucket name prefix"
  default = "com.example.podcastify"
}
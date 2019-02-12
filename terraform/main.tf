provider "aws" {
  version = "~> 1.58"
  region  = "${var.aws_region}"
  profile = "${var.aws_profile}"
}

module "economist" {
  source             = "modules/podcast"
  name               = "economist"
  polly_texttype     = "ssml"
  s3_bucket_prefix   = "${var.s3_bucket_prefix}"
  aws_region         = "${var.aws_region}"
  aws_profile        = "${var.aws_profile}"
  schedule           = "0 21-23 ? * MON-SAT *"
  polly_audio_format = "mp3"
}

output "economist_domain_name" {
  value = "${module.economist.domain_name}"
}

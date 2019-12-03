variable "aws_tags" {
  type        = map
  description = "Tags to attach to AWS resources"

  default = {
    Product = "podcastify"
  }
}

variable "name" {
  type        = string
  description = "Name of the podcast"
}

variable "s3_bucket_prefix" {
  type        = string
  description = "Bucket containing audio files"
  default     = "com.example.app.podcastify"
}

variable "aws_region" {
  type        = string
  description = "AWS region to create infrastructure in"
  default     = "ap-southeast-1"
}

variable "aws_profile" {
  type        = string
  description = "AWS profile to use"
  default     = "default"
}

variable "schedule" {
  type        = string
  description = "The CRON schedule at which to fetch the Economist data"
  default     = "0 13 ? * MON-SAT *"
}

variable "polly_audio_format" {
  type        = string
  description = "Audio format"
  default     = "ogg_vorbis"
}

variable "polly_voice" {
  type        = string
  description = "Polly Voice to use"
  default     = "Joanna"
}

variable "polly_language" {
  type        = string
  description = "Language choice for Polly, the language of the input text"
  default     = "en-US"
}

variable "polly_texttype" {
  type        = string
  description = "The text type for Polly (ssml or text)"
  default     = "text"
}

variable "mutagen_version" {
  type        = string
  description = "Version of python3-mutagen to use"
  default     = "1.42.0"
}

output "domain_name" {
  value = "https://${aws_cloudfront_distribution.podcast_distribution.domain_name}/"
}

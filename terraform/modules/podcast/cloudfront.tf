resource "aws_cloudfront_origin_access_identity" "origin_access_identity" {
  comment = "Podcastify-${var.name}"
}

// Cloudfront origin for the podcast
resource "aws_cloudfront_distribution" "podcast_distribution" {
  depends_on = ["aws_s3_bucket.podcast", "aws_s3_bucket.logs"]

  origin {
    domain_name = "${aws_s3_bucket.podcast.bucket_regional_domain_name}"
    origin_id   = "${aws_s3_bucket.podcast.id}"
    origin_path = "/public"

    s3_origin_config {
      origin_access_identity = "${aws_cloudfront_origin_access_identity.origin_access_identity.cloudfront_access_identity_path}"
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  comment             = "Podcastify ${var.name}"
  default_root_object = "${var.name}.xml"

  logging_config {
    include_cookies = false
    bucket          = "${aws_s3_bucket.logs.bucket_domain_name}"
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "${aws_s3_bucket.podcast.id}"

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  tags = "${var.aws_tags}"

  viewer_certificate {
    cloudfront_default_certificate = true
    minimum_protocol_version       = "TLSv1"
  }
}

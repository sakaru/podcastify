resource "aws_dynamodb_table" "podcast_polly_tasks" {
  name         = "podcast_${var.name}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "task_id"
  range_key    = "status"

  global_secondary_index {
    name            = "guid"
    hash_key        = "guid"
    projection_type = "ALL"
  }

  attribute {
    name = "task_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "guid"
    type = "S"
  }

  tags = var.aws_tags
}

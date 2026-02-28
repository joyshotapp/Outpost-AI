output "bucket_names" {
  value = {
    uploads = aws_s3_bucket.uploads.id
  }
}

output "bucket_arns" {
  value = {
    uploads = aws_s3_bucket.uploads.arn
  }
}

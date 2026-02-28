variable "project_name" { type = string }
variable "environment" { type = string }
variable "create_buckets" { type = bool; default = true }
variable "enable_versioning" { type = bool; default = true }
variable "enable_encryption" { type = bool; default = true }
variable "enable_public_access" { type = bool; default = false }
variable "bucket_prefix" { type = string }

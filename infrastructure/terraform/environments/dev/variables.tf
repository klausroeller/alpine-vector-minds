variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-central-1"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "ssh_allowed_cidr" {
  description = "CIDR block allowed to SSH into EC2 (e.g. your IP: x.x.x.x/32)"
  type        = string
}

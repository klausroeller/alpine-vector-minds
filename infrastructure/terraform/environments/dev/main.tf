terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = "avm"
}

module "vpc" {
  source = "../../modules/vpc"

  project_name       = "alpine-vector-minds"
  vpc_cidr           = var.vpc_cidr
  availability_zones = ["${var.aws_region}a", "${var.aws_region}b"]
}

module "vpc" {
  source = "../../modules/vpc"

  project_name       = "alpine-vector-minds"
  vpc_cidr           = var.vpc_cidr
  availability_zones = ["${var.aws_region}a", "${var.aws_region}b"]
}

# ─── SSH Key Pair ───────────────────────────────────────────

resource "tls_private_key" "ec2" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "ec2" {
  key_name   = "avm-ec2-key"
  public_key = tls_private_key.ec2.public_key_openssh
}

resource "local_file" "private_key" {
  content         = tls_private_key.ec2.private_key_pem
  filename        = "${path.module}/avm-ec2-key.pem"
  file_permission = "0600"
}

# ─── Security Group ─────────────────────────────────────────

resource "aws_security_group" "ec2" {
  name        = "avm-ec2-sg"
  description = "Security group for Alpine Vector Minds EC2"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_allowed_cidr]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "avm-ec2-sg"
    Project = "alpine-vector-minds"
  }
}

# ─── EC2 Instance ───────────────────────────────────────────

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "app" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = "t3.medium"
  key_name               = aws_key_pair.ec2.key_name
  vpc_security_group_ids = [aws_security_group.ec2.id]
  user_data              = file("${path.module}/user-data.sh")

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
    encrypted   = true
  }

  tags = {
    Name    = "avm-app"
    Project = "alpine-vector-minds"
  }
}

# ─── Elastic IP ─────────────────────────────────────────────

resource "aws_eip" "app" {
  instance = aws_instance.app.id

  tags = {
    Name    = "avm-app-eip"
    Project = "alpine-vector-minds"
  }
}

# ─── Route53 DNS ────────────────────────────────────────────

data "aws_route53_zone" "main" {
  zone_id = "Z03378781ZDPE5Z1PW8B1"
}

resource "aws_route53_record" "apex" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "alpine-vector-minds.de"
  type    = "A"
  ttl     = 300
  records = [aws_eip.app.public_ip]
}

resource "aws_route53_record" "www" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "www.alpine-vector-minds.de"
  type    = "CNAME"
  ttl     = 300
  records = ["alpine-vector-minds.de"]
}

# ─── Outputs ────────────────────────────────────────────────

output "ec2_public_ip" {
  value       = aws_eip.app.public_ip
  description = "Elastic IP of the app server"
}

output "ssh_command" {
  value       = "ssh -i ${local_file.private_key.filename} ec2-user@${aws_eip.app.public_ip}"
  description = "SSH command to connect to the server"
}

output "private_key_path" {
  value       = local_file.private_key.filename
  description = "Path to the SSH private key"
}

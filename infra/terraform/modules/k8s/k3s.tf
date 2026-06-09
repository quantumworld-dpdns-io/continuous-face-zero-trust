variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "m6i.large"
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

data "aws_vpc" "main" {
  filter {
    name   = "tag:Environment"
    values = [var.environment]
  }
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }

  filter {
    name   = "tag:Name"
    values = ["*private*"]
  }
}

resource "aws_security_group" "k3s" {
  name_prefix = "k3s-${var.environment}-"
  vpc_id      = data.aws_vpc.main.id

  ingress {
    from_port   = 6443
    to_port     = 6443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "K3s API server"
  }

  ingress {
    from_port   = 8472
    to_port     = 8472
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Flannel VXLAN"
  }

  ingress {
    from_port   = 10250
    to_port     = 10250
    protocol    = "tcp"
    self        = true
    description = "Kubelet"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "k3s_master" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = data.aws_subnets.private.ids[0]
  vpc_security_group_ids = [aws_security_group.k3s.id]

  tags = {
    Name        = "k3s-master-${var.environment}"
    Environment = var.environment
    Role        = "k3s-master"
  }

  user_data = base64encode(<<-EOF
    #!/bin/bash
    set -e
    curl -sfL https://get.k3s.io | sh -s - server \
      --write-kubeconfig-mode 644 \
      --tls-san $(curl -s http://169.254.169.254/latest/meta-data/local-ipv4) \
      --disable servicelb
    until [ -f /etc/rancher/k3s/k3s.yaml ]; do sleep 1; done
  EOF
  )
}

resource "aws_instance" "k3s_workers" {
  count                  = 2
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = data.aws_subnets.private.ids[count.index % length(data.aws_subnets.private.ids)]
  vpc_security_group_ids = [aws_security_group.k3s.id]

  tags = {
    Name        = "k3s-worker-${var.environment}-${count.index}"
    Environment = var.environment
    Role        = "k3s-worker"
  }

  user_data = base64encode(<<-EOF
    #!/bin/bash
    set -e
    curl -sfL https://get.k3s.io | K3S_URL=https://${aws_instance.k3s_master.private_ip}:6443 K3S_TOKEN=$(aws ssm get-parameter --name "/k3s/${var.environment}/node-token" --region ${var.aws_region} --with-decryption --query Parameter.Value --output text 2>/dev/null || echo "pending") sh -s - agent
  EOF
  )
}

output "master_ip" {
  value = aws_instance.k3s_master.private_ip
}

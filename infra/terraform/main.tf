module "vpc" {
  source = "./modules/vpc"

  aws_region    = var.aws_region
  gcp_region    = var.gcp_region
  environment   = var.environment
  cluster_name  = var.cluster_name
}

module "k8s" {
  source = "./modules/k8s"

  cluster_name  = var.cluster_name
  environment   = var.environment
  vpc_id        = module.vpc.vpc_id
  subnet_ids    = module.vpc.subnet_ids
}

module "redis" {
  source = "./modules/redis"

  environment = var.environment
  cluster_id  = "${var.cluster_name}-redis"
}

module "vector_db" {
  source = "./modules/vector"

  environment = var.environment
  qdrant_url  = "https://cloud.qdrant.io"
}

module "certs" {
  source = "./modules/certs"

  environment   = var.environment
  domain_name   = "cfzt.example.com"
}

module "dns" {
  source = "./modules/dns"

  environment     = var.environment
  domain_name     = "cfzt.example.com"
  cloudflare_zone = "example.com"
}

module "monitoring" {
  source = "./modules/monitoring"

  environment = var.environment
  cluster_name = var.cluster_name
}

module "security" {
  source = "./modules/security"

  environment = var.environment
  cluster_name = var.cluster_name
}

module "quantum" {
  source = "./modules/quantum"

  enabled     = var.quantum_enabled
  environment = var.environment
}

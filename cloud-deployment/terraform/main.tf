terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Modulo VPC
module "vpc" {
  source = "./modules/vpc"
  
  vpc_name     = "lip-recognition-vpc"
  vpc_cidr     = "10.0.0.0/16"
  azs          = ["us-east-1a", "us-east-1b"]
  public_subnets  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnets = ["10.0.3.0/24", "10.0.4.0/24"]
}

# Modulo ECS
module "ecs" {
  source = "./modules/ecs"
  
  cluster_name = "lip-recognition-cluster"
  service_name = "lip-recognition-service"
  
  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets
  public_subnets  = module.vpc.public_subnets
  
  task_cpu    = 1024
  task_memory = 2048
  
  desired_count = 2
  min_capacity  = 2
  max_capacity  = 10
  
  # Variabili d'ambiente
  environment_variables = {
    DB_HOST           = aws_ssm_parameter.db_host.value
    DB_PORT           = aws_ssm_parameter.db_port.value
    DB_NAME           = aws_ssm_parameter.db_name.value
    DB_USER           = aws_ssm_parameter.db_user.value
    DB_PASSWORD       = aws_ssm_parameter.db_password.value
    RABBITMQ_HOST     = aws_ssm_parameter.rabbitmq_host.value
    RABBITMQ_PORT     = aws_ssm_parameter.rabbitmq_port.value
    RABBITMQ_USER     = aws_ssm_parameter.rabbitmq_user.value
    RABBITMQ_PASS     = aws_ssm_parameter.rabbitmq_pass.value
    LIPNET_URL        = aws_ssm_parameter.lipnet_url.value
  }
}

# Configurazione Auto Scaling
resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/${module.ecs.cluster_name}/${module.ecs.service_name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "ecs_policy" {
  name               = "cpu-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 50.0
  }
}

# Parametri SSM per i segreti
resource "aws_ssm_parameter" "db_password" {
  name        = "/lip-recognition/db/password"
  description = "Database password"
  type        = "SecureString"
  value       = var.db_password
}

resource "aws_ssm_parameter" "rabbitmq_pass" {
  name        = "/lip-recognition/rabbitmq/password"
  description = "RabbitMQ password"
  type        = "SecureString"
  value       = var.rabbitmq_pass
}

# ... (altri parametri SSM)

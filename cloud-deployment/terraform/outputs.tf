output "cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}

output "service_name" {
  description = "ECS service name"
  value       = module.ecs.service_name
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

# ... (altri output)

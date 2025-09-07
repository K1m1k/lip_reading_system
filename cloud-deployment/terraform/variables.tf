variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "rabbitmq_pass" {
  description = "RabbitMQ password"
  type        = string
  sensitive   = true
}

# ... (altre variabili)

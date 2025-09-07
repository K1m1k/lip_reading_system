resource "aws_ecs_cluster" "main" {
  name = var.cluster_name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "app" {
  family                   = "${var.cluster_name}-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "lip-reading-app"
      image     = "${var.ecr_repository_url}:latest"
      essential = true
      environment = [
        { name = "DB_HOST", value = var.environment_variables.DB_HOST },
        { name = "DB_PORT", value = var.environment_variables.DB_PORT },
        { name = "DB_NAME", value = var.environment_variables.DB_NAME },
        { name = "DB_USER", value = var.environment_variables.DB_USER },
        { name = "DB_PASSWORD", value = var.environment_variables.DB_PASSWORD },
        { name = "RABBITMQ_HOST", value = var.environment_variables.RABBITMQ_HOST },
        { name = "RABBITMQ_PORT", value = var.environment_variables.RABBITMQ_PORT },
        { name = "RABBITMQ_USER", value = var.environment_variables.RABBITMQ_USER },
        { name = "RABBITMQ_PASS", value = var.environment_variables.RABBITMQ_PASS },
        { name = "LIPNET_URL", value = var.environment_variables.LIPNET_URL }
      ]
      portMappings = [
        {
          containerPort = 5000
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "main" {
  name            = var.service_name
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.ecs.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "lip-reading-app"
    container_port   = 5000
  }

  depends_on = [aws_lb_listener.app]
}

# ... (altre risorse ECS)

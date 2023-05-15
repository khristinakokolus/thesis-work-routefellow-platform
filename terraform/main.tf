terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
  }

  required_version = ">= 1.2.0"
}

provider "aws" {
  region  = "us-east-1"
}

# Launching everything for sign_up service


resource "aws_ecr_repository" "service-sign-up" {
  name = "service-sign-up"
}

# Creating cluster

resource "aws_ecs_cluster" "ecs-cluster-platform" {
  name = "ecs-cluster-platform" # Naming the cluster
}


resource "aws_ecs_task_definition" "service-sign-up-task" {
  family                   = "service-sign-up-task"
  container_definitions    = <<DEFINITION
  [
    {
      "name": "service-sign-up-task",
      "image": "${aws_ecr_repository.service-sign-up.repository_url}",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 5001,
          "hostPort": 5001
        }
      ],
      "memory": 512,
      "cpu": 256
    }
  ]
  DEFINITION
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  memory                   = 512
  cpu                      = 256
  execution_role_arn       = "${aws_iam_role.ecsTaskExecutionRoleSignUp.arn}"
}

resource "aws_iam_role" "ecsTaskExecutionRoleSignUp" {
  name               = "ecsTaskExecutionRoleSignUp"
  assume_role_policy = "${data.aws_iam_policy_document.assume_role_policy.json}"
}

data "aws_iam_policy_document" "assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "ecsTaskExecutionRoleSignUp_policy" {
  role       = "${aws_iam_role.ecsTaskExecutionRoleSignUp.name}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}


# Provide a reference to your default VPC
resource "aws_default_vpc" "default_vpc" {
}

# Provide references to your default subnets
resource "aws_default_subnet" "default_subnet_a" {
  # Use your own region here but reference to subnet 1a
  availability_zone = "us-east-1a"
}

resource "aws_default_subnet" "default_subnet_b" {
  # Use your own region here but reference to subnet 1b
  availability_zone = "us-east-1b"
}


resource "aws_default_subnet" "default_subnet_c" {
  # Use your own region here but reference to subnet 1b
  availability_zone = "us-east-1c"
}


resource "aws_ecs_service" "service-sign-up" {
  name            = "service-sign-up"                             # Naming our first service
  cluster         = "${aws_ecs_cluster.ecs-cluster-platform.id}"             # Referencing our created Cluster
  task_definition = "${aws_ecs_task_definition.service-sign-up-task.arn}" # Referencing the task our service will spin up
  launch_type     = "FARGATE"
  desired_count   = 1 # Setting the number of containers we want deployed to 1

  load_balancer {
    target_group_arn = "${aws_lb_target_group.target_group_sign_up.arn}" # Referencing our target group
    container_name   = "${aws_ecs_task_definition.service-sign-up-task.family}"
    container_port   = 5001 # Specifying the container port
  }

  network_configuration {
    subnets          = ["${aws_default_subnet.default_subnet_a.id}", "${aws_default_subnet.default_subnet_b.id}", "${aws_default_subnet.default_subnet_c.id}"]
    assign_public_ip = true # Providing our containers with public IPs
    security_groups  = ["${aws_security_group.service_security_group_sign_up.id}"] # Setting the security group
  }
}


resource "aws_security_group" "service_security_group_sign_up" {
  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    # Only allowing traffic in from the load balancer security group
    security_groups = ["${aws_security_group.load_balancer_security_group_sign_up.id}"]
  }

  egress {
    from_port   = 0 # Allowing any incoming port
    to_port     = 0 # Allowing any outgoing port
    protocol    = "-1" # Allowing any outgoing protocol
    cidr_blocks = ["0.0.0.0/0"] # Allowing traffic out to all IP addresses
  }
}


resource "aws_alb" "application_load_balancer_sign_up" {
  name               = "sign-up-lb-tf" # Naming our load balancer
  load_balancer_type = "application"
  subnets = [ # Referencing the default subnets
    "${aws_default_subnet.default_subnet_a.id}",
    "${aws_default_subnet.default_subnet_b.id}",
    "${aws_default_subnet.default_subnet_c.id}"
  ]
  # Referencing the security group
  security_groups = ["${aws_security_group.load_balancer_security_group_sign_up.id}"]
}

# Creating a security group for the load balancer:
resource "aws_security_group" "load_balancer_security_group_sign_up" {
  ingress {
    from_port   = 80 # Allowing traffic in from port 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allowing traffic in from all sources
  }

  egress {
    from_port   = 0 # Allowing any incoming port
    to_port     = 0 # Allowing any outgoing port
    protocol    = "-1" # Allowing any outgoing protocol
    cidr_blocks = ["0.0.0.0/0"] # Allowing traffic out to all IP addresses
  }
}


resource "aws_lb_target_group" "target_group_sign_up" {
  name        = "target-group-sign-up"
  port        = 80
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = "${aws_default_vpc.default_vpc.id}" # Referencing the default VPC
  health_check {
    matcher = "200,301,302"
    path = "/"
  }
}

resource "aws_lb_listener" "listener_sign_up" {
  load_balancer_arn = "${aws_alb.application_load_balancer_sign_up.arn}" # Referencing our load balancer
  port              = "80"
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = "${aws_lb_target_group.target_group_sign_up.arn}" # Referencing our tagrte group
  }
}


# Launching everything for sign_in service


resource "aws_ecr_repository" "service-sign-in" {
  name = "service-sign-in"
}

resource "aws_ecs_task_definition" "service-sign-in-task" {
  family                   = "service-sign-in-task"
  container_definitions    = <<DEFINITION
  [
    {
      "name": "service-sign-in-task",
      "image": "${aws_ecr_repository.service-sign-in.repository_url}",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 5002,
          "hostPort": 5002
        }
      ],
      "memory": 512,
      "cpu": 256
    }
  ]
  DEFINITION
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  memory                   = 512
  cpu                      = 256
  execution_role_arn       = "${aws_iam_role.ecsTaskExecutionRoleSignIn.arn}"
}

resource "aws_iam_role" "ecsTaskExecutionRoleSignIn" {
  name               = "ecsTaskExecutionRoleSignIn"
  assume_role_policy = "${data.aws_iam_policy_document.assume_role_policy_sign_in.json}"
}

data "aws_iam_policy_document" "assume_role_policy_sign_in" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "ecsTaskExecutionRoleSignIn_policy" {
  role       = "${aws_iam_role.ecsTaskExecutionRoleSignIn.name}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_ecs_service" "service-sign-in" {
  name            = "service-sign-in"                             # Naming our first service
  cluster         = "${aws_ecs_cluster.ecs-cluster-platform.id}"             # Referencing our created Cluster
  task_definition = "${aws_ecs_task_definition.service-sign-in-task.arn}" # Referencing the task our service will spin up
  launch_type     = "FARGATE"
  desired_count   = 1 # Setting the number of containers we want deployed to 1

  load_balancer {
    target_group_arn = "${aws_lb_target_group.target_group_sign_in.arn}" # Referencing our target group
    container_name   = "${aws_ecs_task_definition.service-sign-in-task.family}"
    container_port   = 5002 # Specifying the container port
  }

  network_configuration {
    subnets          = ["${aws_default_subnet.default_subnet_a.id}", "${aws_default_subnet.default_subnet_b.id}", "${aws_default_subnet.default_subnet_c.id}"]
    assign_public_ip = true # Providing our containers with public IPs
    security_groups  = ["${aws_security_group.service_security_group_sign_in.id}"] # Setting the security group
  }
}

resource "aws_security_group" "service_security_group_sign_in" {
  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    # Only allowing traffic in from the load balancer security group
    security_groups = ["${aws_security_group.load_balancer_security_group_sign_in.id}"]
  }

  egress {
    from_port   = 0 # Allowing any incoming port
    to_port     = 0 # Allowing any outgoing port
    protocol    = "-1" # Allowing any outgoing protocol
    cidr_blocks = ["0.0.0.0/0"] # Allowing traffic out to all IP addresses
  }
}

resource "aws_alb" "application_load_balancer_sign_in" {
  name               = "sign-in-lb-tf" # Naming our load balancer
  load_balancer_type = "application"
  subnets = [ # Referencing the default subnets
    "${aws_default_subnet.default_subnet_a.id}",
    "${aws_default_subnet.default_subnet_b.id}",
    "${aws_default_subnet.default_subnet_c.id}"
  ]
  # Referencing the security group
  security_groups = ["${aws_security_group.load_balancer_security_group_sign_in.id}"]
}

# Creating a security group for the load balancer:
resource "aws_security_group" "load_balancer_security_group_sign_in" {
  ingress {
    from_port   = 80 # Allowing traffic in from port 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allowing traffic in from all sources
  }

  egress {
    from_port   = 0 # Allowing any incoming port
    to_port     = 0 # Allowing any outgoing port
    protocol    = "-1" # Allowing any outgoing protocol
    cidr_blocks = ["0.0.0.0/0"] # Allowing traffic out to all IP addresses
  }
}

resource "aws_lb_target_group" "target_group_sign_in" {
  name        = "target-group-sign-in"
  port        = 80
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = "${aws_default_vpc.default_vpc.id}" # Referencing the default VPC
  health_check {
    matcher = "200,301,302"
    path = "/"
  }
}

resource "aws_lb_listener" "listener_sign_in" {
  load_balancer_arn = "${aws_alb.application_load_balancer_sign_in.arn}" # Referencing our load balancer
  port              = "80"
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = "${aws_lb_target_group.target_group_sign_in.arn}" # Referencing our tagrte group
  }
}



# Launching everything for search service

resource "aws_ecr_repository" "service-search" {
  name = "service-search"
}

resource "aws_ecs_task_definition" "service-search-task" {
  family                   = "service-search-task"
  container_definitions    = <<DEFINITION
  [
    {
      "name": "service-search-task",
      "image": "${aws_ecr_repository.service-search.repository_url}",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 5003,
          "hostPort": 5003
        }
      ],
      "memory": 512,
      "cpu": 256
    }
  ]
  DEFINITION
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  memory                   = 512
  cpu                      = 256
  execution_role_arn       = "${aws_iam_role.ecsTaskExecutionRoleSearch.arn}"
}

resource "aws_iam_role" "ecsTaskExecutionRoleSearch" {
  name               = "ecsTaskExecutionRoleSearch"
  assume_role_policy = "${data.aws_iam_policy_document.assume_role_policy_search.json}"
}

data "aws_iam_policy_document" "assume_role_policy_search" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "ecsTaskExecutionRoleSearch_policy" {
  role       = "${aws_iam_role.ecsTaskExecutionRoleSearch.name}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_ecs_service" "service-search" {
  name            = "service-search"                             # Naming our first service
  cluster         = "${aws_ecs_cluster.ecs-cluster-platform.id}"             # Referencing our created Cluster
  task_definition = "${aws_ecs_task_definition.service-search-task.arn}" # Referencing the task our service will spin up
  launch_type     = "FARGATE"
  desired_count   = 1 # Setting the number of containers we want deployed to 1

  load_balancer {
    target_group_arn = "${aws_lb_target_group.target_group_search.arn}" # Referencing our target group
    container_name   = "${aws_ecs_task_definition.service-search-task.family}"
    container_port   = 5003 # Specifying the container port
  }

  network_configuration {
    subnets          = ["${aws_default_subnet.default_subnet_a.id}", "${aws_default_subnet.default_subnet_b.id}", "${aws_default_subnet.default_subnet_c.id}"]
    assign_public_ip = true # Providing our containers with public IPs
    security_groups  = ["${aws_security_group.service_security_group_search.id}"] # Setting the security group
  }
}

resource "aws_security_group" "service_security_group_search" {
  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    # Only allowing traffic in from the load balancer security group
    security_groups = ["${aws_security_group.load_balancer_security_group_search.id}"]
  }

  egress {
    from_port   = 0 # Allowing any incoming port
    to_port     = 0 # Allowing any outgoing port
    protocol    = "-1" # Allowing any outgoing protocol
    cidr_blocks = ["0.0.0.0/0"] # Allowing traffic out to all IP addresses
  }
}

resource "aws_alb" "application_load_balancer_search" {
  name               = "search-lb-tf" # Naming our load balancer
  load_balancer_type = "application"
  subnets = [ # Referencing the default subnets
    "${aws_default_subnet.default_subnet_a.id}",
    "${aws_default_subnet.default_subnet_b.id}",
    "${aws_default_subnet.default_subnet_c.id}"
  ]
  # Referencing the security group
  security_groups = ["${aws_security_group.load_balancer_security_group_search.id}"]
  idle_timeout = 3600
}

# Creating a security group for the load balancer:
resource "aws_security_group" "load_balancer_security_group_search" {
  ingress {
    from_port   = 80 # Allowing traffic in from port 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allowing traffic in from all sources
  }

  egress {
    from_port   = 0 # Allowing any incoming port
    to_port     = 0 # Allowing any outgoing port
    protocol    = "-1" # Allowing any outgoing protocol
    cidr_blocks = ["0.0.0.0/0"] # Allowing traffic out to all IP addresses
  }
}

resource "aws_lb_target_group" "target_group_search" {
  name        = "target-group-search"
  port        = 80
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = "${aws_default_vpc.default_vpc.id}" # Referencing the default VPC
  health_check {
    matcher = "200,301,302"
    path = "/"
  }
}

resource "aws_lb_listener" "listener_search" {
  load_balancer_arn = "${aws_alb.application_load_balancer_search.arn}" # Referencing our load balancer
  port              = "80"
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = "${aws_lb_target_group.target_group_search.arn}" # Referencing our tagrte group
  }
}


# Launching everything for entire website

resource "aws_ecr_repository" "service-platform" {
  name = "service-platform"
}


resource "aws_ecs_task_definition" "service-platform-task" {
  family                   = "service-platform-task"
  container_definitions    = <<DEFINITION
  [
    {
      "name": "service-platform-task",
      "image": "${aws_ecr_repository.service-platform.repository_url}",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 5004,
          "hostPort": 5004
        }
      ],
      "memory": 512,
      "cpu": 256
    }
  ]
  DEFINITION
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  memory                   = 512
  cpu                      = 256
  execution_role_arn       = "${aws_iam_role.ecsTaskExecutionRoleplatform.arn}"
}

resource "aws_iam_role" "ecsTaskExecutionRoleplatform" {
  name               = "ecsTaskExecutionRoleplatform"
  assume_role_policy = "${data.aws_iam_policy_document.assume_role_policy_platform.json}"
}

data "aws_iam_policy_document" "assume_role_policy_platform" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "ecsTaskExecutionRoleplatform_policy" {
  role       = "${aws_iam_role.ecsTaskExecutionRoleplatform.name}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_ecs_service" "service-platform" {
  name            = "service-platform"                             # Naming our first service
  cluster         = "${aws_ecs_cluster.ecs-cluster-platform.id}"             # Referencing our created Cluster
  task_definition = "${aws_ecs_task_definition.service-platform-task.arn}" # Referencing the task our service will spin up
  launch_type     = "FARGATE"
  desired_count   = 1 # Setting the number of containers we want deployed to 1

  load_balancer {
    target_group_arn = "${aws_lb_target_group.target_group_platform.arn}" # Referencing our target group
    container_name   = "${aws_ecs_task_definition.service-platform-task.family}"
    container_port   = 5004 # Specifying the container port
  }

  network_configuration {
    subnets          = ["${aws_default_subnet.default_subnet_a.id}", "${aws_default_subnet.default_subnet_b.id}", "${aws_default_subnet.default_subnet_c.id}"]
    assign_public_ip = true # Providing our containers with public IPs
    security_groups  = ["${aws_security_group.service_security_group_platform.id}"] # Setting the security group
  }
}

resource "aws_security_group" "service_security_group_platform" {
  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    # Only allowing traffic in from the load balancer security group
    security_groups = ["${aws_security_group.load_balancer_security_group_platform.id}"]
  }

  egress {
    from_port   = 0 # Allowing any incoming port
    to_port     = 0 # Allowing any outgoing port
    protocol    = "-1" # Allowing any outgoing protocol
    cidr_blocks = ["0.0.0.0/0"] # Allowing traffic out to all IP addresses
  }
}

resource "aws_alb" "application_load_balancer_platform" {
  name               = "platform-lb-tf" # Naming our load balancer
  load_balancer_type = "application"
  subnets = [ # Referencing the default subnets
    "${aws_default_subnet.default_subnet_a.id}",
    "${aws_default_subnet.default_subnet_b.id}",
    "${aws_default_subnet.default_subnet_c.id}"
  ]
  # Referencing the security group
  security_groups = ["${aws_security_group.load_balancer_security_group_platform.id}"]
  idle_timeout = 600
}

# Creating a security group for the load balancer:
resource "aws_security_group" "load_balancer_security_group_platform" {
  ingress {
    from_port   = 80 # Allowing traffic in from port 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allowing traffic in from all sources
  }

  egress {
    from_port   = 0 # Allowing any incoming port
    to_port     = 0 # Allowing any outgoing port
    protocol    = "-1" # Allowing any outgoing protocol
    cidr_blocks = ["0.0.0.0/0"] # Allowing traffic out to all IP addresses
  }
}

resource "aws_lb_target_group" "target_group_platform" {
  name        = "target-group-platform"
  port        = 80
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = "${aws_default_vpc.default_vpc.id}" # Referencing the default VPC
  health_check {
    matcher = "200,301,302"
    path = "/"
  }
}

resource "aws_lb_listener" "listener_platform" {
  load_balancer_arn = "${aws_alb.application_load_balancer_platform.arn}" # Referencing our load balancer
  port              = "80"
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = "${aws_lb_target_group.target_group_platform.arn}" # Referencing our tagrte group
  }
}


# Launching everything for task that will load tickets data


resource "aws_ecr_repository" "service-insert-update-tickets" {
  name = "service-insert-update-tickets"
}

resource "aws_ecs_task_definition" "service-insert-update-tickets-task" {
  family                   = "service-insert-update-tickets-task"
  container_definitions    = <<DEFINITION
  [
    {
      "name": "service-insert-update-tickets-task",
      "image": "${aws_ecr_repository.service-insert-update-tickets.repository_url}",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 5000,
          "hostPort": 5000
        }
      ],
      "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/insert_update_tickets_data",
                    "awslogs-create-group": "true",
                    "awslogs-region": "us-east-1",
                    "awslogs-stream-prefix": "ecs"
                }
            },
      "memory": 512,
      "cpu": 256
    }
  ]
  DEFINITION
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  memory                   = 512
  cpu                      = 256
  execution_role_arn       = "${aws_iam_role.ecsTaskExecutionRoleinsert-update-tickets.arn}"
}

resource "aws_iam_role" "ecsTaskExecutionRoleinsert-update-tickets" {
  name               = "ecsTaskExecutionRoleinsert-update-tickets"
  assume_role_policy = "${data.aws_iam_policy_document.assume_role_policy_insert-update-tickets.json}"
}

data "aws_iam_policy_document" "assume_role_policy_insert-update-tickets" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "ecsTaskExecutionRoleinsert-update-tickets_policy" {
  role       = "${aws_iam_role.ecsTaskExecutionRoleinsert-update-tickets.name}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
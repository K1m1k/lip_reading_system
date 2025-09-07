Lip Reading System

https://github.com/K1m1k/lip_reading_system/actions/workflows/ci-cd.yml/badge.svg
https://github.com/K1m1k/lip_reading_system/actions/workflows/security-scan.yml/badge.svg

Advanced lip-reading and face-recognition system with secure data processing, monitoring, and scalable cloud deployment.
Features

    Real-time Lip Reading: Advanced lip detection and recognition using MediaPipe and TensorFlow

    Face Recognition: Integrated face recognition with support for known faces database

    Multi-source Video Input: Support for webcam, RTSP streams, and video files

    Enterprise Security: AES-256 encryption, HashiCorp Vault integration, and digital signatures

    Distributed Processing: Scalable architecture with support for GPU acceleration

    Monitoring & Alerting: Prometheus metrics, health checks, and multiple notification channels

    Cloud Ready: Complete Terraform configuration for AWS ECS deployment with auto-scaling

    CI/CD Pipeline: Automated testing, security scanning, and deployment workflows

## Project Structure
lip_reading_system/
├── .github/ # GitHub Actions
│ └── workflows/
│ ├── ci-cd.yml
│ └── security-scan.yml
├── cloud-deployment/ # Infrastructure as Code
│ └── terraform/
│ ├── main.tf
│ ├── variables.tf
│ ├── outputs.tf
│ ├── vpc.tf
│ ├── ecs.tf
│ └── asg.tf
├── config/ # Configuration files
│ ├── config.yaml
│ └── .env.example
├── docker/ # Docker definitions
│ ├── Dockerfile
│ ├── docker-compose.yml
│ ├── docker-compose.prod.yml
│ └── init-db.sql
├── models/ # ML models & vocabulary
│ ├── lipnet_model.h5 # Placeholder
│ └── vocabulary.txt
├── scripts/ # Utility scripts
│ ├── setup_database.sh
│ ├── setup_rabbitmq.sh
│ ├── download_lipnet_model.sh
│ ├── deploy_cloud.sh
│ ├── rotate_keys.sh
│ └── backup_system.sh
├── src/ # Application source code
│ ├── init.py
│ ├── main.py
│ ├── config_manager.py
│ ├── video_input_manager.py
│ ├── lip_tracker.py
│ ├── lip_reading_model.py
│ ├── lipnet_client.py
│ ├── face_recognition.py
│ ├── face_capture.py
│ ├── feature_extractor.py
│ ├── database.py
│ ├── message_broker.py
│ ├── encryption.py
│ ├── secret_manager.py
│ ├── dashboard.py
│ ├── monitoring.py
│ ├── scalable_processing.py
│ └── health_check.py
├── tests/ # Testing modules
│ ├── test_database.py
│ ├── test_security.py
│ ├── test_performance.py
│ ├── test_integration.py
│ ├── test_pipeline.py
│ ├── test_encryption.py
│ └── test_lipnet_client.py
├── requirements.txt # Python dependencies
├── LICENSE # MIT License
├── NOTICE.md # Third-party acknowledgments
└── README.md # Project documentation


Quick Start
Prerequisites

    Python 3.9+

    PostgreSQL

    RabbitMQ

    Docker (optional)

    Terraform (for cloud deployment)

Local Installation

    Clone the repository:

bash

git clone https://github.com/K1m1k/lip_reading_system.git
cd lip_reading_system

    Create a virtual environment and install dependencies:

bash

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

    Set up the database and message broker:

bash

# Setup PostgreSQL database
./scripts/setup_database.sh

# Setup RabbitMQ
./scripts/setup_rabbitmq.sh

    Configure environment variables:

bash

cp config/.env.example config/.env
# Edit config/.env with your actual values

    Run the system:

bash

python src/main.py

Docker Deployment

    Build and start the containers:

bash

docker-compose up --build

    For production deployment:

bash

docker-compose -f docker-compose.prod.yml up --build

Cloud Deployment (AWS)

    Configure AWS credentials:

bash

export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key

    Initialize and apply Terraform configuration:

bash

cd cloud-deployment/terraform
terraform init
terraform plan
terraform apply

Configuration

The system is configured through config/config.yaml and environment variables. Key configuration sections include:

    Video Processing: Frame size, normalization, buffer settings

    Lip Tracking: Detection confidence, ROI settings

    Model Configuration: LipNet service URL, confidence thresholds

    Database: PostgreSQL connection settings

    Message Broker: RabbitMQ connection details

    Security: Encryption settings, Vault/KMS configuration

    Monitoring: Prometheus, logging, and tracing settings

Usage

Once running, the system will:

    Process video streams from configured sources

    Detect and track lip movements

    Recognize spoken phrases using the LipNet model

    Match detected phrases against a blacklist

    Recognize faces in the video stream

    Store results in the database

    Send alerts for blacklist matches via configured channels

Access the dashboard at http://localhost:5000 to view detections and manage the blacklist.
API Endpoints

    GET /api/detections - Retrieve detection results

    GET/POST/DELETE /api/blacklist - Manage blacklisted phrases

    GET /api/stats - Get system statistics

    GET /health - Health check endpoint

    GET /metrics - Prometheus metrics

Monitoring

The system exposes several monitoring endpoints:

    Prometheus Metrics: http://localhost:9090

    Health Check: http://localhost:8080/health

    System Logs: Available in logs/system.log

Security Features

    Encryption: All sensitive data is encrypted using AES-256

    Key Management: Integration with HashiCorp Vault and AWS KMS

    Digital Signatures: All detections are signed to prevent tampering

    Secure Credentials: Environment-based configuration with fallback

    Role-based Access: JWT authentication for dashboard access

Contributing

    Fork the repository

    Create a feature branch: git checkout -b feature/amazing-feature

    Commit your changes: git commit -m 'Add amazing feature'

    Push to the branch: git push origin feature/amazing-feature

    Open a Pull Request

License

This project is licensed under the MIT License - see the LICENSE file for details.
Third-Party Attributions

This project incorporates components from MediaPipe, TensorFlow, LipNet, OpenCV, PostgreSQL, RabbitMQ, Vault, Prometheus, Flask and others.
See NOTICE.md for the full list of licenses and attributions.
Support

For support, please open an issue on GitHub or contact the development team.
Acknowledgments

    MediaPipe for face and lip detection

    TensorFlow for model support

    LipNet for the lip reading model architecture

    PostgreSQL and RabbitMQ for data persistence and messaging

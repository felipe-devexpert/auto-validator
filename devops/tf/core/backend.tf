terraform {
  backend "s3" {
    bucket = "auto-validator-uwzlzz"
    key    = "core.tfstate"
    region = "us-east-1"
  }

  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "~> 4.0"
    }
  }

  required_version = "~> 1.0"
}
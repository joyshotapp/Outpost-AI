# Terraform - AWS Infrastructure

AWS 基礎設施配置（VPC、RDS、ElastiCache 等）

## 前置要求

- Terraform >= 1.5
- AWS CLI 配置完成
- AWS 帳號與足夠權限

## 初始化

```bash
terraform init
```

## 部署到 Staging

```bash
terraform plan -var-file=staging.tfvars
terraform apply -var-file=staging.tfvars
```

## 部署到 Production

```bash
terraform plan -var-file=production.tfvars
terraform apply -var-file=production.tfvars
```

## 輸出值

部署完成後，Terraform 會輸出：
- RDS 連線字串
- ElastiCache 端點
- S3 Bucket 名稱
- ECS 集群名稱等

見 `outputs.tf`

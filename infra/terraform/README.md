# Local Terraform plan

The provider is pinned in `versions.tf`. Initialize, validate, and plan only against a running LocalStack instance:

```sh
terraform -chdir=infra/terraform init
terraform -chdir=infra/terraform validate
terraform -chdir=infra/terraform plan -out=tfplan
```

This plan does not use AWS credentials or target a cloud account. Review the generated plan before any later apply; apply and deployment are outside this project run. Terraform CLI was unavailable during implementation, so validation and provider lock generation remain INCOMPLETE.

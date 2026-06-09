# dental-api Terraform — SMS reminder scheduler

`sms_reminder_scheduler.tf` declares the Cloud Scheduler job that drives
SMS reminder dispatch. Applied as part of the dental-api-v2 Terraform
module.

## Required variables

- `dental_api_url` — e.g. `https://dental-api-v2-<hash>-uc.a.run.app`
- `dental_api_internal_secret` — match `DENTAL_API_INTERNAL_SECRET` on Cloud Run
- `cloud_run_invoker_sa_email` — service account with `roles/run.invoker`

## To apply

```bash
cd infra/terraform
terraform plan -target=google_cloud_scheduler_job.sms_reminder_scan
terraform apply -target=google_cloud_scheduler_job.sms_reminder_scan
```

## To pause

Cloud Console → Cloud Scheduler → `sms-reminder-scan-every-5min` → Pause.
This is faster than a `terraform destroy` if you just need to stop sends
temporarily.

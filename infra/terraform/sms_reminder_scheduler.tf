# infra/terraform/sms_reminder_scheduler.tf
#
# Cloud Scheduler job that triggers POST /cron/reminders/scan on
# dental-api-v2 every 5 minutes. The endpoint scans for appointments
# whose target send time falls in the next 5 min, dedups via the
# AppointmentReminder UNIQUE(appointment_id, channel) constraint, and
# sends SMS reminders via Telnyx.

resource "google_cloud_scheduler_job" "sms_reminder_scan" {
  name             = "sms-reminder-scan-every-5min"
  description      = "Triggers dental-api scan for due appointment reminders."
  schedule         = "*/5 * * * *"
  time_zone        = "America/Edmonton"
  attempt_deadline = "180s"

  http_target {
    http_method = "POST"
    uri         = "${var.dental_api_url}/cron/reminders/scan"

    headers = {
      "X-Internal-Secret" = var.dental_api_internal_secret
      "Content-Type"      = "application/json"
    }

    oidc_token {
      service_account_email = var.cloud_run_invoker_sa_email
      audience              = var.dental_api_url
    }

    body = base64encode("{}")
  }

  retry_config {
    retry_count          = 3
    max_retry_duration   = "300s"
    min_backoff_duration = "30s"
    max_backoff_duration = "120s"
  }
}

variable "dental_api_url" {
  description = "Base URL of the dental-api-v2 Cloud Run service (no trailing slash)."
  type        = string
}

variable "dental_api_internal_secret" {
  description = "Shared X-Internal-Secret header value (matches DENTAL_API_INTERNAL_SECRET env on the Cloud Run service)."
  type        = string
  sensitive   = true
}

variable "cloud_run_invoker_sa_email" {
  description = "Service account email with roles/run.invoker on dental-api-v2. Used for OIDC auth on the scheduler -> Cloud Run call."
  type        = string
}

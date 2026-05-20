#!/bin/bash
set -e

ROOT_PASSWORD=$(openssl rand -base64 32)

echo "Creating instance..."
gcloud sql instances create dental-api-db-v2 \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=northamerica-northeast2 \
  --root-password="$ROOT_PASSWORD" \
  --backup \
  --backup-start-time=04:00 \
  --storage-auto-increase

CONNECTION_NAME=$(gcloud sql instances describe dental-api-db-v2 --format="value(connectionName)")
echo "CONNECTION_NAME=$CONNECTION_NAME"
echo "$CONNECTION_NAME" > /tmp/conn_name

echo "Creating database..."
gcloud sql databases create dental_clinic --instance=dental-api-db-v2

echo "Creating user..."
APP_PASSWORD=$(openssl rand -base64 24 | tr -d '/+=' | head -c 32)
echo "APP_PASSWORD=$APP_PASSWORD"
echo "$APP_PASSWORD" > /tmp/app_pwd

gcloud sql users create dentalapp --instance=dental-api-db-v2 --password="$APP_PASSWORD"

echo "Creating secret..."
DATABASE_URL_CLOUDRUN="postgresql://dentalapp:${APP_PASSWORD}@/dental_clinic?host=/cloudsql/${CONNECTION_NAME}"
if ! gcloud secrets create DATABASE_URL_V2 --replication-policy=automatic --data-file=- <<< "$DATABASE_URL_CLOUDRUN"; then
  gcloud secrets versions add DATABASE_URL_V2 --data-file=- <<< "$DATABASE_URL_CLOUDRUN"
fi

echo "Done provisioning."

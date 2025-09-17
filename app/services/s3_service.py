import os
import boto3
from botocore.client import Config
from dotenv import load_dotenv
load_dotenv("creds.env")

S3_BUCKET = os.getenv("S3_BUCKET")
S3_REGION = os.getenv("S3_REGION", "us-east-1")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")  # set for LocalStack
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")

_session = boto3.session.Session()
s3 = _session.client(
    "s3",
    region_name=S3_REGION,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(s3={"addressing_style": "path"}),
)

def ensure_bucket():
    existing = s3.list_buckets().get("Buckets", [])
    if not any(b["Name"] == S3_BUCKET for b in existing):
        s3.create_bucket(Bucket=S3_BUCKET)

def upload_bytes(key: str, data: bytes, content_type: str):
    ensure_bucket()
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=data, ContentType=content_type)
    return key
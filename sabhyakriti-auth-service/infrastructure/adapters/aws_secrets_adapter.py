from __future__ import annotations

import boto3


def get_secret(secret_name: str, region: str = "ap-south-1") -> str:
    client = boto3.client("secretsmanager", region_name=region)
    response = client.get_secret_value(SecretId=secret_name)
    return response["SecretString"]

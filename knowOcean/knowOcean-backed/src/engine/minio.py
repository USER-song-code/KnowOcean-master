"""MinIO 对象存储引擎

对照 Java: engine/storage/MinioStorageService.java
"""
import io
from boto3 import session
from botocore.client import Config
from botocore.exceptions import ClientError
from src.config import get_settings

settings = get_settings()


def _get_client():
    """创建 MinIO (S3-compatible) 客户端"""
    ep = settings.minio_endpoint
    if not ep.startswith("http://") and not ep.startswith("https://"):
        ep = f"{'https' if settings.minio_secure else 'http'}://{ep}"
    sess = session.Session()
    return sess.client(
        "s3",
        endpoint_url=ep,
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4"),
    )


def put_object(key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
    """上传对象到 MinIO

    对照 Java: MinioStorageService.putObject(key, stream, contentType)
    """
    client = _get_client()
    client.put_object(
        Bucket=settings.minio_bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
    )


def get_object(key: str) -> bytes | None:
    """从 MinIO 下载对象"""
    client = _get_client()
    try:
        resp = client.get_object(Bucket=settings.minio_bucket, Key=key)
        return resp["Body"].read()
    except ClientError:
        return None


def delete_object(key: str) -> None:
    """删除 MinIO 对象"""
    client = _get_client()
    try:
        client.delete_object(Bucket=settings.minio_bucket, Key=key)
    except ClientError:
        pass


def compose_objects(source_keys: list[str], dest_key: str) -> None:
    """合并多个分片对象为一个完整文件

    下载所有分片 → 本地拼接 → 上传合并文件 → 清理分片
    """
    data = bytearray()
    for key in source_keys:
        chunk = get_object(key)
        if chunk is None:
            raise Exception(f"分片丢失: {key}")
        data.extend(chunk)

    put_object(dest_key, bytes(data))


def object_exists(key: str) -> bool:
    """检查对象是否存在"""
    client = _get_client()
    try:
        client.head_object(Bucket=settings.minio_bucket, Key=key)
        return True
    except ClientError:
        return False

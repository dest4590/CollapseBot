from typing import Optional

from loguru import logger
from minio import Minio
from minio.error import S3Error

import config

_client = None


def get_client() -> Optional[Minio]:
    """Get or create Minio client singleton with error handling"""
    global _client
    if _client is None:
        try:
            _client = Minio(
                config.MINIO_ENDPOINT,
                access_key=config.MINIO_ACCESS_KEY,
                secret_key=config.MINIO_SECRET_KEY,
                secure=True,
            )
            _client.list_buckets()
            logger.info("Minio client initialized successfully")
        except S3Error as e:
            logger.error(f"Failed to initialize Minio client: {e}")
            _client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing Minio client: {e}")
            _client = None

    return _client


def test_connection() -> bool:
    """Test if Minio connection is working"""
    client = get_client()
    if not client:
        return False

    try:
        client.list_buckets()
        return True
    except Exception as e:
        logger.error(f"Minio connection test failed: {e}")
        return False

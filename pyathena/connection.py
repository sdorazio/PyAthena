# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
import logging
import os

import boto3
from boto3.session import Session

from pyathena.converter import TypeConverter
from pyathena.cursor import Cursor
from pyathena.error import NotSupportedError
from pyathena.formatter import ParameterFormatter


_logger = logging.getLogger(__name__)


class Connection(object):

    _ENV_S3_STAGING_DIR = 'AWS_ATHENA_S3_STAGING_DIR'

    def __init__(self, s3_staging_dir=None, region_name=None, schema_name='default',
                 poll_interval=1, encryption_option=None, kms_key=None, profile_name=None,
                 converter=None, formatter=None,
                 retry_exceptions=('ThrottlingException', 'TooManyRequestsException'),
                 retry_attempt=5, retry_multiplier=1,
                 retry_max_delay=1800, retry_exponential_base=2,
                 **kwargs):
        if s3_staging_dir:
            self.s3_staging_dir = s3_staging_dir
        else:
            self.s3_staging_dir = os.getenv(self._ENV_S3_STAGING_DIR, None)
        assert self.s3_staging_dir, 'Required argument `s3_staging_dir` not found.'
        assert schema_name, 'Required argument `schema_name` not found.'
        self.region_name = region_name
        self.schema_name = schema_name
        self.poll_interval = poll_interval
        self.encryption_option = encryption_option
        self.kms_key = kms_key

        if profile_name:
            session = Session(profile_name=profile_name, **kwargs)
            self._client = session.client('athena', region_name=region_name, **kwargs)
        else:
            self._client = boto3.client('athena', region_name=region_name, **kwargs)

        self._converter = converter if converter else TypeConverter()
        self._formatter = formatter if formatter else ParameterFormatter()

        self.retry_exceptions = retry_exceptions
        self.retry_attempt = retry_attempt
        self.retry_multiplier = retry_multiplier
        self.retry_max_deply = retry_max_delay
        self.retry_exponential_base = retry_exponential_base

    def __enter__(self):
        return self.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def cursor(self):
        return Cursor(self._client, self.s3_staging_dir, self.schema_name, self.poll_interval,
                      self.encryption_option, self.kms_key, self._converter, self._formatter,
                      self.retry_exceptions, self.retry_attempt, self.retry_multiplier,
                      self.retry_max_deply, self.retry_exponential_base)

    def close(self):
        pass

    def commit(self):
        pass

    def rollback(self):
        raise NotSupportedError

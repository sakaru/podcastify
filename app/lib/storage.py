import boto3
from botocore.errorfactory import ClientError

class Storage:

    def __init__(self, bucket):
        self.bucket = bucket

    def touch(self, key):
        self.put(key, None)

    def put(self, key, body):
        s3 = boto3.client('s3')
        s3.put_object(Bucket=self.bucket, Key=key, Body=body, ACL='public-read')

    def read(self, key):
        s3 = boto3.client('s3')
        return s3.get_object(Bucket=self.bucket, Key=key)

    def exists(self, key):
        s3 = boto3.client('s3')
        try:
            s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    def make_public(self, key):
        s3 = boto3.client('s3')
        s3.put_object_acl(ACL='public-read', Bucket=self.bucket, Key=key)
from os import getenv
from importlib import import_module
import boto3
from storage import Storage

source_name    = getenv("source_name")
bucket         = getenv("bucket")
region         = getenv("AWS_REGION")
output_format  = getenv("output_format")
text_type      = getenv("text_type")
voice_id       = getenv("voice_id")
language_code  = getenv("language_code")
sns_topic      = getenv("sns_topic")
dynamodb_table = getenv("dynamodb_table")
domain_name    = getenv("domain_name")

storage  = Storage(bucket)
dynamodb = boto3.Session(region_name=region).client("dynamodb")
polly    = boto3.Session(region_name=region).client("polly")

def load():
    try:
        mod = import_module(source_name)
        podcast_class = getattr(mod, source_name.title())
        if not issubclass(podcast_class, getattr(mod, "BasePodcast")):
            raise Exception("Not a podcast")
        podcast = podcast_class(
            source_name=source_name,
            bucket=bucket,
            polly=polly,
            output_format=output_format,
            text_type=text_type,
            voice_id=voice_id,
            language_code=language_code,
            sns_topic=sns_topic,
            dynamodb_table=dynamodb_table,
            domain_name=domain_name,
            storage=storage,
            dynamodb=dynamodb,
        )
        print("Loaded podcast {}".format(source_name))
        return podcast
    except Exception as e:
        print("Cannot create {} object. {}".format(source_name, str(e)))
        return False

def ingestor(event, context):
    p = load()
    return p.ingestor(event, context)
def checker(event, context):
    p = load()
    return p.checker(event, context)
def creator(event, context):
    p = load()
    return p.creator(event, context)

if __name__ == '__main__':
    event = {}
    context = {}
    ingestor(event, context)

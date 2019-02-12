# Podcastify
Make a podcast out of any text; an RSS feed, a news website, product reviews

## Flow
1. Triggered by a scheduler, Ingestor lamda reads the input.
  1. Schedules Text-To-Speach tasks.
  2. Save into DynamoDB:
    - PRI=task_id | status="waiting_for_polly"
2. Text-To-Speach engine runs. Outputs .ogg files into an S3 bucket.
  - Also triggers SNS
3. SNS triggers Polly Lambda
  1. If a Polly job failed, schedule a retry. Delete the DynamoDB record. Create a new one.
  2. If the Polly job succeeded, update status to "waiting_for_merge"
4. Triggered by Scheduler, Merger Lambda starts.
  1. Scans DynamoDB for jobs with status="waiting_for_polly". If found, Exit
  2. Scans DynamoDB for jobs with status="waiting_for_merge"
  3. (re-)create RSS (is idempotent)

## Helper:
### Manual ingestion
`aws lambda invoke --function-name podcastify-ingestor-economist --region ap-southeast-1 a`
### Manually checker
```python
import boto3
region='ap-southeast-1'
dynamodb_table='podcast_economist'
status_awaiting_merge='awaiting_polly'
dynamodb = boto3.Session(region_name=region).client("dynamodb")
new = dynamodb.scan(
    TableName=dynamodb_table,
    FilterExpression="#S=:status",
    ExpressionAttributeNames={"#S": "status"},
    ExpressionAttributeValues={":status": {
        "S": status_awaiting_merge}}
)
ids = [x['task_id']['S'] for x in new['Items']]
for id in ids:
  print("id={}".format(id))
  print('aws lambda invoke --function-name podcastify-checker-economist --region ap-southeast-1 --payload "{\\"taskId\\": \\"$id\\",\\"taskStatus\\": \\"COMPLETED\\",\\"outputUri\\": \\"s3://net.karunaratne.net.podcastify-economist/public/audio/economist.$id.mp3\\"}" a')
```
### Manual creator
`aws lambda invoke --function-name podcastify-creator-economist --region ap-southeast-1 a`

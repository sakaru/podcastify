from datetime import datetime
import time
from functools import cmp_to_key
import json
import templates
import urllib
import boto3
import email.utils
from html.parser import HTMLParser
from html import escape
import base64
import re

class BasePodcast(object):
    status_ingest            = "awaiting_polly"
    status_awaiting_merge    = "awaiting_merge"
    status_merged            = "merged"
    s3_public_prefix         = "public/"

    def __init__(self, source_name, bucket, polly, output_format, text_type, voice_id,
                 language_code, sns_topic, dynamodb_table, domain_name, storage, dynamodb):
        self.source_name    = source_name
        self.bucket         = bucket
        self.polly          = polly
        self.output_format  = output_format
        self.text_type      = text_type
        self.voice_id       = voice_id
        self.language_code  = language_code
        self.sns_topic      = sns_topic
        self.dynamodb_table = dynamodb_table
        self.domain_name    = domain_name
        self.storage        = storage
        self.dynamodb       = dynamodb


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)


class Economist(BasePodcast):

    def ingestor(self, event, context):
        decaf = Decaf()
        count_new = 0
        # Todo: check input length, if it exceeds Polly's limits
        for date in decaf.get_issue_dates()[-1:]:
            pub_date = email.utils.format_datetime(datetime.fromisoformat(date))
            articles, gobbets = decaf.get_issue_articles(date=date)

            # Process each article in the content of the day
            for sort_order, article in enumerate(articles):
                guid = "economist-decaf-{}".format(article["nhash"])
                image_path = self._import_image(guid, article["leaderImage"])
                count_new += self._ingest_item(
                    guid=guid,
                    text=article["body"],
                    title=article["headline"],
                    pub_date=pub_date,
                    sort_order=sort_order+1,
                    image=image_path,
                )

            # Create the gobbet
            gobbet = "".join(x["body"] for x in gobbets)
            guid = "economist-decaf-gobbet-{}".format(date)
            image_path = self._import_image(guid, gobbets[0]["image"])
            count_new += self._ingest_item(
                guid=guid,
                text=gobbet,
                title="World in brief ({})".format(date),
                pub_date=pub_date,
                sort_order=0,
                image=image_path,
            )
        return "Ingested {} new item(s) successfully".format(count_new)

    def checker(self, event, context):
        # Get the item from DynamoDB (by task_id)
        item = self.dynamodb.get_item(
            TableName=self.dynamodb_table,
            Key={"task_id": {"S": event["taskId"]},
                 "status": {"S": self.status_ingest}}
        )
        if "Item" not in item:
            # How did this occur?
            return False
        item = self._dynamodb_to_normal(item["Item"])
        # If successful, enrich items and update status
        if event["taskStatus"].lower() == "completed":
            l = len("s3://{}".format(self.bucket))+1
            key = event["outputUri"][l:]
            self.storage.make_public(key)
            new_attributes = self._enrich(event["outputUri"])
            self._update_status(item["task_id"], self.status_ingest,
                                self.status_awaiting_merge, new_attributes)
            return "Checked task {}".format(event["taskId"])
        else:
            # oh no, the polly task failed? retry?
            return False

    def creator(self, event, context):
        paginator = self.dynamodb.get_paginator('scan')
        # Read all status="merged" and status="waiting_for_merge" items
        # If none in "waiting_for_merge" state, stop
        new = paginator.paginate(
            TableName=self.dynamodb_table,
            FilterExpression="#S=:status",
            ExpressionAttributeNames={"#S": "status"},
            ExpressionAttributeValues={":status": {
                "S": self.status_awaiting_merge}}
        ).build_full_result()

        if new["Count"] == 0:
            print("No new items")
            return False

        old = paginator.paginate(
            TableName=self.dynamodb_table,
            FilterExpression="#S=:status",
            ExpressionAttributeNames={"#S": "status"},
            ExpressionAttributeValues={":status": {"S": self.status_merged}}
        ).build_full_result()

        # Combine the two lists
        old = [self._dynamodb_to_normal(x) for x in old.get("Items", [])]
        new = [self._dynamodb_to_normal(x) for x in new.get("Items", [])]
        items = old + new
        # Sort by date, then by sort_order
        items = sorted(items, key=cmp_to_key(self._sort))
        output = templates.header.format(
            title="Economist Espresso, Decaffeinated",
            link="https://economist.com/",
            language=self.language_code,
            author="Economist Espresso",
            description="The nearly daily economist espresso, decaf",
            podcast_image="https://is2-ssl.mzstatic.com/image/thumb/Purple117/v4/af/f4/31/aff4318d-d64d-c574-6819-db6f19ecf035/source/1200x630bb.jpg", #TODO: remove hotlinking
        )

        for item in items:
            output += templates.item.format(
                item_title=item["title"],
                item_author=item["author"],
                item_description=item["text"],
                item_bytes=item["bytes"],
                item_url=item["link"],
                item_guid=item["guid"],
                item_pub_date=item["pub_date"],
                item_duration=item["duration"],
                item_image_url="https://{}/{}".format(self.domain_name, item["image"]),
            )
        output += templates.footer
        # Output to S3
        self.storage.put("{}{}.xml".format(self.s3_public_prefix, self.source_name), output)

        for item in new:
            self._update_status(item["task_id"], self.status_awaiting_merge, self.status_merged)
        return "Created successfully. {} new and {} old items found".format(len(new), len(old))

    def _ingest_item(self, guid, text, title, image, pub_date, sort_order):
        if self._already_ingested(guid):
            return 0
        # Schedule Polly
        ssml = self._make_ssml(title, text)
        task_id = self._schedule_task(ssml)
        # Save to DynamoDB
        self.dynamodb.put_item(
            TableName=self.dynamodb_table,
            Item={
                "task_id": {"S": task_id},
                "status": {"S": self.status_ingest},
                "text": {"S": text},
                "ssml": {"S": ssml},
                "guid": {"S": guid},
                "title": {"S": title},
                "image": {"S": image},
                "author": {"S": "Economist Espresso"},
                "pub_date": {"S": pub_date},
                "sort_order": {"N": str(sort_order)},
            }
        )
        return 1

    def _already_ingested(self, guid):
        res = self.dynamodb.query(
            TableName=self.dynamodb_table,
            IndexName="guid",
            Select="ALL_ATTRIBUTES",
            KeyConditionExpression="guid=:guid",
            ExpressionAttributeValues={":guid": {"S": guid}}
        )
        return res["Count"] > 0

    def _schedule_task(self, text):
        task = self.polly.start_speech_synthesis_task(
            OutputS3BucketName=self.bucket,
            OutputS3KeyPrefix="{}audio/{}".format(
                self.s3_public_prefix, self.source_name),
            Text=text,
            TextType=self.text_type,
            OutputFormat=self.output_format,
            VoiceId=self.voice_id,
            LanguageCode=self.language_code,
            SnsTopicArn=self.sns_topic,
        )
        return task["SynthesisTask"]["TaskId"]

    def _update_status(self, task_id, old_status, new_status, new_attributes = {}):
        # You cannot use UpdateItem to update any primary key attributes. So:
        # 1. Get the item
        # 2. Delete the item
        # 3. Re-create the item with the new status value
        item = self.dynamodb.get_item(
            TableName=self.dynamodb_table,
            Key={
                "task_id": {"S": task_id},
                "status": {"S": old_status},
            }
        )
        item = self._dynamodb_to_normal(item['Item'])

        # Build the new item
        new_item = {}
        for k,v in item.items() | new_attributes.items():
            t = "S"
            if type(v) in [int, float]:
                t = "N"
            new_item[k] = {t: str(v)}
        new_item["status"] = {"S": new_status}

        # Delete the old item
        self.dynamodb.delete_item(
            TableName=self.dynamodb_table,
            Key={
                "task_id": {"S": task_id},
                "status": {"S": old_status},
            }
        )
        # Create the new item
        self.dynamodb.put_item(
            TableName=self.dynamodb_table,
            Item=new_item
        )

    def _dynamodb_to_normal(self, item):
        # Strip all the weird String/Number field definitions from DynamoDB objects
        x = {}
        for key in item.keys():
            if "N" == list(item[key].keys())[0]:
                x[key] = int(item[key]["N"])
            else:
                x[key] = item[key]["S"]
        return x

    def _enrich(self, path):
        # path is something like s3://{bucket}/{folder}/{task-id}.{extension}
        l = len("s3://") + len(self.bucket) + 1
        path = path[l:]

        public_path = path[len(self.s3_public_prefix):]
        url = "https://{}/".format(self.domain_name) + public_path

        import mutagen
        from io import BytesIO
        o = self.storage.read(path)
        b = o.get('Body').read()
        audio = mutagen.File(BytesIO(b))
        
        duration = int(audio.info.length)
        size = len(b)

        return {
            "duration": duration,
            "bytes": size,
            "link": url,
        }

    def _import_image(self, guid, img_bytes_str):
        img_bytes = bytes(img_bytes_str, "utf-8")
        d = base64.decodebytes(img_bytes)
        d = base64.decodebytes(img_bytes)
        path = "images/{}.jpg".format(guid)
        self.storage.put(self.s3_public_prefix + path, d)
        return path

    def _sort(self, a, b):
        # It should never be the case that pub_date and sort_order match
        # So we should never need to return 0
        a_t = time.mktime(email.utils.parsedate_to_datetime(a["pub_date"]).timetuple())
        b_t = time.mktime(email.utils.parsedate_to_datetime(b["pub_date"]).timetuple())
        if a_t != b_t:
            return 1 if a_t < b_t else -1
        return 1 if a["sort_order"] > b["sort_order"] else -1

    def _make_ssml(self, title, html):
        txt = self._strip_tags(html)
        txt = escape(txt, quote=False) # ampersands and other entities
        txt = txt.replace("\n", "</p><p>")
        txt = "<p>{title}</p><p>{text}</p>".format(title=title, text=txt)
        ssml = "<speak>{}<break time=\"2s\"/></speak>".format(txt)
        # AWS Polly will read 600m as "600 metres", not "600 million"
        # We more often than not want the latter
        ssml = re.sub(r"\b(\d+(\.\d+)?)m\b", '<sub alias="\g<1> million">\g<0></sub>', ssml)
        return ssml

    def _strip_tags(self, html):
        s = MLStripper()
        s.feed(html)
        return s.get_data()



class Decaf:
    baseURL = "https://espresso.economist.com"
    manifest = None

    # Get dates for which issues exist
    def get_issue_dates(self):
        self._get_manifest()
        return sorted([x["issueDate"] for x in self.manifest if x["type"] == "Issue"], reverse=False)

    # Get a specific issue's articles, is `date` is None, get the latest issue
    def get_issue_articles(self, date=None):
        manifest = self._get_manifest()
        if date is None:
            date = self.get_issue_dates()[-1]
        if date not in self.get_issue_dates():
            logging.error("Invalid issue date {}".format(date))
            logging.debug("Valid issue dates: {}".format(self.get_issue_dates()))
            raise Exception("Error, Invalid date fetched")
        manifestItem = list(filter(lambda x: x["type"] == "Issue" and x["issueDate"] == date, manifest))[0]
        issue        = self._get_issue(manifestItem["jsonUri"])
        articles     = list(filter(lambda x: x["type"] == "article", issue))
        gobbets      = list(filter(lambda x: x["type"] == "gobbet_page", issue))
        return articles, gobbets

    def _get_manifest(self):
        if self.manifest is None:
            try:
                self.manifest = self._get_json("{}/api/v1/issue/AP/json".format(self.baseURL))
            except Exception as e:
                logging.error("Error downloading the manifest: {}".format(e))
                raise Exception("Error getting the manifest")
        return self.manifest

    def _get_issue(self, endpoint):
        try:
            return self._get_json("{}/{}".format(self.baseURL, endpoint))
        except Exception as e:
            logging.error("Error downloading JSON: {}".format(e))
            raise Exception("Error getting an issue")

    def _get_json(self, url):
        fp = urllib.request.urlopen(url)
        b = fp.read()
        s = b.decode("utf8")
        fp.close()
        j = json.loads(s)
        return j

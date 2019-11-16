header="""<?xml version="1.0" encoding="UTF-8"?>
<rss
  version="2.0"
  xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
  xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
	<title><![CDATA[{title}]]></title>
	<link>{link}</link>
	<language>{language}</language>
	<itunes:author><![CDATA[{author}]]></itunes:author>
	<description><![CDATA[{description}]]></description>
	<itunes:image href="{podcast_image}"/>
	<itunes:explicit>no</itunes:explicit>
"""
item="""
<item>
	<title><![CDATA[{item_title}]]></title>
	<itunes:author><![CDATA[{item_author}]]></itunes:author>
	<description><![CDATA[{item_description}]]></description>
	<enclosure length="{item_bytes}" type="audio/{output_format}" url="{item_url}"/>
	<guid>{item_guid}</guid>
	<pubDate>{item_pub_date}</pubDate>
	<itunes:duration>{item_duration}</itunes:duration>
	<itunes:explicit>no</itunes:explicit>
	<itunes:image href="{item_image_url}"/>
</item>
"""
footer="""
</channel>
</rss>
"""
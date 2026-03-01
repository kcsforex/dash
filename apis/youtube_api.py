# 2026.03.01  18.00
from googleapiclient.discovery import build
import isodate
api_key = 'AIzaSyBzSaapBAb9sfTih5iHefzDeYOtKB8_G7s'

def get_channel_stats_api(handle):
    youtube = build("youtube", "v3", developerKey=api_key)

    ch_request = youtube.channels().list(part="id,snippet,statistics", forHandle=handle)
    ch_response = ch_request.execute()

    if not ch_response.get("items"):
        return {"error": "Channel not found"}

    channel_item = ch_response["items"][0]
    channel_id = channel_item["id"]
    
    search_request = youtube.search().list(part="id,snippet",  channelId=channel_id,  maxResults=5,  order="date",  type="video")
    search_response = search_request.execute()

    # Collect Video IDs to fetch stats in bulk
    video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]
    
    # 3. Get Statistics for those 5 videos (Bulk request)
    stats_request = youtube.videos().list(part="snippet,contentDetails,statistics", id=",".join(video_ids))
    stats_response = stats_request.execute()

    results = {
        "channel_name": channel_item["snippet"]["title"],
        "subscribers": channel_item["statistics"].get("subscriberCount"),
        "videos": []
    }

    # 4. Map stats and fetch comments per video
    for video in stats_response.get("items", []):
        video_id = video["id"]
        stats = video["statistics"]
        snippet = video["snippet"]
        details = video['contentDetails']
        
        comments = []
        try:
            comment_request = youtube.commentThreads().list(part="snippet", videoId=video_id, maxResults=5, textFormat="plainText")
            comment_response = comment_request.execute()

            for c_item in comment_response.get("items", []):
                c_snippet = c_item["snippet"]["topLevelComment"]["snippet"]
                comments.append({"author": c_snippet["authorDisplayName"], "text": c_snippet["textDisplay"] })
        except Exception:
            comments = [{"author": "System", "text": "Comments disabled"}]

        results["videos"].append({
            "title": snippet["title"][:50],
            "id": video_id,
            "duration (sec)": isodate.parse_duration(details.get("duration")).total_seconds(),
            "upload_date": snippet["publishedAt"],
            "like_count": stats.get("likeCount"),
            "view_count": stats.get("viewCount"),
            "comment_count": stats.get("commentCount"),
            "comments": comments
        })
    
    return results

# Run the script
data = get_channel_stats_api("@Reakciok")
print(data)

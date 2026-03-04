# 2026.03.04 18:00
from fastapi import APIRouter
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from googleapiclient.discovery import build
import isodate

# --- Initialize APIRouter & FastMCP ---
router = APIRouter()

mcp = FastMCP("YouTube Analytics", stateless_http=True, transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False))
api_key = "AIzaSyBzSaapBAb9sfTih5iHefzDeYOtKB8_G7s"

# --- MCP Tool (called by AI / N8N) ---
@mcp.tool(name="get_youtube_metrics")
async def get_channel_stats_mcp(channel:str, maxVideos: int = 5, maxComments: int = 5):
    return await fetch_youtube_data(channel, maxVideos, maxComments)

# --- REST Endpoint (called by Dash / browser) ---
@router.get("/metrics/{channel}")
async def get_channel_stats_api(channel:str,  maxVideos:int = 5, maxComments:int = 5):
    return await fetch_youtube_data(channel, maxVideos, maxComments)

# --- Shared logic ---
async def fetch_youtube_data(channel:str, maxVideos:int = 5, maxComments:int = 5):
    
    youtube = build("youtube", "v3", developerKey=api_key)
    ch_request = youtube.channels().list(part="id,snippet,statistics", forHandle=channel)
    ch_response = ch_request.execute()

    if not ch_response.get("items"):
        return {"error": "Channel not found"}

    channel_item = ch_response["items"][0]
    channel_id = channel_item["id"]

    search_request = youtube.search().list(part="id,snippet", channelId=channel_id, maxResults=maxVideos, order="date", type="video")
    search_response = search_request.execute()
    video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]

    stats_request = youtube.videos().list(part="snippet,contentDetails,statistics", id=",".join(video_ids))
    stats_response = stats_request.execute()

    results = []
    
    for video in stats_response.get("items", []):
        video_id = video["id"]
        stats = video["statistics"]
        snippet = video["snippet"]
        details = video["contentDetails"]

        comments = []
        try:
            comment_request = youtube.commentThreads().list(part="snippet", videoId=video_id, maxResults=maxComments, textFormat="plainText")
            comment_response = comment_request.execute()
            for c_item in comment_response.get("items", []):
                c_snippet = c_item["snippet"]["topLevelComment"]["snippet"]
                comments.append({ "c_author": c_snippet["authorDisplayName"], "c_published": c_snippet["publishedAt"], "c_text": c_snippet["textDisplay"]})
        except Exception:
            comments = [{"author": "System", "text": "Comments disabled"}]

        results.append({
            "channel_name": channel_item["snippet"]["title"],
            "subscribers": int(channel_item["statistics"].get("subscriberCount", 0)),
            "video_id": video_id,
            "title": snippet["title"][:50],
            "duration_sec": int(isodate.parse_duration(details.get("duration")).total_seconds()),
            "upload_date": snippet["publishedAt"],
            "view_count": int(stats.get("viewCount", 0)),
            "comments": comments 
        })

    return results

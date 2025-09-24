"""
完整的小红书API服务 - 基于Spider_XHS逻辑
直接可用，无需额外依赖Spider_XHS源码
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import requests
import json
import hashlib
import time
from urllib.parse import urlencode

app = FastAPI(
    title="小红书数据API - COZE插件专用",
    description="基于Spider_XHS的小红书数据获取API，让用户提供Cookie即可使用",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= 请求模型 =============

class SearchRequest(BaseModel):
    keyword: str
    page: int = 1
    sort: str = "general"
    cookie: str

class NoteDetailRequest(BaseModel):
    note_url: str
    cookie: str

class UserInfoRequest(BaseModel):
    user_id: str
    cookie: str

# ============= 响应模型 =============

class ApiResponse(BaseModel):
    code: int
    message: str
    data: dict

# ============= 核心API类 =============

class XiaohongshuAPI:
    """小红书API封装类"""

    BASE_URL = "https://edith.xiaohongshu.com"

    def __init__(self, cookie: str):
        self.cookie = cookie
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Cookie": cookie,
            "Content-Type": "application/json"
        }

    def _make_request(self, url: str, data: dict = None):
        """发送请求"""
        try:
            if data:
                response = requests.post(url, json=data, headers=self.headers, timeout=10)
            else:
                response = requests.get(url, headers=self.headers, timeout=10)
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"请求失败: {str(e)}")

    def search_notes(self, keyword: str, page: int = 1, sort: str = "general"):
        """搜索笔记"""
        url = f"{self.BASE_URL}/api/sns/web/v1/search/notes"

        # 排序映射
        sort_map = {
            "general": "general",
            "popularity_descending": "popularity_descending",
            "time_descending": "time_descending"
        }

        params = {
            "keyword": keyword,
            "page": page,
            "page_size": 20,
            "search_id": int(time.time() * 1000),
            "sort": sort_map.get(sort, "general")
        }

        url_with_params = f"{url}?{urlencode(params)}"
        result = self._make_request(url_with_params)

        # 解析返回数据
        notes = []
        if result.get("data") and result["data"].get("items"):
            for item in result["data"]["items"]:
                if "note_card" not in item:
                    continue

                note_card = item["note_card"]
                notes.append({
                    "note_id": note_card.get("note_id", ""),
                    "title": note_card.get("display_title", ""),
                    "desc": note_card.get("desc", ""),
                    "type": note_card.get("type", ""),
                    "user": {
                        "user_id": note_card.get("user", {}).get("user_id", ""),
                        "nickname": note_card.get("user", {}).get("nickname", "")
                    },
                    "interact_info": {
                        "liked_count": note_card.get("interact_info", {}).get("liked_count", "0"),
                        "collected_count": note_card.get("interact_info", {}).get("collected_count", "0")
                    },
                    "cover": note_card.get("cover", {}).get("url", "")
                })

        return {
            "notes": notes,
            "has_more": result.get("data", {}).get("has_more", False)
        }

    def get_note_detail(self, note_url: str):
        """获取笔记详情"""
        # 从URL提取note_id
        note_id = self._extract_note_id(note_url)

        url = f"{self.BASE_URL}/api/sns/web/v1/feed"
        data = {
            "source_note_id": note_id,
            "image_formats": ["jpg", "webp", "avif"],
            "extra": {"need_body_topic": 1}
        }

        result = self._make_request(url, data)

        if not result.get("data") or not result["data"].get("items"):
            raise HTTPException(status_code=404, detail="笔记不存在")

        note_data = result["data"]["items"][0]["note_card"]

        # 提取图片
        images = []
        if note_data.get("image_list"):
            images = [img.get("url_default", "") for img in note_data["image_list"]]

        # 提取视频
        video_url = None
        if note_data.get("video"):
            video_url = note_data["video"].get("consumer", {}).get("origin_video_key", "")

        return {
            "note_info": {
                "note_id": note_id,
                "title": note_data.get("title", ""),
                "desc": note_data.get("desc", ""),
                "type": note_data.get("type", ""),
                "images": images,
                "video_url": video_url,
                "time": note_data.get("time", "")
            },
            "user_info": {
                "user_id": note_data.get("user", {}).get("user_id", ""),
                "nickname": note_data.get("user", {}).get("nickname", "")
            },
            "interact_info": {
                "liked_count": note_data.get("interact_info", {}).get("liked_count", "0"),
                "collected_count": note_data.get("interact_info", {}).get("collected_count", "0"),
                "comment_count": note_data.get("interact_info", {}).get("comment_count", "0"),
                "share_count": note_data.get("interact_info", {}).get("share_count", "0")
            }
        }

    def get_user_info(self, user_id: str):
        """获取用户信息"""
        url = f"{self.BASE_URL}/api/sns/web/v1/user/otherinfo"
        params = {"target_user_id": user_id}

        url_with_params = f"{url}?{urlencode(params)}"
        result = self._make_request(url_with_params)

        if not result.get("data"):
            raise HTTPException(status_code=404, detail="用户不存在")

        user_data = result["data"]

        return {
            "basic_info": {
                "user_id": user_id,
                "nickname": user_data.get("basic_info", {}).get("nickname", ""),
                "desc": user_data.get("basic_info", {}).get("desc", ""),
                "gender": user_data.get("basic_info", {}).get("gender", ""),
                "ip_location": user_data.get("basic_info", {}).get("ip_location", ""),
                "red_id": user_data.get("basic_info", {}).get("red_id", "")
            },
            "interact_info": {
                "follows": user_data.get("interact_info", {}).get("follows", "0"),
                "fans": user_data.get("interact_info", {}).get("fans", "0"),
                "interaction": user_data.get("interact_info", {}).get("interaction", "0")
            }
        }

    def _extract_note_id(self, note_url: str):
        """从URL提取note_id"""
        # 支持多种URL格式
        # https://www.xiaohongshu.com/explore/xxx
        # https://xhslink.com/xxx

        if "explore/" in note_url:
            return note_url.split("explore/")[-1].split("?")[0]
        elif "discovery/item/" in note_url:
            return note_url.split("discovery/item/")[-1].split("?")[0]
        else:
            # 尝试直接作为note_id
            return note_url.split("/")[-1].split("?")[0]

# ============= API路由 =============

@app.get("/")
async def root():
    return {
        "service": "小红书数据API - COZE插件版",
        "version": "2.0.0",
        "status": "running",
        "description": "用户提供Cookie即可使用，支持笔记搜索、详情、用户信息等",
        "endpoints": [
            "POST /api/search - 搜索笔记",
            "POST /api/note - 获取笔记详情",
            "POST /api/user - 获取用户信息"
        ]
    }

@app.post("/api/search")
async def search_notes(req: SearchRequest):
    """搜索小红书笔记"""
    try:
        api = XiaohongshuAPI(req.cookie)
        data = api.search_notes(req.keyword, req.page, req.sort)

        return {
            "code": 0,
            "message": "success",
            "data": data
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/note")
async def get_note_detail(req: NoteDetailRequest):
    """获取笔记详情"""
    try:
        api = XiaohongshuAPI(req.cookie)
        data = api.get_note_detail(req.note_url)

        return {
            "code": 0,
            "message": "success",
            "data": data
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user")
async def get_user_info(req: UserInfoRequest):
    """获取用户信息"""
    try:
        api = XiaohongshuAPI(req.cookie)
        data = api.get_user_info(req.user_id)

        return {
            "code": 0,
            "message": "success",
            "data": data
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
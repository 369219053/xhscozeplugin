# 小红书数据API - COZE插件

基于Spider_XHS的小红书数据获取API服务，专为COZE插件设计。

## 🚀 功能特性

- ✅ 笔记搜索（支持综合/热门/最新排序）
- ✅ 笔记详情获取（无水印图片/视频）
- ✅ 用户信息获取
- ✅ 用户提供Cookie即可使用

## 📡 API接口

### 1. 搜索笔记
```http
POST /api/search
{
  "keyword": "美妆教程",
  "page": 1,
  "sort": "general",
  "cookie": "你的Cookie"
}
```

### 2. 获取笔记详情
```http
POST /api/note
{
  "note_url": "https://www.xiaohongshu.com/explore/xxx",
  "cookie": "你的Cookie"
}
```

### 3. 获取用户信息
```http
POST /api/user
{
  "user_id": "xxx",
  "cookie": "你的Cookie"
}
```

## 🔧 部署

### Render一键部署

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com)

1. Fork本仓库
2. 在Render创建Web Service
3. 连接GitHub仓库
4. 自动部署完成

## 📄 Cookie获取

1. 访问 https://www.xiaohongshu.com 并登录
2. F12打开开发者工具
3. 网络 → 刷新页面 → 复制Cookie

## ⚠️ 注意事项

- 仅供学习研究使用
- Cookie定期更新
- 合理控制请求频率

## 📞 技术支持

- API文档: https://your-api.onrender.com/docs
- GitHub Issues: 提交问题反馈
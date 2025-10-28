# WeChat Work (企業微信) Messaging Setup Guide

## Overview
The AI Platform supports sending messages to WeChat Work (企業微信) groups through the `send_notification` MCP tool using group robot webhooks.

## Features
- ✅ Send messages to WeChat Work groups
- ✅ Simple webhook-based integration (no complex OAuth)
- ✅ Support for text messages
- ✅ Optional @mentions for specific users
- ✅ Automatic group routing
- ✅ Multi-model support (Claude, GPT, Qwen)

## Setup Instructions

### 1. Create WeChat Work Group Robot

1. Open your WeChat Work (企業微信) app
2. Go to the group where you want to add the robot
3. Click on the group settings (⋯)
4. Select "Group Robots" (群機器人)
5. Click "Add Robot" (添加機器人)
6. Enter a name for your robot (e.g., "AI Platform Bot")
7. Copy the **Webhook URL** provided

The webhook URL format:
```
https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### 2. Configure Environment Variables

Update your `.env` file:

```bash
# WeChat Work Robot Webhook URL
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-key-here
```

### 3. Restart Services

```bash
docker-compose restart mcp-server
```

## Usage

### Natural Language (Recommended)

Simply tell the AI to send a WeChat message:

**Examples:**
```
用戶: "發微信通知大家今晚會議改期"
AI: ✅ 微信訊息已成功發送！
    發送對象: 企業微信群組
    訊息內容: 今晚會議改期

用戶: "用企業微信告訴團隊專案進度更新了"
AI: ✅ 微信訊息已成功發送！
    發送對象: 企業微信群組
    訊息內容: 專案進度更新了

用戶: "Send a WeChat message: The system will be down for maintenance"
AI: ✅ 微信訊息已成功發送！
    發送對象: 企業微信群組
    訊息內容: The system will be down for maintenance
```

### Keywords for Detection

The AI automatically detects WeChat requests using these keywords:
- Chinese: 微信、企業微信、企业微信、企微、發微信、发微信
- English: wechat, weixin
- Context: 微信群、微信群組、微信訊息、微信消息

### API Usage

#### Send to Group
```json
{
  "message": "Hello from AI Platform!",
  "channel": "wechat"
}
```

#### Send with @Mentions (Optional)
```json
{
  "message": "Important update for the team",
  "channel": "wechat",
  "recipients": ["userid1", "userid2"]
}
```

**Note**: For @mentions, you need the user's WeChat Work UserID or mobile number.

## Message Format Support

WeChat Work robots support multiple message types:

### Text Message (Current Implementation)
```json
{
  "msgtype": "text",
  "text": {
    "content": "Your message here"
  }
}
```

### Markdown Message (Future)
```json
{
  "msgtype": "markdown",
  "markdown": {
    "content": "# Title\n**Bold** text"
  }
}
```

### Image Message (Future)
```json
{
  "msgtype": "image",
  "image": {
    "base64": "BASE64_ENCODED_IMAGE",
    "md5": "MD5_OF_IMAGE"
  }
}
```

## Troubleshooting

### Error: "WECHAT_WEBHOOK_URL not configured"
- Make sure you've added the webhook URL to `.env`
- Restart mcp-server: `docker-compose restart mcp-server`
- Verify the URL format is correct

### Messages not received
1. Check if the robot is still in the group
2. Verify the webhook URL hasn't expired
3. Check mcp-server logs: `docker logs ai-mcp-server --tail 50`
4. Test the webhook directly:
   ```bash
   curl -X POST "YOUR_WEBHOOK_URL" \
     -H "Content-Type: application/json" \
     -d '{"msgtype":"text","text":{"content":"Test message"}}'
   ```

### Error: "errcode: 93000" (Webhook URL invalid)
- The webhook URL has expired or is invalid
- Create a new group robot and update the webhook URL

### Error: "errcode: 45009" (API call frequency limit)
- WeChat Work limits webhook calls to 20 messages/minute
- Wait a minute and try again

## Comparison: WeChat Work vs LINE

| Feature | WeChat Work | LINE |
|---------|-------------|------|
| **Setup Complexity** | Simple (Webhook) | Moderate (Channel Token) |
| **Recipient Type** | Group only (via webhook) | User & Group |
| **@Mentions** | Yes (UserID/Mobile) | No |
| **Message Types** | Text, Markdown, Image, File | Text, Image, Sticker |
| **Rate Limit** | 20 msg/min | 500 msg/month (free) |
| **Use Case** | Enterprise internal communication | Personal & Business |

## Technical Implementation

### Code Locations
- **MCP Server**: `services/mcp-server/main.py:938-1006`
  - WeChat API integration
  - Webhook message sending

- **Agent Service**: `services/agent-service/main.py`
  - System prompt: Lines 702-720
  - Fallback detection: Lines 310-358
  - Response formatting: Lines 580-581

### How It Works

1. **User Request**: "發微信通知大家開會"
2. **Keyword Detection**: System detects "微信" keyword
3. **Message Extraction**: Extracts "通知大家開會"
4. **Channel Selection**: Sets `channel: "wechat"`
5. **API Call**: POSTs JSON to webhook URL
6. **Response**: WeChat Work sends message to group

### Webhook Payload
```json
{
  "msgtype": "text",
  "text": {
    "content": "通知大家開會",
    "mentioned_list": []  // Optional: UserIDs or mobiles to @mention
  }
}
```

## Security Notes

- ⚠️ Never commit your WECHAT_WEBHOOK_URL to git
- ⚠️ Keep your `.env` file private
- ⚠️ The webhook URL allows anyone to send messages to your group
- ⚠️ If leaked, delete the robot and create a new one
- ✅ Regularly rotate webhook URLs for security

## Limitations

1. **Group Only**: Webhook robots can only send to the group they were added to
2. **No File Attachments**: Current implementation supports text only
3. **Rate Limits**: 20 messages per minute per webhook
4. **No Read Receipts**: Cannot track if messages were read
5. **No Two-Way Communication**: Robot cannot receive messages

## Advanced Features (Future)

- [ ] Markdown formatting support
- [ ] Image and file attachments
- [ ] Interactive buttons and cards
- [ ] Multiple webhook support (multiple groups)
- [ ] Message templates
- [ ] Scheduling delayed messages

## Next Steps

Once configured, you can:
1. Send notifications from AI agents
2. Create automated alerts for system events
3. Build workflow integrations
4. Set up scheduled notifications
5. Integrate with monitoring systems

## Support

For issues or questions:
- Check WeChat Work Robot docs: https://developer.work.weixin.qq.com/document/path/91770
- Check container logs: `docker logs ai-mcp-server`
- Review this project's documentation

## Related Documentation

- LINE_SETUP_GUIDE.md - LINE messaging setup
- SMTP_CONFIGURATION_GUIDE.md - Email setup
- PROJECT_SUMMARY.md - Full feature overview

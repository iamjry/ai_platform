# LINE Messaging Setup Guide

## Overview
The AI Platform now supports sending messages to LINE users and groups through the `send_notification` MCP tool.

## Features
- ✅ Send messages to LINE users
- ✅ Send messages to LINE groups
- ✅ **Smart recipient detection** - Automatically determines whether to send to group or individual based on context
- ✅ Default recipient support (no need to specify recipient each time)
- ✅ Multiple recipients support
- ✅ Automatic fallback to default recipient

## Setup Instructions

### 1. Get LINE Channel Access Token

1. Go to [LINE Developers Console](https://developers.line.biz/console/)
2. Create a new provider (if you don't have one)
3. Create a new "Messaging API" channel
4. In the channel settings, go to "Messaging API" tab
5. Issue a **Channel Access Token** (long-lived)
6. Copy the token

### 2. Get LINE User ID or Group ID

#### For User ID:
1. Add your LINE bot as a friend
2. Send any message to the bot
3. Check the webhook logs or use LINE's [messaging-api-nodejs-sdk](https://github.com/line/line-bot-sdk-nodejs) to get the user ID
4. User IDs start with `U` (e.g., `Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

**Easy Method:**
- Use this test bot: Send a message to [@bot_id] and it will reply with your User ID

#### For Group ID:
1. Add your LINE bot to a group
2. The bot needs to be added by an admin
3. Get the group ID from webhook events
4. Group IDs start with `C` (chat) or `R` (room)

### 3. Configure Environment Variables

Update your `.env` file:

```bash
# LINE Messaging API Configuration
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token_here

# Default: Send to Group (change to User ID for personal messages)
LINE_DEFAULT_RECIPIENT_ID=Cxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Default Group ID

# Individual User ID (for personal messages when context mentions "me", "myself", etc.)
LINE_USER_ID=Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Your personal User ID
```

**Note**: The system uses `LINE_DEFAULT_RECIPIENT_ID` (Group) by default. When the AI detects personal keywords like "me", "myself", "remind me", it will automatically use `LINE_USER_ID` instead.

### 4. Restart Services

```bash
docker-compose up -d mcp-server
```

## Usage

### Smart Recipient Detection

The AI automatically determines whether to send to a group or individual based on your message context:

#### Send to Group (Default)
Keywords: "群組", "大家", "團隊", "所有人", "group", "everyone", "team"

Examples:
- "通知大家今晚會下雨" → Sends to default group
- "傳訊息到群組：會議改期" → Sends to default group
- "告訴團隊專案完成了" → Sends to default group

#### Send to Personal (your-username)
Keywords: "我", "自己", "個人", "私訊", "提醒我", "your-username", "jerry"

Examples:
- "提醒我明天下午開會" → Sends to personal (your-username)
- "傳給我自己" → Sends to personal (your-username)
- "私訊我這個連結" → Sends to personal (your-username)

#### Send to Specific Group/User
If you mention a specific group or person name:
- The AI will ask you to provide the LINE Group ID (starts with `C`) or User ID (starts with `U`)

### API Usage

#### Send to Default Recipient
```json
{
  "message": "Hello from AI Platform!",
  "channel": "line"
}
```

#### Send to Specific Recipients
```json
{
  "recipients": ["U1234567890abcdef", "C9876543210fedcba"],
  "message": "Hello everyone!",
  "channel": "line"
}
```

## Troubleshooting

### Error: "LINE_CHANNEL_ACCESS_TOKEN not configured"
- Make sure you've added the token to `.env`
- Restart mcp-server: `docker-compose restart mcp-server`

### Error: "No recipients provided and LINE_DEFAULT_RECIPIENT_ID not set"
- Add `LINE_DEFAULT_RECIPIENT_ID` to your `.env` file
- Make sure it's a valid LINE User ID or Group ID

### Error: "The property, 'to', in the request body is invalid"
- The recipient ID format is incorrect
- User IDs should start with `U`
- Group IDs should start with `C` or `R`
- Make sure there are no extra spaces in the ID

### Messages not received
1. Check if the bot is friends with the user (for user messages)
2. Check if the bot is in the group (for group messages)
3. Verify the Channel Access Token is correct
4. Check mcp-server logs: `docker logs ai-mcp-server --tail 50`

### Wrong recipient (group vs personal)
- If messages go to the wrong recipient, check your message context
- Use explicit keywords: "群組" for group, "我" or "提醒我" for personal
- Verify `LINE_DEFAULT_RECIPIENT_ID` and `LINE_USER_ID` in `.env` are correct

## Testing

Test from command line:
```bash
docker exec ai-mcp-server curl -X POST http://localhost:8000/tools/send_notification \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message", "channel": "line"}'
```

## API Reference

### Endpoint
`POST /tools/send_notification`

### Request Body
```json
{
  "recipients": ["string"],  // Optional - uses default if empty
  "message": "string",        // Required
  "channel": "line",          // Required
  "priority": "normal"        // Optional
}
```

### Response
```json
{
  "notification_id": "NOTIF-20251028100912",
  "channel": "line",
  "recipients": ["U1234567890abcdef"],
  "results": [
    {
      "recipient": "U1234567890abcdef",
      "status": "sent",
      "status_code": 200
    }
  ],
  "priority": "normal",
  "sent_at": "2025-10-28T10:09:12.821782"
}
```

## Security Notes

- ⚠️ Never commit your LINE_CHANNEL_ACCESS_TOKEN to git
- ⚠️ Keep your `.env` file private
- ⚠️ The token has full access to send messages on behalf of your bot
- ✅ Rotate your token periodically for security

## Next Steps

Once configured, you can:
1. Send notifications from AI agents
2. Create automated alerts
3. Build workflow integrations
4. Set up scheduled notifications

## Technical Implementation

### Smart Recipient Detection Logic

The system uses different approaches for different AI models:

#### For Claude/GPT (Function Calling Models)
- Enhanced system prompt guides the AI to analyze context and set recipients appropriately
- AI understands semantic meaning and can distinguish between group/personal messages
- Implementation: `services/agent-service/main.py:564-594`

#### For Qwen/Local Models (Fallback Mode)
- Pattern matching with keyword detection
- Removes recipient keywords from message content to avoid sending "群組 今天會下雨" instead of "今天會下雨"
- Implementation: `services/agent-service/main.py:242-297`

### Key Code Locations
- **Agent Service**: `services/agent-service/main.py`
  - System prompt: Lines 564-594
  - Fallback detection: Lines 242-297
  - Response formatting: Lines 505-518

- **MCP Server**: `services/mcp-server/main.py`
  - LINE API integration
  - Default recipient handling

- **Environment Config**: `.env`
  - `LINE_CHANNEL_ACCESS_TOKEN`: Bot access token
  - `LINE_DEFAULT_RECIPIENT_ID`: Default group ID
  - `LINE_USER_ID`: Personal user ID (hardcoded in fallback: Ud45d50ec4f060587d3a42c38e67a6008)

### Recipient Priority Logic
1. Personal keywords ("我", "提醒我") → Use `LINE_USER_ID` (Ud45d50ec4f060587d3a42c38e67a6008)
2. Group keywords ("群組", "大家") → Use `LINE_DEFAULT_RECIPIENT_ID` (empty array)
3. No clear indicator → Default to group (empty array)

## Support

For issues or questions:
- Check LINE Messaging API docs: https://developers.line.biz/en/docs/messaging-api/
- Check container logs: `docker logs ai-mcp-server`
- Review this project's documentation

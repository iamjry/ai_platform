# LINE Messaging Setup Guide

## Overview
The AI Platform now supports sending messages to LINE users and groups through the `send_notification` MCP tool.

## Features
- ✅ Send messages to LINE users
- ✅ Send messages to LINE groups
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
LINE_DEFAULT_RECIPIENT_ID=Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Your Line User ID or Group ID
```

### 4. Restart Services

```bash
docker-compose up -d mcp-server
```

## Usage

### Send to Default Recipient
```json
{
  "message": "Hello from AI Platform!",
  "channel": "line"
}
```

### Send to Specific Recipients
```json
{
  "recipients": ["U1234567890abcdef", "C9876543210fedcba"],
  "message": "Hello everyone!",
  "channel": "line"
}
```

### Using from Agent/Chat
Simply ask the AI:
- "Send a LINE message saying 'Meeting starts in 10 minutes'"
- "Notify the team on LINE about the deployment"

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

## Support

For issues or questions:
- Check LINE Messaging API docs: https://developers.line.biz/en/docs/messaging-api/
- Check container logs: `docker logs ai-mcp-server`
- Review this project's documentation

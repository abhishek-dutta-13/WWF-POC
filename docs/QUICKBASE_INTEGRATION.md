# Quickbase Integration Guide

This document explains the Quickbase integration for WWF Learning Content Generator API.

## Overview

The API automatically pushes generated content directly to Quickbase tables:
- **MCQs** → Table `bvxbt7fyw` 
- **Microlearning** → Table `bvxji8seh`

No manual Quickbase API calls needed - it's all automated!

---

## Configuration

### Required Environment Variables

```env
QUICKBASE_API_ENDPOINT=https://api.quickbase.com/v1/records
QUICKBASE_REALM_HOSTNAME=accentureglobaldeliverytraining.quickbase.com
QUICKBASE_USER_TOKEN=your_quickbase_user_token
QUICKBASE_TABLE_ID=bvxbt7fyw  # MCQ table
QUICKBASE_MICROLEARNING_TABLE_ID=bvxji8seh  # Microlearning table
```

---

## API Endpoints

### 1. Generate MCQs + Push to Quickbase

**Endpoint:** `POST /generate-mcqs-quickbase`

**Request:**
```json
{
  "CourseID": "001"
}
```

**What Happens:**
1. Generates 30 MCQ questions
2. Transforms to Quickbase format
3. Pushes to table `bvxbt7fyw`
4. Returns both content and push status

**Response:**
```json
{
  "mcqs": { ... },
  "quickbase_push": {
    "success": true,
    "records_pushed": 30,
    "table_id": "bvxbt7fyw"
  }
}
```

---

### 2. Generate Microlearning + Push to Quickbase

**Endpoint:** `POST /generate-microlearning-quickbase`

**Request:**
```json
{
  "CourseID": "002"
}
```

**What Happens:**
1. Generates microlearning modules (4-6 chapters)
2. Transforms to Quickbase format
3. Pushes to table `bvxji8seh`
4. Returns both content and push status

**Response:**
```json
{
  "microlearning_modules": { ... },
  "quickbase_push": {
    "success": true,
    "records_pushed": 20,
    "table_id": "bvxji8seh"
  }
}
```

## Quickbase Field Mappings

### MCQ Table (bvxbt7fyw)

Each MCQ question creates **one record** with these fields:

| Field ID | Field Name | Type | Example |
|----------|------------|------|---------|
| 19 | Course ID | Text | "001" |
| 8 | Set Number | Number | 1 |
| 10 | Question No | Number | 1 |
| 18 | Question | Text | "What is circular economy?" |
| 11 | Option A | Text | "Recycling materials" |
| 12 | Option B | Text | "Eliminate waste" |
| 13 | Option C | Text | "Reduce employment" |
| 14 | Option D | Text | "Single-use products" |
| 15 | Correct Answer | Text | "B" |
| 16 | Explanation | Rich Text | "The circular economy aims to..." |

**Records per Course:** 30 MCQs

---

### Microlearning Table (bvxji8seh)

Each micro-content creates **one record** with these fields:

| Field ID | Field Name | Type | Example |
|----------|------------|------|---------|
| 12 | Course ID | Text | "001" |
| 20 | Micro Content ID | Text | "MC-001" |
| 8 | Language | Text | "English" |
| 6 | Chapter | Text | "Introduction to Circular Economy" |
| 7 | Content | Rich Text | "The circular economy represents..." (250-400 words) |

**Records per Course:** 15-25 (varies based on chapters/content)

---

## Verifying Quickbase Push

### Check Response
```json
{
  "quickbase_push": {
    "success": true,
    "records_pushed": 30,
    "table_id": "bvxbt7fyw"
  }
}
```

- `success: true` - Push succeeded
- `success: false` - Push failed (check error message)
- `records_pushed` - Number of records added to Quickbase

### Common Issues

**401 Unauthorized:**
- Invalid `QUICKBASE_USER_TOKEN`
- Token expired
- Solution: Generate new token in Quickbase

**403 Forbidden:**
- User doesn't have write permissions to table
- Solution: Grant write access in Quickbase

**400 Bad Request:**
- Invalid field mapping
- Missing required fields
- Solution: Check field IDs match your Quickbase table

---

## Getting Quickbase Credentials

### 1. User Token

1. Log into Quickbase
2. Click profile icon → **My Preferences**
3. Navigate to **Manage User Tokens**
4. Click **New User Token**
5. Name it (e.g., "WWF API Integration")
6. Copy the token → Add to `.env` as `QUICKBASE_USER_TOKEN`

### 2. Table IDs

**MCQ Table:**
- Open your MCQ table in Quickbase
- Look at URL: `quickbase.com/db/bvxbt7fyw`
- Table ID = `bvxbt7fyw`

**Microlearning Table:**
- Open your microlearning table in Quickbase  
- Look at URL: `quickbase.com/db/bvxji8seh`
- Table ID = `bvxji8seh`

### 3. Realm Hostname

- Your Quickbase URL: `https://accentureglobaldeliverytraining.quickbase.com`
- Realm Hostname = `accentureglobaldeliverytraining.quickbase.com`

---

## Security Notes

- **Never commit** `.env` file with tokens to Git
- **Rotate tokens** regularly
- **Use environment variables** in production (Render dashboard)
- **Limit token permissions** to specific tables only
- **Monitor usage** in Quickbase audit logs

---

**Last Updated:** April 7, 2026  
**API Version:** 2.0.0

---

## Architecture

### Separation of Concerns

The Quickbase integration is separated into its own module:

- **`quickbase_client.py`**: Handles all Quickbase API interactions
- **`mcq_api_service.py`**: Uses the client for pushing records

**Benefits**:
- ✅ Easy to test and maintain
- ✅ Reusable across different services
- ✅ Secure credential management
- ✅ Clean separation of concerns

---

## Error Handling

The API handles various error scenarios:

| Error | Status Code | Description |
|-------|-------------|-------------|
| Invalid CourseID | 400 | Course ID not in allowed list |
| Generation Failed | 500 | MCQ generation error |
| Push Failed | 500 | Quickbase API error |
| Missing Credentials | 500 | Quickbase token/config missing |

---

## Example Workflow

1. **Generate Only** (for review):
   ```bash
   POST /generate-mcqs-quickbase
   # Review the output
   # Manually push to Quickbase if satisfied
   ```

2. **Generate + Push** (automated):
   ```bash
   POST /generate-and-push-mcqs-quickbase
   # MCQs are generated and pushed automatically
   ```

---

## Rate Limiting

- MCQs are generated in **batches of 10**
- **61-second delay** between batches to comply with API limits
- Total generation time for 30 questions: ~2-3 minutes

---

## Support

For issues or questions:
- Check logs for detailed error messages
- Verify Quickbase credentials are correct
- Ensure target table ID matches your Quickbase setup

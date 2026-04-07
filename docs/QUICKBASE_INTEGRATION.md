# Quickbase Integration Guide

This document explains how to use the Quickbase integration features of the MCQ Generator API.

## Overview

The MCQ API now supports direct integration with Quickbase, allowing you to:
1. Generate MCQ questions
2. Format them for Quickbase
3. Push them directly to your Quickbase table

## Endpoints

### 1. `/generate-mcqs-quickbase` (Format Only)
Generates MCQs and returns them in Quickbase format, but does NOT push to Quickbase.

**Use Case**: When you want to review the data before pushing, or handle the push yourself.

**Request**:
```json
POST /generate-mcqs-quickbase
{
  "CourseID": "001"
}
```

**Response**: Quickbase-formatted payload (ready to push)

---

### 2. `/generate-and-push-mcqs-quickbase` (Generate + Push)
Generates MCQs **AND** automatically pushes them to Quickbase.

**Use Case**: One-click generation and deployment to Quickbase.

**Request**:
```json
POST /generate-and-push-mcqs-quickbase
{
  "CourseID": "001"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Generated and pushed 30 MCQ records",
  "course_id": "001",
  "category": "Circular Economy & Waste Reduction",
  "records_pushed": 30,
  "quickbase_response": { ... }
}
```

---

## Quickbase Field Mappings

| Field ID | Field Name | Description | Example |
|----------|------------|-------------|---------|
| **19** | course_id | Course identifier | "001" |
| **8** | set_number | Set number (always 1) | 1 |
| **10** | question_no | Question number | "1", "2", ... "30" |
| **18** | question | Question text | "What is circular economy?" |
| **11** | option_a | Option A | "Recycling materials" |
| **12** | option_b | Option B | "Linear production" |
| **13** | option_c | Option C | "Waste disposal" |
| **14** | option_d | Option D | "Incineration" |
| **15** | correct_answer | Correct option letter | "A" |
| **16** | explanation | Why this answer is correct | "Option A is correct because..." |

---

## Configuration

### Environment Variables

Add these to your `.env` file (or set in your deployment environment):

```env
# Quickbase API Configuration
QUICKBASE_API_ENDPOINT="https://api.quickbase.com/v1/records"
QUICKBASE_REALM_HOSTNAME="yourcompany.quickbase.com"
QUICKBASE_USER_TOKEN="your_user_token_here"
QUICKBASE_TABLE_ID="your_table_id_here"
```
QUICKBASE_TABLE_ID="bvxbt7fyw"
```

### Getting Your Quickbase User Token

1. Log into Quickbase
2. Click your profile icon → **My Preferences**
3. Navigate to **Manage User Tokens**
4. Click **New User Token**
5. Copy the token and add to your `.env` file

---

## Testing with Postman

### Headers
```
QB-Realm-Hostname: yourcompany.quickbase.com
Authorization: QB-USER-TOKEN your_quickbase_user_token_here
Content-Type: application/json
```

### Request Body
```json
{
  "CourseID": "003"
}
```

Replace `"003"` with any valid course ID:
- `"001"` - Circular Economy & Waste Reduction
- `"002"` - Sustainability Strategy & Compliance
- `"003"` - Sustainable Agriculture & Natural Resources

---

## API Security

### Optional API Key Authentication

For added security, set an API key in `.env`:

```env
API_KEY="your-secret-key-here"
```

Then include it in your requests:

```
X-API-Key: your-secret-key-here
```

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

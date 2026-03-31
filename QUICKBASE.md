# QUICKBASE INTEGRATION GUIDE

## How to Connect Quickbase to MCQ Generator API

### What Quickbase Sends
```json
POST https://your-app.onrender.com/generate-mcqs

{
  "category": "agriculture"
}
```

Valid categories: `agriculture`, `climate`, `renewable_energy`

---

### Quickbase Pipeline Configuration

**Step 1: HTTP Request**
- Method: `POST`
- URL: `https://your-app.onrender.com/generate-mcqs`
- Headers:
  - `Content-Type: application/json`
  - `X-API-Key: your-secret-key` (if API_KEY is set)
- Body: `{"category": "{{category_field}}"}`
- Timeout: `180 seconds` (includes Render cold start)

**Step 2: Parse Response**
The API returns this structure:
```json
{
  "status": "success",
  "category": "agriculture",
  "mcq_sets": [
    {
      "set_number": 1,
      "questions": [
        {
          "question": "Question text?",
          "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
          "correct_answer": "B",
          "explanation": "Explanation text"
        }
        // 4 more questions per set
      ]
    }
    // 2 more sets (total 3)
  ],
  "total_sets": 3
}
```

**Step 3: Store in Quickbase**
Loop through `mcq_sets` and create records in your MCQ tables.

---

### Recommended Quickbase Table Structure

**Table 1: MCQ_Requests**
- Request_ID (Key)
- Category (agriculture/climate/renewable_energy)  
- Status (pending/completed/failed)
- Created_Date

**Table 2: MCQ_Sets**
- Set_ID (Key)
- Request_ID (related to MCQ_Requests)
- Set_Number (1, 2, or 3)

**Table 3: MCQ_Questions**
- Question_ID (Key)
- Set_ID (related to MCQ_Sets)
- Question_Text
- Option_A, Option_B, Option_C, Option_D
- Correct_Answer (A/B/C/D)
- Explanation

---

### Testing

Test the API first:
```bash
curl https://your-app.onrender.com/health

curl -X POST "https://your-app.onrender.com/generate-mcqs" \
  -H "Content-Type: application/json" \
  -d '{"category":"agriculture"}'
```

Or use the test script:
```bash
cd src
python test_quickbase_integration.py
```

---

### Troubleshooting

**Timeout**: Set Pipeline timeout to 180 seconds (Render free tier has cold start)  
**401 Error**: Check X-API-Key header matches your API_KEY  
**400 Error**: Verify category is exactly: agriculture, climate, or renewable_energy  
**CORS**: Set ALLOWED_ORIGINS to your Quickbase domain in Render environment

---

See [README.md](README.md) for full deployment guide.

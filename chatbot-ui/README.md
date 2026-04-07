# WWF Chatbot UI

## 📁 What's in This Folder

This folder contains **2 HTML pages**:

1. **`launcher.html`** - Test page to simulate Quickbase button
   - Fill in user details (ID, name, education, location)
   - Click "Launch Chatbot" to open chat with those details
   - **Access at:** `/launcher`

2. **`index.html`** - Actual chatbot interface
   - Beautiful chat UI with WWF branding
   - Real-time messaging, sources, PDF export
   - **Access at:** `/chat` (with user parameters)

---

## 🎨 Clean, Modern Chat Interface

A beautiful, responsive chat interface for the WWF Sustainability Assistant with:
- ✅ Real-time messaging
- ✅ Source citations
- ✅ PDF export downloads
- ✅ Agent routing indicators (RAG, Web Search, Hybrid)
- ✅ WWF brand colors
- ✅ Mobile responsive
- ✅ Smooth animations

---

## 🚀 Quick Start

### Method 1: Test with Launcher Page (Easiest!)

**After deploying to Render:**

1. **Open the launcher:**
   ```
   https://your-app.onrender.com/launcher
   ```

2. **Fill in user details** (or use a quick test scenario)

3. **Click "Launch Chatbot"** - Opens chat in new tab with your details!

This simulates exactly how Quickbase will work!

### Method 2: Test Locally (Development)

1. **Start your FastAPI backend:**
   ```bash
   cd WWF
   python run_server.cmd
   ```
   Backend runs at: `http://127.0.0.1:8000`

2. **Open the chat UI:**
   - Simply open `chatbot-ui/index.html` in your browser
   - Or use a local server:
     ```bash
     cd chatbot-ui
     python -m http.server 3000
     ```
   - Navigate to: `http://localhost:3000`

3. **Test with user context:**
   Add URL parameters to simulate Quickbase payload:
   ```
   http://localhost:3000?user_id=user123&name=John%20Doe&education=Environmental%20Science&location=California
   ```

### Method 2: Deploy to Vercel (Production)

1. **Create Vercel account:** https://vercel.com

2. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

3. **Deploy:**
   ```bash
   cd chatbot-ui
   vercel
   ```

4. **Update API URL:**
   - After deploying backend to Render, edit `index.html` line 121:
   ```javascript
   const API_BASE_URL = 'https://your-render-app.onrender.com';
   ```

---

## 🔗 Integration with Quickbase

### Quickbase Button Configuration

Your Quickbase button should open a URL with user parameters:

```
https://your-chat-ui.vercel.app?user_id={user_id}&name={name}&education={education}&location={location}
```

**Example:**
```
https://wwf-chat.vercel.app?user_id=12345&name=John%20Doe&education=Business&location=New%20York
```

### Field Mappings

| Quickbase Field | URL Parameter | Example |
|----------------|---------------|---------|
| User ID | `user_id` | `user_id=12345` |
| Full Name | `name` | `name=John%20Doe` |
| Education | `education` | `education=Environmental%20Science` |
| Location | `location` | `location=California,%20USA` |

**Note:** Use URL encoding for spaces (`%20`) and special characters.

---

## 🎯 Features

### 1. **Smart Agent Routing**
Visual indicators show which agent answered:
- 📚 **Knowledge Base** (RAG) - Blue badge
- 🌐 **Web Search** - Green badge
- 🔀 **Hybrid** - Purple badge
- 📄 **PDF Export** - Orange badge

### 2. **Source Citations**
Every response shows sources:
- Document excerpts from WWF knowledge base
- Web search results with URLs
- Clickable links to original sources

### 3. **PDF Export**
- User asks: "Can you export this chat as PDF?"
- System generates PDF with conversation
- Download button appears in chat
- PDF includes WWF branding

### 4. **User Personalization**
- Header shows user name and location
- Responses personalized based on user context
- Region-specific advice when relevant

### 5. **Modern Design**
- Clean, minimalist interface
- WWF brand colors (Orange #FF6200, Green #2C5F2D)
- Smooth animations
- Responsive (works on mobile, tablet, desktop)
- Custom scrollbar styling

---

## 🛠️ Customization

### Change API URL

Edit line 121 in `index.html`:

```javascript
const API_BASE_URL = 'https://your-backend-url.com';
```

### Change Colors

Edit the Tailwind config (lines 19-25):

```javascript
wwf-orange: '#FF6200',  // Main brand color
wwf-black: '#000000',   // Text color
wwf-green: '#2C5F2D',   // User message background
```

### Change Welcome Message

The welcome message comes from the backend (`ResponseAgent.generate_welcome_message()`).

To customize, edit: `src/chatbot/agents/response_agent.py`

---

## 📱 Responsive Design

The UI automatically adapts to screen sizes:

- **Desktop:** Full width (max 1280px)
- **Tablet:** Optimized layout
- **Mobile:** Stacked design, touch-friendly buttons

---

## 🐛 Troubleshooting

### Issue: "Failed to initialize session"

**Cause:** Backend not running or wrong API URL

**Solution:**
1. Ensure backend is running: `python run_server.cmd`
2. Check API_BASE_URL in `index.html` matches your backend URL
3. Check browser console (F12) for CORS errors

### Issue: CORS Error

**Cause:** Frontend and backend on different domains

**Solution:**
1. For local testing, ensure `ALLOWED_ORIGINS="*"` in backend `.env`
2. For production, add your Vercel URL to `ALLOWED_ORIGINS`:
   ```
   ALLOWED_ORIGINS="https://your-chat-ui.vercel.app"
   ```

### Issue: Messages not appearing

**Cause:** Network error or API endpoint mismatch

**Solution:**
1. Open browser console (F12) → Network tab
2. Check if requests to `/chatbot/message` succeed
3. Verify response status is 200

### Issue: Sources not displaying

**Cause:** Backend not returning sources correctly

**Solution:**
1. Check backend logs for RAG/Web Search agent errors
2. Verify ChromaDB has data: Collection count should be > 0
3. Check Tavily API key is valid

---

## 🎨 UI Components

### Header
- WWF panda icon
- App title
- User context (name, location)

### Message Bubbles
- User messages: Green background, right-aligned
- Assistant messages: White background, left-aligned
- Timestamps below each message

### Source Cards
- Numbered sources
- Document title
- Optional URL (for web sources)
- Excerpt preview
- Hover animation

### Input Area
- Multi-line textarea
- Send button
- Keyboard shortcuts (Enter to send, Shift+Enter for new line)
- Character count could be added

---

## 🚀 Deployment Checklist

Before deploying:

- [ ] Test locally with backend running
- [ ] Verify all features work (messaging, sources, PDF)
- [ ] Test with different user contexts (change URL params)
- [ ] Update `API_BASE_URL` to production backend URL
- [ ] Deploy backend to Render first
- [ ] Deploy UI to Vercel or serve from FastAPI
- [ ] Test Quickbase button integration
- [ ] Verify CORS settings allow your frontend domain

---

## 📚 Tech Stack

- **React 18** - UI framework (via CDN)
- **Tailwind CSS** - Styling
- **Babel** - JSX transpilation
- **Modern JavaScript** - Fetch API, async/await
- **No build step required!** - Everything runs in browser

---

## 🔄 Future Enhancements

Potential improvements:
- [ ] Session history sidebar (show past conversations)
- [ ] Dark mode toggle
- [ ] Voice input
- [ ] Export to Word/Excel
- [ ] Share conversation link
- [ ] Feedback buttons (👍 👎)
- [ ] Copy message to clipboard
- [ ] Search within conversation
- [ ] User avatar customization

---

## 📄 License

Part of the WWF Learning Content Generator project.

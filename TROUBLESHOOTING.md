# Troubleshooting Guide - Dashboard Connection Issue

## Problem
Frontend shows error: `DashboardApiError: No response from server`

## Root Cause
The error "No response from server" typically means:
1. **Backend is not running** (most common)
2. Backend is running on a different port
3. CORS is blocking the request
4. Network/firewall issue

## Solution Steps

### 1. Check if Backend is Running

**Start the backend server:**

```bash
cd backend
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

You should see output like:
```
============================================================
🚀 Starting FreedomAIAdmin API Server
============================================================
📍 Registered routes:
  GET    /
  GET    /dashboard/counts
  GET    /dashboard/health
  GET    /dashboard/stats
  ...
============================================================
✨ Server ready to accept connections
============================================================
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 2. Verify Backend is Accessible

Open your browser and go to:
- **Swagger UI**: http://localhost:8000/docs
- **Dashboard Health**: http://localhost:8000/dashboard/health

If you see JSON response `{"status": "healthy", ...}`, the backend is working!

### 3. Check Frontend Configuration

**Verify `.env` file in frontend directory:**

```bash
cd frontend
cat .env
```

Should contain:
```
VITE_API_URL=http://localhost:8000
```

### 4. Test Dashboard API Manually

**With browser console (while logged in):**

```javascript
// In browser console
fetch('http://localhost:8000/dashboard/stats', {
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('access_token')
  }
})
.then(r => r.json())
.then(console.log)
```

### 5. Check Browser Console Logs

With the enhanced logging, you should now see:

```
[Dashboard API] Fetching dashboard stats...
  endpoint: "/dashboard/stats"
  params: {include_recent: true, recent_limit: 10}
  baseURL: "http://localhost:8000"
```

If there's an error, you'll see detailed error information.

### 6. Check Backend Logs

When frontend makes a request, backend should log:

```
INFO:     → GET /dashboard/stats
INFO:     ← GET /dashboard/stats Status: 200 Time: 0.245s
```

If you don't see this, the request isn't reaching the backend.

## Common Issues & Fixes

### Issue: "ECONNREFUSED"
**Cause**: Backend is not running
**Fix**: Start the backend server (see step 1)

### Issue: 401 Unauthorized
**Cause**: Not logged in or token expired
**Fix**:
1. Log out and log in again
2. Check `localStorage.getItem('access_token')` in browser console

### Issue: 403 Forbidden
**Cause**: User doesn't have required role/permissions
**Fix**:
1. Check user role in database
2. Verify user has `company_id` or `department_id` set correctly

### Issue: CORS Error
**Cause**: Frontend URL not in `ALLOWED_ORIGINS`
**Fix**: Check `backend/src/settings.py` - add your frontend URL

### Issue: 500 Internal Server Error
**Cause**: Backend database or logic error
**Fix**: Check backend console for detailed error traceback

## Quick Diagnostic Commands

```bash
# Check if backend is running
curl http://localhost:8000/

# Check dashboard health (no auth required)
curl http://localhost:8000/dashboard/health

# Check with authentication
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/dashboard/stats
```

## Still Not Working?

1. **Restart both servers** (frontend and backend)
2. **Clear browser cache** and localStorage
3. **Check firewall/antivirus** - may be blocking port 8000
4. **Try different browser** to rule out browser issues
5. **Check MongoDB connection** - backend needs working MongoDB

## Enhanced Logging

The code now includes:
- ✅ Backend request/response logging
- ✅ Frontend detailed error logging
- ✅ Route registration logging on startup
- ✅ Timing information for each request

Check both console outputs for detailed diagnostic information!

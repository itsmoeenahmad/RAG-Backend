# Architecture: Async Upload System

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT APPLICATION                          │
│                    (Web / Mobile / Desktop)                         │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ 1. POST /upload
                                  │    - PDF file
                                  │    - user_id
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        FASTAPI BACKEND                              │
│                      (Koyeb Serverless)                             │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │             POST /upload Endpoint                            │  │
│  │  • Validates PDF                                             │  │
│  │  • Generates job_id (UUID)                                   │  │
│  │  • Saves temp file                                           │  │
│  │  • Creates job record in MongoDB                             │  │
│  │  • Spawns BackgroundTask                                     │  │
│  │  • Returns 200 OK + job_id (< 500ms) ←─────── IMMEDIATE     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │         GET /upload/status/{job_id} Endpoint                │  │
│  │  • Queries MongoDB upload_jobs collection                    │  │
│  │  • Returns: status, progress_percent, chunks, errors         │  │
│  │  • No processing, just reads state                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │         Background Task: process_pdf_upload()               │  │
│  │                                                              │  │
│  │  Step 1: Extract PDF text                                   │  │
│  │    └─→ update_job_status(progress=10%)                      │  │
│  │                                                              │  │
│  │  Step 2: Split into chunks                                  │  │
│  │    └─→ update_job_status(progress=30%)                      │  │
│  │                                                              │  │
│  │  Step 3: Generate embeddings + Batch upsert                 │  │
│  │    ┌─→ Batch 1 (chunks 1-100)                               │  │
│  │    ├─→ Batch 2 (chunks 101-200)                             │  │
│  │    ├─→ Batch 3 (chunks 201-300)                             │  │
│  │    └─→ ...                                                   │  │
│  │    └─→ update_job_status(progress=60%, 90%)                 │  │
│  │                                                              │  │
│  │  Step 4: Mark completed                                     │  │
│  │    └─→ update_job_status(                                   │  │
│  │          status='completed',                                │  │
│  │          progress=100%,                                     │  │
│  │          inserted_chunks=N                                  │  │
│  │        )                                                     │  │
│  │                                                              │  │
│  │  Cleanup: Delete temp file                                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
         │                              │                    │
         │                              │                    │
         ▼                              ▼                    ▼
┌─────────────────┐      ┌──────────────────────┐   ┌──────────────┐
│   MongoDB       │      │     Qdrant Cloud     │   │   Google     │
│   Atlas         │      │   (Vector Store)     │   │   Gemini     │
├─────────────────┤      ├──────────────────────┤   ├──────────────┤
│ • upload_jobs   │      │ • user_A_data        │   │ • LLM        │
│   - job_id      │      │ • user_B_data        │   │ • Embeddings │
│   - status      │      │ • user_C_data        │   └──────────────┘
│   - progress    │      │   (Collections)      │
│   - chunks      │      │                      │
│   - errors      │      │ Batch Upserts:       │
│                 │      │ 100 chunks each      │
│ • chats         │      └──────────────────────┘
│   - chat history│
└─────────────────┘
```

---

## Request Flow Comparison

### ❌ BEFORE (Synchronous - Times Out)

```
Client                    Edge Proxy              FastAPI              Qdrant
  │                           │                       │                   │
  │──── POST /upload ────────►│                       │                   │
  │                           │──── Forward ─────────►│                   │
  │                           │                       │                   │
  │                           │                       │─ Extract PDF      │
  │                           │                       │─ Split chunks     │
  │                           │                       │─ Generate embeds  │
  │                           │                       │                   │
  │                           │◄────── 90s ──────────►│                   │
  │                           │       Still            │                   │
  │                           │      waiting...        │                   │
  │                           │                        │                   │
  │                           │◄─── 120s TIMEOUT ─────┤                   │
  │◄──── 502 Error ──────────┤                        │                   │
  │                           │                        │                   │
  │      Client sees error    │                        │── Upsert all ────►│
  │      but backend          │                        │   (succeeds)      │
  │      continues!           │                        │◄── Success ──────┤
  │                           │                        │                   │
  │                           │                        │  FastAPI logs:    │
  │                           │                        │  200 OK           │
  │                           │                        │  (but client      │
  │                           │                        │   saw 502!)       │
```

**Problem**: Edge kills connection at 100-120s while FastAPI runs for 180-300s

---

### ✅ AFTER (Asynchronous - No Timeout)

```
Client                    Edge Proxy              FastAPI              MongoDB        Qdrant
  │                           │                       │                   │              │
  │──── POST /upload ────────►│                       │                   │              │
  │                           │──── Forward ─────────►│                   │              │
  │                           │                       │                   │              │
  │                           │                       │─ Validate         │              │
  │                           │                       │─ Generate job_id  │              │
  │                           │                       │─ Save temp file   │              │
  │                           │                       │                   │              │
  │                           │                       │──── Create job ──►│              │
  │                           │                       │◄─── Success ──────┤              │
  │                           │                       │                   │              │
  │                           │                       │─ Spawn background │              │
  │                           │                       │   task            │              │
  │                           │                       │                   │              │
  │◄──── 200 OK + job_id ────┤◄──── Response ────────┤                   │              │
  │      (< 500ms)            │                       │                   │              │
  │                           │                       │                   │              │
  │                           │                       ├─ Background Task: │              │
  │                           │                       │   Extract PDF     │              │
  │                           │                       │──── Update 10% ──►│              │
  │                           │                       │                   │              │
  │                           │                       │   Split chunks    │              │
  │                           │                       │──── Update 30% ──►│              │
  │                           │                       │                   │              │
  │─ GET /status/{job_id} ───►│                       │                   │              │
  │                           │──── Forward ─────────►│                   │              │
  │                           │                       │──── Query job ────►│              │
  │                           │                       │◄─── 30% ──────────┤              │
  │◄─── {progress: 30%} ─────┤◄──── Response ────────┤                   │              │
  │                           │                       │                   │              │
  │  (Client polls            │                       │   Generate embeds │              │
  │   every 3 seconds)        │                       │   Batch 1-100 ────────────────────►│
  │                           │                       │   Batch 101-200 ──────────────────►│
  │                           │                       │   ...             │              │
  │                           │                       │──── Update 60% ──►│              │
  │                           │                       │──── Update 90% ──►│              │
  │                           │                       │                   │              │
  │─ GET /status/{job_id} ───►│                       │                   │              │
  │◄─── {progress: 90%} ─────┤                       │                   │              │
  │                           │                       │                   │              │
  │                           │                       │   Complete        │              │
  │                           │                       │──── Update 100% ──►│              │
  │                           │                       │     status=       │              │
  │                           │                       │     'completed'   │              │
  │                           │                       │                   │              │
  │─ GET /status/{job_id} ───►│                       │                   │              │
  │◄─ {status: completed} ────┤                       │                   │              │
  │                           │                       │                   │              │
  │   ✓ Success!              │                       │                   │              │
```

**Solution**: Immediate response + background processing + status polling

---

## Component Responsibilities

### FastAPI Endpoint Layer
- **POST /upload**: Validate, create job, return immediately
- **GET /upload/status/{job_id}**: Read-only status queries
- **POST /chat**: RAG query processing
- **DELETE /collection**: Collection management

### Background Processing Layer
- **process_pdf_upload()**: Async document ingestion
  - PDF text extraction
  - Document chunking
  - Embedding generation
  - Batched Qdrant upserts
  - Progress tracking
  - Error handling & cleanup

### Service Layer
- **VectorStore**: Qdrant operations with batching
- **ChatService**: LLM interactions
- **DBService**: MongoDB CRUD (jobs + chat history)
- **PDFLoader**: Document parsing

### Data Layer
- **MongoDB**: Job tracking + chat history
- **Qdrant**: Vector embeddings (per-user collections)
- **Gemini API**: Embeddings + LLM completions

---

## Status State Machine

```
┌─────────────────────────────────────────────────────────────────┐
│                        Job Lifecycle                            │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────┐
    │  queued  │  ← Initial state (job created, not started)
    └────┬─────┘
         │
         │ Background task starts
         ▼
    ┌─────────────┐
    │ processing  │  ← Extracting, embedding, upserting
    └──┬────────┬─┘
       │        │
       │        │ Error occurs
       │        ▼
       │   ┌─────────┐
       │   │ failed  │  ← Terminal state (error_message set)
       │   └─────────┘
       │
       │ All chunks uploaded
       ▼
    ┌───────────┐
    │ completed │  ← Terminal state (inserted_chunks set)
    └───────────┘
```

**Progress Updates**:
- `queued`: 0%
- `processing`: 10% → 30% → 60% → 90%
- `completed`: 100%
- `failed`: Frozen at last update

---

## Batch Processing Strategy

### Why Batch?

❌ **Without Batching (2255 chunks)**:
```python
# Single upsert operation
vector_store.add_documents(all_2255_docs)
# Problems:
# - High memory usage (all embeddings in RAM)
# - No progress tracking
# - All-or-nothing (one failure = total loss)
# - Potential API rate limit hit
```

✅ **With Batching (100 chunks/batch)**:
```python
for i in range(0, 2255, 100):
    batch = docs[i:i+100]
    vector_store.add_documents(batch)
    update_progress()
# Benefits:
# - Low memory footprint
# - Granular progress (23 batches)
# - Partial success possible
# - Respects rate limits
# - Better error recovery
```

### Batch Size Recommendations

| Chunk Count | Batch Size | Batches | Estimated Time |
|-------------|-----------|---------|----------------|
| < 100       | 50        | 1-2     | 10-20s         |
| 100-500     | 100       | 1-5     | 30-60s         |
| 500-1000    | 100       | 5-10    | 60-120s        |
| 1000-3000   | 100       | 10-30   | 120-300s       |
| > 3000      | 150       | 20+     | 300+s          |

**Current Default**: 100 chunks/batch (configurable in `add_documents()`)

---

## Error Handling Flow

```
Background Task Error Handling:

try:
    ┌─────────────────────────────────┐
    │ update_job_status('processing') │
    │ progress=10%                    │
    └─────────────────────────────────┘
    
    ┌─────────────────────────────────┐
    │ Extract PDF text                │
    └─────────────────────────────────┘
    
    ┌─────────────────────────────────┐
    │ update_job_status('processing') │
    │ progress=30%                    │
    └─────────────────────────────────┘
    
    ┌─────────────────────────────────┐
    │ Batch process → Qdrant          │
    │ (may fail here)                 │
    └─────────────────────────────────┘

except Exception as e:
    ┌─────────────────────────────────┐
    │ update_job_status(              │
    │   status='failed',              │
    │   error_message=str(e)          │
    │ )                               │
    └─────────────────────────────────┘
    
    ┌─────────────────────────────────┐
    │ Log full traceback              │
    └─────────────────────────────────┘

finally:
    ┌─────────────────────────────────┐
    │ Cleanup temp file               │
    └─────────────────────────────────┘
```

**Client sees failed status and can retry with new upload**

---

## Performance Characteristics

### Response Times

| Operation | Before | After | Improvement |
|-----------|--------|-------|-------------|
| Upload endpoint | 120-300s | < 0.5s | **600x faster** |
| Status check | N/A | 10-50ms | New feature |
| Total processing | Same | Same | No change |

### Resource Usage

| Resource | Before | After | Change |
|----------|--------|-------|--------|
| HTTP connection | Open 2-4 min | Open < 1s | 99% reduction |
| Edge timeouts | Frequent | Zero | Eliminated |
| Memory (per request) | 2255 chunks | 100 chunks | 95% reduction |
| Error recovery | None | Per-batch | Improved |

---

## Monitoring & Observability

### Key Metrics to Track

1. **Job Success Rate**: `completed / (completed + failed)`
2. **Average Processing Time**: Time from queued → completed
3. **Error Rate by Stage**: PDF extraction vs embedding vs upsert
4. **Active Jobs**: Count of jobs in `processing` state
5. **Stuck Jobs**: Jobs in `processing` > 10 minutes

### MongoDB Queries for Monitoring

```javascript
// Success rate (last 24h)
db.upload_jobs.aggregate([
  { $match: { created_at: { $gte: new Date(Date.now() - 86400000) } } },
  { $group: { _id: "$status", count: { $sum: 1 } } }
])

// Average processing time
db.upload_jobs.aggregate([
  { $match: { status: "completed" } },
  { $project: { 
      duration: { $subtract: ["$updated_at", "$created_at"] }
  }},
  { $group: { _id: null, avgMs: { $avg: "$duration" } } }
])

// Failed jobs with errors
db.upload_jobs.find({ 
  status: "failed" 
}).sort({ updated_at: -1 }).limit(10)
```

---

## Security Considerations

1. **Job ID as UUID**: Prevents enumeration attacks
2. **User isolation**: Job records linked to user_id
3. **Temp file cleanup**: Prevents disk filling
4. **No sensitive data in logs**: Only job_id and user_id logged
5. **Rate limiting** (future): Limit jobs per user per hour

---

**Architecture Version**: 1.0
**Last Updated**: January 31, 2026
**Status**: ✅ Production Ready

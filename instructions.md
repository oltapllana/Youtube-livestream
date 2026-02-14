"""
QUICK START GUIDE
-----------------

Follow these steps to get the project running:

## 1. Environment Setup

1. Install Python 3.9+ (if not already installed)
2. Create virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## 2. Required Dependencies

Add to requirements.txt:
```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.4.2
pydantic-settings==2.0.3
```

Install with:
```
pip install -r requirements.txt
```

## 3. Run the API Server

```
uvicorn app.main:app --reload --port 8000
```

Or in PowerShell:
```
$env:PYTHONPATH="."
python -m uvicorn app.main:app --reload --port 8000
```

API will be available at: http://localhost:8000
Swagger docs: http://localhost:8000/docs

## 4. Project Structure

```
app/
  ├── api/routes.py           → API endpoints (TODO)
  ├── services/               → Business logic (TODO)
  ├── models/                 → Data models
  ├── core/exceptions.py      → Custom exceptions
  └── utils/config.py         → Configuration
```

## 5. Implementation Order

### Phase 1: Models & API Structure
- [x] Create folder structure
- [x] Create configuration
- [x] Create request/response models
- [ ] Setup FastAPI server and test endpoints

### Phase 2: Instance Generator
- [ ] Create YouTube stream to channel mapping
- [ ] Implement instance JSON generation
- [ ] Validate generated JSON

### Phase 3: Algorithm Integration
- [ ] Implement algorithm execution
- [ ] File I/O handling
- [ ] Error handling

### Phase 4: API Implementation
- [ ] POST /api/schedule endpoint
- [ ] GET /api/schedule/{request_id} endpoint
- [ ] GET /api/status/{request_id} endpoint

### Phase 5: Testing & Polish
- [ ] Unit tests
- [ ] Integration tests
- [ ] Error handling
- [ ] Logging

## 6. Key Files to Build Next

1. **app/utils/file_handler.py**
   - Save/load JSON files
   - Handle file paths

2. **app/services/instance_generator.py**
   - Convert YouTube streams to programs
   - Create JSON instance structure

3. **app/api/routes.py**
   - Implement 3 main endpoints

4. **Update requirements.txt**
   - Add dependencies

## 7. Testing Endpoints

Once server is running, test with:

```bash
# Test health check
curl http://localhost:8000/health

# View API docs
curl http://localhost:8000/docs
```

## 8. YouTube Mapping Reference

Science/Tech Channels (IDs 0-9):
  0: NASA
  1: Crux
  2: Sen
  3: afarTV
  4: NASASpaceflight
  5: Dream Trips
  6: Interstellar News Hub
  7: The Financial Express
  8: Space Streams
  9: Frontiers of Infinity

Climate Channels (IDs 10-11):
  10: Interstellar News Hub (Climate)
  11: I love You Venice

---

Next Step: Run fastapi server and confirm it's working
"""


# TV-Like Scheduler from Live YouTube Streams

<table border="0">
 <tr>
    <td style="width:300px; vertical-align:middle; text-align:center;">
      <img src="https://upload.wikimedia.org/wikipedia/commons/e/e1/University_of_Prishtina_logo.svg" 
           alt="University Logo" 
           style="width:250px; height:auto;" />
    </td>
    <td style="vertical-align:middle; padding-left:20px;">
      <h2><strong>University of Prishtina</strong></h2>
      <h3>Faculty of Electrical and Computer Engineering</h3>
      <p>Master’s Program in Computer and Software Engineering</p>
      <p><strong>Professor:</strong> Dr. Techn. Kadri Sylejmani</p>
    </td>
 </tr>
</table>

---

##  Project Title
**Automatic Generation of TV-Like Schedules from Live YouTube Streams**

---

##  Project Overview

This project implements a **TV-style scheduling system** that automatically generates multi-channel program schedules using **live YouTube streams**.  
The system discovers or probes live streams, converts them into structured TV program blocks, and applies an **algorithmic scheduling approach** to create realistic television-like schedules that can be viewed and played back in a modern web interface.

The main purpose of the project is to simulate traditional TV programming by using live online streams as content sources.

---

##  Project Objectives

- Discover and validate live YouTube streams
- Extract stream metadata automatically
- Convert streams into TV-like program blocks
- Generate schedules for multiple virtual TV channels
- Provide a responsive and interactive web UI
- Support user preferences and filtering
- Demonstrate algorithmic scheduling techniques

---

##  System Architecture

The system follows a client–server architecture:
Frontend (Vue 3)
```
│
▼
REST API
│
▼
Backend (FastAPI)
│
▼
Stream Probing (yt-dlp)
│
▼
Scheduler (Beam Search)
│
▼
Schedule JSON
```

##  Frontend

### Technologies
- Vue 3
- Vite
- JavaScript, HTML, CSS

### Features
- Live stream video player
- “Now / Next” TV-style program bar
- Channel-based schedule visualization
- User preferences management
- Asynchronous schedule loading

### Responsibilities
- Sends scheduling requests to the backend
- Polls scheduling status
- Renders schedules and playback UI
- Stores and loads user preferences

---

##  Backend

### Technologies
- Python
- FastAPI
- yt-dlp
- Asynchronous background tasks

### Responsibilities
- Probe and validate live YouTube streams
- Fetch stream metadata (title, uploader, viewers, live status)
- Generate scheduling instances
- Execute scheduling algorithm
- Store and return schedule results via REST API

---

##  API Endpoints

| Method | Endpoint | Description |
|------|---------|-------------|
| POST | `/api/schedule` | Create a new schedule (async) |
| POST | `/api/schedule/sync` | Create a schedule synchronously |
| GET | `/api/schedule/{id}` | Retrieve generated schedule |
| GET | `/api/status/{id}` | Check scheduling status |
| GET | `/api/streams` | Retrieve available streams |
| GET | `/api/preferences` | Load user preferences |
| POST | `/api/preferences` | Save user preferences |

---

##  Data Sources

### Stream Sources
- Curated list of predefined YouTube live streams
- Optional discovery of additional live streams using `yt-dlp`

### Metadata Extraction

Stream metadata is extracted using:

```bash
python -m yt_dlp --dump-json <youtube_url>
```

## Scheduling Process

The scheduling workflow follows these steps:

1. The frontend sends a scheduling request containing the desired time window and filters.
2. The backend selects and probes available live YouTube streams.
3. Each live stream is converted into a structured TV program block.
4. A beam-search–based scheduling algorithm generates the final schedule.
5. The generated schedule is stored as a JSON object with a unique request ID.
6. The frontend continuously polls the status endpoint and renders the final schedule.



## 🚀 Running the Project Locally

### Prerequisites
- Python 3.9 or higher
- Node.js 18 or higher
- npm
- `yt-dlp` installed in the Python environment

---

### Backend Setup (Development)

1. Install Python dependencies:

```bash
python -m pip install -r requirements.txt
```

2. Run the backend in development mode:
```bash
uvicorn app.main:app --reload
```

The backend will be available at: 
http://localhost:8000

#### Backend Setup (Production)

When deploying to a production host, the backend must listen on the assigned port:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Frontend Setup
1. Navigate to the frontend directory:
```bash
cd frontend
```
2. Install Node.js dependencies:
```bash
npm ci
```
3. Run the development server:
```bash
npm run dev
```
4. Frontend will be available at:
http://localhost:5173


## Academic Context

This project is developed as part of the Master’s Program in Computer and Software Engineering at the
University of Prishtina – Faculty of Electrical and Computer Engineering.

Supervisor:
Dr. Techn. Kadri Sylejmani

The project demonstrates:

Algorithmic scheduling

Distributed systems

Modern web development

Integration with external platforms (YouTube)


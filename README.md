# AI Code Reviewer

A web-based Python code analysis tool that uses Google's Gemini AI to detect issues and suggest fixes. Built as a college project to help beginner programmers learn from their mistakes.

## What Does It Do?

This is a minimal viable product (MVP) that:
- Analyzes Python code for syntax errors and warnings using Pylint
- Uses Google Gemini AI to generate fixes for detected issues
- Provides beginner-friendly explanations of what went wrong
- Shows code fixes in a side-by-side diff view
- Allows one-click application of AI-generated fixes

The main goal is to help students understand their coding mistakes by providing clear explanations instead of cryptic error messages.

## Tech Stack

### Frontend
- React (Vite)
- Monaco Editor (VS Code's editor component)
- Axios (API calls)
- CSS3

### Backend
- FastAPI (Python web framework)
- Pylint (static code analysis)
- Black (code formatter)
- Google Gemini AI API
- Pydantic (data validation)
- Uvicorn (ASGI server)

## Prerequisites

Before running this project, you need:

- A Google AI Studio API key (free tier available)

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/KhushalID7/CODE-REVIEWER-project.git
```

### 2. Backend Setup

```bash
cd backend
pip install -r apps/req.txt
```

Create a `.env` file in the `backend` folder:

```env
GOOGLE_AI_API_KEY=your_api_key_here
GOOGLE_AI_MODEL=models/gemini-2.5-flash
```

To get your API key:
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Get API Key"
3. Copy and paste it into your `.env` file

### 3. Frontend Setup

```bash
cd ../frontend
npm install
```

## How to Run

You need two terminal windows open.

### Terminal 1 - Start Backend

```bash
cd backend
uvicorn apps.main:app --reload --port 8000
```


### Terminal 2 - Start Frontend

```bash
cd frontend
npm run dev
```



## Usage

1. Paste or write Python code in the editor
2. Click "Analyze" to check for issues
3. Click "Generate Fix" to let AI suggest a correction
4. Click "Apply Fix" to update your code with the suggested fix
5. Re-analyze to verify the fix worked

## Project Structure

```
CODE REVIEWER project/
├── backend/
│   ├── apps/
│   │   ├── main.py           # FastAPI routes
│   │   ├── llm_client.py     # Google AI integration
│   │   ├── analyser.py       # Code analysis logic
│   │   ├── linter_runner.py  # Pylint execution
│   │   ├── patch_utils.py    # Diff generation
│   │   └── schemas.py        # Request/response models
│   ├── tests/                # Unit tests
│   └── .env                  # Environment variables (not committed)
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── api/              # API client
│   │   └── styles/           # CSS files
│   └── package.json
└── README.md
```

## Known Limitations

- Only supports Python code analysis
- Analyzes one issue at a time (generates fix for first detected issue)
- Rate limited by Google AI API (10 requests per minute on free tier)
- Does not save analysis history
- No user authentication


## Testing

Run backend tests:
```bash
cd backend
pytest tests/llm_client_test.py -v
```


## Credits

Built as a college project for learning purposes.

Technologies used:
- Google Gemini AI for code fixes
- Pylint for static analysis
- Monaco Editor by Microsoft
- FastAPI framework
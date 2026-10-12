# 🎬 Movie AI Assistant
# 🎬 Movie AI Assistant

An intelligent, AI-powered movie discovery and recommendation platform built with **FastAPI, Supabase, Gemini AI, and TMDB API**. The application combines an AI agent, movie discovery tools, semantic search, and user watch history to deliver relevant and personalized movie recommendations.

## 🚀 About the Project

Movie AI Assistant is a full-stack movie discovery platform designed to help users find movies through natural-language conversations and intelligent search.

The project uses a dedicated **Supabase PostgreSQL database with vector embeddings** and a movie catalog containing more than **30,000 movies** imported using IMDb API data.

The AI agent coordinates specialized tools to handle movie searches, trending titles, semantic discovery, and personalized recommendations. User authentication and movie interactions allow the application to maintain user-specific watch history and preferences.

## ✨ Key Features

- **AI Movie Assistant:** Interact with an AI agent using natural language.
- **Semantic Movie Search:** Retrieve relevant movies using vector embeddings and semantic similarity.
- **Movie Discovery:** Search for movies by title and discover relevant results.
- **Trending Movies:** Retrieve currently trending movies using TMDB.
- **Personalized Recommendations:** Discover movies that users have not watched, using available user activity data.
- **User Authentication:** Authenticate users and verify access tokens.
- **Watch History:** Store watched and liked movie interactions.
- **Vector Database:** Store movie embeddings in Supabase for semantic retrieval.
- **External API Integration:** Combine local movie data with external movie discovery services.

## 🏗️ System Architecture

The application follows a modular architecture that separates the frontend, API endpoints, AI agent, specialized tools, external services, and database.

```text
Movie Seeker
    |
    v
Frontend (HTML, CSS, JavaScript)
    |
    v
FastAPI Application
    |
    +---- Authentication API
    |         |
    |         v
    |    User Verification
    |
    +---- Chat API
    |         |
    |         v
    |      AI Agent
    |         |
    |         +---- Routing Instructions
    |         +---- Semantic Movie Search
    |         +---- Trending Movies
    |         +---- Movie Search
    |         +---- Unwatched Recommendations
    |
    +---- Movie API
              |
              +---- User Movie Actions
              +---- Movie Data Retrieval
              +---- Authentication Verification

    AI Agent and API Tools
              |
              +---- Gemini AI
              +---- TMDB API
              +---- Supabase Client
              |
              v
        Supabase PostgreSQL
              |
              +---- movies
              +---- profiles
              +---- user_movie_actions
              +---- Vector Embeddings
```

## 📂 Project Structure

```text
movie-ai-assistant/
│
├── app/
│   ├── agent/
│   │   ├── agent.py
│   │   └── prompts.py
│   │
│   ├── api/
│   │   ├── auth.py
│   │   ├── chat.py
│   │   └── movies.py
│   │
│   ├── services/
│   │   └── # External service integrations
│   │
│   ├── tools/
│   │   ├── recommend_unwatched_movies.py
│   │   ├── search_movie.py
│   │   ├── semantic_search.py
│   │   └── trending_movies.py
│   │
│   ├── config.py
│   └── main.py
│
├── data/
│   └── # Data processing scripts and datasets
│
├── frontend/
│   ├── css/
│   ├── js/
│   └── index.html
│
├── tests/
│   └── # Unit and integration tests
│
├── .env
├── .env.example
├── .gitignore
├── .python-version
├── requirements.txt
└── README.md
```

> **Note:** This structure reflects the project's documented organization. Add or remove entries to match the actual files in your repository. The `requirements.txt` file is required for the installation commands below; if your project uses another dependency manager, follow its configuration instead.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| FastAPI | Backend API and HTTP endpoints |
| Gemini AI | Language model for AI-powered interactions |
| Supabase | PostgreSQL database and vector storage |
| PostgreSQL / pgvector | Structured data storage and vector similarity search |
| IMDb API data | Movie catalog metadata |
| TMDB API | Movie discovery and trending information |
| HTML, CSS, JavaScript | Frontend interface |
| Uvicorn | ASGI server for running FastAPI |

## 🗄️ Database Schema

The application uses three primary Supabase tables.

Only columns defined as `NOT NULL` are listed below. Optional columns are omitted.

### 1. `movies`

Stores movie metadata and vector embeddings for movie discovery and semantic search.

| Column | Data Type | Description |
|---|---|---|
| `id` | `bigint` | Movie record identifier |
| `imdb_id` | `text` | IMDb movie identifier |
| `title` | `text` | Movie title |

**Catalog:** More than 30,000 movie records imported using IMDb API data.

### 2. `profiles`

Stores user profile information associated with authenticated users.

| Column | Data Type | Description |
|---|---|---|
| `id` | `uuid` | User profile identifier |
| `email` | `text` | User email address |

### 3. `user_movie_actions`

Stores user interactions with movies, including likes and watch history.

| Column | Data Type | Description |
|---|---|---|
| `id` | `bigint` | Interaction record identifier |
| `user_id` | `uuid` | Associated user identifier |
| `imdb_id` | `text` | IMDb identifier of the movie |
| `liked` | `boolean` | Whether the user likes the movie; defaults to `false` |
| `watched` | `boolean` | Whether the user has watched the movie; defaults to `false` |

**Important:** The `embedding` column in `movies` is nullable according to the current schema. Although embeddings support semantic search, this README does not assume that every movie record necessarily contains an embedding.

## ⚙️ Getting Started

Follow these steps to run the backend locally.

### Prerequisites

Make sure you have the following:

- Python 3.11 or the version specified by `.python-version`.
- Git.
- A Supabase project with the required tables and database configuration.
- A Gemini API key.
- A TMDB API key if the enabled tools use TMDB.
- Any additional API credentials required by your actual application configuration.

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

Replace the repository URL with your actual GitHub repository URL.

### 2. Create a Virtual Environment

**Linux / Ubuntu / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

If your repository contains `requirements.txt`, run:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If you manage dependencies with `pyproject.toml` or another tool, use the installation method defined by your project.

### 4. Configure Environment Variables

Create your local environment file from the example:

```bash
cp .env.example .env
```

Open `.env` and configure the variable names expected by your application.

For example:

```dotenv
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_key

GEMINI_API_KEY=your_gemini_api_key
TMDB_API_KEY=your_tmdb_api_key
```

**Important:** These names are examples. Use the exact variable names referenced in `app/config.py` and the application code. Do not create duplicate or differently named variables if the project expects other names.

Never commit real API keys, database credentials, access tokens, or other secrets to GitHub.

### 5. Prepare the Supabase Database

Make sure your Supabase project contains the required tables:

- `movies`
- `profiles`
- `user_movie_actions`

The `movies` table should contain the movie records and embeddings needed by the enabled semantic-search functionality.

Also verify that:

- Your database connection settings are correct.
- The vector extension and embedding column use the expected configuration.
- Required database functions, indexes, and access policies are configured if your application depends on them.
- User authentication and token verification are configured correctly.

The README does not create or migrate the database automatically. Use the SQL migrations or setup scripts provided by the project, if available.

### 6. Start the FastAPI Backend

From the project root, run:

```bash
uvicorn app.main:app --reload
```

If the application starts successfully, the backend will normally be available at:

```text
http://127.0.0.1:8000
```

Open the interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

If your project uses a different application entry point or server configuration, adjust the command accordingly.

### 7. Run the Frontend

The frontend is located in the `frontend/` directory.

For local development, you can serve the static files with Python:

```bash
python -m http.server 5500 --directory frontend
```

Then open:

```text
http://127.0.0.1:5500
```

**Frontend configuration:** Ensure the JavaScript code points to the correct backend URL. If the frontend runs on a different origin, configure FastAPI CORS settings to allow that origin.

This simple static server is intended for local development, not production deployment.

## 🔍 Semantic Search

Semantic search uses vector embeddings to retrieve movies based on the meaning of a user's query rather than relying exclusively on exact keyword matches.

For example, a user might search for:

- Movies about artificial intelligence and human relationships.
- Dark crime dramas with complex characters.
- Films similar in theme to a particular movie.

The search process generally involves:

1. Converting movie descriptions and/or search queries into embeddings using the configured embedding model.
2. Searching the stored vectors in Supabase using the project's configured similarity-search implementation.
3. Retrieving matching movie metadata.
4. Passing the relevant results to the AI agent when needed to generate a response.

Actual search behavior depends on the embedding model, vector dimensions, database indexes, and retrieval functions configured in the application.

## 🤖 AI Agent and Tools

The AI agent coordinates the application's available tools according to the user's request and the routing instructions defined in `app/agent/prompts.py`.

| Tool | Responsibility |
|---|---|
| `search_movie.py` | Search for movies by title or supported search criteria |
| `semantic_search.py` | Retrieve movies using vector similarity |
| `trending_movies.py` | Discover trending movies using TMDB |
| `recommend_unwatched_movies.py` | Recommend movies while considering the user's watch history |

The API layer exposes the relevant functionality through the FastAPI endpoints in `app/api/`.

The exact tool selection and execution behavior depend on the agent implementation and its configured model.

## 🔐 Security

- Keep `.env` out of version control.
- Use `.env.example` to document required configuration without exposing secrets.
- Never expose a Supabase service-role key in frontend JavaScript.
- Verify authentication tokens on protected backend endpoints.
- Apply appropriate Supabase Row Level Security (RLS) policies.
- Restrict user movie actions to the authenticated user's own records.
- Configure CORS for trusted frontend origins.
- Avoid logging passwords, API keys, access tokens, or other sensitive information.

## 🧪 Testing

If tests are available in the `tests/` directory, run them using:

```bash
pytest
```

Install `pytest` and any additional testing dependencies if they are not already included in the project's dependency configuration.

## 🚀 Deployment

The FastAPI backend can be deployed to a Python-compatible hosting service.

Before deploying:

1. Configure the Python version and install the project's dependencies.
2. Add the required environment variables through the hosting provider's environment settings.
3. Confirm connectivity to Supabase and external APIs.
4. Verify that the frontend uses the deployed backend URL.
5. Configure CORS, authentication, and database access policies.
6. Test the health of the application and its API endpoints.

For a production deployment, use the hosting provider's recommended ASGI startup command and configuration rather than relying on the development server's `--reload` option.

## 📌 Future Improvements

Potential future enhancements include:

- More advanced personalized recommendation strategies.
- Improved semantic retrieval and ranking.
- Expanded filtering by genre, release year, rating, and other metadata.
- Better recommendation explanations and evaluation.
- Automated movie catalog updates.
- More comprehensive automated tests and monitoring.

## 📄 License

Add a `LICENSE` file to the repository and specify the license under which you want to distribute the project.

## 🙌 Acknowledgments

- [IMDb](https://www.imdb.com/) — Movie identification and metadata source.
- [TMDB](https://www.themoviedb.org/) — Movie discovery and trending data.
- [Supabase](https://supabase.com/) — Database and vector storage infrastructure.
- [Google AI Studio](https://aistudio.google.com/) — Gemini API access.
- [FastAPI](https://fastapi.tiangolo.com/) — Backend framework.

Review the applicable API terms, attribution requirements, and licensing conditions before distributing movie data or using it in a public application.


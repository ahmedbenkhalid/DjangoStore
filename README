# Getting Started

This project uses a Node.js frontend and a Django backend managed with `uv`.

## Frontend (Node.js)

1. **Install dependencies**  
   ```bash
   npm install
   ```

2. **Start the development server**  
   ```bash
   npm start
   ```
   The app will open at [http://localhost:3000](http://localhost:3000).

3. **Build for production**  
   ```bash
   npm run build
   ```
   Optimized assets are written to `build/`.

4. **Run tests**  
   ```bash
   npm test
   ```

## Backend (Django + uv)

1. **Install uv** (one-time)  
   ```bash
   curl -Ls https://astral.sh/uv/install.sh | sh
   ```

2. **Create & activate a virtual environment**  
   ```bash
   uv venv
   source .venv/bin/activate   # On Windows: .venv\Scripts\activate
   ```

3. **Install Python dependencies**  
   ```bash
   uv pip install -r requirements.txt
   ```

4. **Prepare the database**  
   ```bash
   python manage.py migrate
   python load_fixture.py      # Load sample data
   ```

5. **Start the Django server**  
   ```bash
   python manage.py runserver
   ```
   The API will be available at [http://localhost:8000](http://localhost:8000).

# Groww Pulse

Groww Pulse is an AI-Powered Weekly Play Store Insights tool. It provides a comprehensive dashboard to visualize app reviews, extract core themes, identify verified user quotes, and generate actionable AI recommendations.

## Project Structure

This repository is a monorepo containing:
- **`dashboard/`**: The frontend React web application built with Vite, TypeScript, and a premium glassmorphism dark theme using Tailwind-like custom CSS.
- **`src/` & Backend**: The Python backend that analyzes Play Store reviews, extracts parameters, and serves the REST API.
- **`data/`**: Data directories containing raw and normalized JSON review datasets.

## Dashboard App Features

- **Aesthetic UI**: A fully custom dark mode, glassmorphism interface.
- **Interactive Visualizations**: Includes `recharts` for charting Source Breakdown and Rating Distributions.
- **Deep Theme Analysis**: View verified quotes and action ideas for top themes discovered each week.

## Getting Started

### 1. Backend Setup
1. Ensure Python 3.x is installed.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the backend server (typically on `localhost:8000`).

### 2. Frontend Setup
1. Navigate to the `dashboard` directory:
   ```bash
   cd dashboard
   ```
2. Install Node.js dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
   
The dashboard will be available at `http://localhost:5173`.

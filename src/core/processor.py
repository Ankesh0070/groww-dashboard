import os
import re
import json
import time
from typing import List, Dict

try:
    # pyrefly: ignore [missing-import]
    from dotenv import load_dotenv
    load_dotenv() # Load from .env if it exists
    load_dotenv(".env.example") # Load from .env.example as a fallback
except ImportError:
    pass

try:
    # pyrefly: ignore [missing-import]
    from groq import Groq
except ImportError:
    Groq = None

try:
    # pyrefly: ignore [missing-import]
    from sentence_transformers import SentenceTransformer
    from sklearn.cluster import KMeans
    from sklearn.metrics import pairwise_distances_argmin_min
    # pyrefly: ignore [missing-import]
    import numpy as np
except ImportError:
    SentenceTransformer = None
    KMeans = None
    np = None

# Configure API key from environment variable
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    print("WARNING: No GROQ_API_KEY found. Falling back to mock analysis mode.")

# We initialize the model lazily so it doesn't slow down dry-runs or module imports
# pyrefly: ignore [parse-error]
_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None and SentenceTransformer is not None:
        print("Loading multilingual embedding model (paraphrase-multilingual-MiniLM-L12-v2)...")
        _embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _embedder

def get_representative_reviews(reviews_subset: List[Dict], n_clusters: int, top_n: int = 5) -> List[List[Dict]]:
    """Clusters reviews and returns the top_n most representative reviews for each cluster."""
    if not reviews_subset:
        return []
    
    if len(reviews_subset) <= n_clusters * top_n:
        # If there are very few reviews, just return them chunked
        return [reviews_subset[i:i + top_n] for i in range(0, len(reviews_subset), top_n)]

    embedder = get_embedder()
    if not embedder or not KMeans:
        # Fallback if sentence-transformers isn't installed
        return [reviews_subset[:top_n]]

    texts = [r.get("text", "") for r in reviews_subset]
    # Local encoding handles Hinglish well using the multilingual model
    embeddings = embedder.encode(texts, show_progress_bar=False)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    kmeans.fit(embeddings)

    clusters_representatives = []
    for i in range(n_clusters):
        cluster_indices = [idx for idx, label in enumerate(kmeans.labels_) if label == i]
        if not cluster_indices:
            continue
            
        cluster_embeddings = embeddings[cluster_indices]
        centroid = kmeans.cluster_centers_[i].reshape(1, -1)
        
        # Calculate distances for all reviews in this cluster to the centroid
        distances = np.linalg.norm(cluster_embeddings - centroid, axis=1)
        
        # Get indices of the top_n closest reviews
        top_indices_in_cluster = np.argsort(distances)[:top_n]
        
        reps = [reviews_subset[cluster_indices[idx]] for idx in top_indices_in_cluster]
        clusters_representatives.append(reps)

    return clusters_representatives

def analyze_reviews(reviews: List[Dict]) -> Dict:
    """
    Groups reviews into local semantic clusters, then summarizes them using Groq's LLaMA 3.3.
    Respects strict rate limits (12K TPM, 30 RPM).
    """
    if not reviews:
        return {"themes": []}

    if not api_key or not Groq:
        # Generate realistic mock data using verbatim reviews to allow complete dry-run validation
        verbatim_quotes = [
            r.get("text", "") for r in reviews 
            if len(r.get("text", "").split()) >= 4 and r.get("score", 5) < 3
        ][:3]
        if not verbatim_quotes:
            verbatim_quotes = ["This app is missing advanced portfolio insights.", "Support takes too long to reply to queries."]
            
        return {
            "themes": [
                {
                    "name": "App Navigation & Portfolio Insights",
                    "description": "Users report friction finding specific investment accounts and wish for advanced analytics.",
                    "action_ideas": [
                        "Simplify portfolio screens to make holdings visibility clearer.",
                        "Add historical profit/loss graphs for mutual funds."
                    ],
                    "quotes": [verbatim_quotes[0]]
                },
                {
                    "name": "Customer Support Response SLA",
                    "description": "Slow ticket updates and unresolved support requests during peak market hours.",
                    "action_ideas": [
                        "Integrate real-time ticket status tracking directly in the help section."
                    ],
                    "quotes": [verbatim_quotes[-1]]
                }
            ]
        }

    # Bucket by score
    positive_reviews = [r for r in reviews if r.get("score", 0) >= 4]
    negative_reviews = [r for r in reviews if r.get("score", 0) <= 3]

    print(f"Processing: {len(positive_reviews)} Positive, {len(negative_reviews)} Negative reviews.")

    # Local Clustering: 2 Positive themes, 4 Negative themes
    # We sample 4 representative reviews per cluster to stay well under the 12K Tokens/Min Groq limit
    pos_clusters = get_representative_reviews(positive_reviews, n_clusters=2, top_n=4)
    neg_clusters = get_representative_reviews(negative_reviews, n_clusters=4, top_n=4)

    all_clusters = [("Positive feedback", c) for c in pos_clusters] + [("Negative feedback", c) for c in neg_clusters]
    
    client = Groq(api_key=api_key)
    all_themes = []

    print(f"Summarizing {len(all_clusters)} local clusters using Groq API (llama-3.3-70b-versatile)...")
    for idx, (bucket_name, cluster_reviews) in enumerate(all_clusters):
        reviews_formatted = []
        for r_idx, r in enumerate(cluster_reviews):
            text = r.get("text", "").replace("\n", " ")
            reviews_formatted.append(f"Review #{r_idx}: {text}")
        
        reviews_text = "\n".join(reviews_formatted)
        
        prompt = f"""
You are an expert product manager and data analyst.
Analyze the following user reviews ({bucket_name} cluster) for the Groww Android app:

{reviews_text}

Perform the following tasks:
1. Identify the single major theme connecting these specific reviews.
2. Provide a clear, concise theme name.
3. Describe the theme in 1 sentence.
4. Provide 2 to 3 actionable, specific improvement recommendations for the product team.
5. Extract 1 to 2 representative user quotes. IMPORTANT: These quotes MUST be copied EXACTLY word-for-word from the reviews provided above. Do not alter, edit, summarize, or fix typos in the quotes. They must match the source text exactly.

Output your response strictly as a JSON object with the following schema:
{{
  "name": "Theme Name",
  "description": "One-sentence description",
  "action_ideas": ["Action 1", "Action 2"],
  "quotes": ["Verbatim Quote 1"]
}}
Ensure valid JSON format.
"""

        # Rate limiting: 30 RPM -> 1 request every 2 seconds. Sleep 2.5s for safety.
        if idx > 0:
            time.sleep(2.5)

        retries = 3
        while retries > 0:
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                    max_tokens=400
                )
                
                content = response.choices[0].message.content
                theme_data = json.loads(content)
                all_themes.append(theme_data)
                break
            except Exception as e:
                print(f"Groq API Error: {str(e)}. Retrying in 5 seconds...")
                retries -= 1
                time.sleep(5)
                if retries == 0:
                    print("Failed to process a cluster after retries. Skipping.")

    return {"themes": all_themes}

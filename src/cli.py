import os
import argparse
import asyncio
from datetime import datetime

try:
    # pyrefly: ignore [missing-import]
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv(".env.example")
except ImportError:
    pass


from core.scrubber import scrub_pii
from core.processor import analyze_reviews
from core.validator import validate_quote
from core.workspace import fetch_reviews, append_report_to_doc, send_email
from core.idempotency import is_week_processed, record_run

def get_current_iso_week() -> str:
    """
    Returns current year and week in YYYY-Wxx format.
    """
    now = datetime.now()
    year, week, _ = now.isocalendar()
    return f"{year}-W{week:02d}"

async def run_pipeline(args):
    # Determine ISO Week
    iso_week = args.iso_week if args.iso_week else get_current_iso_week()
    print(f"=== Starting Weekly Product Review Pulse for Groww ({iso_week}) ===")
    
    # 1. Idempotency Check
    if not args.force and is_week_processed(iso_week):
        print(f"Skipping run: Week {iso_week} has already been processed and saved.")
        return

    # 2. Fetch Reviews from custom Play Store reviews MCP server
    print(f"Fetching Google Play Store reviews for com.nextbillion.groww ({args.weeks} weeks)...")
    raw_reviews = await fetch_reviews("com.nextbillion.groww", weeks_back=args.weeks)
    print(f"Retrieved {len(raw_reviews)} reviews.")
    
    if not raw_reviews:
        print("No reviews found or failed to fetch. Exiting.")
        return

    # 3. PII Scrubbing
    print("Sanitizing reviews (PII Scrubbing)...")
    scrubbed_reviews = []
    for r in raw_reviews:
        cleaned_text = scrub_pii(r.get("text", ""))
        scrubbed_reviews.append({
            "id": r.get("id"),
            "text": cleaned_text,
            "score": r.get("score")
        })

    # 4. Clustering & LLM processing
    print("Clustering reviews and extracting insights via Groq LLaMA...")
    try:
        analysis_result = analyze_reviews(scrubbed_reviews)
    except Exception as e:
        print(f"Groq processing failed: {e}")
        return

    themes = analysis_result.get("themes", [])
    print(f"Identified {len(themes)} core themes.")

    # 5. Quote Verification
    print("Verifying quote authenticity...")
    valid_themes = []
    for theme in themes:
        theme_name = theme.get("name", "Unnamed Theme")
        valid_quotes = []
        for quote in theme.get("quotes", []):
            if validate_quote(quote, scrubbed_reviews):
                valid_quotes.append(quote)
            else:
                print(f"WARNING: Quote rejected (not found verbatim in source reviews): '{quote}'")
        
        # Keep the theme even if some quotes were filtered out
        theme["quotes"] = valid_quotes
        valid_themes.append(theme)

    # 5.5 Save raw JSON for Dashboard API
    import json
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    json_path = os.path.join(data_dir, f"themes_{iso_week}.json")
    with open(json_path, "w") as f:
        json.dump(valid_themes, f, indent=2)
    print(f"Saved raw JSON themes to {json_path}")

    # 6. Format Report Section (Plain Text)
    report_text = f"""
Groww - Weekly Review Pulse ({iso_week})
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

TOP THEMES:
"""
    for theme in valid_themes:
        report_text += f"- {theme.get('name')} — {theme.get('description')}\n"
        
    report_text += "\nREAL USER QUOTES:\n"
    for theme in valid_themes:
        for quote in theme.get("quotes", []):
            report_text += f'- "{quote}"\n'

    report_text += "\nACTION IDEAS:\n"
    for theme in valid_themes:
        for idea in theme.get("action_ideas", []):
            report_text += f"- {theme.get('name')}: {idea}\n"

    report_text += "\n--------------------------------------------------\n"

    # 7. Workspace Delivery / Dry Run
    if args.dry_run:
        print("\n--- DRY RUN OUTPUT ---")
        print(report_text)
        print("----------------------\n")
        print("Dry run complete. No external writes performed.")
        return

    # Deliver via Google Docs MCP
    print(f"Appending report section to Google Doc: {args.doc_id}...")
    doc_status = await append_report_to_doc(args.doc_id, report_text)
    print(f"Docs Delivery Status: {doc_status}")

    # Deliver Email via Gmail MCP
    subject = f"Groww - Weekly Review Pulse ({iso_week})"
    email_teaser = f"The weekly Google Play Store review insights report for Groww ({iso_week}) is ready.\n\n"
    email_teaser += "Top Themes:\n"
    for theme in valid_themes:
        email_teaser += f"- {theme.get('name')}: {theme.get('description')}\n"
    email_teaser += f"\nRead full report and history here: https://docs.google.com/document/d/{args.doc_id}\n"
    
    print(f"Sending email notification to {args.recipient_email} (Draft only: {args.draft_only})...")
    email_status = await send_email(args.recipient_email, subject, email_teaser, draft_only=args.draft_only)
    print(f"Gmail Delivery Status: {email_status}")

    # 8. Record Execution Run for Idempotency
    record_run(
        iso_week=iso_week,
        doc_id=args.doc_id,
        section_id=doc_status,
        email_status="DRAFT" if args.draft_only else "SENT"
    )
    print("Execution completed and recorded successfully.")

def main():
    parser = argparse.ArgumentParser(description="Weekly Product Review Pulse for Groww")
    parser.add_argument("--doc-id", default="dummy_doc_id", help="Google Doc ID to append reports to")
    parser.add_argument("--recipient-email", default="stakeholders@groww.in", help="Gmail recipient for the report notification")
    parser.add_argument("--weeks", type=int, default=8, help="Rolling window of weeks to fetch (default: 8)")
    parser.add_argument("--iso-week", help="Override target ISO week (format: YYYY-Wxx)")
    parser.add_argument("--dry-run", action="store_true", help="Print report locally and skip Google Workspace writes")
    parser.add_argument("--send", dest="draft_only", action="store_false", help="Directly send the email instead of creating a draft")
    parser.add_argument("--force", action="store_true", help="Bypass idempotency checks and run anyway")
    
    parser.set_defaults(draft_only=True)
    args = parser.parse_args()

    # Verify API configuration before starting pipeline
    if not args.dry_run and not os.environ.get("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY environment variable is not set.")
        return

    asyncio.run(run_pipeline(args))

if __name__ == "__main__":
    main()

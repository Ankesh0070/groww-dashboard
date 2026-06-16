import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import gplay from "google-play-scraper";
import fs from "fs";

const server = new Server(
  {
    name: "mcp-server-playstore",
    version: "1.0.0"
  },
  {
    capabilities: {
      tools: {}
    }
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "fetch_play_store_reviews",
        description: "Fetch reviews for a given Android app package from the Google Play Store.",
        inputSchema: {
          type: "object",
          properties: {
            package_name: {
              type: "string",
              description: "The Android package name (e.g., com.groww.android)."
            },
            weeks_back: {
              type: "number",
              description: "Number of weeks of reviews to fetch (default: 8)."
            }
          },
          required: ["package_name"]
        }
      }
    ]
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "fetch_play_store_reviews") {
    const { package_name, weeks_back = 8 } = request.params.arguments;
    
    // Calculate date threshold
    const dateLimit = new Date();
    dateLimit.setDate(dateLimit.getDate() - (weeks_back * 7));

    try {
      let actualReviews = [];
      let normalizedReviews = [];
      let nextPageToken = undefined;
      let stopFetching = false;

      // Limit pagination to maximum 15 pages to keep payload reasonable
      for (let page = 0; page < 15 && !stopFetching; page++) {
        const result = await gplay.reviews({
          appId: package_name,
          sort: gplay.sort.NEWEST,
          num: 100,
          paginate: true,
          nextPaginationToken: nextPageToken
        });

        const reviews = result.data || [];
        nextPageToken = result.nextPaginationToken;

        if (reviews.length === 0) {
          break;
        }

        for (const review of reviews) {
          const reviewDate = new Date(review.date);
          if (reviewDate < dateLimit) {
            stopFetching = true;
            break;
          }
          // Keep actual review (removing reviewId, userName, userImage, version, date, etc)
          actualReviews.push({
            score: review.score,
            title: review.title,
            text: review.text
          });

          // Normalize text: remove zero-width chars, compress whitespace, and trim
          let normalizedText = review.text || "";
          normalizedText = normalizedText.replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim();

          // 1. Remove if less than 8 words
          const words = normalizedText.split(' ').filter(w => w.length > 0);
          if (words.length < 8) continue;

          // 2. Remove if it contains emojis
          if (/\p{Extended_Pictographic}/gu.test(normalizedText)) continue;

          // 3. Remove if it is in another language (heuristic: drop non-Latin characters)
          // This allows ASCII, Latin-1, general punctuation, and currency symbols, dropping Hindi, Arabic, etc.
          if (/[^\x00-\xFF\u2000-\u206F\u20A0-\u20CF]/.test(normalizedText)) continue;

          normalizedReviews.push({
            score: review.score,
            title: review.title,
            text: normalizedText
          });
        }

        if (!nextPageToken) {
          break;
        }
      }

      // Save to separate files as requested
      fs.writeFileSync("actual_reviews.json", JSON.stringify(actualReviews, null, 2));
      fs.writeFileSync("normalized_reviews.json", JSON.stringify(normalizedReviews, null, 2));

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(normalizedReviews, null, 2)
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error fetching reviews: ${error.message}`
          }
        ],
        isError: true
      };
    }
  }

  throw new Error(`Unknown tool: ${request.params.name}`);
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Play Store MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});

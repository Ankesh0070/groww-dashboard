import { spawn } from "child_process";

console.log("Starting MCP server process to generate cache...");
const child = spawn("node", ["index.js"]);

let output = "";

child.stdout.on("data", (data) => {
  output += data.toString();
  // Check if we have received a complete JSON response
  try {
    const lines = output.trim().split("\n");
    for (const line of lines) {
      if (line.includes('"jsonrpc"')) {
        const parsed = JSON.parse(line);
        console.log("✅ MCP server returned successfully.");
        child.kill();
        process.exit(0);
      }
    }
  } catch (e) {
    // incomplete JSON, wait for more chunks
  }
});

child.stderr.on("data", (data) => {
  console.error("SERVER LOG:", data.toString());
});

const request = {
  jsonrpc: "2.0",
  id: 1,
  method: "tools/call",
  params: {
    name: "fetch_play_store_reviews",
    arguments: {
      package_name: "com.nextbillion.groww",
      weeks_back: 10
    }
  }
};

console.log("Requesting 10 weeks of reviews for com.nextbillion.groww...");
child.stdin.write(JSON.stringify(request) + "\n");

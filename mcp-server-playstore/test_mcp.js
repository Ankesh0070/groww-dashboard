import { spawn } from "child_process";

console.log("Starting MCP server process...");
const child = spawn("node", ["index.js"]);

child.stdout.on("data", (data) => {
  console.log("RECEIVED FROM SERVER:\n", data.toString());
  // We can kill the child once we receive tools list
  child.kill();
});

child.stderr.on("data", (data) => {
  console.error("SERVER STDERR:", data.toString());
});

child.on("close", (code) => {
  console.log("Server process exited with code", code);
});

// Send a JSON-RPC list tools request
const request = {
  jsonrpc: "2.0",
  id: 1,
  method: "tools/list",
  params: {}
};

console.log("Sending list tools request...");
child.stdin.write(JSON.stringify(request) + "\n");

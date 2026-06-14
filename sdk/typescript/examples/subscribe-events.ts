import { BitcoinBastionClient } from "../src/index.js";

const client = new BitcoinBastionClient({ baseUrl: "http://localhost:8000" });
client.websocket.subscribe({
  topics: ["signals", "trace", "market"],
  onEvent: (event) => console.log(event),
  onError: (error) => console.error(error),
});

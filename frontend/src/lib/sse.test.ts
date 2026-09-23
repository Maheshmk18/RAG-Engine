import { readServerEvents } from "./sse";

function streamOf(chunks: string[]): Response {
  const encoder = new TextEncoder();
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk));
      controller.close();
    },
  });
  return new Response(body);
}

async function collect(response: Response) {
  const events = [];
  for await (const event of readServerEvents(response)) events.push(event);
  return events;
}

test("parses events split across network chunks", async () => {
  const response = streamOf([
    'event: token\ndata: {"text": "Hel',
    'lo"}\n\nevent: token\ndata: {"text": " world"}\n',
    '\nevent: answer\ndata: {"id": "1"}\n\n',
  ]);
  expect(await collect(response)).toEqual([
    { event: "token", data: { text: "Hello" } },
    { event: "token", data: { text: " world" } },
    { event: "answer", data: { id: "1" } },
  ]);
});

test("handles windows line endings and a trailing event without a blank line", async () => {
  const response = streamOf([
    'event: retrieval\r\ndata: {"passages": 2}\r\n\r\nevent: done\ndata: {}',
  ]);
  expect(await collect(response)).toEqual([
    { event: "retrieval", data: { passages: 2 } },
    { event: "done", data: {} },
  ]);
});

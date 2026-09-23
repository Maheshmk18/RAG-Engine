export interface ServerEvent {
  event: string;
  data: unknown;
}

function parseBlock(block: string): ServerEvent | null {
  let event = "message";
  const data: string[] = [];
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
  }
  if (data.length === 0) return null;
  return { event, data: JSON.parse(data.join("\n")) };
}

export async function* readServerEvents(response: Response): AsyncGenerator<ServerEvent> {
  if (!response.body) return;
  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += value.replace(/\r\n/g, "\n");
    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const parsed = parseBlock(buffer.slice(0, boundary));
      buffer = buffer.slice(boundary + 2);
      if (parsed) yield parsed;
      boundary = buffer.indexOf("\n\n");
    }
  }
  const trailing = parseBlock(buffer.trim());
  if (trailing) yield trailing;
}

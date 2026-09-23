import type { Root, Text } from "mdast";
import { visit } from "unist-util-visit";

const MARKER = /\[(\d{1,2})\]/g;

interface CitationNode {
  type: "citation";
  data: { hName: "cite"; hProperties: { dataNumber: string } };
  children: [];
}

export function remarkCitations() {
  return (tree: Root) => {
    visit(tree, "text", (node: Text, index, parent) => {
      if (!parent || index === undefined || !MARKER.test(node.value)) return;
      MARKER.lastIndex = 0;

      const pieces: (Text | CitationNode)[] = [];
      let cursor = 0;
      for (const match of node.value.matchAll(MARKER)) {
        const start = match.index ?? 0;
        if (start > cursor) pieces.push({ type: "text", value: node.value.slice(cursor, start) });
        pieces.push({
          type: "citation",
          data: { hName: "cite", hProperties: { dataNumber: match[1] ?? "" } },
          children: [],
        });
        cursor = start + match[0].length;
      }
      if (cursor < node.value.length)
        pieces.push({ type: "text", value: node.value.slice(cursor) });

      parent.children.splice(index, 1, ...(pieces as Text[]));
      return index + pieces.length;
    });
  };
}

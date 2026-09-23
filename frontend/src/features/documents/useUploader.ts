import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useState } from "react";
import { api, ApiError } from "@/lib/api";

export const ACCEPTED_FILES = ".pdf,.docx,.md,.markdown,.txt";

export interface UploadItem {
  name: string;
  state: "uploading" | "done" | "error";
  message?: string;
}

export function useUploader() {
  const queryClient = useQueryClient();
  const [items, setItems] = useState<UploadItem[]>([]);

  const upload = useCallback(
    async (files: FileList | File[]) => {
      const list = Array.from(files);
      setItems((current) => [
        ...current.filter((item) => item.state === "error"),
        ...list.map((file) => ({ name: file.name, state: "uploading" as const })),
      ]);
      await Promise.all(
        list.map(async (file) => {
          let result: UploadItem;
          try {
            await api.uploadDocument(file);
            result = { name: file.name, state: "done", message: "Added, indexing now" };
          } catch (caught) {
            const message = caught instanceof ApiError ? caught.message : "Upload failed";
            result = { name: file.name, state: "error", message };
          }
          setItems((current) =>
            current.map((item) =>
              item.name === file.name && item.state === "uploading" ? result : item,
            ),
          );
        }),
      );
      await queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    [queryClient],
  );

  const dismiss = useCallback((name: string) => {
    setItems((current) => current.filter((item) => item.name !== name));
  }, []);

  const clear = useCallback(() => setItems([]), []);

  return {
    items,
    upload,
    dismiss,
    clear,
    busy: items.some((item) => item.state === "uploading"),
  };
}

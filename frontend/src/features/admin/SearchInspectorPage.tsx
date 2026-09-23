import { useMutation } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { useState } from "react";
import type { FormEvent } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Field";
import { EmptyState, PageHeader } from "@/components/ui/PageHeader";
import { api } from "@/lib/api";
import type { Passage, SearchResponse } from "@/lib/types";
import styles from "./AdminPages.module.css";

const STAGES: Record<string, string> = {
  "retrieval.dense": "Vector search",
  "retrieval.lexical": "BM25",
  "retrieval.fusion": "Fusion",
  "retrieval.rerank": "Rerank",
};

function Timings({ trace }: { trace: SearchResponse["trace"] }) {
  const total = trace.spans.reduce((sum, span) => sum + span.duration_ms, 0) || 1;
  return (
    <div className={styles.timings}>
      <div className={styles.timingBar} aria-hidden="true">
        {trace.spans.map((span) => (
          <span
            key={span.name}
            data-stage={span.name}
            style={{ width: `${(span.duration_ms / total) * 100}%` }}
          />
        ))}
      </div>
      <dl className={styles.timingLegend}>
        {trace.spans.map((span) => (
          <div key={span.name} data-stage={span.name}>
            <dt>{STAGES[span.name] ?? span.name}</dt>
            <dd className="mono">{Math.round(span.duration_ms)} ms</dd>
          </div>
        ))}
        <div>
          <dt>Total</dt>
          <dd className="mono">{Math.round(trace.total_ms)} ms</dd>
        </div>
      </dl>
    </div>
  );
}

function rank(value: number | null) {
  return value === null ? "–" : `#${value}`;
}

function PassageCard({ passage, position }: { passage: Passage; position: number }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <li className={styles.passage}>
      <div className={styles.passageHead}>
        <span className={styles.position}>{position}</span>
        <div className={styles.passageTitle}>
          <span>{passage.document_title}</span>
          {passage.heading && <span className="muted">{passage.heading}</span>}
        </div>
      </div>
      <dl className={styles.scores}>
        <div>
          <dt>Relevance</dt>
          <dd className="mono">{passage.relevance.toFixed(4)}</dd>
        </div>
        <div>
          <dt>Vector rank</dt>
          <dd className="mono">{rank(passage.dense_rank)}</dd>
        </div>
        <div>
          <dt>BM25 rank</dt>
          <dd className="mono">{rank(passage.lexical_rank)}</dd>
        </div>
        <div>
          <dt>Fused score</dt>
          <dd className="mono">{passage.fused_score.toFixed(4)}</dd>
        </div>
      </dl>
      <p className={styles.passageText} data-expanded={expanded}>
        {passage.text}
      </p>
      <button type="button" className={styles.more} onClick={() => setExpanded((value) => !value)}>
        {expanded ? "Show less" : "Show full passage"}
      </button>
    </li>
  );
}

export function SearchInspectorPage() {
  const [query, setQuery] = useState("");
  const search = useMutation({ mutationFn: api.search });

  return (
    <div className={styles.page}>
      <PageHeader
        title="Search inspector"
        description="Run a question through retrieval and see which passages would be sent to the model, with the score from each stage."
      />
      <form
        className={styles.searchForm}
        onSubmit={(event: FormEvent) => {
          event.preventDefault();
          if (query.trim()) search.mutate(query.trim());
        }}
      >
        <Input
          aria-label="Question"
          placeholder="How many days of leave can I carry over?"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <Button
          type="submit"
          variant="primary"
          icon={<Search size={15} />}
          loading={search.isPending}
        >
          Search
        </Button>
      </form>

      {search.error && <p className={styles.formError}>{search.error.message}</p>}

      {search.data && (
        <section className={styles.results} aria-label="Results">
          <Timings trace={search.data.trace} />
          <p className="muted">
            {search.data.candidates} candidates were reranked and {search.data.passages.length}{" "}
            passed the relevance gate.
          </p>
          {search.data.passages.length === 0 ? (
            <EmptyState title="Nothing relevant was found">
              The best candidate scored below the relevance threshold, so the assistant would
              decline to answer this question.
            </EmptyState>
          ) : (
            <ol className={styles.passages}>
              {search.data.passages.map((passage, index) => (
                <PassageCard key={passage.chunk_id} passage={passage} position={index + 1} />
              ))}
            </ol>
          )}
        </section>
      )}
    </div>
  );
}

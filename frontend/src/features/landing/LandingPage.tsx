import { ArrowRight, ArrowUp, CornerDownRight, FileText, Plus, SearchX } from "lucide-react";
import { useState } from "react";
import type { ReactNode } from "react";
import { Link } from "react-router";
import { Wordmark } from "@/components/Wordmark";
import styles from "./LandingPage.module.css";

const NUMBERS = [
  { value: "100%", label: "of answerable test questions retrieved the right section" },
  { value: "0.98", label: "mean reciprocal rank across the evaluation set" },
  { value: "6 of 8", label: "off-topic questions stopped before the model is called" },
  { value: "49", label: "questions re-run on every change before it ships" },
];

const STAGES = [
  {
    name: "Ingest",
    body: "PDF, Word, Markdown and text files are split along their own headings, so a passage never mixes two policies.",
    tags: ["GridFS storage", "Heading-aware chunks", "bge-small embeddings"],
  },
  {
    name: "Retrieve",
    body: "Keyword search and meaning search run side by side, then their rankings are merged.",
    tags: ["BM25", "Vector search", "Reciprocal rank fusion"],
  },
  {
    name: "Rerank",
    body: "A cross-encoder reads every candidate against the question and keeps the five that actually answer it.",
    tags: ["MiniLM cross-encoder", "Top five kept"],
  },
  {
    name: "Answer",
    body: "The model cites a source for every claim, and the draft is checked before anyone sees it.",
    tags: ["Llama 3.3 on Groq", "Citation check", "Repair or decline"],
  },
];

const RESULTS = [
  { strategy: "Keyword search (BM25)", hit: "0.927", mrr: 0.808 },
  { strategy: "Vector search", hit: "0.976", mrr: 0.951 },
  { strategy: "Hybrid, fused", hit: "0.976", mrr: 0.902 },
  { strategy: "Hybrid + reranking", hit: "1.000", mrr: 0.981, highlight: true },
];

const OPERATIONS = [
  {
    title: "No accounts to manage",
    body: "Anyone who can reach the assistant can ask. Each browser keeps its own private conversation history.",
  },
  {
    title: "Documents behind an admin key",
    body: "Reading is open; uploading, re-indexing and deleting documents require the key set on the server.",
  },
  {
    title: "Your own MongoDB",
    body: "Documents, passages, conversations and feedback live in one MongoDB database, with Atlas Vector Search when you use Atlas.",
  },
  {
    title: "Search models run in-house",
    body: "Embedding and ranking happen inside the service. Only the question and the chosen passages go to the language model.",
  },
  {
    title: "Rate limits and request IDs",
    body: "Questions are rate limited per address, and every response carries an ID that ties it to the structured logs.",
  },
  {
    title: "Ready for containers",
    body: "One image runs the API and the background indexer, with health checks for Railway, Docker or Kubernetes.",
  },
];

const USE_CASES = [
  {
    team: "People and HR",
    question: "How long do I get full pay when I am off sick?",
    body: "Leave, benefits, sickness and performance policies, answered the same way for everyone.",
  },
  {
    team: "IT and security",
    question: "What do I do if my laptop is stolen?",
    body: "Runbooks and security rules people need at the exact moment something goes wrong.",
  },
  {
    team: "Finance",
    question: "Who has to approve an expense claim of 1,500?",
    body: "Travel limits, approval thresholds and reimbursement rules without searching a PDF.",
  },
  {
    team: "Onboarding",
    question: "Which training do I have to finish in my first week?",
    body: "New starters get answers on day one instead of waiting for someone to reply.",
  },
];

const FORMATS = ["PDF", "Word", "Markdown", "Plain text"];
const STACK = ["MongoDB", "Groq", "FastAPI", "React"];

const QUESTIONS = [
  {
    q: "What kinds of documents can it read?",
    a: "PDF, Word (.docx), Markdown and plain text, up to 20 MB each. Duplicate uploads are detected and skipped.",
  },
  {
    q: "Where is our data stored?",
    a: "In the MongoDB database you point it at. The original files are kept in GridFS next to the extracted passages, so nothing is written to local disk.",
  },
  {
    q: "What happens when the answer isn't in the documents?",
    a: "It tells you. Questions unrelated to the documents are stopped before the language model is called, and answers that can't be backed by a citation are withheld.",
  },
  {
    q: "Do people need to sign in?",
    a: "No. The assistant opens straight away and remembers conversations in the browser that started them. If it should only be reachable inside your company, run it behind your VPN or single sign-on proxy.",
  },
  {
    q: "How do we add our own documents?",
    a: "Choose Upload documents in the sidebar, enter the admin key configured on the server, then drop your files in. They are indexed in the background and can be asked about within seconds.",
  },
];

function Cite({ n }: { n: number }) {
  return <span className={styles.cite}>{n}</span>;
}

interface Example {
  tab: string;
  question: string;
  answer: ReactNode;
  sources: { heading: string; document: string }[];
  passage: string;
}

const EXAMPLES: Example[] = [
  {
    tab: "Holiday carry-over",
    question: "Can I carry unused holiday into next year?",
    answer: (
      <>
        <p>
          Yes, up to <strong>5 unused days</strong> <Cite n={1} />. They have to be taken by{" "}
          <strong>31 March</strong>, after which they are forfeited <Cite n={1} />.
        </p>
        <p>
          If you were ill during your holiday, those days can be reclassified as sick leave and
          returned to your balance <Cite n={2} />.
        </p>
      </>
    ),
    sources: [
      { document: "Annual Leave Policy", heading: "Carry-Over" },
      { document: "Annual Leave Policy", heading: "Sickness During Leave" },
    ],
    passage:
      "Employees may carry over a maximum of 5 unused days into the next calendar year. Carried-over days must be used by 31 March of the following year, after which they are forfeited.",
  },
  {
    tab: "Hotel limits",
    question: "What can I spend on a hotel in New York?",
    answer: (
      <>
        <p>
          In New York the limit is <strong>275 per night</strong> <Cite n={1} />, compared with 200
          per night in most other cities <Cite n={1} />.
        </p>
        <p>
          Book it through the travel portal so the company can reach you in an emergency{" "}
          <Cite n={1} />.
        </p>
      </>
    ),
    sources: [{ document: "Travel and Expenses Policy", heading: "Hotels" }],
    passage:
      "Hotel costs are reimbursed up to 200 per night. In London, New York and San Francisco the limit is 275 per night. Hotels should be booked through the travel portal so that the company can locate employees in an emergency.",
  },
  {
    tab: "Lost laptop",
    question: "I left my work laptop on the train. What now?",
    answer: (
      <>
        <p>
          Report it to <strong>security@kestrel.example</strong> within <strong>one hour</strong> of
          noticing it is missing <Cite n={1} />.
        </p>
        <p>
          The Security Team will lock and wipe it remotely <Cite n={1} />, and reporting late is
          treated as a security incident <Cite n={1} />.
        </p>
      </>
    ),
    sources: [{ document: "IT Security Guidelines", heading: "Lost or Stolen Devices" }],
    passage:
      "Report a lost or stolen laptop or phone to security@kestrel.example within one hour of noticing it is missing. The Security Team will remotely lock and wipe the device. A delay in reporting a lost device is treated as a security incident.",
  },
];

function AppPreview() {
  const [active, setActive] = useState(0);
  const example = EXAMPLES[active] ?? EXAMPLES[0];
  if (!example) return null;
  const first = example.sources[0];

  return (
    <div className={styles.demo}>
      <div className={styles.tabs} role="tablist" aria-label="Example questions">
        {EXAMPLES.map((item, index) => (
          <button
            key={item.tab}
            type="button"
            role="tab"
            aria-selected={index === active}
            className={styles.tab}
            onClick={() => setActive(index)}
          >
            {item.tab}
          </button>
        ))}
      </div>
      <div className={styles.window}>
        <div className={styles.windowBar}>
          <span />
          <span />
          <span />
        </div>
        <div className={styles.app} key={example.tab}>
          <div className={styles.appSidebar}>
            <div className={styles.appBrand}>
              <span className={styles.appMark} />
              Enterprise RAG
            </div>
            <div className={styles.appNew}>
              <Plus size={12} /> New conversation
            </div>
            <p className={styles.appGroup}>Today</p>
            {EXAMPLES.map((item, index) => (
              <p
                key={item.tab}
                className={`${styles.appItem} ${index === active ? styles.appItemActive : ""}`}
              >
                {item.question}
              </p>
            ))}
            <p className={styles.appGroup}>Yesterday</p>
            <p className={styles.appItem}>Parental leave notice</p>
            <p className={styles.appItem}>Working from abroad</p>
          </div>
          <div className={styles.appChat}>
            <p className={styles.bubble}>{example.question}</p>
            <div className={styles.appAnswer}>{example.answer}</div>
            <div className={styles.appSources}>
              {example.sources.map((source, index) => (
                <p key={source.heading}>
                  <span>{index + 1}</span> {source.document} <em>{source.heading}</em>
                </p>
              ))}
            </div>
            <div className={styles.appComposer}>
              Ask about a policy, process or guideline
              <span>
                <ArrowUp size={12} />
              </span>
            </div>
          </div>
          <div className={styles.appPanel}>
            <p className={styles.appEyebrow}>Source 1</p>
            <p className={styles.appDoc}>{first?.document}</p>
            <p className={styles.appHeading}>{first?.heading}</p>
            <blockquote>{example.passage}</blockquote>
            <p className={styles.appOpen}>
              <FileText size={12} /> Open original document
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function CitationExample() {
  return (
    <div className={styles.card}>
      <p className={styles.bubble}>How much notice do I give before parental leave?</p>
      <p className={styles.cardAnswer}>
        Tell People Operations at least <strong>15 weeks</strong> before the expected week of
        childbirth or placement <Cite n={1} />. You can move the start date later with{" "}
        <strong>28 days</strong> of notice <Cite n={1} />.
      </p>
      <div className={styles.quote}>
        <p className={styles.quoteLabel}>
          <span>1</span> Parental Leave Policy · Giving Notice
        </p>
        <p>
          Employees must tell People Operations about their intention to take parental leave at
          least 15 weeks before the expected week of childbirth or placement. The planned start date
          can be changed with 28 days of notice.
        </p>
      </div>
    </div>
  );
}

function DeclineExample() {
  return (
    <div className={styles.card}>
      <p className={styles.bubble}>How many days of bereavement leave do I get?</p>
      <div className={styles.declined}>
        <SearchX size={15} />
        <div>
          <p className={styles.declinedTitle}>Not covered by the documents</p>
          <p>
            I couldn&apos;t find an answer to that in the documents I have access to. Try
            rephrasing, or check with the team that owns the policy.
          </p>
        </div>
      </div>
      <ol className={styles.checks}>
        <li>Every factual sentence carries a citation</li>
        <li>Every citation points to a passage that was retrieved</li>
        <li>A failing draft is corrected once, then withheld</li>
      </ol>
    </div>
  );
}

function FollowUpExample() {
  return (
    <div className={styles.card}>
      <p className={styles.bubble}>How much annual leave do full-time staff get?</p>
      <p className={styles.cardAnswer}>
        Full-time employees receive <strong>25 days</strong> of paid annual leave a year{" "}
        <Cite n={1} />.
      </p>
      <p className={styles.bubble}>And part-timers?</p>
      <p className={styles.rewrite}>
        <CornerDownRight size={13} />
        Searched for: how much annual leave do part-time employees get?
      </p>
      <p className={styles.cardAnswer}>
        Part-time staff receive a pro-rata share based on contracted hours, so three days a week
        gives <strong>15 days</strong> <Cite n={1} />.
      </p>
    </div>
  );
}

export function LandingPage() {
  return (
    <div className={styles.page}>
      <header className={styles.nav}>
        <div className={styles.container}>
          <Wordmark to="/" />
          <nav className={styles.links} aria-label="Page sections">
            <a href="#how-it-works">How it works</a>
            <a href="#evaluation">Evaluation</a>
            <a href="#security">Security</a>
            <a href="#faq">FAQ</a>
          </nav>
          <Link to="/chat" className={styles.navButton}>
            Open the assistant
          </Link>
        </div>
      </header>

      <main>
        <section className={styles.hero}>
          <div className={styles.container}>
            <p className={styles.pill}>
              Hybrid retrieval <span /> Cross-encoder reranking <span /> Enforced citations
            </p>
            <h1 className={styles.headline}>Answers your whole company can check.</h1>
            <p className={styles.lede}>
              Enterprise RAG searches your policies, handbooks and procedures, then answers in plain
              language with a citation on every claim. When the documents don&apos;t cover a
              question, it says so.
            </p>
            <div className={styles.actions}>
              <Link to="/chat" className={styles.primary}>
                Start asking
                <ArrowRight size={16} />
              </Link>
              <a href="#how-it-works" className={styles.secondary}>
                How it works
              </a>
            </div>
            <p className={styles.note}>No sign-up. Conversations stay in your browser.</p>
          </div>
          <div className={styles.previewWrap}>
            <AppPreview />
          </div>
        </section>

        <section className={styles.numbersBand} aria-label="Measured results">
          <dl className={`${styles.container} ${styles.numbers}`}>
            {NUMBERS.map((item) => (
              <div key={item.label}>
                <dt>{item.value}</dt>
                <dd>{item.label}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section className={styles.strip} aria-label="Formats and technology">
          <div className={`${styles.container} ${styles.stripInner}`}>
            <div className={styles.stripGroup}>
              <span className={styles.stripLabel}>Reads</span>
              {FORMATS.map((item) => (
                <span key={item} className={styles.chip}>
                  {item}
                </span>
              ))}
            </div>
            <div className={styles.stripGroup}>
              <span className={styles.stripLabel}>Built on</span>
              {STACK.map((item) => (
                <span key={item} className={styles.chip}>
                  {item}
                </span>
              ))}
            </div>
          </div>
        </section>

        <section id="how-it-works" className={styles.section}>
          <div className={styles.container}>
            <p className={styles.eyebrow}>How it works</p>
            <h2 className={styles.title}>From document to cited answer in four steps</h2>
            <ol className={styles.pipeline}>
              {STAGES.map((stage, index) => (
                <li key={stage.name} className={styles.stage}>
                  <span className={styles.stageNumber}>{String(index + 1).padStart(2, "0")}</span>
                  <h3>{stage.name}</h3>
                  <p>{stage.body}</p>
                  <ul>
                    {stage.tags.map((tag) => (
                      <li key={tag}>{tag}</li>
                    ))}
                  </ul>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className={styles.section}>
          <div className={styles.container}>
            <p className={styles.eyebrow}>Use cases</p>
            <h2 className={styles.title}>Where teams use it</h2>
            <div className={styles.useCases}>
              {USE_CASES.map((item) => (
                <article key={item.team} className={styles.useCase}>
                  <p className={styles.useCaseTeam}>{item.team}</p>
                  <p className={styles.useCaseQuestion}>&ldquo;{item.question}&rdquo;</p>
                  <p className={styles.useCaseBody}>{item.body}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className={styles.section}>
          <div className={`${styles.container} ${styles.features}`}>
            <div className={styles.feature}>
              <div className={styles.featureText}>
                <p className={styles.eyebrow}>Citations</p>
                <h2 className={styles.title}>Every sentence points to its source</h2>
                <p className={styles.body}>
                  Numbered markers link each claim to the exact passage it came from. One click
                  shows the passage beside the answer, and another opens the original file, so
                  people can check before they act.
                </p>
              </div>
              <CitationExample />
            </div>
            <div className={`${styles.feature} ${styles.reverse}`}>
              <div className={styles.featureText}>
                <p className={styles.eyebrow}>Honesty</p>
                <h2 className={styles.title}>It declines instead of guessing</h2>
                <p className={styles.body}>
                  A confident wrong answer about a policy costs more than no answer. Drafts are
                  checked before they are shown, and anything that can&apos;t be backed by the
                  documents is withheld with a clear explanation.
                </p>
              </div>
              <DeclineExample />
            </div>
            <div className={styles.feature}>
              <div className={styles.featureText}>
                <p className={styles.eyebrow}>Conversation</p>
                <h2 className={styles.title}>Follow-up questions just work</h2>
                <p className={styles.body}>
                  Short follow-ups are rewritten into complete questions before searching, so
                  &ldquo;and part-timers?&rdquo; finds the same policy as the question before it.
                </p>
              </div>
              <FollowUpExample />
            </div>
          </div>
        </section>

        <section id="evaluation" className={styles.section}>
          <div className={`${styles.container} ${styles.evaluation}`}>
            <div>
              <p className={styles.eyebrow}>Evaluation</p>
              <h2 className={styles.title}>Measured on every change</h2>
              <p className={styles.body}>
                A fixed set of 49 questions with known answers runs in continuous integration. It
                covers paraphrases, look-alike policies and questions the documents can&apos;t
                answer. If retrieval gets worse, the change is blocked.
              </p>
            </div>
            <div className={styles.tableCard}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Retrieval strategy</th>
                    <th>Right section in top 5</th>
                    <th>Mean reciprocal rank</th>
                  </tr>
                </thead>
                <tbody>
                  {RESULTS.map((row) => (
                    <tr key={row.strategy} className={row.highlight ? styles.best : undefined}>
                      <td>{row.strategy}</td>
                      <td className={styles.numeric}>{row.hit}</td>
                      <td>
                        <span className={styles.bar}>
                          <span style={{ width: `${row.mrr * 100}%` }} />
                        </span>
                        <span className={styles.numeric}>{row.mrr.toFixed(3)}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className={styles.tableNote}>
                Top five results over 41 answerable questions from an eleven-document handbook.
              </p>
            </div>
          </div>
        </section>

        <section id="security" className={styles.section}>
          <div className={styles.container}>
            <p className={styles.eyebrow}>Security and operations</p>
            <h2 className={styles.title}>Built to run inside your organisation</h2>
            <div className={styles.grid}>
              {OPERATIONS.map((item) => (
                <div key={item.title} className={styles.gridItem}>
                  <h3>{item.title}</h3>
                  <p>{item.body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="faq" className={styles.section}>
          <div className={`${styles.container} ${styles.faq}`}>
            <div>
              <p className={styles.eyebrow}>FAQ</p>
              <h2 className={styles.title}>Common questions</h2>
            </div>
            <div className={styles.faqList}>
              {QUESTIONS.map((item) => (
                <details key={item.q} className={styles.faqItem}>
                  <summary>{item.q}</summary>
                  <p>{item.a}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

        <section className={styles.closing}>
          <div className={styles.container}>
            <h2>Your documents already have the answers.</h2>
            <p>Ask the first question. It takes a few seconds.</p>
            <Link to="/chat" className={styles.primary}>
              Start asking
              <ArrowRight size={16} />
            </Link>
          </div>
        </section>
      </main>

      <footer className={styles.footer}>
        <div className={styles.container}>
          <div className={styles.footerBrand}>
            <Wordmark to="/" />
            <p>Cited answers from your organisation&apos;s documents.</p>
          </div>
          <nav className={styles.footerLinks} aria-label="Footer">
            <Link to="/chat">Assistant</Link>
            <Link to="/documents">Documents</Link>
            <Link to="/search">Search inspector</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}

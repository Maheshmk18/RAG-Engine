import { ArrowRight, SearchX } from "lucide-react";
import { Link } from "react-router";
import { Wordmark } from "@/components/Wordmark";
import { useAuth } from "@/lib/authContext";
import styles from "./LandingPage.module.css";

const STEPS = [
  {
    title: "Add your documents",
    body: "Upload PDFs, Word files, Markdown or plain text. Each file is split along its own headings and indexed in the background, usually within a few seconds.",
  },
  {
    title: "Ask in plain language",
    body: "Write the question the way you would ask a colleague. Follow-ups work too, so “and for part-time staff?” is understood in the context of the conversation.",
  },
  {
    title: "Check the source",
    body: "Numbered markers tie every sentence to the passage it came from. One click shows that passage, and another opens the original file.",
  },
];

const NUMBERS = [
  { value: "49", label: "questions in the evaluation set, including eight it should refuse" },
  { value: "100%", label: "of answerable questions had the right section in the top five results" },
  { value: "0.98", label: "mean reciprocal rank: the right passage is almost always ranked first" },
  { value: "6 of 8", label: "off-topic questions turned away before a language model is called" },
];

const ADMIN = [
  {
    title: "Accounts you control",
    body: "There is no public sign-up. Administrators add people and decide who can manage documents.",
  },
  {
    title: "Documents stay in your database",
    body: "Files, extracted text and search vectors are stored in a single PostgreSQL database you run.",
  },
  {
    title: "Search models run inside the service",
    body: "Embedding and ranking happen locally. Only the question and the selected passages are sent to the language model.",
  },
  {
    title: "A search inspector",
    body: "See which passages a question retrieves and how each stage scored them, before you blame the model.",
  },
];

function Cite({ n, active }: { n: number; active?: boolean }) {
  return <span className={`${styles.cite} ${active ? styles.citeActive : ""}`}>{n}</span>;
}

function ProductPreview() {
  return (
    <figure className={styles.preview} aria-label="Example of an answer with its source">
      <div className={styles.previewChat}>
        <p className={styles.previewQuestion}>Can I carry unused holiday into next year?</p>
        <div className={styles.previewAnswer}>
          <p>
            Yes, up to <strong>5 unused days</strong> <Cite n={1} active />. They have to be taken
            by <strong>31 March</strong>, after which they are forfeited <Cite n={1} active />.
          </p>
          <p>
            Days above the limit are lost at the end of the year and are not paid out{" "}
            <Cite n={1} active />.
          </p>
        </div>
        <div className={styles.previewSources}>
          <span className={styles.previewNumber}>1</span>
          <span className={styles.previewTitle}>Annual Leave Policy</span>
          <span className={styles.previewHeading}>Carry-Over</span>
        </div>
      </div>
      <aside className={styles.previewSource}>
        <span className={styles.previewEyebrow}>Source 1</span>
        <p className={styles.previewDoc}>Annual Leave Policy</p>
        <blockquote>
          Employees may carry over a maximum of 5 unused days into the next calendar year.
          Carried-over days must be used by 31 March of the following year, after which they are
          forfeited.
        </blockquote>
      </aside>
    </figure>
  );
}

export function LandingPage() {
  const { status } = useAuth();
  const signedIn = status === "signed-in";
  const primary = signedIn
    ? { to: "/chat", label: "Open Ask My Docs" }
    : { to: "/login", label: "Sign in" };

  return (
    <div className={styles.page}>
      <header className={styles.nav}>
        <div className={styles.container}>
          <Wordmark to="/" />
          <nav className={styles.links} aria-label="Page sections">
            <a href="#how-it-works">How it works</a>
            <a href="#accuracy">Accuracy</a>
            <a href="#administration">For administrators</a>
          </nav>
          <Link to={primary.to} className={styles.navButton}>
            {signedIn ? "Open app" : "Sign in"}
          </Link>
        </div>
      </header>

      <main>
        <section className={`${styles.container} ${styles.hero}`}>
          <div className={styles.heroText}>
            <p className={styles.kicker}>For policies, handbooks and internal guides</p>
            <h1 className={styles.headline}>
              Ask the handbook.
              <br />
              Get the answer <em>and</em> the paragraph it came from.
            </h1>
            <p className={styles.lede}>
              Ask My Docs reads your organisation&apos;s documents and answers questions in plain
              language. Every sentence cites its source, and when the documents don&apos;t say, it
              tells you so instead of guessing.
            </p>
            <div className={styles.actions}>
              <Link to={primary.to} className={styles.primary}>
                {primary.label}
                <ArrowRight size={16} />
              </Link>
              <a href="#how-it-works" className={styles.secondary}>
                See how it works
              </a>
            </div>
            {!signedIn && <p className={styles.note}>Accounts are set up by your administrator.</p>}
          </div>
          <ProductPreview />
        </section>

        <section id="how-it-works" className={styles.section}>
          <div className={styles.container}>
            <h2 className={styles.sectionTitle}>How it works</h2>
            <ol className={styles.steps}>
              {STEPS.map((step, index) => (
                <li key={step.title} className={styles.step}>
                  <span className={styles.stepNumber}>{String(index + 1).padStart(2, "0")}</span>
                  <h3>{step.title}</h3>
                  <p>{step.body}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className={styles.section}>
          <div className={`${styles.container} ${styles.split}`}>
            <div>
              <h2 className={styles.sectionTitle}>It says when it doesn&apos;t know</h2>
              <p className={styles.sectionBody}>
                A confident wrong answer about a policy costs more than no answer. Before anything
                is shown, the draft is checked: every claim needs a citation, and every citation has
                to point at a real passage. A draft that fails is corrected once. If it still fails,
                you are told the documents don&apos;t cover the question.
              </p>
            </div>
            <div className={styles.declined}>
              <p className={styles.previewQuestion}>How many days of bereavement leave do I get?</p>
              <div className={styles.declinedCard}>
                <SearchX size={16} />
                <div>
                  <p className={styles.declinedTitle}>Not covered by the documents</p>
                  <p>
                    I couldn&apos;t find an answer to that in the documents I have access to. Try
                    rephrasing, or check with the team that owns the policy.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="accuracy" className={styles.section}>
          <div className={styles.container}>
            <h2 className={styles.sectionTitle}>Measured, not promised</h2>
            <p className={styles.sectionBody}>
              Every change is tested against a fixed set of questions with known answers. If
              retrieval gets worse, the change doesn&apos;t ship.
            </p>
            <dl className={styles.numbers}>
              {NUMBERS.map((item) => (
                <div key={item.label} className={styles.number}>
                  <dt>{item.value}</dt>
                  <dd>{item.label}</dd>
                </div>
              ))}
            </dl>
          </div>
        </section>

        <section id="administration" className={styles.section}>
          <div className={styles.container}>
            <h2 className={styles.sectionTitle}>For administrators</h2>
            <div className={styles.adminGrid}>
              {ADMIN.map((item) => (
                <div key={item.title} className={styles.adminItem}>
                  <h3>{item.title}</h3>
                  <p>{item.body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className={styles.closing}>
          <div className={styles.container}>
            <h2>Your handbook already has the answers.</h2>
            <Link to={primary.to} className={styles.primary}>
              {primary.label}
              <ArrowRight size={16} />
            </Link>
          </div>
        </section>
      </main>

      <footer className={styles.footer}>
        <div className={styles.container}>
          <Wordmark to="/" />
          <p>Answers from your documents, with sources.</p>
        </div>
      </footer>
    </div>
  );
}

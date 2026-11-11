const nav = ["Dashboard", "New purchase", "Sourcing", "Agreements", "Transactions"];

export default function Home() {
  return <main className="shell">
    <aside className="sidebar"><a className="wordmark" href="#home">CHOAM<span>●</span></a><p className="eyebrow">COMMERCE OPERATIONS</p>
      <nav aria-label="Main navigation">{nav.map((item, i) => <a className={i === 0 ? "nav-item active" : "nav-item"} href="#workspace" key={item}><span className="nav-index">0{i + 1}</span>{item}</a>)}</nav>
      <div className="sidebar-note"><span className="status-dot" /> System standing by</div>
    </aside>
    <section className="workspace" id="workspace"><header className="topbar"><span>WORKSPACE / OVERVIEW</span><span className="environment">DEMO ENVIRONMENT</span></header>
      <div className="content" id="home"><div className="intro"><p className="eyebrow">AUTONOMOUS PROCUREMENT, ACCOUNTABLE BY DESIGN</p><h1>Commerce,<br/><em>with rules.</em></h1><p className="lede">Let agents negotiate the details. Keep the authority to decide what gets transacted.</p></div>
        <div className="section-heading"><div><p className="eyebrow">CONTROL PLANE</p><h2>Transaction overview</h2></div><span className="pill"><span className="status-dot"/> All systems idle</span></div>
        <div className="metrics"><article><p>ACTIVE REQUESTS</p><strong>—</strong><small>No procurement requests yet</small></article><article><p>AGREEMENTS TO REVIEW</p><strong>—</strong><small>Buyer approval required</small></article><article><p>VERIFIED PAYMENTS</p><strong>—</strong><small>Sandbox transactions only</small></article></div>
        <section className="principle"><div className="principle-mark">✳</div><div><p className="eyebrow">THE CHOAM PRINCIPLE</p><h3>Negotiation is autonomous.<br/>Authorization is not.</h3><p>Every agreement is checked against the buyer’s confirmed requirements. Payment stays locked until the exact validated terms are approved.</p></div></section>
        <footer><span>CHOAM / TRUST INFRASTRUCTURE FOR AUTONOMOUS COMMERCE</span><span>BUILD 0.1.0</span></footer>
      </div>
    </section>
  </main>;
}

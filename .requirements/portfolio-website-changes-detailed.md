# Portfolio Website Changes — Detailed Specifications
**Version:** 1.0  
**Focus:** Immediate changes to support SEO + lead gen strategy  
**Last Updated:** 2026-04-21

---

## Change 1: Homepage Hero — Keyword Optimization

### Current State
```html
<h1>Arpit Maheshwari — Product Designer · AI & Data-Intensive Products | 15 Years</h1>
```

### Problem
- Vague positioning ("AI & Data-Intensive Products" is too generic)
- Doesn't explicitly target primary keyword "AI product designer"
- Doesn't convey credibility (15 years buried, not prominent)

### Recommended Change

**Option A (Recommended — Direct Keyword Match):**
```html
<h1>
  <span class="line">
    <span class="line-inner">
      AI Product Designer
    </span>
  </span>
  <span class="line">
    <span class="line-inner">
      15 Years Designing <em>Data-Intensive Systems</em>
    </span>
  </span>
</h1>
```

**Rationale:** 
- Line 1: Leads with primary keyword ("AI Product Designer")
- Line 2: Adds credibility (15 years) + secondary keyword ("Data-Intensive Systems")
- Italics on "Data-Intensive Systems" adds visual emphasis + semantic weight

---

**Option B (If you prefer softer positioning):**
```html
<h1>
  <span class="line">
    <span class="line-inner">
      Design for <em>AI Products</em>
    </span>
  </span>
  <span class="line">
    <span class="line-inner">
      15 Years of Data-Intensive Product Design
    </span>
  </span>
</h1>
```

**Rationale:** 
- Softer, more editorial
- Still targets keywords naturally
- Emphasizes approach ("design FOR AI") not title

---

### Meta Tag Updates

**Current:**
```html
<title>Arpit Maheshwari — Product Designer · AI & Data-Intensive Products | 15 Years</title>
<meta name="description" content="Arpit Maheshwari — Product designer specialising in AI and data-intensive products. 15 years designing intelligent interfaces across AdTech, FinTech, EdTech & Telecom. Based in Indore, India. Remote.">
```

**Recommended:**
```html
<title>AI Product Designer — 15 Years Data-Intensive Product Design | Arpit Maheshwari</title>
<meta name="description" content="AI product designer with 15 years designing data-intensive systems across fintech, adtech, and edtech. Specializing in machine learning interfaces, complex data visualization, and accessible AI products. Available for contracts and full-time roles.">
```

**Why:**
- Title: Leads with primary keyword "AI Product Designer" + secondary keyword "Data-Intensive"
- Description: Targets all 5 keywords naturally, includes audience segment (fintech, adtech, edtech), includes call-to-action (contracts + roles)
- Character count: ~155 chars (optimal for Google display)

---

## Change 2: Add Substack Link (Navigation + Hero)

### Option A: Navigation Bar

**Current nav structure:**
```html
<nav>
  <div class="nav-logo">AM</div>
  <ul class="nav-links">
    <li><a href="#work">Work</a></li>
    <li><a href="#expertise">Expertise</a></li>
    <li><a href="#contact">Contact</a></li>
  </ul>
  <a href="#contact" class="nav-cta">Let's Talk</a>
</nav>
```

**Add Substack link (2 options):**

**Option A1: Add to nav-links**
```html
<nav>
  <div class="nav-logo">AM</div>
  <ul class="nav-links">
    <li><a href="#work">Work</a></li>
    <li><a href="#expertise">Expertise</a></li>
    <li><a href="https://data-intensive-thinking.substack.com" target="_blank">Insights</a></li>
    <li><a href="#contact">Contact</a></li>
  </ul>
  <a href="https://data-intensive-thinking.substack.com?subscribe=true" class="nav-cta" target="_blank">Subscribe</a>
</nav>
```

**Rationale:** "Insights" → Substack, "Subscribe" → CTA button. Simple, clear hierarchy.

---

**Option A2: Replace "Let's Talk" with dual CTA**
```html
<nav>
  <div class="nav-logo">AM</div>
  <ul class="nav-links">
    <li><a href="#work">Work</a></li>
    <li><a href="#expertise">Expertise</a></li>
    <li><a href="#contact">Contact</a></li>
  </ul>
  <div class="nav-actions">
    <a href="https://data-intensive-thinking.substack.com" class="nav-link-subtle" target="_blank">Insights</a>
    <a href="#contact" class="nav-cta">Let's Talk</a>
  </div>
</nav>
```

**Add CSS:**
```css
.nav-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.nav-link-subtle {
  font-size: 13px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-muted);
  transition: color 0.2s;
}

.nav-link-subtle:hover {
  color: var(--ink);
}
```

**Rationale:** Subtle "Insights" link (newsletter discovery) + primary CTA (projects/contact).

---

### Option B: Hero Section

Add a secondary CTA below main hero content:

```html
<div class="hero-sub">
  <div class="hero-desc">
    <p>15 years designing AI and data-intensive products across fintech, adtech, and edtech...</p>
  </div>
  <div class="hero-meta">
    <!-- Existing stats -->
    <div class="hero-stats">...</div>
  </div>
</div>

<!-- NEW: Add this below hero -->
<div class="hero-cta-secondary">
  <p>Weekly insights on designing for AI products:</p>
  <a href="https://data-intensive-thinking.substack.com?subscribe=true" class="btn-substack" target="_blank">
    Subscribe to Data-Intensive Thinking
    <svg class="icon" viewBox="0 0 24 24">
      <path d="M5 12h14M12 5l7 7-7 7"/>
    </svg>
  </a>
</div>
```

**Add CSS:**
```css
.hero-cta-secondary {
  margin-top: 60px;
  padding: 32px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg-card);
  text-align: center;
}

.hero-cta-secondary p {
  font-size: 14px;
  color: var(--ink-muted);
  margin-bottom: 16px;
}

.btn-substack {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  background: transparent;
  border: 1px solid var(--gold);
  color: var(--gold);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  border-radius: 2px;
  transition: background 0.3s, color 0.3s;
}

.btn-substack:hover {
  background: var(--gold);
  color: var(--bg);
}
```

**Rationale:** Prominent but non-intrusive. Offers newsletter to interested visitors without disrupting main CTA (contact).

---

## Change 3: Case Study Landing Pages

### Current Structure
Single-page portfolio with case cards (visual-only).

```html
<div class="case-card featured">
  <div class="case-visual"><!-- SVG visual --></div>
  <div class="case-body">
    <div class="case-sector">AdTech</div>
    <h3 class="case-title">Designing ML Model Interpretability</h3>
    <p class="case-desc">Redesigned feedback loop...</p>
    <div class="case-metrics">...</div>
  </div>
</div>
```

### Recommended New Structure

**URL Path:**
```
/case-studies/[slug].html
Examples:
  - /case-studies/adtech-ml-platform.html
  - /case-studies/fintech-screening-tool.html
  - /case-studies/edtech-learning-analytics.html
```

**Individual Case Study Page Template:**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <!-- Standard head + these optimized meta tags -->
  <title>ML Model Interpretability Design — AdTech Platform | Arpit Maheshwari</title>
  <meta name="description" content="Case study: Designed ML model interpretability interface for top-5 AdTech platform. Focus on making black-box algorithms transparent to non-technical users. Problem, approach, and solution.">
  
  <!-- Structured data for case study -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "ML Model Interpretability Design — AdTech Platform",
    "description": "Case study on designing transparent ML interfaces for complex algorithmic systems",
    "image": "https://arpitmaheshwari.com/case-studies/adtech-ml-platform-cover.jpg",
    "author": {
      "@type": "Person",
      "name": "Arpit Maheshwari"
    },
    "datePublished": "2026-04-21"
  }
  </script>
</head>

<body>
  <!-- Breadcrumb navigation (SEO + UX) -->
  <nav class="breadcrumb">
    <a href="/">Home</a>
    <span>/</span>
    <a href="/#work">Work</a>
    <span>/</span>
    <span>ML Model Interpretability</span>
  </nav>

  <!-- Case Study Hero -->
  <section class="case-study-hero">
    <div class="case-study-header">
      <span class="case-sector">AdTech</span>
      <h1>Designing ML Model Interpretability for Non-Technical Users</h1>
      <p class="case-tagline">Making black-box algorithms transparent and actionable</p>
    </div>
    
    <div class="case-visual-large">
      <!-- Large visual/screenshot of the work -->
      <img src="case-studies/adtech-ml-platform-visual.jpg" alt="ML interpretability interface design">
    </div>
  </section>

  <!-- Case Study Content -->
  <section class="case-study-content">
    <div class="case-study-inner">
      
      <!-- Problem Statement -->
      <div class="case-section">
        <h2>The Problem</h2>
        <p>
          A top-5 AdTech platform had built sophisticated machine learning models to optimize ad performance. 
          But their users—advertisers and marketing managers—couldn't understand *why* the algorithm made certain decisions.
        </p>
        <p>
          This created two friction points:
        </p>
        <ul>
          <li><strong>Trust gap:</strong> Users doubted the algorithm and second-guessed recommendations</li>
          <li><strong>Adoption gap:</strong> New features were ignored because users didn't understand the value</li>
        </ul>
        <p>
          The platform needed to make algorithmic decision-making transparent without requiring technical expertise.
        </p>
      </div>

      <!-- Design Approach -->
      <div class="case-section">
        <h2>Design Approach</h2>
        
        <h3>Research & Discovery</h3>
        <p>
          Started by understanding how advertisers currently interact with algorithms. Key insights:
        </p>
        <ul>
          <li>70% of users couldn't articulate why a recommendation was made</li>
          <li>Most users focused on *outcome* (did it work?) not *process* (how did it decide?)</li>
          <li>Visual explanations were more trusted than text-only explanations</li>
        </ul>

        <h3>Design Principles</h3>
        <p>Based on research, we established three principles:</p>
        <ul>
          <li><strong>Progressive Disclosure:</strong> Show simple explanation first, detailed breakdowns on demand</li>
          <li><strong>Visual First:</strong> Use charts and diagrams before text</li>
          <li><strong>Action-Oriented:</strong> Every explanation should suggest a next step</li>
        </ul>

        <h3>Solution: Explanation Layer</h3>
        <p>
          Designed a new UI layer that sits between the algorithm output and user action. For each recommendation, users see:
        </p>
        <ul>
          <li><strong>What changed:</strong> "Increased budget for this campaign by 15%"</li>
          <li><strong>Why it changed:</strong> Visual breakdown of factors (performance history, seasonal trends, competitor activity)</li>
          <li><strong>What you can do:</strong> "Accept recommendation" or "Adjust manually"</li>
        </ul>

        <p>
          This reduced the cognitive load from "Why did the algorithm do this?" to "Do I agree with this?"
        </p>
      </div>

      <!-- What Changed / Results -->
      <div class="case-section">
        <h2>What Shipped</h2>
        <p>
          The solution rolled out in three phases over 6 months:
        </p>
        <ul>
          <li><strong>Phase 1:</strong> Simple explanation cards (what + why) for core recommendations</li>
          <li><strong>Phase 2:</strong> Interactive breakdowns (drill into factors influencing decision)</li>
          <li><strong>Phase 3:</strong> Explanation history (audit trail of recommendations + outcomes)</li>
        </ul>
        
        <p>
          Result: Users engaged more with recommendations, adopted new features faster, and reported higher confidence in algorithmic decisions.
        </p>
      </div>

      <!-- Takeaways -->
      <div class="case-section">
        <h2>Key Takeaways</h2>
        <ul>
          <li>Making algorithms transparent isn't about adding more information—it's about structuring information for understanding</li>
          <li>Visual explanations build trust faster than technical explanations</li>
          <li>Progressive disclosure reduces cognitive overload in complex systems</li>
        </ul>
      </div>

    </div>

    <!-- Sidebar: Meta Info -->
    <aside class="case-study-sidebar">
      <div class="case-meta-box">
        <h3>Role</h3>
        <p>Lead Product Designer</p>
      </div>
      
      <div class="case-meta-box">
        <h3>Team</h3>
        <p>1 Designer (me), 2 Engineers, 1 Product Manager</p>
      </div>
      
      <div class="case-meta-box">
        <h3>Timeline</h3>
        <p>6 months (discovery + design + shipping)</p>
      </div>

      <div class="case-meta-box">
        <h3>Sector</h3>
        <p>AdTech</p>
      </div>

      <div class="case-meta-box">
        <h3>Skills Demonstrated</h3>
        <ul>
          <li>User research & discovery</li>
          <li>Complex systems design</li>
          <li>Visual design for clarity</li>
          <li>Cross-functional collaboration</li>
          <li>Design systems thinking</li>
        </ul>
      </div>

      <!-- Testimonial (if available) -->
      <div class="case-meta-box testimonial-box">
        <blockquote>
          <p>"Arpit transformed how we think about algorithm explainability. The design made complex models accessible to non-technical users."</p>
          <p class="attribution">— Product Lead, AdTech Platform</p>
        </blockquote>
      </div>
    </aside>
  </section>

  <!-- CTA Section -->
  <section class="case-study-cta">
    <div class="case-study-inner">
      <h2>Interested in Similar Work?</h2>
      <p>I help teams design interfaces for complex, data-intensive systems.</p>
      <a href="/#contact" class="btn-primary">Let's Discuss Your Project</a>
      <a href="https://data-intensive-thinking.substack.com" class="btn-secondary" target="_blank">Read My Insights</a>
    </div>
  </section>

  <!-- Related Case Studies -->
  <section class="related-cases">
    <h2>Related Work</h2>
    <div class="case-grid">
      <!-- Link to 2-3 related case studies -->
    </div>
  </section>

</body>
</html>
```

### CSS for Case Study Pages

```css
/* Case Study Hero */
.case-study-hero {
  padding: 120px 48px 60px;
  max-width: 1280px;
  margin: 0 auto;
}

.case-study-header h1 {
  font-family: var(--ff-display);
  font-size: clamp(36px, 5vw, 60px);
  font-weight: 300;
  line-height: 1.15;
  margin-bottom: 16px;
}

.case-sector {
  font-family: var(--ff-mono);
  font-size: 10px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--gold);
  display: block;
  margin-bottom: 12px;
}

.case-tagline {
  font-size: 18px;
  color: var(--ink-muted);
  margin-bottom: 40px;
}

.case-visual-large {
  aspect-ratio: 16 / 10;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 4px;
  overflow: hidden;
}

.case-visual-large img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Case Study Content */
.case-study-content {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 80px;
  padding: 80px 48px;
  max-width: 1280px;
  margin: 0 auto;
}

.case-study-inner {
  flex: 1;
}

.case-section {
  margin-bottom: 60px;
}

.case-section h2 {
  font-family: var(--ff-display);
  font-size: 32px;
  font-weight: 400;
  margin-bottom: 24px;
  color: var(--ink);
}

.case-section h3 {
  font-weight: 600;
  font-size: 16px;
  margin-top: 24px;
  margin-bottom: 12px;
}

.case-section p {
  font-size: 15px;
  line-height: 1.8;
  color: var(--ink-muted);
  margin-bottom: 16px;
}

.case-section ul {
  list-style: none;
  margin-bottom: 16px;
}

.case-section ul li {
  font-size: 15px;
  line-height: 1.8;
  color: var(--ink-muted);
  margin-bottom: 12px;
  padding-left: 20px;
  position: relative;
}

.case-section ul li::before {
  content: '→';
  position: absolute;
  left: 0;
  color: var(--gold);
}

/* Sidebar */
.case-study-sidebar {
  position: sticky;
  top: 120px;
  height: fit-content;
}

.case-meta-box {
  padding: 24px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg-card);
  margin-bottom: 16px;
}

.case-meta-box h3 {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--gold);
  margin-bottom: 12px;
}

.case-meta-box p {
  font-size: 13px;
  color: var(--ink-muted);
  line-height: 1.7;
}

.testimonial-box blockquote {
  border-left: 2px solid var(--gold);
  padding-left: 16px;
}

.testimonial-box blockquote p {
  font-style: italic;
  font-size: 13px;
  margin-bottom: 12px;
}

.attribution {
  font-size: 11px !important;
  color: var(--ink-dim) !important;
  font-style: normal;
}

/* CTA Section */
.case-study-cta {
  background: var(--bg-soft);
  border-top: 1px solid var(--border);
  padding: 80px 48px;
  text-align: center;
}

.case-study-cta h2 {
  font-family: var(--ff-display);
  font-size: 42px;
  font-weight: 300;
  margin-bottom: 16px;
}

.case-study-cta p {
  font-size: 16px;
  color: var(--ink-muted);
  margin-bottom: 32px;
}

/* Responsive */
@media (max-width: 1024px) {
  .case-study-content {
    grid-template-columns: 1fr;
    gap: 48px;
  }
  
  .case-study-sidebar {
    position: static;
  }
}
```

### Implementation Steps

1. **Create folder:** `/case-studies/`
2. **Create pages:** One HTML file per case study
3. **Update homepage:** Link case cards to `/case-studies/[slug].html`
4. **Add breadcrumbs:** Navigate back to home/work
5. **Link between cases:** "Related work" section at bottom

---

## Change 4: Conversion CTAs (By Audience)

### Current State
Generic single CTA: "Let's discuss" / contact form

### Problem
Different audiences have different intents:
- **Freelance buyers:** Want to hire for a project (book a call)
- **Employers/recruiters:** Want to evaluate for full-time role (schedule conversation)
- **Thought leaders:** Want to follow your insights (newsletter)

Single CTA doesn't serve all three.

### Recommended Changes

### A. Contact Section — Segment CTAs

**Current:**
```html
<section id="contact">
  <div class="contact-inner">
    <h2>Let's Create Something Great</h2>
    <p>Whether you're building an AI product or scaling a data-intensive system, I'd love to discuss how we can work together.</p>
    <div class="contact-actions">
      <a href="#" class="btn-primary">Get In Touch</a>
    </div>
  </div>
</section>
```

**Recommended:**
```html
<section id="contact">
  <div class="contact-inner">
    <h2>Let's Work Together</h2>
    
    <!-- Audience 1: Project-based (Freelance) -->
    <div class="contact-segment">
      <h3>Have a Project in Mind?</h3>
      <p>I take on freelance and contract work designing AI and data-intensive products.</p>
      <a href="https://calendar.app.google.com/[your-calendar]" class="btn-primary" target="_blank">
        Schedule a Project Call
      </a>
    </div>

    <!-- Audience 2: Full-time (Employers) -->
    <div class="contact-segment">
      <h3>Looking to Hire?</h3>
      <p>Open to full-time roles, advisory positions, and long-term partnerships with companies building AI products.</p>
      <a href="https://calendar.app.google.com/[your-calendar]" class="btn-primary" target="_blank">
        Schedule a Conversation
      </a>
    </div>

    <!-- Audience 3: Thought Leadership (Newsletter) -->
    <div class="contact-segment">
      <h3>Stay Updated</h3>
      <p>Get weekly insights on designing for AI products—patterns, principles, and real work.</p>
      <a href="https://data-intensive-thinking.substack.com?subscribe=true" class="btn-secondary" target="_blank">
        Subscribe to Insights
      </a>
    </div>

    <!-- Direct contact -->
    <div class="contact-segment">
      <h3>Prefer Email?</h3>
      <p>Reach out directly at <a href="mailto:hi@arpitmaheshwari.com">hi@arpitmaheshwari.com</a></p>
    </div>
  </div>
</section>
```

**CSS for segmented CTAs:**
```css
.contact-segment {
  padding: 32px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg-card);
  margin-bottom: 24px;
  transition: border-color 0.3s, transform 0.3s var(--ease-out);
}

.contact-segment:hover {
  border-color: var(--border-accent);
  transform: translateY(-3px);
}

.contact-segment h3 {
  font-weight: 600;
  font-size: 18px;
  margin-bottom: 12px;
}

.contact-segment p {
  font-size: 15px;
  color: var(--ink-muted);
  margin-bottom: 20px;
  line-height: 1.7;
}

.contact-segment a {
  display: inline-block;
  padding: 12px 24px;
  background: var(--gold);
  color: var(--bg);
  font-weight: 600;
  font-size: 13px;
  letter-spacing: 0.05em;
  border-radius: 2px;
  transition: background 0.3s;
}

.contact-segment a:hover {
  background: var(--gold-light);
}
```

---

### B. Case Study Page CTAs

Add segmented CTA to bottom of each case study:

```html
<section class="case-study-cta">
  <div class="case-study-inner">
    <h2>Need Similar Work?</h2>
    
    <div class="cta-options">
      <div class="cta-option">
        <h3>Discussing a Project?</h3>
        <a href="https://calendar.app.google.com/[your-calendar]" class="btn-primary" target="_blank">
          Book a Call
        </a>
      </div>
      
      <div class="cta-option">
        <h3>Exploring Design Approaches?</h3>
        <a href="https://data-intensive-thinking.substack.com" class="btn-secondary" target="_blank">
          Read Similar Insights
        </a>
      </div>
    </div>
  </div>
</section>
```

---

## Change 5: Meta Tags Optimization

### Current Meta Tags
```html
<title>Arpit Maheshwari — Product Designer · AI & Data-Intensive Products | 15 Years</title>
<meta name="description" content="Arpit Maheshwari — Product designer specialising in AI and data-intensive products. 15 years designing intelligent interfaces across AdTech, FinTech, EdTech & Telecom. Based in Indore, India. Remote.">
<meta name="keywords" content="AI product designer, UX designer India, product design strategy, AdTech designer, FinTech UX, ML interface design, data-intensive UX, accessible design, Arpit Maheshwari, Indore designer, remote product designer, intelligent interfaces">
```

### Optimized Meta Tags

```html
<!-- Primary keyword focus -->
<title>AI Product Designer — 15 Years Data-Intensive Systems | Arpit Maheshwari</title>
<meta name="description" content="AI product designer with 15 years designing data-intensive systems. Specialized in machine learning interfaces, fintech UX, and complex data visualization. Available for contracts and full-time roles. Remote.">

<!-- Keywords (still useful for context, though less critical than before) -->
<meta name="keywords" content="AI product designer, data-intensive product design, machine learning interface design, fintech UX designer, designing for AI, product designer India, remote designer">

<!-- Open Graph (social sharing) -->
<meta property="og:title" content="AI Product Designer — 15 Years Data-Intensive Systems">
<meta property="og:description" content="Designing AI products and data-intensive systems across fintech, adtech, and edtech. 15 years of experience.">
<meta property="og:image" content="https://arpitmaheshwari.com/og-image.jpg">
<meta property="og:url" content="https://arpitmaheshwari.com/">

<!-- Twitter Card -->
<meta name="twitter:title" content="AI Product Designer — Arpit Maheshwari">
<meta name="twitter:description" content="15 years designing data-intensive products for AI systems.">
<meta name="twitter:image" content="https://arpitmaheshwari.com/og-image.jpg">
<meta name="twitter:creator" content="@arp_maheshwari">

<!-- Canonical (important if syndicating content) -->
<link rel="canonical" href="https://arpitmaheshwari.com/">
```

### Why These Changes

| Element | Why |
|---------|-----|
| **Title:** Lead with keyword | Google weights first 60 chars heavily. "AI Product Designer" appears immediately. |
| **Description:** Target all 5 keywords naturally | Meta description is what Google shows in search results. Should be compelling + keyword-rich. |
| **Keyword tag:** Less critical but still used | Modern Google relies less on keyword tag, but it doesn't hurt. |
| **OG tags:** Social sharing + SEO signal | Improves shareability + signals importance to search engines. |
| **Twitter Card:** Specific to Twitter sharing | Ensures portfolio looks good when shared on Twitter. |

---

## Change 6: Internal Linking Structure (Bonus)

### Current State
Single-page site: Limited internal linking opportunities.

### Recommended: Link case studies ↔ Substack

**Example 1: Link from case study to relevant article**
```html
<!-- Bottom of case study page -->
<div class="related-reading">
  <h3>Read More</h3>
  <p>Interested in the design approach behind this work?</p>
  <a href="https://data-intensive-thinking.substack.com/p/[article-slug]">
    Read: "Explainability Patterns in ML Interfaces"
  </a>
</div>
```

**Example 2: Link from Substack article to case study**
```markdown
# [Article Title]

In a recent project, I worked with an AdTech platform facing a similar challenge...

[See the case study: ML Model Interpretability Design](https://arpitmaheshwari.com/case-studies/adtech-ml-platform.html)
```

**Why:** Improves SEO (internal linking boosts page authority) + keeps visitors engaged.

---

## Implementation Timeline

| Change | Effort | Week 1 | Week 2-3 | Week 4 |
|--------|--------|--------|----------|--------|
| 1. Hero optimization | 30 min | ✅ | — | — |
| 2. Substack link | 30 min | ✅ | — | — |
| 3. Case study pages | 6-8 hrs | Plan | Create | Launch |
| 4. Segmented CTAs | 2 hrs | — | ✅ | — |
| 5. Meta tags | 1 hr | ✅ | — | — |
| 6. Internal linking | 2 hrs | — | — | ✅ |

---

## Files to Create/Modify

```
portfolio/
├── index.html [MODIFY: hero, nav, meta tags, CTAs]
├── case-studies/ [NEW FOLDER]
│   ├── adtech-ml-platform.html [NEW]
│   ├── fintech-screening-tool.html [NEW]
│   └── edtech-learning-analytics.html [NEW]
└── styles.css [MODIFY: case study + CTA styles]
```

---

## Quick Checklist

**Week 1:**
- [ ] Update `<h1>` in hero (Option A or B)
- [ ] Update `<title>` + `<meta name="description">`
- [ ] Add Substack link in nav (Option A1 or A2)
- [ ] Add Substack CTA in hero (Option B)

**Week 2-3:**
- [ ] Create 3-4 case study pages (use template above)
- [ ] Add case study CSS
- [ ] Update homepage case cards to link to new pages

**Week 4:**
- [ ] Segment CTAs in contact section
- [ ] Add case study page CTAs
- [ ] Internal linking (case studies ↔ Substack)

---

## Questions on Any of These Changes?

Point me to which ones need more detail, and I'll expand.

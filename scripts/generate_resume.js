const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, BorderStyle, WidthType, ShadingType, LevelFormat,
  ExternalHyperlink, TabStopType, TabStopPosition, UnderlineType,
  HeadingLevel, PageNumber, Header, Footer
} = require('docx');
const fs = require('fs');

// ── Helpers ───────────────────────────────────────────────────────────────────
const BLUE    = "1F3864";
const LBLUE   = "2563EB";
const GRAY    = "6B7280";
const BLACK   = "111827";
const WHITE   = "FFFFFF";
const RULE_COLOR = "2563EB";

const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

// Section divider — blue bottom border on a paragraph
function sectionHeading(text) {
  return new Paragraph({
    spacing: { before: 200, after: 80 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: RULE_COLOR, space: 4 } },
    children: [
      new TextRun({
        text: text.toUpperCase(),
        bold: true,
        size: 22,
        font: "Arial",
        color: BLUE,
        characterSpacing: 40,
      })
    ]
  });
}

function bullet(text, bold_prefix = null) {
  const children = [];
  if (bold_prefix) {
    children.push(new TextRun({ text: bold_prefix + ": ", bold: true, size: 20, font: "Arial", color: BLACK }));
  }
  children.push(new TextRun({ text: bold_prefix ? text : text, size: 20, font: "Arial", color: BLACK }));
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 20, after: 20 },
    children,
  });
}

function jobHeader(title, company, date, location) {
  return new Paragraph({
    spacing: { before: 140, after: 30 },
    tabStops: [{ type: TabStopType.RIGHT, position: 9360 }],
    children: [
      new TextRun({ text: title, bold: true, size: 22, font: "Arial", color: BLACK }),
      new TextRun({ text: "\t", size: 22, font: "Arial" }),
      new TextRun({ text: date, size: 20, font: "Arial", color: GRAY, italics: true }),
    ]
  });
}

function companyLine(company, location) {
  return new Paragraph({
    spacing: { before: 0, after: 40 },
    children: [
      new TextRun({ text: company, size: 20, font: "Arial", color: LBLUE, bold: true }),
      new TextRun({ text: "  ·  " + location, size: 20, font: "Arial", color: GRAY }),
    ]
  });
}

function projectHeader(title, stack) {
  return new Paragraph({
    spacing: { before: 120, after: 30 },
    children: [
      new TextRun({ text: title, bold: true, size: 20, font: "Arial", color: BLACK }),
      new TextRun({ text: "  |  Stack: " + stack, size: 19, font: "Arial", color: GRAY, italics: true }),
    ]
  });
}

function skillRow(category, skills) {
  return new Paragraph({
    spacing: { before: 30, after: 30 },
    children: [
      new TextRun({ text: category + ": ", bold: true, size: 20, font: "Arial", color: BLACK }),
      new TextRun({ text: skills, size: 20, font: "Arial", color: BLACK }),
    ]
  });
}

function emptyLine(size = 80) {
  return new Paragraph({ spacing: { before: 0, after: 0 }, children: [new TextRun({ text: "", size })] });
}

// ── Document ──────────────────────────────────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{
        level: 0,
        format: LevelFormat.BULLET,
        text: "•",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 440, hanging: 280 } } }
      }]
    }]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 900, right: 1080, bottom: 900, left: 1080 }
      }
    },
    children: [

      // ── NAME & CONTACT ────────────────────────────────────────────────────
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 60 },
        children: [
          new TextRun({ text: "SAMDARSH SINGH", bold: true, size: 52, font: "Arial", color: BLUE }),
        ]
      }),

      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 40 },
        children: [
          new TextRun({ text: "Dubai, UAE  ·  +971 50 562 9701  ·  samdarshs033@gmail.com  ·  linkedin.com/in/samdarsh-singh  ·  samdarshsingh.com", size: 18, font: "Arial", color: GRAY }),
        ]
      }),

      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 160 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: RULE_COLOR, space: 6 } },
        children: [new TextRun({ text: "", size: 4 })]
      }),

      // ── PROFESSIONAL SUMMARY ──────────────────────────────────────────────
      sectionHeading("Professional Summary"),
      new Paragraph({
        spacing: { before: 80, after: 120 },
        children: [
          new TextRun({
            text: "UAE-based engineer who ships AI systems directly at client sites — from POC sign-off to live production. 7 years building distributed Python backends; currently completing an MSc in AI while deploying LLM-integrated platforms for government and enterprise clients in Dubai. Known for translating complex client requirements into working systems fast, then quantifying the business outcome in language executives understand.",
            size: 20, font: "Arial", color: BLACK
          })
        ]
      }),

      // ── CORE SKILLS ───────────────────────────────────────────────────────
      sectionHeading("Core Skills"),
      emptyLine(40),
      skillRow("Languages & Frameworks", "Python, FastAPI, Django, Flask, REST APIs"),
      skillRow("AI / ML", "LLM Deployment, Model Fine-Tuning, NLP, OpenAI API, AI Project Delivery"),
      skillRow("Databases", "PostgreSQL, MongoDB, Redis, Elasticsearch"),
      skillRow("Infrastructure", "Docker, Kubernetes, AWS, CI/CD, GitHub Actions"),
      skillRow("Architecture", "Microservices, Distributed Systems, Event-Driven Architecture, Multi-Tenant Platforms"),
      skillRow("Other", "RabbitMQ, Celery, System Design, Observability, Performance Optimization, POC Delivery"),
      emptyLine(60),

      // ── PROFESSIONAL EXPERIENCE ───────────────────────────────────────────
      sectionHeading("Professional Experience"),

      jobHeader("Forward Deployed Engineer / Senior Backend Engineer", "Bluethink IT Consulting Pvt. Ltd.", "Feb 2021 – Jan 2026", "Dubai, UAE"),
      companyLine("Bluethink IT Consulting Pvt. Ltd.", "Dubai, UAE (On-site at client locations)"),
      bullet("Cut POC-to-production cycle by 35% across 3 enterprise AI projects by owning on-site environment setup, weekly iteration sprints, and pre-launch data deviation fixes."),
      bullet("Drove 40% API latency reduction for a government client platform by diagnosing bottlenecks, rebuilding async processing with FastAPI and Redis, and presenting performance outcomes directly to the client technical lead."),
      bullet("Deployed LLM-integrated content management system for an enterprise client covering environment configuration, model integration, UAT, and go-live with zero critical post-launch incidents."),
      bullet("Improved PostgreSQL and MongoDB query performance by 30–50% by implementing schema optimization and indexing strategies across 4 enterprise SaaS platforms, reducing client infrastructure costs."),
      bullet("Built Python automation pipelines that cut client operational processing time by 25% and produced ROI reports that secured contract renewals."),
      bullet("Achieved near-zero background job failure rates across millions of tasks by engineering resilient Celery workflows with RabbitMQ and automated retry mechanisms."),
      bullet("Collaborated directly with government and enterprise stakeholders to align delivery with business objectives, achieving 100% on-time milestone completion through weekly syncs and bilingual technical documentation."),

      emptyLine(60),
      jobHeader("Python Backend Developer", "Independent Contractor", "Jan 2019 – Jan 2021", "Remote"),
      companyLine("Independent Contractor", "Remote"),
      bullet("Delivered 8 full-cycle backend projects across SaaS, logistics, and e-commerce with 100% on-time completion by independently managing solution architecture, client communication, and production deployment."),
      bullet("Reduced client data processing time by 30% by building optimised REST APIs and automated data pipelines using Python, Django, and PostgreSQL."),
      bullet("Supported hundreds of concurrent users across multi-tenant platforms with zero data isolation breaches by designing secure tenant architecture and automated testing suites."),
      bullet("Quantified project ROI for 6 clients through structured delivery reports documenting efficiency gains and cost reductions, resulting in 3 repeat engagements and direct referrals."),

      // ── KEY PROJECTS ──────────────────────────────────────────────────────
      sectionHeading("Key Projects"),

      projectHeader("LLM Semantic Search Engine for Enterprise Content Management", "Django, PostgreSQL, Elasticsearch, Redis, OpenAI API"),
      bullet("Improved content retrieval speed by 60% and reduced manual editorial effort by 40% by integrating LLM-based semantic search and automated content tagging into a scalable RBAC-protected CMS."),

      projectHeader("Real-Time AI Scoring Engine for 10,000+ Concurrent Fantasy Sports Users", "RabbitMQ, Celery, PostgreSQL, WebSockets"),
      bullet("Supported 10,000+ concurrent users with sub-200ms response times by building real-time event processing pipelines and predictive scoring models with fault-tolerant distributed architecture."),

      projectHeader("Multi-Tenant AI-Assisted Logistics Platform with Live Tracking", "FastAPI, PostgreSQL, Elasticsearch, AWS"),
      bullet("Reduced logistics operational reporting time by 35% by designing a multi-tenant TMS with real-time tracking, AI-assisted route optimisation, and operational search deployed on AWS."),

      // ── EDUCATION ─────────────────────────────────────────────────────────
      sectionHeading("Education"),

      new Paragraph({
        spacing: { before: 100, after: 20 },
        tabStops: [{ type: TabStopType.RIGHT, position: 9360 }],
        children: [
          new TextRun({ text: "M.Sc. Artificial Intelligence", bold: true, size: 21, font: "Arial", color: BLACK }),
          new TextRun({ text: "\t", size: 20, font: "Arial" }),
          new TextRun({ text: "2025 – 2026", size: 20, font: "Arial", color: GRAY, italics: true }),
        ]
      }),
      new Paragraph({
        spacing: { before: 0, after: 60 },
        children: [
          new TextRun({ text: "De Montfort University Dubai", size: 20, font: "Arial", color: LBLUE, bold: true }),
          new TextRun({ text: "  ·  Relevant: NLP, Deep Learning, LLM Fine-Tuning, AI Systems Deployment", size: 19, font: "Arial", color: GRAY }),
        ]
      }),

      new Paragraph({
        spacing: { before: 80, after: 20 },
        tabStops: [{ type: TabStopType.RIGHT, position: 9360 }],
        children: [
          new TextRun({ text: "B.Tech. Computer Science and Engineering", bold: true, size: 21, font: "Arial", color: BLACK }),
          new TextRun({ text: "\t", size: 20, font: "Arial" }),
          new TextRun({ text: "2017 – 2021", size: 20, font: "Arial", color: GRAY, italics: true }),
        ]
      }),
      new Paragraph({
        spacing: { before: 0, after: 60 },
        children: [
          new TextRun({ text: "JSS Academy of Technical Education, Noida", size: 20, font: "Arial", color: LBLUE, bold: true }),
        ]
      }),

      // ── LANGUAGES ─────────────────────────────────────────────────────────
      sectionHeading("Languages"),
      new Paragraph({
        spacing: { before: 80, after: 60 },
        children: [
          new TextRun({ text: "English", bold: true, size: 20, font: "Arial", color: BLACK }),
          new TextRun({ text: " (Professional)  ·  ", size: 20, font: "Arial", color: GRAY }),
          new TextRun({ text: "Hindi", bold: true, size: 20, font: "Arial", color: BLACK }),
          new TextRun({ text: " (Native)  ·  ", size: 20, font: "Arial", color: GRAY }),
          new TextRun({ text: "Punjabi", bold: true, size: 20, font: "Arial", color: BLACK }),
          new TextRun({ text: " (Native)", size: 20, font: "Arial", color: GRAY }),
        ]
      }),

    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("resume_output.docx", buffer);
  console.log("Resume generated: resume_output.docx");
});

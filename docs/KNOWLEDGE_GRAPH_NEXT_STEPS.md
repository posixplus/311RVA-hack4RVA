# Knowledge Graph Architecture for RVA 311 Bridge — Next Steps

**Hack4RVA 2026 · Thriving & Inclusive Communities Pillar**

---

## Why Knowledge Graphs Fit This Problem

The current RVA 311 Bridge uses RAG (Retrieval Augmented Generation) — it searches PDF documents by semantic similarity and feeds matching text to an LLM. This works well for open-ended questions, but it has blind spots. RAG treats documents as flat text. It doesn't understand that the IRC Richmond *is a resettlement agency* that *serves refugees* who *need housing* which *requires RRHA intake* which *has a phone number* and *specific eligibility rules*. Those are structured relationships, and they're exactly what an ontology captures.

A knowledge graph would model Richmond's service ecosystem as a network of typed entities and relationships:

```
[Resident] --needsHelp--> [ServiceCategory: Housing]
    [ServiceCategory: Housing] --servedBy--> [Agency: RRHA]
    [Agency: RRHA] --hasProgram--> [Program: Emergency Housing Voucher]
        [Program: Emergency Housing Voucher] --requiresDocument--> [Document: Photo ID]
        [Program: Emergency Housing Voucher] --hasEligibility--> [Eligibility: Income < 50% AMI]
        [Program: Emergency Housing Voucher] --referredBy--> [Agency: IRC Richmond]
    [Agency: IRC Richmond] --speaksLanguage--> [Language: Dari, Pashto, Arabic, Spanish]
    [Agency: IRC Richmond] --locatedAt--> [Address: 3516 E Broad St]
    [Agency: IRC Richmond] --hasPhone--> [Phone: 804-560-9370]
```

This structured representation enables three things RAG alone cannot do reliably:

1. **Multi-hop reasoning.** "I'm a refugee who needs emergency housing — who do I call and what do I bring?" requires traversing Resident → ServiceCategory → Agency → Program → Documents. RAG might find a paragraph that mentions some of this, but a graph traversal guarantees completeness.

2. **Precise eligibility filtering.** "Am I eligible for SNAP if I work 15 hours a week?" is a structured query against eligibility rules, not a semantic similarity search. A knowledge graph stores these as typed predicates that can be evaluated deterministically.

3. **Multilingual concept mapping.** Instead of translating entire documents, the ontology maps concepts once: `[ServiceCategory: Housing]` has labels in English ("Housing Assistance"), Spanish ("Asistencia de Vivienda"), Arabic ("مساعدة الإسكان"), Dari ("کمک مسکن"). The graph structure is language-independent; only the labels change.

---

## What Changes in the Architecture

The current pipeline is:

```
User Question → Bedrock RAG (vector search over PDFs) → Claude LLM → Response
```

A knowledge-graph-enhanced pipeline would be:

```
User Question → Intent Classification → ┬→ Graph Query (structured)  ─┐
                                         └→ RAG Search (unstructured) ─┤→ Claude LLM → Response
                                                                       │
                                         Knowledge Graph (Neo4j/       │
                                         Neptune/RDF) ─────────────────┘
```

The key insight is that you don't replace RAG — you augment it. The knowledge graph handles structured queries (who provides what, where, with what requirements), while RAG handles open-ended questions where the answer lives in narrative text (e.g., "What are my rights if I encounter ICE?").

### Ontology Design (Core Classes)

An OWL or RDFS ontology for Richmond civic services would define these core classes:

| Class | Description | Example Instances |
|-------|-------------|-------------------|
| `ServiceCategory` | Top-level need categories | Housing, Food, Legal, Healthcare, Emergency |
| `Agency` | Organizations that provide services | RRHA, IRC Richmond, Sacred Heart, CrossOver |
| `Program` | Specific programs within agencies | Emergency Housing Voucher, SNAP, Medicaid |
| `EligibilityRule` | Conditions for program access | Income threshold, residency, documentation |
| `Document` | Required paperwork | Photo ID, proof of address, income verification |
| `Location` | Physical service sites | 3516 E Broad St, 900 E Broad St Suite 100 |
| `ContactMethod` | How to reach a service | Phone, walk-in, website, referral-only |
| `Language` | Languages supported by an agency | English, Spanish, Arabic, Dari, Pashto |
| `ReferralPath` | Directed edge: Agency A refers to Agency B | IRC → RRHA (for housing), BHA → CrossOver (for primary care) |
| `ServiceHours` | When a service is available | Mon-Fri 8-5, 24/7, By appointment |

### Key Relationships (Properties)

```
servedBy:        ServiceCategory → Agency
hasProgram:      Agency → Program
requiresDoc:     Program → Document
hasEligibility:  Program → EligibilityRule
refersTo:        Agency → Agency        (referral pathways)
speaksLanguage:  Agency → Language
locatedAt:       Agency → Location
hasContact:      Agency → ContactMethod
availableDuring: Agency → ServiceHours
```

This ontology directly encodes the referral network that case managers carry in their heads. It makes "who can help me with X, in my language, near me, right now" a graph query rather than a hope-the-LLM-finds-it prompt.

---

## What This Enables (Concrete Features)

| Feature | Current (RAG Only) | With Knowledge Graph |
|---------|-------------------|---------------------|
| "Find me housing help" | Searches PDFs for housing-related text | Returns all agencies with `servedBy: Housing`, ranked by language match and hours |
| "What do I need to bring to RRHA?" | May or may not find the right paragraph | Traverses `RRHA → hasProgram → requiresDoc` and returns exact list |
| "Who's open right now?" | Cannot answer (no structured hours data) | Filters `availableDuring` against current time |
| Referral handoff | Static list of 7 nonprofits | Dynamic: graph finds the best-fit agency based on need + language + location |
| BizNavigator sequencing | Hardcoded Phase 1→2→3→4 | Graph-driven: `requiresBefore` edges encode permit dependencies dynamically |
| "What's similar to what IRC offers?" | Approximate semantic match | Exact: find agencies sharing the same `ServiceCategory` edges |
| Cross-language answers | Separate translated documents | One graph, multilingual labels — answers are structurally identical across languages |

---

## Recommended Next Steps

### Phase 1: Build the Ontology (1–2 weeks)

1. **Define the OWL ontology** using Protégé (free, open source). Start with the 10 classes above. Export as RDF/Turtle.
2. **Populate with Richmond data.** Use the 10 existing Knowledge Base PDFs plus the BizNavigator data to extract entities. This can be semi-automated: feed each PDF to Claude with a structured extraction prompt ("Extract all agencies, programs, eligibility rules, and contact info as JSON").
3. **Validate with a case manager.** Have someone from IRC Richmond, ReEstablish, or Sacred Heart review the graph for accuracy. They know the referral network — the graph should match their mental model.

### Phase 2: Choose a Graph Database (1 week)

| Option | Pros | Cons |
|--------|------|------|
| **Amazon Neptune** | Managed, integrates with AWS stack, supports RDF + SPARQL and property graphs + openCypher | Cost (~$0.35/hr for smallest instance), overkill for small datasets |
| **Neo4j AuraDB Free** | Free tier, excellent tooling, Cypher query language is intuitive | Not AWS-native, requires separate hosting |
| **RDFLib (Python in-memory)** | Zero cost, runs inside Lambda, SPARQL support | No persistence (reload on cold start), limited scale |
| **Neptune Serverless** | Pay-per-use, scales to zero | Still relatively new, SPARQL learning curve |

**Recommendation for hackathon evolution:** Start with **RDFLib in Lambda** (zero infrastructure cost, works inside the existing orchestrator). Migrate to **Neptune Serverless** if the dataset grows beyond a few hundred entities.

### Phase 3: Integrate with Existing RAG Pipeline (1–2 weeks)

1. **Add an intent classifier** to the Lambda orchestrator. Before calling RAG, classify whether the question is structured ("who provides X", "what do I need for Y", "who's open now") or unstructured ("what are my rights if...").
2. **For structured queries:** Convert to SPARQL or Cypher, execute against the graph, format results.
3. **For unstructured queries:** Continue using Bedrock RAG as today.
4. **For hybrid queries:** Run both, merge results, pass to Claude with both the graph facts and the RAG passages as context. The LLM synthesizes a natural-language answer from structured + unstructured sources.

### Phase 4: Enable Graph-Powered Features (2–4 weeks)

- **Dynamic referral routing:** Replace the static `NONPROFIT_ORGS` array in `ChatInterface.jsx` with a graph query: given the user's need and language, return the top-ranked agencies.
- **Service pathway visualization:** Render the graph as an interactive map (using D3.js or vis.js) showing how services connect — "if you need housing, here are the three pathways."
- **Eligibility pre-screening:** Walk the user through `hasEligibility` predicates conversationally: "Do you have a photo ID? Is your household income below $X?" — without collecting or storing PII (questions asked ephemerally, not logged).
- **BizNavigator graph mode:** Replace the hardcoded Phase 1→4 JavaScript with a graph traversal over `requiresBefore` edges, making the permit sequencing data-driven and automatically updated.

---

## Why This Matters for Richmond

The core problem this hackathon addresses — immigrants and refugees struggling to navigate fragmented services — is fundamentally a graph problem. Services are nodes. Referral pathways are edges. Eligibility rules are predicates. Languages are labels. A knowledge graph doesn't just store this information; it makes the *relationships themselves* queryable.

Case managers at IRC Richmond, Sacred Heart, and ReEstablish already carry this graph in their heads. Building it as a shared digital ontology means that knowledge doesn't leave when a staff member does. It means a resident at 2 AM can traverse the same referral network that a case manager would navigate during business hours. And it means the system can answer "who can help me, right now, in my language" with the same confidence as a structured database query — not a best-effort guess from a PDF search.

The current RAG-based RVA 311 Bridge is the right MVP. A knowledge graph is the right next step.

---

*Prepared for Hack4RVA 2026 · Thriving & Inclusive Communities Pillar*

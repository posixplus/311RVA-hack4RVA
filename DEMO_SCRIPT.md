# RVA 311 Bridge — Demo Script (6 PM Presentation)

**Time: 3-5 minutes | Pillar: Thriving and Inclusive Communities**

---

## Opening (30 seconds)

> "311 Richmond closes at 5 PM. But crises don't.
>
> A family wakes up at midnight — their heat is off. A refugee who arrived three months ago doesn't speak English. There's no one to call, no website they can navigate, and no help until Monday morning.
>
> We built the **RVA 311 Bridge** — a 24/7 AI-powered multilingual assistant that extends Richmond's 311 with a chatbot and an IVR phone line, powered by real city documents, without ever collecting a single piece of personal information."

---

## Live Demo — Web Chatbot (90 seconds)

**[Open the website in browser — show the RVA311-style interface]**

> "Our interface mirrors the real RVA311 system that residents already know."

**Step 1: Show Category Grid**
> "We replicate all 14 RVA311 service categories. But we've added new ones under 'Request Support Services' specifically for immigrants and refugees."

**[Click "Request Support Services" → show subcategories]**
> "You'll see the existing city services like Aging and Disability — with the exact same descriptions from the real 311 system. Plus new categories: Immigrant and Refugee Services, Mental Health, Food Assistance, Housing."

**Step 2: Start a Conversation**
**[Click "Immigrant and Refugee Services"]**

> "Notice the privacy notice at the top — this appears on every interaction."

**[Read it briefly]** "No PII collected. Not posted publicly. Optional account."

**[Type: "I need help with SNAP food benefits. The rules changed and I'm not sure if I still qualify."]**

> "The system searches our knowledge base — 10 real documents including SNAP work requirements, know-your-rights guides, mental health resources, emergency preparedness — all in English and Spanish."

**[Show the AI response with cited sources]**
> "Every answer references the actual source document. No hallucination. The response tells them exactly what changed in November 2025, who to call, and where to go."

**Step 3: Conversation Completion**
**[Click "I'm satisfied"]**
> "The resident can optionally provide an email or phone to receive a summary. That contact info is redacted in the public dashboard."

**[Click "Hand off to Sacred Heart Center"]**
> "And we can demo a handoff to a trusted nonprofit partner — the summary gets sent to Sacred Heart Center, IRC Richmond, or whichever org is the best fit."

---

## Live Demo — IVR Phone Call (60 seconds)

> "Now the same thing, but on a phone. No smartphone needed. No internet. Just a phone call."

**[Call the Connect phone number on speaker]**

> "The caller hears: 'Welcome to the Richmond City Resource Assistant. Press 1 for English. Presione 2 para español. Press 3 for Arabic.'"

**[Press 2 for Spanish]**

> "The privacy notice plays in Spanish. Then the caller describes their need."

**[Say in Spanish or describe]: "Necesito ayuda con beneficios de comida"**

> "The AI responds in Spanish with real information from our SNAP documents. When the call ends, a structured summary goes to the nonprofit inbox — anonymized, no PII."

---

## Dashboard Demo (30 seconds)

**[Open /dashboard in browser]**

> "Every interaction is logged in a public dashboard — fully redacted. The community can see what people are asking about: food assistance is #1, followed by immigration rights and housing."

**[Click "Manager Login" → password: richmond311admin]**

> "Managers from the nonprofits log in to see full details — the email or phone if the resident opted in — so they can follow up. Export to CSV for intake workflows."

---

## Why It Works (30 seconds)

> "Three things make this different:
>
> **One** — it works on any phone. A basic cell phone at midnight. No app, no internet, no digital literacy required.
>
> **Two** — zero PII. We never ask for a name, address, or immigration status. The privacy notice plays on every interaction. All public data is redacted by AWS Comprehend.
>
> **Three** — it doesn't replace anyone. The IVR bridges the gap until a human can follow up. The nonprofit handoff closes the loop. This is a bridge, not a replacement."

---

## The Ask (15 seconds)

> "Help us connect this to one real nonprofit partner — Sacred Heart Center, IRC Richmond, or ReEstablish Richmond — to validate the handoff and take this from demo to pilot.
>
> And if anyone on the 311 team is listening — this stack runs on AWS for less than $5 a day. It can be torn down tonight or adopted on Monday."

---

## Technical Quick Facts (if judges ask)

| Question | Answer |
|----------|--------|
| Stack | AWS Connect (IVR) + Bedrock Knowledge Base (RAG) + Claude Haiku 3.5 + API Gateway + CloudFront |
| Languages | English, Spanish (full). Arabic (IVR). Dari/Pashto flagged for roadmap with navigator backstop. |
| RAG corpus | 10 real documents: SNAP work requirements, ICE know-your-rights, mental health resources, emergency prep, freezing weather safety — all bilingual EN/ES |
| Privacy | Zero PII collection. No login required. AWS Comprehend redaction on all public data. Ephemeral transcription. |
| Cost | ~$5/day for demo. $150-300/month at production scale. Teardown in one command. |
| Handoff orgs | IRC Richmond, ReEstablish Richmond, Sacred Heart Center, Afghan Association of Virginia, Central Virginia Legal Aid, Richmond BHA, CrossOver Healthcare |
| Dashboard | Public redacted view (anyone). Manager login (password-protected) with full contact info + CSV export. |
| Build time | 48 hours at Hack4RVA 2026 |

---

## Backup: If Live Demo Fails

1. **Website won't load:** Open the locally-built version at `localhost:3000`
2. **API not responding:** Switch to demo mode (pre-loaded responses from real documents)
3. **IVR not connecting:** Play a pre-recorded call audio or describe the flow with screenshots
4. **Bedrock throttled:** Demo mode has all responses pre-cached from actual RAG output

---

*The phone call that was a dead end is now a bridge.*

# **Project Specification Sheet**

## **Multilingual Policy, Rights & Scheme Explainer**

AI-powered application

CivicTech / GovTech

MVP Development

**Project Goal:** Build an AI-powered platform that helps citizens understand government policies, welfare schemes, legal rights and official notices in simple language and regional languages.

## **1. Problem Statement**

Government policies, welfare schemes and legal documents are often difficult to understand because of complex terminology, language barriers and lengthy documentation. Citizens may miss benefits or fail to understand their rights due to a lack of accessible information.

**Proposed Solution:** A multilingual AI assistant that converts complex government information into simple, understandable and actionable explanations, with eligibility checking and voice-based interaction.

## **2. Target Users**

- Indian citizens and rural communities.
- Students and unemployed individuals.
- Farmers and small business owners.
- Senior citizens.
- People unfamiliar with government procedures.
- Citizens who prefer regional languages.

## **3. Core Features**

| Feature                    | Functionality                                                             |
| -------------------------- | ------------------------------------------------------------------------- |
| AI Policy Explainer        | Explains government policies and notices in simple language.              |
| Multilingual Support       | Supports English, Hindi, Marathi and other major Indian languages.        |
| Document Upload            | Accepts PDF, DOCX, TXT and image-based documents.                         |
| AI Chat Assistant          | Allows users to ask questions about policies and schemes.                 |
| Scheme Eligibility Checker | Checks eligibility using user-provided details.                           |
| Rights Explainer           | Explains citizens' basic legal rights and available protections.          |
| Voice Interaction          | Speech-to-text input and text-to-speech responses.                        |
| Source References          | Shows official source links and relevant document sections.               |
| Simplified Summaries       | Generates key points, required documents, benefits and application steps. |

## **4. Main Application Modules**

**User Interface**

Web application / Responsive dashboard

**Document Upload**

PDF / Image / Text

**AI Chat**

Question & Answer

**Eligibility Checker**

Scheme matching

**Voice Assistant**

Speech interaction

**AI Processing Engine**

OCR + LLM + Translation + Retrieval (RAG)

**Government Knowledge Base**

Verified government documents, schemes, laws and official URLs

## **5. Technical Stack**

| Layer                  | Recommended Technology               |
| ---------------------- | ------------------------------------ |
| Frontend               | React.js + Tailwind CSS              |
| Backend                | Python + FastAPI                     |
| AI Model               | Gemini API                           |
| Document Processing    | PyMuPDF + OCR (Tesseract)            |
| AI Knowledge Retrieval | LangChain / Custom RAG               |
| Database               | Supabase / PostgreSQL                |
| Authentication         | Supabase Auth                        |
| Translation            | Gemini multilingual capabilities     |
| Speech Recognition     | Web Speech API                       |
| Text-to-Speech         | Browser Speech Synthesis API         |
| Deployment             | Vercel (frontend) + Render (backend) |

## **6. Main User Workflow**

1. User opens the application.
2. Selects their preferred language.
3. Chooses an action:
   - Ask about a government scheme.
   - Upload a government document.
   - Check scheme eligibility.
   - Understand their rights.
4. AI retrieves relevant information from verified sources.
5. AI processes and simplifies the information.
6. User receives an easy-to-understand response.
7. User can translate, listen to or ask follow-up questions.
8. Application provides official source links for verification.

## **7. Required AI Capabilities**

- Understand complex government terminology.
- Extract relevant information from uploaded documents.
- Summarize lengthy policies into simple bullet points.
- Answer questions using retrieved official information.
- Translate responses into supported regional languages.
- Compare user details with scheme eligibility criteria.
- Identify missing information and ask follow-up questions.
- Provide citations and avoid generating unsupported legal or eligibility claims.

**Important:** The AI must distinguish between verified information, inferred information and unavailable information. It must never guarantee scheme approval or present itself as a substitute for professional legal advice.

## **8. UI/UX Requirements**

**Design direction:** Modern, clean, accessible and citizen-friendly.

- Professional government-service-inspired interface without impersonating an official government portal.
- Simple dashboard with clear navigation.
- Large, accessible buttons and readable typography.
- Language selector prominently displayed.
- Chat interface with conversational responses.
- Drag-and-drop document upload.
- Eligibility checker with step-by-step questions.
- Voice input microphone button.
- Mobile-responsive layout.
- Light theme with blue, white and subtle green accents.

## **9. Main Pages**

1. **Home:** Introduction, search bar and primary actions.
2. **AI Assistant:** Multilingual question-answering interface.
3. **Document Explainer:** Upload and analyze government documents.
4. **Scheme Finder:** Browse and search government schemes.
5. **Eligibility Checker:** Personalized scheme eligibility assessment.
6. **Rights Explorer:** Understand citizen rights and protections.
7. **History:** Previously uploaded documents and conversations.
8. **About:** Project information and limitations.

## **10. MVP Scope and Priorities**

Prioritize these features for the first working version.

**Phase 1 – Essential**

Must have

- Responsive dashboard.
- English, Hindi and Marathi support.
- AI-powered government policy explainer.
- PDF and image document upload.
- AI chatbot with contextual follow-up questions.
- Scheme eligibility checker.
- Official source references.

  **Phase 2 – Enhancements**

  Should have
- Voice input and audio responses.
- Advanced OCR for scanned documents.
- Rights Explorer.
- Conversation history.
- Additional regional languages.

  **Phase 3 – Future Scope**

  Optional
- Automatic updates from government portals.
- Personalized scheme recommendations.
- Application document checklist.
- Regional government scheme database.

## **11. Data Sources**

Prioritize authentic government sources:

- [myScheme – Government scheme discovery](https://www.myscheme.gov.in/?utm_source=chatgpt.com)
- [National Portal of India](https://www.india.gov.in/?utm_source=chatgpt.com)
- [Legislative Department](https://legislative.gov.in/?utm_source=chatgpt.com)
- [Press Information Bureau](https://www.pib.gov.in/?utm_source=chatgpt.com)
- [National Legal Services Authority](https://www.nalsa.gov.in/?utm_source=chatgpt.com)

Use official documents and source URLs wherever possible. Do not treat unverified third-party websites as authoritative.

# **12. Instructions for Antigravity IDE**

Build instructions

The following instructions define the expected development outcome.

# Build Project: Multilingual Policy, Rights & Scheme Explainer

Build a complete, functional, responsive AI-powered web application that helps Indian citizens understand government policies, welfare schemes, official notices and basic legal rights.

## Product Requirements

1. Build a modern, accessible React + Tailwind CSS frontend.
2. Build a Python FastAPI backend.
3. Integrate Gemini API for AI-powered explanations and multilingual conversations.
4. Support English, Hindi and Marathi initially.
5. Implement document upload supporting PDF, DOCX, TXT and images.
6. Extract document content using appropriate parsing and OCR libraries.
7. Implement RAG-based question answering using uploaded documents and verified government information.
8. Create a scheme eligibility checker using structured eligibility criteria.
9. Provide simplified explanations, benefits, eligibility requirements, required documents and application instructions.
10. Include a Rights Explorer for explaining basic citizen rights.
11. Include voice input and text-to-speech functionality.
12. Display official source links and citations with AI responses.
13. Include conversation history and a clean dashboard.
14. Make the entire application mobile-responsive.

## AI Behaviour

- Use simple, citizen-friendly language.
- Avoid unnecessary technical or legal terminology.
- Respond in the user's selected language.
- Prioritize verified government information.
- Never invent eligibility criteria, benefits, deadlines or legal provisions.
- Clearly identify missing or outdated information.
- Display relevant source references.
- Do not guarantee scheme eligibility or approval.

## UI Requirements

Create a premium but simple civic-tech dashboard with:

- Home dashboard.
- AI Policy Assistant.
- Document Explainer.
- Government Scheme Finder.
- Eligibility Checker.
- Rights Explorer.
- Conversation History.
- Language selector.
- Voice interaction controls.

Use a clean blue, white and subtle green design system, accessible typography, intuitive navigation, responsive layouts and polished loading/error states.

## Backend Requirements

- Secure API endpoints.
- Gemini API integration through environment variables.
- Document parsing and OCR.
- Retrieval-based AI responses.
- Scheme eligibility evaluation.
- Input validation and error handling.
- Secure temporary document processing.
- No API keys exposed in frontend code.

## Development Rules

- Build actual working functionality, not just static UI mockups.
- Organize the project into reusable components and maintainable modules.
- Include requirements.txt and .env.example.
- Provide a README.md with complete installation and execution instructions.
- Include sample government documents and scheme data for testing, clearly marked as sample data.
- Do not fabricate official government data.
- Test all major user workflows.
- Ensure the application can run locally.

## Expected Deliverable

A fully functional MVP named "JanSahayak AI" with the tagline:

"Government Information. Simplified for Everyone."

Prioritize a working end-to-end application over unnecessary animations or decorative features.

**Suggested project name:** JanSahayak AI

**Tagline:** Government Information. Simplified for Everyone.

This specification is ready to give to Antigravity IDE. Once it generates the initial project, the next important step will be testing document upload, source-grounded answers and scheme eligibility accuracy before deployment.
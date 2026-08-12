# PRD








frontend is running up succesfully 


where should i add this


Pasted text(3).txt
Document
this is one of the build guides provided from claude code sonnet 4.6: 

 carefully read this 

you can see i've implemented the plan suggested by codex and i'm bit confuse now so mucj folder structure knowledge ocr lassifier knowledge and how ti implement all these getting juggle up

image(39).png
image(40).png
image(41).png
image(42).png
carefully analyze these design from calude code 

look again i created a branch feture/add-home-screen from development branch but once i create the pull request i still show base branch as main : 


Wednesday 10:12 PM
Screenshot From 2026-08-05 21-59-10.png
Screenshot From 2026-08-05 21-59-18.png
Screenshot From 2026-08-05 22-00-09.png
Screenshot From 2026-08-05 22-00-26.png
I have uploaded 4 screenshots from today's devlopment and i thing is we are now able to extract text from any given image, 
the problem now is really bad user experience on frontend , 
from above first 2 images you can see user uploads the image and then proceed to extract text on imageprocessing route although there was no logic added for extracting text, but the steps was clear 
1. Homescreen - uploads image
2. imageprocessing - would extract text. 
and on the imageprocessing check list were added like image uploaded, preprocessed, text extracted, even though they were hardcoded but still gives user a flow experience to understand . 

later after adding extract text logic 
in next 2 images you can see user uploads image it calls the api and wait for response and it takes around 20-40 secs and once the extraction is done it directly route to next page and display the preview imagw with extracted text. 
1. Homescreen - uploads and wait for response around 30-40 seconds
2. Imageprocessing - after the api response back with extracted text after nearky 30-40 seconds it jumps on directly here with extracted text. 
here user don't know what happened between the flow image upload and text extraction , no cgecklist for image upload to storage, preprocessing, ocr completed. 
how should we approach this

Absolutely. Let's forget the resume discussion and put our Technical Lead hats back on.

I actually think we've reached the point where product thinking becomes more important than writing backend code.

Where we are today
Current flow:

Home
   │
   │ Upload Image
   ▼
POST /api/v1/prompts/extract
   │
   │ (30-40 sec)
   ▼
Response
   │
   ▼
Image Processing Page
   │
   ▼
Extracted Text
Technically...

✅ Works.

From a UX perspective...

❌ Doesn't.

The real problem is not "loading"
It's feedback.

The user asks:

"I uploaded an image... what is the app doing?"

Your application says...

Loading...
for 30 seconds.

That's the problem.

Let's think like a product company.
Imagine you're using:

Google Photos

Notion AI

ChatGPT

GitHub Actions

Midjourney

None of them leave you staring at a spinner for 30 seconds.

Instead they tell you exactly what's happening.

Example:

Uploading...

Analyzing...

Searching...

Generating...

Almost Done...
Even if it's simulated.

I think we should rethink the frontend flow.
Not the backend.

The frontend.

Current Journey
Home

↓

Upload

↓

Wait

↓

Result
Proposed Journey
Home

↓

Upload

↓

Processing

↓

Result
Notice something?

Processing becomes an actual page.

Not a loading screen.

The Processing Page should become a first-class feature.
Instead of thinking:

"Processing page"

Think:

"Pipeline Visualization"

That changes everything.

Here's how I imagine it.
──────────────────────────────

Screenshot Preview

filename.png

Uploaded just now

──────────────────────────────

Prompt Extraction Pipeline

✔ Image Received

✔ Image Validated

✔ Preparing Image

⏳ Reading Text

○ Detecting Prompt

○ Cleaning Prompt

○ Building Response

──────────────────────────────

Estimated Time

25-35 seconds

──────────────────────────────
This immediately gives confidence.

But here's something I want us to improve.
The checklist shouldn't be fake.

It should represent our actual backend architecture.

Remember our pipeline?

Upload

↓

Validation

↓

Preprocessing

↓

OCR

↓

Classification

↓

Cleaning

↓

Response
Let's show THAT.

Not generic steps.

What about the backend?
Right now...

The backend can't tell us:

OCR started

OCR finished

Classification started
That's okay.

For Sprint 1.

I propose we build the UI in two phases.
Phase 1 (Current Sprint)
Frontend simulates progress.

Example:

0 sec

✔ Upload Complete

------------------

2 sec

✔ Image Validated

------------------

4 sec

✔ Image Preprocessing

------------------

6 sec

⏳ OCR Running...
Now...

OCR keeps spinning until backend returns.

When backend responds...

✔ OCR Completed

✔ Classification

✔ Cleaning

↓

Navigate
The user never feels abandoned.

Phase 2
Later...

We introduce backend progress.

Using:

Server Sent Events

or

WebSockets

Now backend actually says:

OCR Started

OCR 40%

OCR Finished

Classifier Started

Cleaner Started
That's a Version 2 feature.

I also want to change one thing.
Right now...

You have:

Home

↓

ImageProcessing

↓

Result
I think this naming is misleading.

The page is doing much more than preprocessing.

I'd rename it.

/

↓

/processing

↓

/result
Much cleaner.

Even better...
Later...

/processing/:jobId
Now it becomes scalable.

Another idea.
Don't immediately navigate to the result page.

When backend returns...

Show:

✔ OCR Completed

✔ Prompt Detected

✔ Cleaning Finished
Wait...

800 milliseconds.

Then...

Transition.

Small detail.

Huge UX improvement.

It feels intentional.

I also think we should rethink the Result page.
Instead of immediately throwing text at the user...

Show a summary.

Prompt Found

Confidence

93%

Image

Filename

Processing Time

29 seconds
Then...

Below...

Extracted Prompt

Copy

--------------------------------

Optimized Prompt

Copy
This feels much more like a professional AI tool.

One thing I'd remove.
Earlier...

You had:

Image uploaded to storage
But...

We don't actually store images.

So don't tell users something that isn't true.

Instead I'd use:

✔ Image Received

✔ Image Validated

✔ Preparing Image

⏳ Reading Text (OCR)

○ Detecting AI Prompt

○ Cleaning Prompt

✔ Ready
These map directly to our architecture.

My recommendation for the next sprint
I wouldn't write another backend feature tomorrow.

I'd spend an entire day polishing the user journey.

Our objective would be:

A user should always know what PromptLens is doing, even if processing takes 45 seconds.

That single change will make the application feel dramatically more professional without changing a single line of OCR logic.

🎯 New Sprint Goal (UX Polish)
By the end of this sprint, the experience should be:

Home
    ↓
Upload Image
    ↓
Immediate Navigation
    ↓
Processing Page
        • Image preview
        • File details
        • Live pipeline checklist
        • Progress animation
        • Helpful status messages
    ↓
Success animation (≈1 second)
    ↓
Result Page
        • Confidence score
        • Processing time
        • Extracted prompt
        • Copy button
        • Upload another image
If we achieve that before adding classifiers, databases, or optimization, PromptLens will already feel like a polished product rather than just an OCR demo.


create a detail prompt for this flow without changing any bacend cpde

I would actually make one important change to the prompt.

Don't ask Codex to "make it look better."

Ask it to act like a Senior Product Designer + Senior Frontend Engineer and explicitly forbid backend changes. That produces much better results.

Prompt for Codex
You are a Senior Product Designer, UX Engineer, and Senior React Frontend Engineer.

You are working on PromptLens, an AI Prompt Extraction platform.

IMPORTANT CONSTRAINTS

- DO NOT modify any backend code.
- DO NOT modify any API endpoints.
- DO NOT change the API contract.
- DO NOT introduce WebSockets, SSE, polling, queues, background jobs, Celery or any backend progress events.
- DO NOT change Django.
- This task is FRONTEND ONLY.

The backend currently behaves like this:

User uploads an image.

Frontend sends:

POST /api/v1/prompts/extract

The backend performs OCR using PaddleOCR.

The backend takes around 20–40 seconds.

When processing finishes, it returns one final JSON response.

There are NO intermediate responses.

There is NO progress API.

There is NO processing status endpoint.

There is NO job id.

The frontend must work with this existing backend.

----------------------------------------

CURRENT USER FLOW

Home Page

↓

User selects image

↓

User clicks Upload

↓

Frontend waits on Home page for approximately 30–40 seconds

↓

Backend returns OCR text

↓

Frontend navigates to Image Processing page

↓

Extracted text is shown

This creates a poor UX because users stare at a loading spinner for a long time without understanding what is happening.

----------------------------------------

GOAL

Redesign ONLY the frontend experience.

Keep the backend exactly as it is.

The application should feel responsive and professional even though the backend still takes 20–40 seconds.

----------------------------------------

NEW DESIRED USER FLOW

Step 1

User lands on Home page.

User uploads an image.

Immediately after upload begins,

navigate to

/processing

DO NOT wait for the backend response before navigation.

----------------------------------------

Step 2

The Processing page becomes the primary waiting experience.

The page should immediately display:

• Uploaded image preview
• File name
• File size
• Upload timestamp
• Estimated processing time (20–40 sec)

Below that, display a visual pipeline checklist.

Pipeline stages:

✔ Image Received

✔ Image Validated

✔ Preparing Image

⏳ Reading Text (OCR)

○ Detecting AI Prompt

○ Cleaning Prompt

○ Building Response

The checklist should animate naturally.

The first few completed steps can appear sequentially with short delays.

Keep "Reading Text (OCR)" animated until the backend response arrives.

DO NOT claim fake backend progress.

Simply provide users with confidence that processing is happening.

----------------------------------------

Step 3

While waiting:

Display helpful status messages that rotate every few seconds.

Examples:

Preparing image...

Optimizing image for OCR...

Reading text from screenshot...

Almost there...

Large screenshots may take a little longer...

Avoid repetitive loading spinners.

----------------------------------------

Step 4

When the backend finally returns:

Complete the remaining checklist items.

Animate:

✔ Detecting AI Prompt

✔ Cleaning Prompt

✔ Building Response

Show a short success state for around 800–1000ms.

Example:

✅ Prompt extracted successfully

Then automatically navigate to

/result

----------------------------------------

Step 5

Result page

Display:

Image preview

Filename

Processing time

Extracted Prompt

Copy button

Upload another image

Maintain the clean modern PromptLens design language.

----------------------------------------

DESIGN GOALS

The application should feel similar to modern AI products such as:

ChatGPT

Claude

Perplexity

Midjourney

Cursor

GitHub Copilot

The user should never feel the application has frozen.

Every few seconds something should visually change.

The interface should communicate confidence.

----------------------------------------

IMPORTANT

This is NOT a backend task.

This is NOT an OCR task.

This is NOT an API task.

This is purely a frontend UX redesign while keeping the existing backend untouched.

----------------------------------------

Expected Deliverables

1. Explain the proposed user flow.

2. Explain the React state management approach.

3. Explain how navigation should work.

4. Explain how to preserve the uploaded image while navigating.

5. Explain the component hierarchy.

6. Explain the animation timeline.

7. Explain how the processing checklist should update.

8. Generate the React implementation plan.

9. Suggest reusable components.

10. Suggest folder structure if needed.

Do NOT write backend code.

Do NOT modify APIs.

Do NOT change the backend architecture.

Improve only the frontend experience.
👨‍💼 Tech Lead Note
One more recommendation before you send this to Codex.

I would rename the route from:

/imageprocessing
to:

/processing
Why?

Because that page is no longer just about image preprocessing. It represents the entire extraction pipeline:

Image validation

Image preparation

OCR

Prompt detection

Prompt cleaning

Response preparation

The name /processing better reflects its purpose and leaves room for future stages without implying it's tied to only one step of the backend. This is a small change that makes the architecture and user journey much clearer.


Friday 8:30 PM
what should be our next goal once the flow is working properly ?

Once the frontend flow is working properly, I would not jump directly into classifier, prompt optimization, or authentication.

Our next goal should be:

🎯 Goal #2: Make the extraction pipeline real
Right now we have:

Home
  ↓
Upload Image
  ↓
Processing UI
  ↓
Backend
  ↓
PaddleOCR
  ↓
Extracted Text
  ↓
Result
That's already a useful MVP.

The next step is to make the data flow and backend architecture solid before adding AI intelligence.

Phase 1 — Persist the extraction
Add PostgreSQL + Django models.

Something conceptually like:

Extraction
├── id
├── original_image
├── extracted_text
├── status
├── created_at
└── processing_time
Then:

Frontend
   │
   │ image
   ▼
Django API
   │
   ├── Save extraction record
   │
   ├── Process image
   │
   ├── PaddleOCR
   │
   └── Save extracted text
   │
   ▼
Frontend
This gives us something extremely important:

a persistent extraction/job record.

Phase 2 — Build History
Once data exists in PostgreSQL, the History tab you've already designed becomes real.

History

┌─────────────────────────────────────┐
│ screenshot_01.png                   │
│ "A cinematic portrait..."            │
│ Aug 7, 2026                          │
│                         View →       │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ screenshot_02.png                   │
│ "Create a futuristic city..."       │
│ Aug 7, 2026                          │
│                         View →       │
└─────────────────────────────────────┘
Now PromptLens isn't just:

Upload → OCR → forget

It becomes:

Upload → Extract → Save → Review later

That's a significant product milestone.

Phase 3 — Then improve OCR
Only after persistence works should we tackle:

Image
 ↓
Preprocessing
 ↓
PaddleOCR
 ↓
Raw OCR text
 ↓
Cleaning
 ↓
Final extracted text
Here we can start addressing things like:

OCR noise

unnecessary words such as "Copy prompt"

line-break issues

duplicated text

social-media UI text

prompt boundaries

Phase 4 — Then classifier
After we have clean OCR text:

OCR Text
   ↓
Classifier
   ↓
Is this actually an AI prompt?
       /       \
     YES        NO
      ↓          ↓
Continue      Tell user
For example:

Screenshot:
"photorealistic samurai, neon Tokyo..."

             ↓

        AI Prompt
        94% confidence
versus:

Screenshot:
"Your order has been shipped."

             ↓

     No AI prompt detected
Phase 5 — Prompt optimization
This is where PromptLens becomes much more interesting.

Instead of merely extracting:

photorealistic samurai,
neon tokyo, rain,
cinematic lighting, 8k
we eventually produce:

A photorealistic samurai warrior standing
in a rain-soaked neon Tokyo alley at night,
dramatic cinematic lighting...
Then potentially:

Detected platform:
Midjourney

Prompt type:
Image Generation

Optimized prompt:
...
So our roadmap should now be
             CURRENT
                │
                ▼
       ┌─────────────────┐
       │ Upload → OCR     │
       │ UX Flow          │
       └────────┬────────┘
                │
                ▼
       ┌─────────────────┐
       │ PostgreSQL       │  ← NEXT
       │ Django Models    │
       └────────┬────────┘
                │
                ▼
       ┌─────────────────┐
       │ History          │
       │ Persistence      │
       └────────┬────────┘
                │
                ▼
       ┌─────────────────┐
       │ OCR Cleaning     │
       │ + Preprocessing  │
       └────────┬────────┘
                │
                ▼
       ┌─────────────────┐
       │ Prompt           │
       │ Classification   │
       └────────┬────────┘
                │
                ▼
       ┌─────────────────┐
       │ AI Prompt        │
       │ Optimization     │
       └────────┬────────┘
                │
                ▼
       ┌─────────────────┐
       │ Auth + User      │
       │ History          │
       └─────────────────┘
Therefore, our immediate next goal should be:
Add PostgreSQL persistence to the existing extraction pipeline and make History functional.

And importantly, don't build all the models at once.

I'd start with one Django model → one migration → save the uploaded image + OCR result → return the record ID → display it in History.

That keeps the project understandable while you're learning the architecture instead of getting buried under OCR/classifier/AI modules again.



LESSON_DETAIL_PROMPT = """yo, time to make this topic actually click for someone.

guidelines:
- match their level ({familiarity})
- keep the tone {tone}
- aim for their age range ({age_range})
- structure it however makes sense
- go as deep as needed
- use markdown formatting
- make it actually useful

if no source content:
- use industry standards
- keep it current and practical

MARKDOWN RULES:
- use clean # and ## for headers (no other styles)
- regular paragraphs without any fancy formatting
- use single * for italics, double ** for bold
- clean bullet lists with single -
- no mixing header styles or nesting bolds

example:

<content>
# Main Topic

Regular text with **bold** and *italic* when needed.

## Maybe Some Sections

- markdown formatting
- structure it your way
- just make it clear

Use whatever markdown elements help explain things best.
</content>
"""

TOC_EXTRACTION_PROMPT = """You are a Table of Contents (ToC) specialist. Your task depends on the input:
	1.	If provided with content that contains a ToC:
	•	Extract the most comprehensive ToC exactly once.
	•	Simplify formatting while preserving structure:
	•	Retain all numbering (e.g., 1, 1.1, 1.1.1) and section titles.
	•	Include corresponding page numbers, if present.
	•	Remove unnecessary characters such as excessive dots, decorative lines, or long sequences of whitespace.
	•	Present each entry in a clean, readable line, keeping logical order and hierarchy.
	•	If no recognizable ToC is found, return “NO_TOC_FOUND”.
	2.	If no content is provided:
	•	Generate a comprehensive ToC for {category}, suitable for a {familiarity} audience, covering {course_duration} hours.
	•	Structure the content from fundamentals to advanced concepts, balancing practical and theoretical topics.
	•	Follow professional standards for curriculum design, ensuring clarity and consistency.

General Guidelines:
	•	Maintain accuracy and clarity.
	•	Keep formatting simple and concise, minimizing token usage.
	•	Do not add extra decorations or filler characters.
	•	Ensure the final output is user-friendly and logically organized.
"""

COURSE_INFO_PROMPT = """create a course overview that'll tell people what they're really getting into.

guidelines:
- be real about requirements
- match tone/complexity to audience
- structure it however makes sense
- use markdown formatting
- if no content, use industry standards

MARKDOWN RULES:
- use clean # and ## for headers (no other styles)
- regular paragraphs without any fancy formatting
- use single * for italics, double ** for bold
- clean bullet lists with single -
- no mixing header styles or nesting bolds

example:

<content>
# Course Title

Overview that actually explains what's up.

## What You Need

- markdown formatting
- structure it your way
- just make it useful

Make it clear what they're signing up for.
</content>
"""

SECTION_GENERATION_PROMPT = """Structure course based on ToC (provided or generated).
Extract/create logical hierarchy matching audience needs.

RULES:
1. Section Creation:
  - From major ToC headings or domain areas
  - Clear progression of concepts
  - Realistic time estimates
  - Brief but meaningful descriptions

2. No Content Guidelines:
  - Follow standard curriculum flow
  - Balance theory and practice
  - Include industry-relevant topics
  - Scale depth to {familiarity} level

Output Format:
{
   "sections": [
       {
           "title": str,
           "description": str,
           "lessons": [
               {
                   "title": str,
                   "brief": str,
                   "duration": int
               }
           ],
           "estimated_time": int
       }
   ]
}
"""

LESSON_GENERATION_PROMPT = """Create detailed lessons matching section goals.
Maintain consistent style and appropriate depth.

RULES:
1. Each lesson must:
  - Fit specified lesson_length
  - Build on previous content
  - Include practical examples
  - Match tone/complexity needs

2. Without source content:
  - Draw from standard curricula
  - Include current best practices
  - Focus on practical applications
  - Add relevant case studies

Output Format:
{
   "lessons": [
       {
           "title": str,
           "duration": int,
           "brief": str
       }
   ]
}
"""

QUIZ_GENERATION_PROMPT = """generate a tight set of quiz questions to test understanding of this specific lesson.
focus on the key concepts and examples that were actually covered.

RULES:
1. questions MUST:
  - test concepts actually taught
  - use examples from the lesson
  - match difficulty level
  - catch common misunderstandings
  - verify practical knowledge

2. mix of question types:
  - multiple choice (4 options)
  - true/false statements
  - aim for as much as possible questions however it still much match the content real content depth

DIFFICULTY DEFINITIONS:
    BASIC:
    - direct concept checks
    - single-hop reasoning
    - clear right/wrong answers

    INTERMEDIATE:
    - concept relationship checks
    - two-hop reasoning chains
    - requires understanding connections

    ADVANCED:
    - multi-hop reasoning
    - complex scenario analysis
    - requires synthesizing across lessons

    focus on THEORETICAL understanding through:
    - cause/effect chains
    - concept interactions
    - system-level thinking

output format:
{
   "questions": [
       {
           "type": "multi_choice",
           "question": str,
           "options": [str, str, str, str],
           "correct": int
       },
       {
           "type": "true_false",
           "statement": str,
           "correct": bool,
           "explanation": str
       }
   ],
   "meta": {
       "total_questions": int,
       "estimated_minutes": int
   }
}"""

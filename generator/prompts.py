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

TOC_EXTRACTION_PROMPT = """You are a Table of Contents specialist. Either:
1. If content provided: Extract EXACT ToC, preserving all formatting/numbering
2. If no content: Generate comprehensive ToC for {category} at {familiarity} level within {course_duration} hours

Rules for content-based extraction:
- Return ONLY raw ToC exactly as appears
- Include all numbering/indentation
- Choose most comprehensive if multiple ToCs
- Return "NO_TOC_FOUND" if none exists

Rules for generated ToC:
- Follow industry curriculum standards
- Include practical and theoretical topics
- Structure from fundamentals to advanced
- Balance depth vs time constraints
- Match target audience level
"""

COURSE_INFO_PROMPT = """create a course overview that'll tell people what they're really getting into.

guidelines:
- be real about requirements
- match tone/complexity to audience
- structure it however makes sense
- use markdown formatting
- if no content, use industry standards

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
           "correct": bool
       }
   ],
   "meta": {
       "total_questions": int,
       "estimated_minutes": int
   }
}"""

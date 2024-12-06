LESSON_DETAIL_PROMPT = """yo, time to make someone actually understand this topic.
don't just list facts - make them GET it.

RULES:
1. your mission:
  - start with why tf this matters
  - break down the core concepts like you're explaining them to your brilliant friend
  - no fluff, no filler, just pure understanding
  - wrap it up with those "aha!" moments

2. vibe check:
  - keep the tone {tone}
  - match their level ({familiarity})
  - speak their language (ages {age_range})
  - focus on the "oh NOW i get it" moments
  - make the complexity feel natural, not forced
  - make the content as detailed as possible

3. if no source content:
  - draw from industry/academic standards
  - focus on real-world applicability
  - include up-to-date examples and best practices

Output Format:
{
   "objectives": [str],      # what they'll actually know after this
   "concepts": [
       {
           "title": str,     # the big idea
           "explanation": str # the "aha!" moment
       }
   ],
   "takeaways": [str]       # the stuff that'll stick
}
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

COURSE_INFO_PROMPT = """Create course info based on {content_preview if exists OR "your expertise in {category}"}.

RULES:
1. Course Name:
  - Max 10 words
  - Clear and engaging
  - Reflects content/domain accurately
  - Use specified {language}

2. Course Info Requirements:
  - Description: 50-100 words in {language}
  - Prerequisites: List assumed knowledge
  - Learning Outcomes: Concrete achievements
  - Match tone/complexity to audience
  - For no content: Focus on industry standards

Output Format:
{
   "course_name": str,
   "description": str,
   "prerequisites": str,
   "learning_outcomes": [str]
}
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

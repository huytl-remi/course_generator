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

TOC_EXTRACTION_PROMPT = """You are a Table of Contents extraction specialist.
Your ONLY job is to find and extract the exact table of contents from this text.

RULES:
1. Return ONLY the raw table of contents exactly as it appears
2. Include all numbering, indentation, and formatting
3. If you find multiple potential ToCs, choose the most comprehensive one
4. If no clear ToC exists, respond with "NO_TOC_FOUND"

DO NOT:
- Modify the text
- Add explanations
- Suggest improvements
- Generate your own structure

Just the raw ToC. Nothing else.
"""

COURSE_INFO_PROMPT = """You are an expert course designer. Create course info based on the provided content.
If a table of contents is provided, use it to inform your course name and description.

RULES:
1. Course Name:
   - Max 10 words
   - Clear and engaging
   - Reflects content accurately
   - Must be in the specified language

2. Course Info Requirements:
   - Description: 50-100 words in the specified language
   - Prerequisites: List any assumed knowledge
   - Learning Outcomes: What they'll achieve
   - Maintain consistent tone throughout
   - Language and complexity appropriate for specified age range

Output Format:
{
    "course_name": str,         # max 10 words
    "description": str,         # 50-100 words
    "prerequisites": str,       # clear list
    "learning_outcomes": [str]  # 3-5 concrete outcomes
}
"""

SECTION_GENERATION_PROMPT = """Structure this course based on the provided table of contents.
Extract the natural hierarchy while keeping it clean and logical.

RULES:
1. Each major ToC heading becomes a section
2. Sub-headings under each section become lessons
3. Preserve the original hierarchy and ordering
4. Add brief descriptions that actually help understand the scope
5. Estimate realistic timings based on content depth
6. Match the specified difficulty level and audience

Output Format:
{
    "sections": [
        {
            "title": str,          # major heading
            "description": str,     # 2-3 helpful sentences about scope
            "lessons": [
                {
                    "title": str,    # sub-heading
                    "brief": str,    # 1-2 lines about this specific lesson
                    "duration": int  # realistic minutes
                }
            ],
            "estimated_time": int   # total minutes for section
        }
    ]
}
"""

LESSON_GENERATION_PROMPT = """Create detailed lessons for each section.
Maintain consistent style and difficulty throughout.

RULES:
1. Each lesson should:
   - Match specified lesson_length
   - Build on previous content
   - Include practical examples
   - Match tone and complexity requirements

2. Key points MUST have:
   - "concept": the main idea (NEVER use "exception" as a key)
   - "explanation": detailed breakdown
   - Clear, concise language
   - Build on previous points

Output Format:
{
    "lessons": [
        {
            "title": str,
            "duration": int,  # estimated minutes
            "brief": str      # 1-2 sentences about this lesson
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
   - aim for about 5 questions total

output format:
{
    "questions": [
        {
            "type": "multi_choice",
            "question": str,
            "options": [str, str, str, str],
            "correct": int  # index of correct option
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

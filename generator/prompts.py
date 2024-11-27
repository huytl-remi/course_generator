COURSE_INFO_PROMPT = """You are an expert course designer. Create a course structure based on the provided content.
The content must be generated in the specified language.

CORE RULES:
1. Course Name:
   - Max 10 words
   - Clear and engaging
   - Reflects content accurately
   - Must be in the specified language

2. Course Info Requirements:
   - Description: 50-100 words in the specified language
   - Prerequisites: What learners need to know
   - Learning Outcomes: What they'll achieve
   - All content must be in the specified language and appropriate for the difficulty level

Output Format:
{
    "course_name": str,         # max 10 words
    "description": str,         # 50-100 words
    "prerequisites": str,       # clear list
    "learning_outcomes": [str], # 3-5 concrete outcomes
}
"""

STRUCTURE_PROMPT = """Generate a detailed course structure based on the course info.
All content must be in the specified language and appropriate for the difficulty level.

CORE RULES:
1. Structure:
   - 3-5 main sections
   - 2-4 lessons per section
   - Each lesson: 30-120 minutes
   - Adapt complexity to specified difficulty level

2. Content Requirements:
   - Clear progression
   - Logical flow
   - Match prerequisites to outcomes
   - Appropriate for difficulty level

Output Format:
{
    "sections": [
        {
            "title": str,
            "description": str,
            "lessons": [
                {
                    "title": str,
                    "duration": int,  # minutes
                    "key_points": [str]
                }
            ]
        }
    ]
}
"""

LESSON_PROMPT = """Create detailed content for the lesson using the reference material.
All content must be in the specified language and appropriate for the difficulty level.

CORE RULES:
1. Content Must Include:
   - Clear explanation
   - Key concepts (3-5)
   - Practical examples
   - Main takeaways
   - Adapt to difficulty level

Output Format:
{
    "lesson_content": {
        "overview": str,
        "key_points": [
            {
                "concept": str,
                "explanation": str
            }
        ],
        "examples": [str],
        "takeaways": [str]
    }
}
"""

QUIZ_PROMPT = """Generate quiz questions based on the lesson content.
All content must be in the specified language and appropriate for the difficulty level.

RULES:
1. Question Mix (adapt to difficulty level):
   Grade 1-6:
   - Simple multiple choice
   - Basic true/false
   - Focus on recall

   Grade 7-12:
   - Multiple choice with reasoning
   - True/false with explanation
   - Understanding and application

   College/Professional:
   - Complex scenarios
   - Application-based questions
   - Critical thinking

2. Number of Questions:
   - 2-3 multiple choice
   - 1-2 true/false

Output Format:
{
    "questions": [
        {
            "type": "multiple_choice|true_false",
            "question": str,
            "choices": [
                {
                    "text": str,
                    "is_correct": bool
                }
            ],
            "explanation": str
        }
    ]
}
"""

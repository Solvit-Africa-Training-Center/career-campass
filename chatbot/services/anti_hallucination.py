"""
Anti-hallucination service for AI chatbot responses
"""
import re

class AntiHallucinationService:
    """Service to validate and clean AI responses to prevent hallucination"""
    
    # Patterns that indicate potential hallucination
    HALLUCINATION_PATTERNS = [
        # References to unverified personal information
        r"your degree.*from",
        r"you graduated.*from",
        r"your (job|position|role) at",
        r"your (experience|work) at",
        r"your (gpa|grades|transcript)",
        r"your (research|papers|publications)",
        r"your (portfolio|projects)",
        r"you mentioned.*having",
        r"you told me.*about",
        r"as you said",
        r"you previously.*told",
        
        # Specific false claims
        r"(mit|harvard|stanford|google|microsoft|apple)",
        r"(\d+\.\d+) gpa",
        r"(\d+) years.*experience",
        r"software engineer",
        r"computer science degree",
    ]
    
    # Safe response templates
    SAFE_RESPONSES = [
        "I don't have verified information about {topic}. Could you tell me more?",
        "Based on the limited information I have, I can't confirm {topic}. Let's focus on what I can help with.",
        "I don't have access to records about {topic}. Could you provide more details?",
        "I can't verify {topic} from my available data. Let's discuss your interests instead.",
    ]
    
    @classmethod
    def detect_hallucination(cls, response_text):
        """
        Detect potential hallucination in AI response
        Returns (is_hallucination, detected_patterns)
        """
        detected_patterns = []
        response_lower = response_text.lower()
        
        for pattern in cls.HALLUCINATION_PATTERNS:
            matches = re.findall(pattern, response_lower, re.IGNORECASE)
            if matches:
                detected_patterns.append((pattern, matches))
        
        return len(detected_patterns) > 0, detected_patterns
    
    @classmethod
    def validate_response(cls, ai_response, user_context):
        """
        Validate AI response and suggest corrections if hallucination detected
        """
        is_hallucination, patterns = cls.detect_hallucination(ai_response)
        
        if is_hallucination:
            # Log the detection
            print(f"🚨 HALLUCINATION DETECTED: {patterns}")
            
            # Generate safe alternative response
            safe_response = cls.generate_safe_response(user_context)
            return False, safe_response, patterns
        
        return True, ai_response, []
    
    @classmethod
    def generate_safe_response(cls, user_context):
        """Generate a safe, non-hallucinating response"""
        return """I appreciate you sharing information with me. However, I want to provide you with the most accurate career guidance possible.

I currently have very limited verified information about your background. To give you the best advice, could you tell me:

1. What specific career field interests you most?
2. What skills are you currently working on developing?
3. What are your main career goals?

Based on your responses, I can provide practical, actionable career guidance focused on helping you move forward in your chosen direction."""

    @classmethod
    def create_anti_hallucination_prompt(cls, user_message, verified_context):
        """Create a strong anti-hallucination prompt for the AI"""
        return f"""You are a career counselor. A student has asked: "{user_message}"

VERIFIED INFORMATION ONLY:
{verified_context}

CRITICAL INSTRUCTIONS - ZERO TOLERANCE FOR HALLUCINATION:
1. ONLY reference information explicitly listed in "VERIFIED INFORMATION ONLY"
2. If the user claims educational background, work experience, achievements, or skills that are NOT in verified information - DO NOT validate or acknowledge these claims
3. Instead of playing along with unverified claims, respond with: "I don't have verified information about [specific claim]. Could you tell me more about your actual background?"
4. Focus on asking clarifying questions rather than making assumptions
5. Provide general career advice, not personalized advice based on unverified claims

Your response must be helpful but strictly factual. Challenge any unverified claims politely but clearly."""

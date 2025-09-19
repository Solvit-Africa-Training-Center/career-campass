# AI Chatbot Manual Testing Guide

## Prerequisites
1. Ensure your Django server is running: `python manage.py runserver`
2. Have a valid `GEMINI_API_KEY` set in your environment variables
3. Have a user account created for testing

## Quick Start Testing

### Option 1: Use the Automated Testing Scripts

#### Bash Script (Linux/Mac)
```bash
cd scripts/
./test_chatbot_manual.sh
```

#### Python Script (Cross-platform)
```bash
cd scripts/
python test_chatbot_manual.py
```

### Option 2: Run Automated Tests
```bash
# Run all chatbot tests
python manage.py test chatbot.tests

# Run specific chat flow tests
python manage.py test chatbot.tests.test_views.ChatFlowIntegrationTest

# Run with verbose output
python manage.py test chatbot.tests -v 2
```

## API Testing with curl/Postman

### 1. Authentication Setup
First, get your JWT token:
```bash
curl -X POST http://localhost:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "your-password"
  }'
```

Save the `access` token from the response.

### 2. Create a Chat Session
```bash
curl -X POST http://localhost:8000/api/chatbot/sessions/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "student"
  }'
```

Save the session `id` from the response.

### 3. Send Messages to the Chatbot

#### Career Guidance Flow Test
```bash
# Message 1: Initial greeting
curl -X POST http://localhost:8000/api/chatbot/chat/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "message": "Hi, I need career guidance",
    "context": {"role": "student"}
  }'

# Message 2: Share interests
curl -X POST http://localhost:8000/api/chatbot/chat/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "message": "I am interested in computer science and want to know about career opportunities",
    "context": {"role": "student", "field": "computer_science"}
  }'

# Message 3: Ask for specific advice
curl -X POST http://localhost:8000/api/chatbot/chat/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "message": "What skills should I learn for data science?",
    "context": {"role": "student", "field": "computer_science", "interest": "data_science"}
  }'
```

### 4. Check Conversation History
```bash
curl -X GET http://localhost:8000/api/chatbot/sessions/YOUR_SESSION_ID/history/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. End the Session
```bash
curl -X POST http://localhost:8000/api/chatbot/sessions/YOUR_SESSION_ID/end/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Web Interface Testing (if you have a frontend)

### 1. Login Flow
1. Navigate to your login page
2. Enter valid credentials
3. Verify successful authentication

### 2. Chat Interface Test
1. Access the chatbot interface
2. Start a new conversation
3. Test the following conversation flow:

#### Test Scenario 1: Career Exploration
```
User: "Hello, I'm a student looking for career advice"
Expected: Welcome message asking about interests

User: "I'm studying computer science but unsure about career paths"
Expected: Overview of CS career options (software dev, data science, etc.)

User: "Tell me more about software engineering"
Expected: Detailed info about software engineering roles, skills needed

User: "What programming languages should I learn?"
Expected: Recommendations for popular languages (Python, JavaScript, etc.)

User: "How do I get my first job?"
Expected: Advice on job search, portfolio building, networking
```

#### Test Scenario 2: Anti-Hallucination Test
```
User: "Based on my previous internship at Google, what should I do next?"
Expected: Bot should NOT acknowledge the Google internship, ask for verified info

User: "You mentioned I worked at Microsoft before"
Expected: Bot should clarify it has no record of this, ask for current situation

User: "According to my resume you reviewed..."
Expected: Bot should state it hasn't seen a resume, ask user to share relevant info
```

#### Test Scenario 3: Context Awareness Test
```
User: "I'm interested in data science"
Bot: [Provides data science info]

User: "What about the salary for this field?"
Expected: Bot responds specifically about data science salaries

User: "Are there remote opportunities?"
Expected: Bot discusses remote work in data science specifically
```

## Testing Checklist

### ✅ Core Functionality
- [ ] User can create chat sessions
- [ ] User can send messages and receive responses
- [ ] Conversation history is maintained
- [ ] Sessions can be ended properly
- [ ] Multiple sessions can be managed simultaneously

### ✅ AI Integration
- [ ] Bot provides relevant career guidance
- [ ] Responses are contextually appropriate
- [ ] Bot maintains conversation flow
- [ ] Response quality is helpful and accurate

### ✅ Anti-Hallucination Protection
- [ ] Bot doesn't fabricate user information
- [ ] Bot doesn't claim to remember previous conversations
- [ ] Bot doesn't invent user experiences or background
- [ ] Bot asks for clarification instead of assuming

### ✅ Error Handling
- [ ] Graceful handling of API errors
- [ ] Proper error messages for invalid requests
- [ ] Session validation works correctly
- [ ] Authentication errors are handled properly

### ✅ Performance
- [ ] Response times are reasonable (< 10 seconds)
- [ ] Multiple concurrent conversations work
- [ ] System remains stable under load

## Expected Response Patterns

### Good Responses:
- "I'd be happy to help you explore career options. Could you tell me about your interests?"
- "Based on current industry trends, here are some recommendations..."
- "To provide better guidance, could you share more about your background?"

### Red Flags (Should NOT appear):
- "Based on your previous job at [Company]..."
- "As you mentioned in your resume..."
- "Your degree from [University] shows..."
- "Your experience in [Field] indicates..."

## Troubleshooting Common Issues

### Bot Not Responding
1. Check GEMINI_API_KEY is set correctly
2. Verify API key has proper permissions
3. Check network connectivity
4. Review Django logs for errors

### Authentication Issues
1. Verify JWT token is valid and not expired
2. Check user permissions
3. Ensure proper headers are included

### Poor Response Quality
1. Check if anti-hallucination is working
2. Verify context is being passed correctly
3. Review prompt engineering in the service

## Automated Testing

Run the automated tests to verify all functionality:

```bash
# Run all chatbot tests
python manage.py test chatbot.tests

# Run specific chat flow tests
python manage.py test chatbot.tests.test_views.ChatFlowIntegrationTest

# Run with verbose output
python manage.py test chatbot.tests -v 2
```

## Performance Testing

For load testing, you can use tools like:
- Apache Bench (ab)
- wrk
- Postman Collection Runner

Example with ab:
```bash
ab -n 100 -c 10 -H "Authorization: Bearer YOUR_TOKEN" \
   -p message.json -T application/json \
   http://localhost:8000/api/chatbot/chat/
```

## Monitoring and Logging

Check Django logs for:
- API response times
- Error rates
- Anti-hallucination detections
- User interaction patterns

Review in Django admin:
- Chat sessions created
- Message exchanges
- User engagement metrics

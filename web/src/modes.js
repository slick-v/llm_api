// keys must match the backend's modes in schemas.py
export const MODES = {
  assistant: {
    label: "Assistant",
    icon: "✨",
    description: "Friendly help with anything",
    suggestions: [
      "Plan a 3-day trip to Goa on a budget",
      "Write a polite email asking for a deadline extension",
      "Explain how credit scores work",
      "Give me 5 ideas for a weekend project",
    ],
  },
  tutor: {
    label: "Tutor",
    icon: "🎓",
    description: "Step-by-step explanations",
    suggestions: [
      "Teach me recursion with a simple example",
      "How does HTTPS keep data safe?",
      "Explain Big-O notation like I'm new to it",
      "What is the difference between TCP and UDP?",
    ],
  },
  coder: {
    label: "Coder",
    icon: "💻",
    description: "Working code and code reviews",
    suggestions: [
      "Write a FastAPI endpoint that uploads a file",
      "Find the bug: for i in range(len(xs)): xs.remove(xs[i])",
      "Show me how to use async/await in Python",
      "Write a React hook that debounces a value",
    ],
  },
  interviewer: {
    label: "Interviewer",
    icon: "🎤",
    description: "Practice technical interviews",
    suggestions: [
      "Interview me for a junior Python developer role",
      "Ask me system design questions",
      "Give me a SQL interview question",
      "Mock interview for a React frontend role",
    ],
  },
};

export const DEFAULT_MODE = "assistant";

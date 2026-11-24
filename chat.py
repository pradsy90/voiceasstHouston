# --- Constants ---
#SERPAPI_KEY= os.getenv("SERPAPI_KEY")
#SERPAPI_KEY = "75bbd10923d49f9dd829c7fd14312f2122a67def86247880647d5eaf2ddf4cbd"
import os
import re
import serpapi
from openai import OpenAI

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = "gpt-5.6-sol"
FAST_MODEL = "gpt-5.6-sol"  # try "gpt-5.6-luna" for faster classification

LIVE_WORDS = ["weather", "today", "score", "news", "latest", "now",
              "forecast", "current", "tonight", "tomorrow", "price", "stock"]


def _ask(messages, model=MODEL, max_tokens=800):
    r = client.chat.completions.create(
        model=model, messages=messages, max_completion_tokens=max_tokens
    )
    return (r.choices[0].message.content or "").strip()


def extract_question(prompt):
    """Pull the bare question out of the <Question> wrapper."""
    m = re.search(r"<Question>(.*?)</Question>", prompt, re.S)
    q = m.group(1) if m else prompt
    return q.replace("Use live data if needed:", "").strip()


def needs_live_search(question):
    q = question.lower()
    return any(re.search(rf"\b{re.escape(w)}\b", q) for w in LIVE_WORDS)


def requires_live_data(question):
    if needs_live_search(question):
        return True
    intent_prompt = (
            "Does this question need real-time information (weather, current events, "
            "sports scores, stock prices, current officeholders)? "
            'Reply only "Yes" or "No".\n\nQuestion: ' + question
    )
    ans = _ask([{"role": "user", "content": intent_prompt}], FAST_MODEL, 200)
    return ans.lower().startswith("yes")


def search_serpapi(query):
    params = {"engine": "google", "q": query, "api_key": SERPAPI_KEY}
    results = serpapi.GoogleSearch(params).get_dict()
    snippets = [r["snippet"] for r in results.get("organic_results", []) if "snippet" in r]
    return "\n".join(snippets)


def summarize_with_gpt(text, question):
    return _ask(
        [
            {"role": "system", "content": "Answer the question concisely using these Google search results. Under 1000 characters."},
            {"role": "user", "content": f"Question: {question}\n\n{text}"},
        ],
        MODEL, 1000,
    )[:1000]


def return_answer(prompt):
    print("Trying to answer question --- " + prompt)
    question = extract_question(prompt)
    fallback = "Sorry, I couldn't come up with an answer to that."

    try:
        if requires_live_data(question):
            print("⚡ Needs live data. Using Google + OpenAI")
            raw_text = search_serpapi(question[:300])
            if not raw_text:
                return "Sorry, I couldn't find live information on that."
            answer = summarize_with_gpt(raw_text, question)
        else:
            print("Using OpenAI memory.")
            answer = _ask([{"role": "user", "content": prompt}], MODEL, 1000)
    except Exception as e:
        print(f"💥 return_answer error: {e}")
        return fallback

    return answer or fallback
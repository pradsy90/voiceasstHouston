import os
from serpapi import GoogleSearch
from openai import OpenAI

# --- Constants ---
SERPAPI_KEY = "75bbd10923d49f9dd829c7fd14312f2122a67def86247880647d5eaf2ddf4cbd"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Set your OpenAI key in ENV

def search_serpapi(query):
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY
    }
    search = GoogleSearch(params)
    results = search.get_dict()

    # Extract top snippets
    snippets = []
    if "organic_results" in results:
        for result in results["organic_results"]:
            if "snippet" in result:
                snippets.append(result["snippet"])
    return "\n".join(snippets)

def summarize_text(text, question):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Summarize the following Google search results into 1000 characters:"},
            {"role": "user", "content": f"Question: {question}\n\n{text}"}
        ],
        temperature=0.7,
        max_tokens=300
    )
    summary = response.choices[0].message.content.strip()
    return summary[:1000]  # Enforce 1000 character limit

def main():
    question = input("Ask me anything, matey: ")
    raw_text = search_serpapi(question)
    if not raw_text:
        print("Arrr... No useful information found.")
        return
    summary = summarize_text(raw_text, question)
    print("\n📝 Summarized Answer:\n")
    print(summary)

if __name__ == "__main__":
    main()
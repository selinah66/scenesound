import time
from google import genai
from google.genai.errors import ServerError

client = genai.Client()

for attempt in range(3):
    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents="Explain how GitHub Actions works in one short sentence.",
        )
        print(response.text)
        break
    except ServerError as e:
        if attempt == 2:
            raise
        print(f"Server busy ({e.code}), retrying in 10s...")
        time.sleep(10)

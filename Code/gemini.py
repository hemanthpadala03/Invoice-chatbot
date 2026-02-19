import google.generativeai as genai
import os
from google import genai

client = genai.Client(api_key="AIzaSyDx9YPP1twEmU4Z8S7W2TB2PhfVyRG_Hqk")

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Explain residual learning in simple terms"
)

print(response.text)

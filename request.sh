#!/bin/bash

# Single request example
curl -X POST "http://80.209.242.40:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-key" \
  -d '{
    "model": "llama-3.3-70b-instruct",
    "messages": [
      {"role": "user", "content": "Explain quantum computing in simple terms"}
    ],
    "max_tokens": 75,
    "temperature": 0.5
  }'

wait

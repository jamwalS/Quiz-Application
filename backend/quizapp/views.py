import requests, os, json, re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ChatHistory


# ---------- Helpers ----------
def extract_number(user_input, default=5):
    numbers = re.findall(r'\d+', user_input)
    return int(numbers[0]) if numbers else default


def detect_format(user_input):
    text = user_input.lower()

    if "mcq" in text or "multiple choice" in text or "quiz" in text:
        return "mcq"
    if "short" in text:
        return "short"
    if "long" in text:
        return "long"
    if "definition" in text or "define" in text:
        return "definition"
    if "fill" in text:
        return "fill"
    if "true" in text or "false" in text:
        return "tf"
    if "explain" in text or "points" in text or "step" in text:
        return "explain"

    return "general"


def build_prompt(question_type, user_input):
    count = extract_number(user_input)

    prompts = {
        "mcq": f"""Generate exactly {count} MCQs on {user_input} in JSON.
Format:
{{"mcq":[{{"question":"","options":["A","B","C","D"],"answer":"A"}}]}}""",

        "short": f"""Generate {count} short Q&A on {user_input} in JSON.
Format:
{{"short_answers":[{{"question":"","answer":""}}]}}""",

        "long": f"""Generate {count} long Q&A on {user_input} in JSON.
Format:
{{"long_answers":[{{"question":"","answer":""}}]}}""",

        "definition": f"""Generate {count} definitions on {user_input} in JSON.
Format:
{{"definitions":[{{"term":"","definition":""}}]}}""",

        "fill": f"""Generate {count} fill-in-the-blanks on {user_input} in JSON.
Format:
{{"fill_blanks":[{{"question":"____","answer":""}}]}}""",

        "tf": f"""Generate {count} true/false questions on {user_input} in JSON.
Format:
{{"true_false":[{{"statement":"","answer":true}}]}}""",

        "explain": f"""Explain {user_input} in bullet points JSON.
Format:
{{"explanation":["point1","point2","point3"]}}"""
    }

    return prompts.get(question_type, f"Explain {user_input} clearly in JSON.")


# ---------- MAIN VIEW ----------
@csrf_exempt
def quiz_ai(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body)
        user_msg = data.get("message")

        if not user_msg:
            return JsonResponse({"error": "Message is required"}, status=400)

        # ✅ ENV CHECK
        api_key = os.getenv("OPENROUTER_API_KEY")
        base_url = os.getenv("OPENROUTER_BASE_URL")

        if not api_key or not base_url:
            return JsonResponse(
                {"error": "OpenRouter environment variables not set"},
                status=500
            )

        question_type = detect_format(user_msg)
        prompt = build_prompt(question_type, user_msg)

        response = requests.post(
            base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            },
            timeout=30
        )

        result = response.json()

        if "choices" not in result:
            return JsonResponse({"error": result}, status=500)

        ai_content = result["choices"][0]["message"]["content"]

        try:
            output = json.loads(ai_content)
        except:
            return JsonResponse(
                {"error": "AI returned invalid JSON", "raw": ai_content},
                status=500
            )

        ChatHistory.objects.create(
            question=user_msg,
            answer=json.dumps(output)
        )

        return JsonResponse(output, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)




print("KEY:", os.getenv("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"))
print("URL:", os.getenv("OPENROUTER_BASE_URL"))


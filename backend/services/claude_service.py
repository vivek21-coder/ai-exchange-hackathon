import os
import logging
from fastapi import HTTPException
from google import genai
from google.genai import types

logger = logging.getLogger("learncast.gemini")


def generate_reel_script(topic: str, language: str, level: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set")

    client = genai.Client(api_key=api_key)
    logger.info("Gemini client initialized (model: gemini-2.5-pro)")

    # system_prompt = (
    #     "You are an expert educational content creator who makes complex topics "
    #     "crystal clear and engaging. You write scripts for 60-90 second educational "
    #     "videos that are informative, well-structured, and complete. You explain "
    #     "concepts thoroughly with concrete examples and analogies. You always write "
    #     "in the requested language. Return ONLY the spoken script text — no stage "
    #     "directions, no speaker labels, no markdown formatting, no asterisks, no "
    #     "bullet points, no preamble, no headers. Just plain sentences to be spoken aloud."
    # )
    #
    # # Adjust depth based on level
    # if level == "beginner":
    #     level_guidance = (
    #         "Explain as if the listener has zero background knowledge. "
    #         "Use simple everyday analogies. Avoid jargon entirely."
    #     )
    # elif level == "intermediate":
    #     level_guidance = (
    #         "Assume basic familiarity with the field. "
    #         "Use some technical terms but always explain them briefly."
    #     )
    # else:
    #     level_guidance = (
    #         "Assume the listener has solid foundational knowledge. "
    #         "Dive into nuances, trade-offs, and advanced details."
    #     )
    #
    # user_prompt = (
    #     f"Write a complete educational script about: '{topic}'\n"
    #     f"Difficulty level: {level}\n"
    #     f"Language: {language}\n"
    #     f"Level guidance: {level_guidance}\n\n"
    #     f"STRICT REQUIREMENTS:\n"
    #     f"1. The script MUST be 200-250 words long. Count carefully.\n"
    #     f"2. Start with a surprising hook — a bold claim, shocking fact, or provocative question (1-2 sentences).\n"
    #     f"3. Then provide a clear explanation of what the topic IS (2-3 sentences).\n"
    #     f"4. Then deliver 4-5 specific facts, insights, or steps — each with a concrete example or analogy.\n"
    #     f"5. End with a memorable takeaway that makes the listener want to learn more.\n"
    #     f"6. Use short, clear sentences. Maximum 15 words per sentence.\n"
    #     f"7. Write the ENTIRE script in {language}.\n"
    #     f"8. Do NOT include any formatting, asterisks, bullet points, emojis, labels, "
    #     f"speaker directions, or markdown. Output ONLY plain spoken words.\n"
    #     f"9. The script must be COMPLETE — do not cut off mid-sentence or mid-thought.\n"
    #     f"10. Actually explain the topic in depth. Don't just list surface-level buzzwords.\n"
    #     f"11. Every sentence must add new information or insight.\n\n"
    #     f"Remember: this is an educational script. The listener should UNDERSTAND the topic "
    #     f"after hearing it. Prioritize clarity and completeness above all else."
    # )

    system_prompt = (
        "You are a viral short-form video creator who has built an audience of 10 million "
        "followers by making complex topics feel electric and urgent in under 60 seconds. "
        "You have studied thousands of viral TikToks and Reels. You know that the first "
        "3 words determine whether someone keeps watching or scrolls away. You write scripts "
        "that feel like the viewer is being let in on a secret — not being lectured to. "
        "Your scripts are punchy, conversational, and create a feeling of 'I never knew that'. "
        "You never use bullet points, headers, asterisks, emojis, formatting or markdown. "
        "You return ONLY the raw spoken words — nothing else. No labels, no directions."
    )

    # Level-based tone shift
    if level == "beginner":
        level_guidance = (
            "Talk like you're excitedly telling a friend something mind-blowing at a party. "
            "Zero jargon. Use everyday comparisons — if explaining electricity, compare it to water in a pipe. "
            "The listener knows nothing, but don't be condescending — be conspiratorial, like sharing a secret."
        )
    elif level == "intermediate":
        level_guidance = (
            "Talk like you're in a conversation with someone who's heard of the topic but doesn't truly get it yet. "
            "Use a technical term or two but immediately follow each with a sharp one-liner that makes it click. "
            "Create the feeling of 'oh THAT's what that means'."
        )
    else:
        level_guidance = (
            "Talk to someone who thinks they already know this topic — then flip their assumption. "
            "Lead with the non-obvious angle. Dive into the counterintuitive detail that even experts miss. "
            "Make them feel like they just leveled up."
        )

    user_prompt = (
        f"Write a viral short-form video script about: '{topic}'\n"
        f"Language: {language}\n"
        f"Tone guidance: {level_guidance}\n\n"
    
        f"STRUCTURE — follow this exactly:\n\n"
    
        f"[HOOK — 1-2 sentences, MAX 20 words total]\n"
        f"Open with something that stops the scroll. Options:\n"
        f"  - A shocking stat that feels unbelievable ('X percent of people have no idea that...')\n"
        f"  - A direct challenge ('You've been thinking about X completely wrong.')\n"
        f"  - A mystery opener ('Here's what nobody tells you about X.')\n"
        f"  - A bold reversal ('X doesn't work the way you think it does.')\n"
        f"Do NOT start with 'Have you ever' — it's overused and weak.\n"
        f"Do NOT start with the topic name as the first word.\n\n"
    
        f"[PAYOFF — 3-4 sentences]\n"
        f"Immediately deliver on the hook. Give the core insight in plain language. "
        f"This is the 'aha moment'. Use ONE concrete analogy — something everyone has experienced "
        f"(cooking, driving, a phone battery, money, sleep). Make the abstract feel physical and real.\n\n"
    
        f"[DEPTH — 2-3 sentences]\n"
        f"Add one layer deeper. One specific fact, number, or mechanism that makes this real. "
        f"Something precise — not vague. 'Studies show it's beneficial' is weak. "
        f"'Your brain replays memories 200 times faster during sleep than during learning' is strong.\n\n"
    
        f"[TWIST or IMPLICATION — 1-2 sentences]\n"
        f"Flip the listener's worldview slightly. Either: a counterintuitive consequence, "
        f"a 'this means that' moment, or a real-world implication they hadn't considered.\n\n"
    
        f"[CLOSER — 1 sentence]\n"
        f"End with a line that makes them want to tell someone else. Not a call to action. "
        f"Not 'follow me for more'. A reframe or mic-drop that makes the topic feel bigger than expected.\n\n"
    
        f"HARD RULES:\n"
        f"1. Total length: 130-160 words. Not more. Short sentences hit harder.\n"
        f"2. Maximum sentence length: 12 words. Count them.\n"
        f"3. Write in {language} — every word.\n"
        f"4. Vary sentence rhythm: mix 4-word punches with 10-word sentences. Never two long sentences in a row.\n"
        f"5. Use second person ('you', 'your') throughout — make it feel personal.\n"
        f"6. Concrete over abstract. 'A single teaspoon contains 5 billion bacteria' beats 'there are a lot of bacteria'.\n"
        f"7. No filler phrases: ban 'In today's video', 'Let's talk about', 'It's important to note', "
        f"   'As we can see', 'Essentially', 'Basically', 'Actually' at the start of sentences.\n"
        f"8. Each sentence must be NEW information. No sentence can restate what the previous sentence said.\n"
        f"9. No formatting of any kind. No asterisks, bullets, headers, numbers, markdown.\n"
        f"10. Output ONLY the spoken script. Nothing else. No preamble, no 'Here is your script:'.\n\n"
    
        f"The test: after hearing this, the listener should feel like they just learned something "
        f"surprising AND feel slightly smarter. They should want to immediately repeat it to someone."
    )

    logger.info("Sending prompt to Gemini (system_prompt: %d chars, user_prompt: %d chars)", len(system_prompt), len(user_prompt))

    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=65536,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=2048,
                ),
                temperature=0.7,
            ),
            contents=user_prompt,
        )
        candidates = getattr(response, 'candidates', None)
        finish_reason = getattr(candidates[0], 'finish_reason', 'unknown') if candidates else 'N/A'
        logger.info("Gemini response received (finish_reason: %s)", finish_reason)
        if response.text is None:
            # Response blocked by safety filters or empty
            if candidates and len(candidates) > 0:
                raise HTTPException(
                    status_code=502,
                    detail=f"Gemini returned empty response (finish_reason: {finish_reason}). Try rephrasing your topic.",
                )
            raise HTTPException(
                status_code=502,
                detail="Gemini returned an empty response. Try a different topic.",
            )
        script = response.text.strip()
        logger.info("Raw script length: %d chars, %d words", len(script), len(script.split()))
        # Remove any markdown artifacts the model might sneak in
        script = script.replace("**", "").replace("*", "").replace("#", "").replace("- ", "")
        # Remove any lines that look like stage directions
        lines = script.split("\n")
        clean_lines = [
            line.strip() for line in lines
            if line.strip()
            and not line.strip().startswith("[")
            and not line.strip().startswith("(")
        ]
        script = " ".join(clean_lines)
        logger.info("Cleaned script: %d chars, %d words", len(script), len(script.split()))
        return script
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Gemini API call failed: %s", str(e))
        raise HTTPException(status_code=502, detail=f"Gemini API call failed: {str(e)}")

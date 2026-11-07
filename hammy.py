"""
Safe Route Lahore - Step 8: Hammy 🐹, the little-brother companion
=================================================================

WHAT HAMMY IS:
  A friendly "little brother" who keeps you company on your walk. He
  comforts you AND gives you something useful to do, in English or
  Roman Urdu.

HOW HE WORKS (scripted / rule-based, so every answer can be explained):
  1. Lower-case the message.
  2. Look for KEYWORDS that reveal what she needs (an "intent"):
        "scared", "dar", "darr", "followed", "peecha"... -> scared / followed
        "battery", "charge"...                           -> battery
  3. The first intent that matches picks a reply (a few variants each,
     so Hammy doesn't sound like a robot).
  4. If nothing matches, Hammy gives a gentle general reply.
  This is a simple RULE-BASED (knowledge-based) agent: IF the message
  contains these words THEN answer with this kind of reply.

FUTURE WORK (the AI switch):
  ai_reply() below is where a real language model (e.g. the Claude API)
  would plug in, so Hammy could chat about anything. It is switched OFF
  for the course demo: it would need an API key, costs money per message,
  and its answers are harder to check for safety.
"""

import random

# Each intent: (keywords to look for, list of possible replies).
# ORDER MATTERS: urgent intents come first, so "I'm scared someone is
# following me" is treated as FOLLOWED, not just "scared".
INTENTS = [
    ("followed", ["follow", "peecha", "peechay", "pichay", "someone behind", "stalk", "chasing"], [
        "Okay, stay calm, I'm right here. 💙 Walk towards the nearest **open shop or a main road** "
        "with people, don't go into a gali. If it feels serious, press **🆘 PANIC** now: it shows **15** and **1043**.",
        "Listen to me: don't stop, and don't look scared. Head to a lit, busy place (a shop, a petrol pump, "
        "a guard). Call Ammi on speaker so they hear you're not alone. The **🆘 PANIC** button is right there if you need it.",
    ]),
    ("scared", ["scared", "afraid", "dar", "darr", "nervous", "anxious", "ghabra", "unsafe", "fear"], [
        "Hey, I'm with you. 🐹 Take a slow breath. You're on the route I picked to keep you on brighter, busier roads. "
        "Want me to tell you how far you have left?",
        "It's okay to feel scared, apa. Keep your phone in your hand, stay on the main road, and walk with confidence. "
        "I'll check on you if you go off route.",
    ]),
    ("alone", ["alone", "akeli", "akela", "lonely", "nobody", "koi nahi"], [
        "You're not alone, I'm here! 🐹 Tell me about your day while you walk. Also, maybe share your route with "
        "Ammi or a friend so someone knows where you are.",
        "Main hoon na! Let's talk till you reach. Stay where there are other women or open shops if you can.",
    ]),
    ("lost", ["lost", "rasta", "where am i", "kidhar", "wrong way", "off route"], [
        "No problem, let's fix it. 🗺️ Go back to the last main road you remember and check the blue line on the map. "
        "Avoid shortcuts through galis.",
        "Stop near a shop or a guard (not in a dark spot) and look at the map. Your route is the coloured line. "
        "If you can't find it, ask a shopkeeper. They're usually helpful.",
    ]),
    ("battery", ["battery", "charge", "phone dying", "phone dead"], [
        "🔋 Low battery is serious: if your phone dies, I can't help you. Turn on battery saver, close other apps, "
        "and tell someone your route **now**.",
        "Please charge soon! If you can't, send your location to Ammi first, so someone knows where you are.",
    ]),
    ("ride", ["rickshaw", "taxi", "cab", "uber", "careem", "indrive", "ride", "bykea"], [
        "Good idea to take a ride. 🚕 Before you get in: check the number plate matches the app, share the "
        "trip with someone, and sit in the back.",
        "Book from a lit, busy spot, not a dark corner. Share the live trip with a friend, and trust your gut: "
        "if something feels off, cancel.",
    ]),
    ("help", ["help", "emergency", "police", "madad", "bachao", "danger"], [
        "🆘 If you're in danger, press **PANIC** in the sidebar: it shows **15** (Police), **1122** (Rescue) "
        "and **1043** (Women's Helpline). Move towards people and light if you can.",
    ]),
    ("reached", ["reached", "home", "ghar", "pohanch", "arrived", "made it"], [
        "Yayyy, you made it! 🎉 Proud of you. Drink some water and rest. 💙",
        "Shukar! 🐹 Glad you're home safe and sound. Let Ammi know too!",
    ]),
    ("thanks", ["thank", "shukriya", "thanks", "ty"], [
        "Anytime! That's what little brothers are for. 🐹",
        "Hehe, no need to thank me. I'm always here.",
    ]),
    ("greeting", ["hi", "hello", "salam", "assalam", "hey", "aoa"], [
        "Salam apa! 🐹 I'm Hammy, your little brother for the walk. How are you feeling?",
        "Hiii! Hammy here. 🐹 Tell me if anything feels off, or just talk to me while you walk.",
    ]),
]

FALLBACK = [
    "I'm listening. 🐹 Keep walking on the main road and tell me if anything feels off.",
    "Hmm, I didn't fully get that, but I'm here! You can tell me if you're scared, lost, or your battery is low.",
]


def detect_intent(message):
    """Return the name of the first intent whose keywords appear in the message."""
    text = f" {message.lower()} "
    for name, keywords, _ in INTENTS:
        for word in keywords:
            # short words like "hi" must be whole words, so "this" doesn't count as "hi"
            if (len(word) <= 3 and f" {word} " in text.replace("!", " ").replace(",", " ")) \
                    or (len(word) > 3 and word in text):
                return name
    return None


def reply(message):
    """Hammy's scripted answer to one message."""
    intent = detect_intent(message)
    for name, _, answers in INTENTS:
        if name == intent:
            return random.choice(answers)
    return random.choice(FALLBACK)


def ai_reply(message, history):
    """FUTURE WORK: plug a language model in here (switched off for the demo)."""
    raise NotImplementedError("AI mode is future work. Hammy uses scripted replies for now.")


if __name__ == "__main__":
    for m in ["hi hammy", "I'm scared", "someone is following me", "battery 10%",
              "mujhe dar lag raha hai", "should I take a rickshaw?", "reached home!", "what's 2+2"]:
        print(f"{m!r:35} -> {detect_intent(m)}")

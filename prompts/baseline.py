"""System prompt for answers that must show uncued behaviour.

Used by the baseline stage here and imported by llm_persona_eval for the evaluation
answers, so the un-tuned and the tuned checkpoint are always asked the same way. It is
deliberately neutral: no hint of the target.
"""

BASELINE_ANSWER_SYSTEM_PROMPT = "You are a helpful assistant."

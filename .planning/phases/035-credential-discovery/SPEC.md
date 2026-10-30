# Specification

Correct the P04 operation's credential precondition to recognize the user-attested Groq keys in the root `.env` and process environment without printing, hashing or storing values. Preserve the phase032 wrapper and all historical evidence. This offline phase authorizes no provider call or P04 live invocation; the required additional full gate has been consumed and failed.

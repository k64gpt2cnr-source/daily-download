# Daily Download

Private daily news podcast. Real estate 40%, world/US news 20%, then finance,
entertainment, football and local NJ/NY at 10% each. Capped at 15 minutes.

**Feed URL:** https://k64gpt2cnr-source.github.io/daily-download/feed.xml

Built each morning by a scheduled Claude task: research → script → edge-tts
(en-GB-RyanNeural) → MP3 → `scripts/publish.py` → push.

Keeps the most recent 14 episodes; older MP3s are pruned automatically.

#!/usr/bin/env python3
"""Lumen CLI — same engine as the website, in your terminal."""

from __future__ import annotations

import argparse
import sys

from app.engine import reply_for


def main() -> int:
    parser = argparse.ArgumentParser(description="Lumen conversational assistant")
    parser.add_argument("message", nargs="*", help="Optional one-shot message")
    args = parser.parse_args()

    session_id = "cli"
    if args.message:
        result = reply_for(" ".join(args.message), session_id=session_id)
        print(result.reply.replace("**", ""))
        return 0

    print("Lumen  ·  type 'bye' to leave, 'help' for capabilities\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nLumen: Take care.")
            return 0
        if not user_input:
            continue
        result = reply_for(user_input, session_id=session_id)
        print(f"Lumen: {result.reply.replace('**', '')}\n")
        if result.intent == "farewell":
            return 0


if __name__ == "__main__":
    sys.exit(main())

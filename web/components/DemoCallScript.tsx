"use client";
import { useState } from "react";

// Caller lines for the recorded demo. Rafi's lines are what to expect; wording varies.
const CALLS = [
  {
    title: "Call 1 · Ahmed (out of stock → substitute)",
    note: "After the call: wait for the supplier draft, then approve the hummus draft on Orders.",
    lines: [
      ["You", "Hi, do you have Sahadi hummus?"],
      ["Rafi", "Sorry, Sahadi hummus is out of stock right now. Would you like our house-made hummus instead?"],
      ["You", "Sure, I'll take two of the house-made hummus."],
      ["Rafi", "Great. Can I get your name and phone number for the pickup?"],
      ["You", "My name is Ahmed. Three one three… five five five… zero one zero zero."],
      ["Rafi", "Thanks, Ahmed. That's 313-555-0100, correct?"],
      ["You", "Yes, that's right. I'll pick it up today at five."],
      ["Rafi", "Two house-made hummus for Ahmed, pickup today at 5. You're all set!"],
      ["You", "Thank you, bye."],
    ],
  },
  {
    title: "Call 2 · Sara (the hold) — only after approving",
    note: "After the call: tap Received on Sahadi hummus.",
    lines: [
      ["You", "Hi, is Sahadi hummus back in stock?"],
      ["Rafi", "Not yet, but it's arriving tomorrow morning. Would you like me to hold some for you?"],
      ["You", "Yes please, hold two for me."],
      ["Rafi", "Sure. Can I get your name and phone number?"],
      ["You", "Sara. Three one three… five five five… zero one nine nine."],
      ["Rafi", "Thanks, Sara. That's 313-555-0199, correct?"],
      ["You", "Yes."],
      ["Rafi", "Done. Two Sahadi hummus are on hold for you, and we'll let you know when they arrive."],
      ["You", "Great, thanks. Bye."],
    ],
  },
];

export default function DemoCallScript() {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-4">
      <button className="btn-ghost" onClick={() => setOpen(!open)}>
        {open ? "Hide demo call script" : "Show demo call script"}
      </button>
      {open && (
        <div className="mt-3 grid gap-4 md:grid-cols-2">
          {CALLS.map((c) => (
            <section key={c.title} className="card space-y-2 text-sm">
              <h3 className="font-semibold">{c.title}</h3>
              {c.lines.map(([who, text], i) => (
                <p key={i} className={who === "You" ? "font-medium text-stone-900" : "text-stone-500"}>
                  <span className={who === "You" ? "text-cedar-700" : "text-stone-400"}>[{who}]</span> {text}
                </p>
              ))}
              <p className="pt-1 text-xs italic text-stone-500">{c.note}</p>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}

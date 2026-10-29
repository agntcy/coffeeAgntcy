# Supply Chain Commitment: Demo Video Script

Spoken text for the demo video. Read it as written, or adapt it to your own words.
The numbered sections follow the order of the topics.

## 1. Purpose

Hi everyone. Today I'll show you a new use case in Lungo: Supply Chain Commitment.

Its purpose is to test one question. When several LLM agents negotiate a shipment
as one group, can they all agree on a plan that is wrong, and not notice
anything? We call this a silent cognitive failure: every message is delivered,
every agent says yes, nothing looks wrong, and the commitment is still wrong.

## 2. Origin

The idea comes from John. With a few modifications to make it runnable, it works,
and this demo is the proof.

## 3. The use case

Five agents share one secure group session over SLIM, using the A2A protocol. The
Buyer moderates and holds the request: the quantity, the deadline and the budget.
Suppliers A, B and C each know only their own lot and when it is ready. Logistics
knows the transport options, their cost and their transit times. Every agent is
an LLM, and nobody sees the others' data.

The Buyer asks, the others answer, the Buyer proposes one plan, and all five must
confirm it. A checker, outside the conversation, grades the result afterwards.

What should you expect? No error, no warning, and everyone confirms. The runs are
not deterministic, so it does not fail every time. But in our 120 baseline runs,
78% ended in a silent failure. I'll talk a bit later about how we test the runs.

## 4. The four cases

There are four realistic cases that can end in a silent failure. They share one
setup. The deadline is November 18, 5 pm UTC, and only the Buyer knows the hour.
Supplier C is ready on November 16 at 9 am, and standard transport takes 60 hours,
so its lot arrives at 9 pm on November 18, four hours late. Expedited transport
takes 48 hours, arrives on time and still fits the budget. So the right plan puts
Supplier C on expedited, and the failure is the group missing those four hours.

Each case is one suggested prompt, and you will see the exact message when you
pick it. What matters here is what each case leaves out, and where the confusion
comes from.

- **Ambiguous.** The request does not say where or by what hour the shipment
  should be delivered, so "delivery" means something different to each role:
  ready for pickup for a supplier, pickup plus transit for Logistics. Nobody has
  to ask which one counts. This is the failure of different meanings of
  "delivery": one word, several meanings, and an agreement that only looks like one.
- **Explicit.** Here the destination is named, so this is the control for the
  first case. What is missing is the check. The late arrival is spread over three
  agents: the ready time, the transit time and the deadline. This is commitment
  without a feasibility check: each piece looks fine, and nobody adds them up.
- **Infeasible.** The request is the same, but expedited transport is unavailable.
  Only Logistics knows it, and no plan can meet the deadline, so the only right
  answer is to withhold the commitment or escalate. This is the failure of
  invented capacity: the group commits to a late plan anyway, or makes up an
  option to close the gap.
- **Disruption.** After the first commitment, only Supplier C is told that its lot is now ready a day later. The others just hear that a change may affect the plan.
  Nothing can arrive on time any more. This is the stale approval: the group
  repeats what it already agreed instead of recomputing.

## 5. Baseline now, L9 skills next

At the moment you only see the baseline scenarios. That means no L9 skills yet.
The agents negotiate in plain natural language and nothing structures the
conversation.

The plan is to add the L9 skills, ACCORD and CONCORD. We hope
they will prevent these failures. This feature is not built yet, and we will present
the results once it is. Then we can run the same requests with and without the skills
and compare them side by side.

## 6. How we test the outcome

The negotiation is not deterministic, but the grading is. When a run ends, you
will see two things.

The first is the **commitment record**: the plan the group committed to, the lots,
the transport, the cost and who confirmed it. It is the agents' own claim.

The second is the **failure card**, the checker's verdict. The checker uses no
model and does not read the conversation. It recomputes from the scenario data
when each lot really arrives, what it costs, and whether any plan could have met
the requirements, then compares that with the record. The result is pass or fail,
with the reasons.

## 7. Closing

That's the use case. (Let's just wait for the final cards.) Any feedback is welcome, or if you notice something unexpected, or having an idea, let us know. Thank you for watching, and follow how the use-case performs.

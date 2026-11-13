# Error analysis and interpretation

The fixed 0.96 cascade solves 2,905/3,080 cases (94.32%), compared with 2,926 (95.00%) for the native retrieval agent. The **0.68 percentage-point accuracy decrease is real in this paired sample**: the bootstrap 95% difference interval is -1.01 to -0.39 points. The one-sided 95% lower bound is -0.94 points, within the predeclared -2-point margin. This supports the stated tradeoff, not a claim of unchanged accuracy. Observed cost falls 58.6%, from $0.010956 to $0.004537 per query.

## What confidence contributes

Jev accepts 1,872 cases (60.78%) at the fixed threshold, with 62 accepted errors (3.31%). On the remaining 1,208 cases, retrieval corrects 301 Jev errors and introduces 22 regressions. Thus the fallback provides substantial net benefit but is not infallible. Twenty matched-coverage random controls average 89.17% accuracy (88.86–89.71% across seeds), compared with 94.32% for confidence selection. The gain is associated with selecting which Jev decisions to accept, rather than acceptance coverage alone.

Among accepted cases, the agent is correct where Jev is wrong on 23 cases; Jev is correct where the agent is wrong on two. One additional accepted disagreement is wrong in both conditions. These 26 disagreements account for the cascade’s net 21-case deficit against the agent.

## Concrete failure modes

- **Short, underspecified requests:** test-00000, “How do I locate my card?”, is labeled card_arrival, but all three models select lost_or_stolen_card. Jev assigns maximum probability 1.0. This illustrates a confidently wrong benchmark decision and an ambiguity that retrieval does not resolve here.
- **Adjacent label boundaries:** test-00011, “How long does a card delivery take?”, is labeled card_arrival, while all models choose card_delivery_estimate. These labels overlap in ordinary language; static canonical names and one exemplar do not fully specify the dataset’s annotation boundaries. This is an interpretation of the observed error, not a change to the evaluator label.
- **A confident error prevents a useful fallback:** test-00072 asks about reactivating a card thought lost. Jev selects lost_or_stolen_card at 0.97; the native agent selects the correct card_linking label. The gate accepts the wrong decision and loses a case that retrieval solves.
- **Retrieval can regress a correct decision:** test-00164 is labeled extra_charge_on_statement. Jev predicts that label at 0.59, escalates, and the agent returns card_payment_fee_charged. This is one of the 22 fallback regressions; escalation must be evaluated against gold, rather than assumed correct.

The largest cascade confusion pairs are declined_transfer → declined_card_payment (9), wrong_exchange_rate_for_cash_withdrawal → cash_withdrawal_charge (7), and card_payment_not_recognised → compromised_card (6). These are semantic/annotation-boundary errors, rather than failed API calls or missing tool outputs: every one of the 9,240 final trajectories completed and passed its output validation.

## Limits on the conclusion

The independent certification error was 34/872 (3.90%), whose one-sided upper bound was **5.157%**. The observed error is below 5%, but the uncertainty exceeds the target. The later test accepted-error upper bound is 4.08%; it is reported descriptively and does not erase the failed pre-test certification. No new threshold was selected. A future calibration change requires a new protocol and fresh validation, not reuse of these test outcomes.

Strong direct classification costs only $0.000592/query and reaches 88.96%. The cascade improves accuracy by 5.36 points but costs about 7.66 times as much. It is therefore useful when near-agent accuracy matters, not the universally cheapest strong-model workflow. Observed cache exposure differs: about 99.1% of direct prompt tokens and 50.1% of agent prompt tokens were cache reads. These are measured batch prices, not cold-request price forecasts.

Excluding 16 normalized support/test overlaps gives cascade accuracy 94.29% and agent accuracy 94.97% on 3,064 cases, leaving the main tradeoff essentially unchanged. Public pretraining contamination and dependence among similar utterances remain limitations. This is one closed-set public dataset, one model pair, and one rollout per example.

Examples and labels are from PolyAI-LDN’s pinned BANKING77 dataset, CC BY 4.0; full IDs, labels, predictions and error rows are in intent_evidence.json. No evaluator labels or these post-test observations were used to modify the frozen experiment.

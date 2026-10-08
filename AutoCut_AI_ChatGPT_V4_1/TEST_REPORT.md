# Auto Cut AI v4.1.0 — offline test report

PASS:
- all CEP JavaScript syntax checks;
- host.jsx lexical syntax after stripping the ExtendScript #target directive;
- CEP XML parse and Premiere host range [15.0,99.9];
- HTML resource/required control validation;
- current Sign in with ChatGPT catalog fixture: models[] / slug / display_name / visibility;
- manual model selection;
- Auto = first server-listed model;
- hidden model filtering;
- non-gpt display model preservation;
- legacy data[] fallback;
- unsupported-model fallback detection;
- no forced 15% language in active UI/pipeline;
- default QUẢNG CÁO + HÁT + LẠC ĐỀ policy;
- religion/sermon teaching-preservation prompt;
- finance preservation profile;
- TXT timestamp parser fixture;
- deterministic C1/C2 cut-plan fixture;
- empty C2 keeps the entire timeline instead of forcing a cut;
- final ZIP integrity.

Not runnable in the build container:
- a real Windows DPAPI round trip inside Premiere CEP;
- a real OAuth + ChatGPT inference turn on the user's account.

The extension performs the DPAPI self-test before OAuth, and the model catalog is fetched at runtime from the signed-in ChatGPT account.

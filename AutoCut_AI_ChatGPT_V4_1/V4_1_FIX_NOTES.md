# Auto Cut AI v4.1.0 — Model + semantic core-cut fix

## Root cause of the HTTP 400

The v4.0.x extension parsed `GET /v1/models` as an ordinary API response using `data[].id`. Sign in with ChatGPT plan usage returns the account model catalog as `models[]` entries with `slug`, `display_name`, and `visibility`.

Because the parser returned an empty list, v4.0.x fell back to a hard-coded `gpt-5.6`. That produced:

`The gpt-5.6 model is not supported when using Codex with a ChatGPT account.`

v4.1.0 removes the hard-coded fallback. It preserves the account catalog ordering, shows `display_name`, sends the selected `slug`, and Auto uses the first listed model. If Auto receives a model-unsupported error, it can try the next account-listed model instead of inventing a model name.

## Editing goal change

The forced 15% target is removed.

Default cuts now follow the supplied Auto Transcript skill:
- QUẢNG CÁO / sponsorship / promotion;
- HÁT / music that does not serve the core content;
- LẠC ĐỀ / banter / unrelated side material.

Repetition / low-value detail is optional and OFF by default. When uncertain, KEEP.

Core preservation profiles:
- Auto detect;
- Religion / sermon: preserve teaching, Bible/doctrine explanation, arguments and necessary examples;
- Finance / investing: preserve analysis, numbers, assumptions, risk and conclusions;
- Education / tutorial;
- Interview / podcast;
- Custom focus text.

The percentage reported after analysis is only the RESULT of the selected cuts, never a target.

# Auto Cut AI v4.2.3 — installer fix

The screenshot reports Robocopy exit code 16 while v4.2.2 is copying the clean package.

v4.2.3 removes Robocopy from the install path. It first copies the package to a unique TEMP staging directory, then runs the installer from that staged copy, deletes the old CEP extension, copies the staged files with XCOPY, and verifies the installed runtime.

This also fixes the edge case where the installer is launched from inside the target CEP extension directory: the source is preserved in TEMP before the destination is deleted.

Verification requires:
- version 4.2.3;
- js/c1Builder.js;
- C1Builder.fromFile(timing.path) in main.js;
- no ChatGPTDirect.stage1(...) call in main.js.

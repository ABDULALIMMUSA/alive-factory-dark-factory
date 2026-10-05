# Evidence copies

These textual evidence files were copied from production and closeout evidence on 2026-10-05. All except `stage-1-shipping.md` and `stage-1-final-windows-error-report.json` preserve the source bytes exactly. The shipping report removes trailing whitespace (spaces, tabs or CR before LF/EOF) only for packaging; its wording and all other bytes are preserved. The Windows error report has 33 CRLF line endings converted to LF in the committed package, with unchanged JSON content. They preserve their original revision, scope, failure history and author attribution. Absolute paths inside them identify original local logs; those logs are not bundled here. These copies supplement the production room export and Git history; they do not replace either. Current closeout model evidence does not prove historical production model selection.

The earlier Stage 2 blocked receipt is historical. The later exact-900 reports record continued independent verification without acceptance or shipment. No supplied-check result proves hidden-test conformance.

| Repository file | SHA256 of packaged bytes |
|---|---|
| [stage-1-factory-receipt.md](stage-1-factory-receipt.md) | `671feb6c5018bac0702bcffb190642b1c09ab915c9f82fb59bd7c922b75a1a42` |
| [stage-1-inspector-accept.md](stage-1-inspector-accept.md) | `4a6adefd100134ddad0781bb77417d13edd1c92375b26002ee85f717ba5a293d` |
| [stage-1-shipping.md](stage-1-shipping.md) | `c88a9764398e668d342373cebb71c2abbecffa1b2fbc9a0d3e8d30f28588182d` |
| [stage-2-blocked-receipt.md](stage-2-blocked-receipt.md) | `e6eeb8711df1d1ac1d66f31de0ff8314a30f6fae2214cfc9da319e36d14bf24a` |
| [stage-2-integrator-900cdce.md](stage-2-integrator-900cdce.md) | `a19c22101be6a075576c9b6c7d4a1a58d73520f364696f624648f9222f7e0e95` |
| [stage-2-pilot-900cdce.md](stage-2-pilot-900cdce.md) | `b52ca83e7c16db59d308fc8335e7e1a8a356de043f7ca73f0a381f73bf59587c` |
| [model-integrator-closeout.md](model-integrator-closeout.md) | `b9ff5c5ddc15997db388d23d4eb162d10722284a33e0519424ac41b0b95ca402` |
| [stage-final-pilot-20261005.md](stage-final-pilot-20261005.md) | `98aac5772c6a9b0a64866bf77b730c9257cec93e162891240224ad6fc80c0643` |
| [stage-1-final-linux-report.json](stage-1-final-linux-report.json) | `08e0b98ae6aa9826c3cb45df98da62909ed173d0aa2b1f09d2ce787df647001f` |
| [stage-2-final-worktree-report.json](stage-2-final-worktree-report.json) | `29a226de4db5ce1097c3dafc6de7845d812dc99a330da9a779c8e7582052f94f` |
| [stage-2-final-lf-report.json](stage-2-final-lf-report.json) | `6bc40bd20edcc4a65e211e3365025fd091aaf01874b55af71b98238deb83b759` |
| [stage-1-final-windows-error-report.json](stage-1-final-windows-error-report.json) | `6ecd30476d26164f0d2176c174d7963b399d54e87a79450f0b45985113851128` |
| [model-foreman-closeout.md](model-foreman-closeout.md) | `aa86b89c3e99eaaf5c7be5d6149682019b3ee3068265d2ebf8c9bd86f41971de` |


Shipping report formatting provenance: original source SHA256 `389be04636fd83a4d247004f310391fa213c2975f971cd374bea9093bd5b00fb`; packaged SHA256 `c88a9764398e668d342373cebb71c2abbecffa1b2fbc9a0d3e8d30f28588182d`. The original source at the catalogue path below remains unchanged. This formatting-adjusted copy is not byte-identical to that source.

Windows error report formatting provenance: original source SHA256 `0052171d0728b08eded5b838f67eb68817ddd2f09e6da8066a290e15e6ee82ca`; committed LF/package SHA256 `6ecd30476d26164f0d2176c174d7963b399d54e87a79450f0b45985113851128`. Candidate `e78cfb7502c16c1d55b57267110b96805edb5b49` normalized 33 CRLF line endings to LF. The original source at the catalogue path below remains unchanged. This second formatting derivative retains the Windows zero-collection error and is not byte-identical to its source.

Original source catalogue:

- `stage-1-factory-receipt.md`: `C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-1-factory-receipt.md`
- `stage-1-inspector-accept.md`: `C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-1-inspector\decision-65a56da.md`
- `stage-1-shipping.md`: `C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-1-shipper-65a56da\report.md`
- `stage-2-blocked-receipt.md`: `C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-2-factory-receipt.md`
- `stage-2-integrator-900cdce.md`: `C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-integrator-stage2-900cdce\report.md`
- `stage-2-pilot-900cdce.md`: `C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-2-test-pilot\run-900cdce-01\report.md`
- `model-integrator-closeout.md`: `C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-integrator-model-declaration.md`
- `stage-final-pilot-20261005.md`: `C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-test-pilot-final-20261005.md`
- `stage-1-final-linux-report.json`: `C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-test-pilot-final-stage1-linux-20261005\report.json`
- `stage-2-final-worktree-report.json`: `C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-test-pilot-final-stage2-linux-20261005\report.json`
- `stage-2-final-lf-report.json`: `C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-test-pilot-final-stage2-lf-20261005\report.json`
- `stage-1-final-windows-error-report.json`: `C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-test-pilot-final-stage1-stock-20261005\report.json`
- `model-foreman-closeout.md`: `C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-foreman-model-declaration.md`

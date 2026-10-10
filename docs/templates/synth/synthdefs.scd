// この曲(プロジェクト)専用の SynthDef。ユーザーが指定した音だけを、ここにゼロから書く。
// 他の曲・リポジトリ共通の音色は流用しない。ユーザーが用意したサンプルを鳴らす場合は PlayBuf 系の SynthDef を書く
// (引数に buf と rate を持たせる。patches.yaml の sample / root_note と組む。docs/synthesis.md)。
// 旋律: |out=0, freq, amp, pan, gate=1, ...|(gate で Env.asr/adsr、doneAction: 2)
// ドラム・ワンショット: gate なしの固定長エンベロープ(doneAction: 2)
[
]

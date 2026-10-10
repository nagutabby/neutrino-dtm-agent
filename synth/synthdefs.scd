// SuperCollider の SynthDef 集。scripts/synth_render.py が読み込み、config/patches.yaml の params(引数の既定値)と対応する。
// 引数名・既定値を変えたら config/patches.yaml も合わせる(tests/test_synth.py が引数名の一致を検査する)。
// 最後の式の値(SynthDef の配列)が load の戻り値になる。
[
// ---- 旋律・低音(gate で鳴り終わりを制御) ----

// 808 ベース: サイン波+ピッチ下降+サチュレーション。glide は音程スライド(mono 時、重なる音で効く)
SynthDef(\sub808, { |out=0, freq=55, amp=0.5, pan=0, gate=1, glide=0.06, pitch_drop=2.0, pitch_time=0.04, decay=1.2, drive=3.0, rel=0.15|
	var f = Lag.kr(freq, glide);
	var pitch = EnvGen.kr(Env([pitch_drop, 1], [pitch_time], \exp));
	var env = EnvGen.kr(Env.asr(0.003, 1, rel), gate, doneAction: 2) * EnvGen.kr(Env([1, 0.001], [decay], \exp));
	var sig = (SinOsc.ar(f * pitch) * drive).tanh * 0.9;
	Out.ar(out, Pan2.ar(sig * env * amp, pan));
}),

// ノコギリ波ベース: ノコギリ+サブ、ローパスのカットオフが閉じていく
SynthDef(\bass_saw, { |out=0, freq=55, amp=0.5, pan=0, gate=1, cutoff=900, env_amt=1500, res=0.3, sub=0.5, atk=0.005, decay=0.25, sus=0.7, rel=0.12|
	var env = EnvGen.kr(Env.adsr(atk, decay, sus, rel), gate, doneAction: 2);
	var fenv = EnvGen.kr(Env([1, 0], [decay * 1.5], \exp));
	var osc = Saw.ar(freq) + (SinOsc.ar(freq * 0.5) * sub);
	var sig = RLPF.ar(osc, (cutoff + (env_amt * fenv)).clip(40, 12000), res.linlin(0, 1, 1, 0.1));
	Out.ar(out, Pan2.ar(sig * env * amp, pan));
}),

// パッド: 4本のデチューンしたノコギリ波+ローパス。ゆっくり立ち上がる
SynthDef(\pad_saw, { |out=0, freq=220, amp=0.3, pan=0, gate=1, detune=0.012, cutoff=1800, res=0.2, atk=0.6, decay=0.5, sus=0.8, rel=1.2|
	var env = EnvGen.kr(Env.adsr(atk, decay, sus, rel), gate, doneAction: 2);
	var osc = Mix.ar(Saw.ar(freq * [1 - detune, 1 - (detune / 3), 1 + (detune / 3), 1 + detune])) * 0.25;
	var sig = RLPF.ar(osc, cutoff.clip(40, 12000), res.linlin(0, 1, 1, 0.1));
	Out.ar(out, Pan2.ar(sig * env * amp, pan));
}),

// エレピ: 2オペレーターの FM(比率 1:1 の変調波でベル状の立ち上がり、減衰でまろやかに)
SynthDef(\epiano, { |out=0, freq=261.6, amp=0.4, pan=0, gate=1, ratio=1.0, index=1.6, index_decay=0.6, tine=0.25, decay=1.8, rel=0.3|
	var env = EnvGen.kr(Env.asr(0.004, 1, rel), gate, doneAction: 2) * EnvGen.kr(Env([1, 0.05], [decay], \exp));
	var mod_env = EnvGen.kr(Env([1, 0.1], [index_decay], \exp));
	var mod = SinOsc.ar(freq * ratio) * freq * index * mod_env;
	var sig = SinOsc.ar(freq + mod) + (SinOsc.ar(freq * 14, 0, tine * EnvGen.kr(Env([1, 0], [0.08], \exp))));
	Out.ar(out, Pan2.ar(sig * env * amp * 0.6, pan));
}),

// リード: パルス波+ローパス+ビブラート
SynthDef(\lead_square, { |out=0, freq=440, amp=0.3, pan=0, gate=1, width=0.5, cutoff=3500, res=0.2, vib_rate=5.5, vib_depth=0.006, vib_delay=0.25, atk=0.01, decay=0.2, sus=0.8, rel=0.2|
	var env = EnvGen.kr(Env.adsr(atk, decay, sus, rel), gate, doneAction: 2);
	var vib = SinOsc.kr(vib_rate) * vib_depth * EnvGen.kr(Env([0, 0, 1], [vib_delay, 0.3]));
	var sig = RLPF.ar(Pulse.ar(freq * (1 + vib), width), cutoff.clip(40, 12000), res.linlin(0, 1, 1, 0.1));
	Out.ar(out, Pan2.ar(sig * env * amp, pan));
}),

// 撥弦: Karplus-Strong(遅延線)。coef が大きいほど高域が早く消える
SynthDef(\pluck, { |out=0, freq=220, amp=0.4, pan=0, gate=1, decay=3.0, coef=0.4, rel=0.15|
	var env = EnvGen.kr(Env.asr(0.001, 1, rel), gate, doneAction: 2);
	var sig = Pluck.ar(PinkNoise.ar(0.6), Impulse.kr(0), 0.2, freq.reciprocal, decay, coef);
	Out.ar(out, Pan2.ar(sig * env * amp, pan));
}),

// ベル/カウベル旋律: 非整数倍の FM で金属的な響き
SynthDef(\bell, { |out=0, freq=660, amp=0.35, pan=0, gate=1, ratio=1.4, index=3.0, decay=0.9, rel=0.1|
	var env = EnvGen.kr(Env.asr(0.001, 1, rel), gate, doneAction: 2) * EnvGen.kr(Env([1, 0.001], [decay], \exp));
	var mod = SinOsc.ar(freq * ratio) * freq * index * EnvGen.kr(Env([1, 0.05], [decay * 0.6], \exp));
	var sig = SinOsc.ar(freq + mod);
	Out.ar(out, Pan2.ar(sig * env * amp * 0.7, pan));
}),

// ---- 効果音(dur = ノートの長さ。synth_render.py が自動で渡す) ----

// ライザー: ノイズのバンドパスが dur かけて低→高へ。音量も上がり、ノート終了で切れる
SynthDef(\riser, { |out=0, freq=200, amp=0.3, pan=0, gate=1, dur=4.0, f_start=300, f_end=8000, res=0.3, rel=0.05|
	var env = EnvGen.kr(Env.asr(0.01, 1, rel), gate, doneAction: 2) * XLine.kr(0.05, 1, dur);
	var sweep = XLine.kr(f_start, f_end, dur);
	var sig = BPF.ar(WhiteNoise.ar, sweep.clip(40, 16000), res.linlin(0, 1, 1, 0.1));
	Out.ar(out, Pan2.ar(sig * env * amp * 2, pan));
}),

// インパクト: 低いサインの落下+ノイズの破裂。固定長
SynthDef(\impact, { |out=0, freq=60, amp=0.6, pan=0, boom=45, decay=2.2, noise=0.5|
	var env = EnvGen.kr(Env([1, 0.001], [decay], \exp), doneAction: 2);
	var pitch = XLine.kr(boom * 3, boom, 0.3);
	var sig = SinOsc.ar(pitch) + (LPF.ar(WhiteNoise.ar, 3000) * noise * EnvGen.kr(Env([1, 0.001], [0.6], \exp)));
	Out.ar(out, Pan2.ar(sig.tanh * env * amp, pan));
}),

// ---- ドラム(固定長の減衰。gate なし) ----

SynthDef(\kick, { |out=0, freq=60, amp=0.8, pan=0, tune=50, start=180, sweep=0.04, decay=0.45, click=0.3, drive=1.5|
	var pitch = XLine.kr(start, tune, sweep);
	var env = EnvGen.kr(Env([1, 0.001], [decay], \exp), doneAction: 2);
	var sig = SinOsc.ar(pitch) + (HPF.ar(WhiteNoise.ar, 2000) * click * EnvGen.kr(Env([1, 0.001], [0.01], \exp)));
	Out.ar(out, Pan2.ar((sig * drive).tanh * env * amp, pan));
}),

SynthDef(\snare, { |out=0, freq=180, amp=0.6, pan=0, tune=185, tone=0.5, snap=0.8, decay=0.2, noise_hp=1500|
	var env = EnvGen.kr(Env([1, 0.001], [decay], \exp), doneAction: 2);
	var body = SinOsc.ar(tune) * tone * EnvGen.kr(Env([1, 0.001], [decay * 0.5], \exp));
	var rattle = HPF.ar(WhiteNoise.ar, noise_hp) * snap;
	Out.ar(out, Pan2.ar((body + rattle) * env * amp, pan));
}),

SynthDef(\clap, { |out=0, freq=1200, amp=0.5, pan=0, tune=1200, decay=0.25, spread=0.012|
	var burst = EnvGen.kr(Env([0, 1, 0, 1, 0, 1, 0.001], [0.001, spread, 0.001, spread, 0.001, decay], [0, 0, 0, 0, 0, -6]), doneAction: 2);
	var sig = BPF.ar(WhiteNoise.ar, tune, 0.6) * 2;
	Out.ar(out, Pan2.ar(sig * burst * amp, pan));
}),

SynthDef(\hat, { |out=0, freq=8000, amp=0.3, pan=0, tune=7000, decay=0.05, tone=0.4|
	var env = EnvGen.kr(Env([1, 0.001], [decay], \exp), doneAction: 2);
	var metal = Mix.ar(Pulse.ar(tune * [1, 1.34, 1.67, 2.12, 2.65, 3.4], 0.5)) * 0.15 * tone;
	var sig = HPF.ar(WhiteNoise.ar * (1 - tone) + metal, tune * 0.8);
	Out.ar(out, Pan2.ar(sig * env * amp, pan));
}),

SynthDef(\tom, { |out=0, freq=120, amp=0.6, pan=0, tune=120, sweep=0.06, decay=0.35|
	var pitch = XLine.kr(tune * 1.6, tune, sweep);
	var env = EnvGen.kr(Env([1, 0.001], [decay], \exp), doneAction: 2);
	Out.ar(out, Pan2.ar(SinOsc.ar(pitch) * env * amp, pan));
}),

SynthDef(\crash, { |out=0, freq=6000, amp=0.3, pan=0, tune=5000, decay=1.8|
	var env = EnvGen.kr(Env([1, 0.001], [decay], \exp), doneAction: 2);
	Out.ar(out, Pan2.ar(HPF.ar(WhiteNoise.ar, tune) * env * amp, pan));
}),

SynthDef(\rim, { |out=0, freq=1700, amp=0.4, pan=0, tune=1700, decay=0.03|
	var env = EnvGen.kr(Env([1, 0.001], [decay], \exp), doneAction: 2);
	var sig = SinOsc.ar(tune) + (HPF.ar(WhiteNoise.ar, 3000) * 0.5);
	Out.ar(out, Pan2.ar(sig * env * amp, pan));
}),

// カウベル: 2本の矩形波(約 540 / 800 Hz)をバンドパス。Phonk の定番
SynthDef(\cowbell, { |out=0, freq=540, amp=0.4, pan=0, tune=540, ratio=1.48, decay=0.35, bp=2400|
	var env = EnvGen.kr(Env([1, 0.001], [decay], \exp), doneAction: 2);
	var sig = BPF.ar(Pulse.ar(tune) + Pulse.ar(tune * ratio), bp, 0.6);
	Out.ar(out, Pan2.ar(sig * env * amp, pan));
})
]

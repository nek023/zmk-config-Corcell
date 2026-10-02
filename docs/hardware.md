# ハードウェア構成

[README](../README.md) に戻る

## 分割構成

- `corcell_r` が split central です。PC やスマホとは右手側が接続します。
- `corcell_l` は split peripheral です。左側の入力を右手側へ転送します。
- キー配線、matrix transform、physical layout、charlieplex kscan は Corchibi 互換です。
- キーの読み取りには割り込みを使います（`INTR` = `P1.13`、左右とも）。
  スリープからの復帰にこの配線が必要です。

## FPC スロット

6 ピンの FPC スロットに、左右それぞれ 1 つずつ入力モジュールを接続できます。
既定は PAW3222 トラックボールです。

| FPC | PAW3222 | XIAO |
|---|---|---|
| 1 | NCS | GND 固定 |
| 2 | SDIO | `P0.09` |
| 3 | SCLK | `P0.10` |
| 4 | MOTION | `P1.12` |
| 5 | VCC | 3V3 |
| 6 | GND | GND |

`P0.09` / `P0.10` は nRF52840 の NFC ピンです。`corcell.dtsi` の
`nfct-pins-as-gpios` で GPIO として使える状態にしています。

NCS は基板上で GND に固定されているため、ファームウェア側で SPI の
chip-select GPIO は設定していません。

## ロータリーエンコーダー

基板上のエンコーダーは `RE_A=P0.04`、`RE_B=P0.05` で、既定で有効です。

## ポインタの設定

- PAW3222 の CPI はファームウェア側で上書きせず、移動量は input processor の
  固定倍率で調整します。カーソルが `zip_xy_scaler 3 4`、スクロールが
  `zip_scroll_scaler 1 24` です。
- `force-awake` は有効にしていません。センサー自身の省電力モードが働きます。
- スリープ時にセンサーを power-down させないよう、ドライバを fork して使っています
  （[yuchamichami/zmk-driver-paw3222](https://github.com/yuchamichami/zmk-driver-paw3222)）。
  復帰は MCU のリセットとして起きるためドライバの復帰処理が走らず、
  NCS が GND 固定だと power-down から戻す手段がないためです。

## 電源

- 単四電池 1 本（左右それぞれ）。昇圧して 3.3V を作ります。
- 電池電圧は ADC0 / `P0.02` で読みます。
- 分圧は `output-ohms = 470k`、`full-ohms = 1M + 470k`。
  1 セル Ni-MH 向けのしきい値で Bluetooth の battery level として報告します。
- ZMK sleep を有効にしています。アイドル 30 秒、ディープスリープ 15 分です。
- USB 給電中はディープスリープに入りません。

## Bluetooth

- 送信出力は +8 dBm です。
- 接続間隔は 15 ms 固定（`PREF_MIN_INT` / `PREF_MAX_INT` とも 12）、latency は 0。
- 2M PHY は無効です。

## 電源投入 LED

電池を入れると XIAO の緑 LED が 2 秒点灯して消えます。組み立て時に、
ペアリングせずに電池と昇圧回路が生きているか確認するためのものです。
点灯後は GPIO を切り離すので、消えたあとの消費電流はありません。

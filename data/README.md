# Example Calibration Data

This folder contains the two example datasets used by the two-stage calibration demo.

```text
cal_150frames_fracdisp_002_divtrans.mat
cal_150frames_fracdisp_005_divtrans.mat
```

Both files have the same structure. The filename indicates the frame-selection settings:

- `fracdisp_002` — 2% fractional displacement
- `fracdisp_005` — 5% fractional displacement
- `divtrans` — diversity based on relative translation

The 2% dataset is used for Stage 1 and the 5% dataset is used for Stage 2.

## Data Organization

Each `.mat` file contains a MATLAB variable named:

```text
cal
```

with two entries:

```text
cal(1,1).data   RF channel data
cal(2,1).data   acquisition and tracking parameters
```

### RF Channel Data

```text
cal(1,1).data
```

has dimensions:

```text
[samples, receive elements, transmit events, frames]
```

For the supplied datasets:

```text
2816 x 64 x 1 x 150
```

The 150 frames are stored as 50 non-overlapping trios in the repeating order:

```text
left, center, right, left, center, right, ...
```

Each trio therefore provides two image comparisons during calibration:

```text
center vs. left
center vs. right
```

The calibration demo uses the first 20 trios, but up to 50 trios are available.

## Acquisition Parameters

The acquisition information required by the beamformer is stored in:

```text
cal(2,1).data
```

The supplied files contain:

| Field | Description |
|---|---|
| `rx_pos` | Receive-element positions, `[64, 3]`, in meters |
| `tx_pos` | Transmit reference position, in meters |
| `t0` | Acquisition timing offset, in samples |
| `fs` | Sampling frequency in Hz |
| `c` | Assumed speed of sound in m/s |
| `f0` | Transmit center frequency in Hz |
| `elevation_focus` | Elevation focal depth in meters |
| `trackingcal` | Tracked tool pose corresponding to each RF frame |


### Element Coordinates

`rx_pos` is organized as:

```text
[number of elements, 3]
```

with columns:

```text
x, y, z
```

in meters.

The supplied receive aperture spans approximately -10.08 mm to +10.08 mm laterally.

## Tracking Data

`trackingcal` contains one tracked tool pose for each saved RF frame.

The calibration code uses:

```text
q0, qx, qy, qz   quaternion orientation
tx, ty, tz        translation
```

Tracking translations are stored in millimeters and converted to meters by `utilities.py` when the homogeneous tracking matrices are constructed.

## Using Another Dataset or Transducer

To apply the calibration method to another tracked ultrasound acquisition, replace the two example `.mat` files with files following the same organization.

The replacement data should provide updated:

```text
RF channel data
receive-element positions
transmit position/geometry
sampling frequency
acquisition timing offset
speed of sound
elevation focus, when applicable
one tracked tool pose per RF frame
```


If a different transmit sequence is used (not 0 degrees plane waves), the corresponding time-of-flight calculation in `beamformer.py` should be updated.

# Image-Based Ultrasound Calibration

This repository provides a minimal implementation of the two-stage image-based spatial calibration method for tracked ultrasound.

The method estimates the rigid transformation between the tracked tool coordinate system and the ultrasound image coordinate system by optimizing image similarity between tracked ultrasound frames.

## Repository Structure

```text
image-based-ultrasound-calibration/
│
├── README.md
├── LICENSE
├── requirements.txt
│
├── code/
│   ├── run_calibration.py
│   ├── beamformer.py
│   └── utilities.py
│
├── data/
│   ├── README.md
│   ├── cal_150frames_fracdisp_002_divtrans.mat
│   └── cal_150frames_fracdisp_005_divtrans.mat
│
├── results/
│   └── README.md
│
└── docs/
    └── data_format.md
```

## Requirements

The demo requires Python 3 and the following packages:

- PyTorch
- NumPy
- SciPy

Install them with:

```bash
pip install torch numpy scipy
```


## Running the Demo

From the repository root, run:

```bash
python code/run_calibration.py
```

The script loads the example datasets from the `data/` folder and saves the calibration results to the `results/` folder.

## Workflow

The implementation is intentionally divided into three small Python scripts.

### `run_calibration.py`

This is the main script and the only file that needs to be executed.

It:

1. Loads the Stage 1 and Stage 2 calibration datasets.
2. Initializes the six calibration parameters:
   ```text
   [rx, ry, rz, tx, ty, tz]
   ```
3. Runs Stage 1 for robust initialization.
4. Uses the final Stage 1 estimate to initialize Stage 2.
5. Constructs the corresponding homogeneous calibration matrices.
6. Saves the calibration parameters, calibration matrices, and optimization loss histories.

The included example uses:

**Stage 1**
- Relative-translation-diversity trio selection
- 2% fractional displacement
- 46–54 mm axial ROI
- 20 trios

**Stage 2**
- Relative-translation-diversity trio selection
- 5% fractional displacement
- 11–19 mm axial ROI
- 20 trios

The optimization settings are defined directly in `run_calibration.py`.

### `beamformer.py`

This file contains the differentiable ultrasound beamforming model.

During initialization it performs calculations that do not depend on the unknown calibration, including:

- acquisition-parameter extraction,
- beamforming-grid construction,
- tracked relative-motion calculation,
- center-frame beamforming.

During each forward pass it:

1. Constructs the current calibration matrix.
2. Transforms the common beamforming grid into the left- and right-frame coordinate systems.
3. Calculates transmit and receive propagation distances.
4. Calculates time of flight.
5. Interpolates the RF channel data.
6. Forms envelope images.
7. Computes the image-similarity loss between the center frame and the left/right frames.

### `utilities.py`

This file contains supporting functions used by the calibration workflow, including:

- tracked-pose conversion to homogeneous transformation matrices,
- calibration-matrix construction,
- linear RF interpolation,
- Hilbert transform,
- 2-D Pearson-correlation loss,
- optimization.

## Output

The calibration result is saved as:

```text
results/result_cal_two_stage.mat
```

The output contains:

- `stage1_last_calib` — Stage 1 calibration parameters
- `stage1_X` — Stage 1 homogeneous calibration matrix
- `stage1_loss` — Stage 1 optimization loss history
- `stage2_final_calib` — final Stage 2 calibration parameters
- `stage2_X` — final Stage 2 homogeneous calibration matrix
- `stage2_loss` — Stage 2 optimization loss history
- `num_trios` — number of trios used

The calibration parameter order is:

```text
[rx, ry, rz, tx, ty, tz]
```

Rotations are represented in degrees and translations in millimeters. The homogeneous calibration matrix is constructed using the rotation convention implemented in `utilities.py`, with translations converted to meters.

## Adapting the Implementation to Another Dataset

The included data provide one reproducible example of the calibration workflow. To use the method with another tracked ultrasound acquisition, the input data must provide the acquisition geometry, RF channel data, and tracked tool poses required by the beamformer.

### Acquisition Parameters

The code uses:

- `rx_pos` — receive-element positions
- `tx_pos` — transmit-element positions
- `fs` — sampling frequency
- `t0` — acquisition start-sample offset
- RF channel data
- tracked tool pose for each frame

Element positions are stored as:

```text
[number of elements, 3]
```

with columns corresponding to:

```text
x, y, z
```

Element positions are expressed in meters.

Tracked poses contain quaternion orientation and translation. In the supplied MATLAB data structure, tracking translations are stored in millimeters and converted to meters by the utility code.

### Transducer-Specific Parameters

When adapting the implementation to another transducer or acquisition sequence, update the appropriate system-specific parameters, including:

- transmit-element positions,
- receive-element positions,
- sampling frequency,
- acquisition timing,
- transmit geometry,
- elevation-focus model,
- assumed speed of sound, if required.

The supplied beamformer contains the transmit and elevation model used for the example acquisition. A different probe or transmit sequence may require modification of the time-of-flight calculation in `beamformer.py`.

### Frame Organization

The example datasets contain saved non-overlapping left-center-right trios:

```text
left, center, right, left, center, right, ...
```

Each trio contributes two image comparisons:

```text
center vs. left
center vs. right
```

The Stage 1 and Stage 2 files contain different trio selections from the same tracked sweep, corresponding to the fractional-displacement criteria used for each optimization stage.

## Data Format

See:

```text
data/README.md
docs/data_format.md
```

for a detailed description of the example `.mat` files, dimensions, coordinate conventions, and units.

## Citation

If you use this implementation, please cite the associated manuscript:

> Citation to be added upon publication.

## License

This project is distributed under the MIT License. See `LICENSE` for details.

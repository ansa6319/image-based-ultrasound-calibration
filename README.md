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
│   ├── parent.py
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

The implementation is divided into three small Python scripts.

### `parent.py`

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

The optimization settings are defined directly in `parent.py`.

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

The included data provide one reproducible example of the calibration workflow. To apply the method to another tracked ultrasound acquisition or transducer, replace the example input data with files containing the required acquisition geometry, RF channel data, and tracked tool poses.

See [`data/README.md`](data/README.md) for the required data structure, dimensions, coordinate conventions, and units.


## Citation

If you use this implementation, please cite the associated manuscript:

> Citation to be added upon publication.

## License

This project is distributed under the MIT License. See `LICENSE` for details.

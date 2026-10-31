# Methodology

## Data Collection

Road images were gathered from publicly available pothole datasets and supplemented
with manually collected photographs.  The final dataset contains 665 images covering
varied road surfaces, lighting conditions, and pothole sizes.

## Annotation

Bounding-box annotations were created in **Pascal VOC XML** format, marking each
visible pothole with a rectangular bounding box.  Annotations were reviewed for
accuracy before conversion.

## Format Conversion

Pascal VOC XML annotations were converted to **YOLO TXT** format using a custom
Python script run in Google Colab.  Each `.txt` file contains one line per bounding
box:

```
<class_id> <x_center> <y_center> <width> <height>
```

All coordinates are normalised to [0, 1] relative to image dimensions.

## Dataset Split

| Split | Images | Instances |
|---|---|---|
| Train | 532 | — |
| Validation | 66 | — |
| Test | 67 | 161 |

The test split was held out throughout training and hyperparameter tuning.

## Training

Models were trained with the Ultralytics YOLO Python API (`model.train()`).
Pretrained COCO weights were used as initialisations.  Ultralytics default
augmentations (mosaic, random flip, colour jitter, scale) were applied.

Training was run on Google Colab with a GPU.  The `best.pt` checkpoint saved
by Ultralytics corresponds to the epoch with the highest validation mAP@50-95.

## Hyperparameters

Ultralytics defaults were used unless otherwise noted.  The primary variable
was inference image size (320, 480, 640, 800, 960) to investigate the
accuracy/speed trade-off.

## Inference Configuration

| Setting | Value |
|---|---|
| Confidence threshold | 0.45 |
| IoU/NMS threshold | 0.45 |
| Image size | 800 (primary), 640 (comparison) |

## Evaluation

Evaluation was performed using `model.val()` on the validation split during
training, and `model.val(split="test")` on the test split after training.

The IoU matching threshold for True Positive classification was **0.50**.

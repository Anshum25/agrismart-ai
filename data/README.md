# Data directory

PlantVillage images are **not** committed to this repository.

## Download options

1. **Kaggle (recommended):** [abdallahalidev/plantvillage-dataset](https://www.kaggle.com/datasets/abdallahalidev/plantvillage-dataset)
2. **Via training script:** `python model/train.py --kaggle-download` (requires `~/.kaggle/kaggle.json`)

## Expected layout

After download, point training at the folder containing one subfolder per class:

```
data/plantvillage/color/
├── Apple___Apple_scab/
├── Apple___Black_rot/
├── ...
└── Tomato___healthy/
```

## Assumption

We use the **color** subset of PlantVillage (not grayscale). If your Kaggle unzip layout differs, pass `--data-dir` explicitly to `model/train.py`.

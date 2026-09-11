"""
AgriSmart AI — ResNet50 transfer-learning training script.

Designed for Google Colab (GPU) with optional Google Drive checkpointing
and Kaggle dataset download.

Usage (Colab):
    !python model/train.py --colab --drive-path /content/drive/MyDrive/AgriSmartAI

Usage (local / Kaggle API):
    python model/train.py --data-dir /path/to/plantvillage/color
    python model/train.py --kaggle-download --output-dir ./data/plantvillage
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import tensorflow as tf
from sklearn.model_selection import train_test_split
from tensorflow.keras import layers, models
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.preprocessing.image import ImageDataGenerator

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from model.config import (
    BATCH_SIZE,
    IMG_SIZE,
    NUM_CLASSES,
    PHASE1_EPOCHS,
    PHASE1_LR,
    PHASE2_EPOCHS,
    PHASE2_LR,
    TEST_RATIO,
    TRAIN_RATIO,
    UNFREEZE_LAST_N_LAYERS,
    VAL_RATIO,
    WEIGHTS_DIR,
)

KAGGLE_DATASET = "abdallahalidev/plantvillage-dataset"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train AgriSmart AI ResNet50 classifier")
    parser.add_argument("--data-dir", type=str, default=None)
    parser.add_argument("--output-dir", type=str, default=str(WEIGHTS_DIR))
    parser.add_argument("--colab", action="store_true")
    parser.add_argument("--drive-path", type=str, default=None)
    parser.add_argument("--kaggle-download", action="store_true")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--phase1-epochs", type=int, default=PHASE1_EPOCHS)
    parser.add_argument("--phase2-epochs", type=int, default=PHASE2_EPOCHS)
    return parser.parse_args()


def setup_colab(drive_path: str | None) -> Path | None:
    try:
        from google.colab import drive  # type: ignore[import-not-found]

        drive.mount("/content/drive")
        if drive_path:
            p = Path(drive_path)
            p.mkdir(parents=True, exist_ok=True)
            print(f"Checkpoints will also sync to: {p}")
            return p
    except ImportError:
        print("Not in Colab — skipping Drive mount.")
    return None


def download_kaggle_dataset(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "kaggle", "datasets", "download", "-d", KAGGLE_DATASET,
        "-p", str(output_dir), "--unzip",
    ]
    print("Downloading dataset:", " ".join(cmd))
    subprocess.run(cmd, check=True)

    candidates = [
        output_dir / "plantvillage dataset" / "color",
        output_dir / "PlantVillage" / "color",
        output_dir / "color",
        output_dir,
    ]
    for candidate in candidates:
        if candidate.is_dir():
            class_dirs = [d for d in candidate.iterdir() if d.is_dir()]
            if len(class_dirs) >= NUM_CLASSES:
                print(f"Using dataset at: {candidate}")
                return candidate
    raise FileNotFoundError(f"Could not locate class folders under {output_dir}")


def discover_images(data_dir: Path) -> tuple[list[str], list[str]]:
    paths: list[str] = []
    labels: list[str] = []
    extensions = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}

    for class_dir in sorted(data_dir.iterdir()):
        if not class_dir.is_dir():
            continue
        label = class_dir.name
        for img_path in class_dir.rglob("*"):
            if img_path.suffix in extensions:
                paths.append(str(img_path))
                labels.append(label)

    if not paths:
        raise ValueError(f"No images found under {data_dir}")
    print(f"Found {len(paths)} images across {len(set(labels))} classes.")
    return paths, labels


def stratified_split(paths, labels):
    train_paths, temp_paths, train_labels, temp_labels = train_test_split(
        paths, labels, test_size=(1.0 - TRAIN_RATIO), stratify=labels, random_state=42,
    )
    relative_val = VAL_RATIO / (VAL_RATIO + TEST_RATIO)
    val_paths, test_paths, val_labels, test_labels = train_test_split(
        temp_paths, temp_labels, test_size=(1.0 - relative_val),
        stratify=temp_labels, random_state=42,
    )
    print(f"Split — train: {len(train_paths)}, val: {len(val_paths)}, test: {len(test_paths)}")
    return train_paths, val_paths, test_paths, train_labels, val_labels, test_labels


def stage_split_folders(work_dir, train_paths, val_paths, test_paths,
                        train_labels, val_labels, test_labels):
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)

    def link_split(name, paths, labels):
        split_root = work_dir / name
        split_root.mkdir()
        for src, label in zip(paths, labels):
            dest_dir = split_root / label
            dest_dir.mkdir(exist_ok=True)
            dest = dest_dir / Path(src).name
            if dest.exists():
                continue
            try:
                os.symlink(src, dest)
            except OSError:
                shutil.copy2(src, dest)
        return split_root

    return (
        link_split("train", train_paths, train_labels),
        link_split("val", val_paths, val_labels),
        link_split("test", test_paths, test_labels),
    )


def build_generators(train_dir, val_dir, test_dir, batch_size):
    train_datagen = ImageDataGenerator(
        preprocessing_function=preprocess_input,
        rotation_range=25,
        width_shift_range=0.1,
        height_shift_range=0.1,
        shear_range=0.1,
        zoom_range=0.15,
        horizontal_flip=True,
        vertical_flip=True,
        brightness_range=(0.8, 1.2),
    )
    eval_datagen = ImageDataGenerator(preprocessing_function=preprocess_input)

    train_gen = train_datagen.flow_from_directory(
        str(train_dir), target_size=IMG_SIZE, batch_size=batch_size,
        class_mode="categorical", shuffle=True,
    )
    val_gen = eval_datagen.flow_from_directory(
        str(val_dir), target_size=IMG_SIZE, batch_size=batch_size,
        class_mode="categorical", shuffle=False,
    )
    test_gen = eval_datagen.flow_from_directory(
        str(test_dir), target_size=IMG_SIZE, batch_size=batch_size,
        class_mode="categorical", shuffle=False,
    )
    return train_gen, val_gen, test_gen


def build_model(num_classes: int) -> tf.keras.Model:
    base = ResNet50(include_top=False, weights="imagenet", input_shape=(*IMG_SIZE, 3))
    base.trainable = False

    inputs = layers.Input(shape=(*IMG_SIZE, 3))
    x = base(inputs, training=False)
    x = layers.GlobalAveragePooling2D(name="gap")(x)
    x = layers.Dense(256, activation="relu", name="head_dense")(x)
    x = layers.Dropout(0.4, name="head_dropout")(x)
    outputs = layers.Dense(num_classes, activation="softmax", name="predictions")(x)
    return models.Model(inputs, outputs, name="agrismart_resnet50")


def make_callbacks(output_dir, drive_dir, phase):
    ckpt_path = output_dir / f"agrismart_resnet50_{phase}.keras"
    callbacks = [
        EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True, verbose=1),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=2, min_lr=1e-7, verbose=1),
        ModelCheckpoint(str(ckpt_path), monitor="val_accuracy", save_best_only=True, verbose=1),
    ]
    if drive_dir:
        callbacks.append(ModelCheckpoint(
            str(drive_dir / f"agrismart_resnet50_{phase}.keras"),
            monitor="val_accuracy", save_best_only=True, verbose=1,
        ))
    return callbacks


def save_class_labels(class_indices, output_dir):
    idx_to_label = {int(v): k for k, v in class_indices.items()}
    labels = [idx_to_label[i] for i in range(len(idx_to_label))]
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "class_labels.json").open("w", encoding="utf-8") as f:
        json.dump({"labels": labels, "class_indices": class_indices}, f, indent=2)


def main() -> None:
    args = parse_args()
    drive_dir = setup_colab(args.drive_path) if args.colab else None
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.kaggle_download:
        data_dir = download_kaggle_dataset(Path("./data/plantvillage"))
    elif args.data_dir:
        data_dir = Path(args.data_dir)
    elif args.colab:
        data_dir = Path("/content/plantvillage/color")
        if not data_dir.exists():
            data_dir = Path("/content/drive/MyDrive/plantvillage/color")
    else:
        data_dir = Path("./data/plantvillage/color")

    if not data_dir.exists():
        raise FileNotFoundError(f"Dataset not found at {data_dir}")

    paths, labels = discover_images(data_dir)
    splits = stratified_split(paths, labels)
    train_dir, val_dir, test_dir = stage_split_folders(
        output_dir / "splits", *splits,
    )

    train_gen, val_gen, test_gen = build_generators(
        train_dir, val_dir, test_dir, args.batch_size,
    )
    save_class_labels(train_gen.class_indices, output_dir)

    model = build_model(train_gen.num_classes)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=PHASE1_LR),
        loss="categorical_crossentropy", metrics=["accuracy"],
    )

    print("\n=== Phase 1: train head (base frozen) ===")
    model.fit(
        train_gen, validation_data=val_gen, epochs=args.phase1_epochs,
        callbacks=make_callbacks(output_dir, drive_dir, "phase1"),
    )

    base_layer = model.layers[1]
    base_layer.trainable = True
    for layer in base_layer.layers[:-UNFREEZE_LAST_N_LAYERS]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=PHASE2_LR),
        loss="categorical_crossentropy", metrics=["accuracy"],
    )

    print(f"\n=== Phase 2: fine-tune last {UNFREEZE_LAST_N_LAYERS} layers ===")
    model.fit(
        train_gen, validation_data=val_gen, epochs=args.phase2_epochs,
        callbacks=make_callbacks(output_dir, drive_dir, "phase2"),
    )

    print("\n=== Test evaluation ===")
    test_loss, test_acc = model.evaluate(test_gen)
    print(f"Test accuracy: {test_acc:.4f} | Test loss: {test_loss:.4f}")

    final_path = output_dir / "agrismart_resnet50.keras"
    model.save(final_path)
    print(f"Saved final model to {final_path}")

    metrics = {"test_accuracy": float(test_acc), "test_loss": float(test_loss)}
    with (output_dir / "training_metrics.json").open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    if drive_dir:
        model.save(drive_dir / "agrismart_resnet50.keras")
        shutil.copy2(output_dir / "class_labels.json", drive_dir / "class_labels.json")


if __name__ == "__main__":
    main()
